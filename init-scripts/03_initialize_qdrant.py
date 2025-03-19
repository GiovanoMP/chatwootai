#!/usr/bin/env python3
"""
Script para inicializar o banco de dados vetorial Qdrant com as regras de negócio
e outras informações relevantes para o sistema ChatwootAI.

Este script cria as coleções necessárias no Qdrant e insere os vetores iniciais
para permitir consultas semânticas sobre regras de negócio, produtos e serviços.
"""

import os
import sys
import time
import json
import psycopg2
from psycopg2.extras import RealDictCursor
import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.http import models
from sentence_transformers import SentenceTransformer

# Configurações
QDRANT_HOST = os.getenv("QDRANT_HOST", "qdrant")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_DB = os.getenv("POSTGRES_DB", "chatwootai")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")

# Modelo para geração de embeddings
MODEL_NAME = "all-MiniLM-L6-v2"  # Modelo leve e eficiente para embeddings

# Caminhos para os arquivos JSON
PRODUCT_DESCRIPTIONS_PATH = "/init-scripts/data/product_descriptions.json"
SERVICE_DESCRIPTIONS_PATH = "/init-scripts/data/service_descriptions.json"
BUSINESS_RULES_PATH = "/init-scripts/data/business_rules.json"

def wait_for_services():
    """Aguarda os serviços estarem disponíveis antes de prosseguir."""
    # Aguarda o Qdrant estar disponível
    qdrant_available = False
    for _ in range(30):  # Tenta por 30 segundos
        try:
            client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
            client.get_collections()
            qdrant_available = True
            print("✅ Qdrant está disponível")
            break
        except Exception as e:
            print(f"Aguardando Qdrant... ({e})")
            time.sleep(1)
    
    if not qdrant_available:
        print("❌ Qdrant não está disponível após 30 tentativas")
        sys.exit(1)
    
    # Aguarda o PostgreSQL estar disponível
    postgres_available = False
    for _ in range(30):  # Tenta por 30 segundos
        try:
            conn = psycopg2.connect(
                host=POSTGRES_HOST,
                port=POSTGRES_PORT,
                dbname=POSTGRES_DB,
                user=POSTGRES_USER,
                password=POSTGRES_PASSWORD
            )
            conn.close()
            postgres_available = True
            print("✅ PostgreSQL está disponível")
            break
        except Exception as e:
            print(f"Aguardando PostgreSQL... ({e})")
            time.sleep(1)
    
    if not postgres_available:
        print("❌ PostgreSQL não está disponível após 30 tentativas")
        sys.exit(1)

def load_json_data(file_path):
    """Carrega dados de um arquivo JSON."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            print(f"✅ Dados carregados do arquivo {file_path}")
            return data
    except Exception as e:
        print(f"❌ Erro ao carregar arquivo {file_path}: {e}")
        return []

def get_model():
    """Carrega o modelo de embeddings."""
    try:
        print(f"Carregando modelo de embeddings: {MODEL_NAME}")
        model = SentenceTransformer(MODEL_NAME)
        print("✅ Modelo de embeddings carregado com sucesso")
        return model
    except Exception as e:
        print(f"❌ Erro ao carregar modelo de embeddings: {e}")
        sys.exit(1)

def create_collections(client):
    """Cria as coleções necessárias no Qdrant."""
    try:
        # Coleção para regras de negócio
        client.recreate_collection(
            collection_name="business_rules",
            vectors_config=models.VectorParams(
                size=384,  # Dimensão do modelo all-MiniLM-L6-v2
                distance=models.Distance.COSINE
            )
        )
        print("✅ Coleção 'business_rules' criada com sucesso")
        
        # Coleção para produtos
        client.recreate_collection(
            collection_name="products",
            vectors_config=models.VectorParams(
                size=384,
                distance=models.Distance.COSINE
            )
        )
        print("✅ Coleção 'products' criada com sucesso")
        
        # Coleção para serviços
        client.recreate_collection(
            collection_name="services",
            vectors_config=models.VectorParams(
                size=384,
                distance=models.Distance.COSINE
            )
        )
        print("✅ Coleção 'services' criada com sucesso")
        
    except Exception as e:
        print(f"❌ Erro ao criar coleções: {e}")
        sys.exit(1)

def get_business_rules_from_db():
    """Obtém as regras de negócio do arquivo JSON ou do banco de dados PostgreSQL."""
    try:
        # Primeiro tentar carregar do arquivo JSON
        if os.path.exists(BUSINESS_RULES_PATH):
            rules = load_json_data(BUSINESS_RULES_PATH)
            if rules:
                print(f"✅ {len(rules)} regras de negócio obtidas do arquivo JSON")
                return rules
        
        # Se não conseguir carregar do JSON, tenta do banco de dados
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            dbname=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            cursor_factory=RealDictCursor
        )
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, name, description, category, rule_text, active
            FROM business_rules
            WHERE active = TRUE
        """)
        
        rules = cursor.fetchall()
        cursor.close()
        conn.close()
        
        print(f"✅ {len(rules)} regras de negócio obtidas do banco de dados")
        return rules
    except Exception as e:
        print(f"❌ Erro ao obter regras de negócio: {e}")
        sys.exit(1)

def get_products_from_db():
    """Obtém os produtos do banco de dados PostgreSQL e combina com informações detalhadas do JSON."""
    try:
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            dbname=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            cursor_factory=RealDictCursor
        )
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT p.id, p.name, p.description, p.price, p.ingredients, 
                   p.benefits, p.usage_instructions, p.detailed_information,
                   pc.name as category_name,
                   COALESCE(i.quantity, 0) as stock_quantity
            FROM products p
            LEFT JOIN product_categories pc ON p.category_id = pc.id
            LEFT JOIN inventory i ON p.id = i.product_id
            WHERE p.active = TRUE
        """)
        
        products = cursor.fetchall()
        
        # Carregar descrições detalhadas do arquivo JSON se existir
        detailed_info = {}
        if os.path.exists(PRODUCT_DESCRIPTIONS_PATH):
            product_descriptions = load_json_data(PRODUCT_DESCRIPTIONS_PATH)
            for desc in product_descriptions:
                detailed_info[desc['name']] = desc['detailed_information']
        
        # Adicionar ou complementar informações detalhadas
        for product in products:
            # Verificar se já tem informação detalhada do banco
            if not product['detailed_information'] and product['name'] in detailed_info:
                product['detailed_information'] = detailed_info[product['name']]
            
            # Obter preços de produtos
            cursor.execute("""
                SELECT price_type, price, start_date, end_date
                FROM product_prices
                WHERE product_id = %s AND active = TRUE
                ORDER BY price_type
            """, (product['id'],))
            
            prices = cursor.fetchall()
            product['prices'] = prices
        
        cursor.close()
        conn.close()
        
        print(f"✅ {len(products)} produtos obtidos do banco de dados")
        return products
    except Exception as e:
        print(f"❌ Erro ao obter produtos: {e}")
        sys.exit(1)

def get_services_from_db():
    """Obtém os serviços do banco de dados PostgreSQL e combina com informações detalhadas do JSON."""
    try:
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            dbname=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            cursor_factory=RealDictCursor
        )
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT s.id, s.name, s.description, s.price, s.duration,
                   s.preparation, s.aftercare, s.contraindications,
                   s.detailed_information,
                   sc.name as category_name
            FROM services s
            LEFT JOIN service_categories sc ON s.category_id = sc.id
            WHERE s.active = TRUE
        """)
        
        services = cursor.fetchall()
        
        # Carregar descrições detalhadas do arquivo JSON se existir
        detailed_info = {}
        if os.path.exists(SERVICE_DESCRIPTIONS_PATH):
            service_descriptions = load_json_data(SERVICE_DESCRIPTIONS_PATH)
            for desc in service_descriptions:
                detailed_info[desc['name']] = desc['detailed_information']
        
        # Adicionar ou complementar informações detalhadas
        for service in services:
            # Verificar se já tem informação detalhada do banco
            if not service['detailed_information'] and service['name'] in detailed_info:
                service['detailed_information'] = detailed_info[service['name']]
            
            # Obter preços de serviços
            cursor.execute("""
                SELECT price_type, price, start_date, end_date
                FROM service_prices
                WHERE service_id = %s AND active = TRUE
                ORDER BY price_type
            """, (service['id'],))
            
            prices = cursor.fetchall()
            service['prices'] = prices
            
            # Obter profissionais que realizam este serviço
            cursor.execute("""
                SELECT p.id, p.first_name, p.last_name, p.specialization
                FROM professionals p
                JOIN professional_services ps ON p.id = ps.professional_id
                WHERE ps.service_id = %s AND p.active = TRUE
            """, (service['id'],))
            
            professionals = cursor.fetchall()
            service['professionals'] = professionals
        
        cursor.close()
        conn.close()
        
        print(f"✅ {len(services)} serviços obtidos do banco de dados")
        return services
    except Exception as e:
        print(f"❌ Erro ao obter serviços: {e}")
        sys.exit(1)

def insert_business_rules(client, model, rules):
    """Insere as regras de negócio no Qdrant."""
    try:
        points = []
        
        for i, rule in enumerate(rules):
            # Preparar o texto para embedding
            text_for_embedding = f"{rule['name']}. {rule['description']}. {rule['rule_text']}"
            
            # Gerar embedding
            embedding = model.encode(text_for_embedding)
            
            # Preparar payload
            payload = {
                "id": rule['id'],
                "name": rule['name'],
                "description": rule['description'],
                "category": rule['category'],
                "rule_text": rule['rule_text'],
                "text_for_search": text_for_embedding
            }
            
            # Adicionar ponto
            points.append(models.PointStruct(
                id=rule['id'],
                vector=embedding.tolist(),
                payload=payload
            ))
        
        # Inserir pontos na coleção
        client.upsert(
            collection_name="business_rules",
            points=points
        )
        
        print(f"✅ {len(points)} regras de negócio inseridas no Qdrant")
    except Exception as e:
        print(f"❌ Erro ao inserir regras de negócio: {e}")
        sys.exit(1)

def insert_products(client, model, products):
    """Insere os produtos no Qdrant."""
    try:
        points = []
        
        for product in products:
            # Preparar o texto para embedding usando informações detalhadas
            text_for_embedding = f"""
                Produto: {product['name']}
                Categoria: {product['category_name']}
                Descrição: {product['description'] or ''}
                Benefícios: {product['benefits'] or ''}
                Ingredientes: {product['ingredients'] or ''}
                Modo de uso: {product['usage_instructions'] or ''}
                Informações detalhadas: {product['detailed_information'] or ''}
            """
            
            # Gerar embedding
            embedding = model.encode(text_for_embedding)
            
            # Preparar payload
            payload = {
                "id": product['id'],
                "name": product['name'],
                "category": product['category_name'],
                "description": product['description'],
                "price": float(product['price']) if product['price'] else 0.0,
                "benefits": product['benefits'],
                "ingredients": product['ingredients'],
                "usage_instructions": product['usage_instructions'],
                "detailed_information": product['detailed_information'],
                "stock_quantity": product['stock_quantity'],
                "prices": [dict(p) for p in product['prices']] if 'prices' in product else [],
                "text_for_search": text_for_embedding
            }
            
            # Adicionar ponto
            points.append(models.PointStruct(
                id=product['id'],
                vector=embedding.tolist(),
                payload=payload
            ))
        
        # Inserir pontos na coleção
        client.upsert(
            collection_name="products",
            points=points
        )
        
        print(f"✅ {len(points)} produtos inseridos no Qdrant")
    except Exception as e:
        print(f"❌ Erro ao inserir produtos: {e}")
        sys.exit(1)

def insert_services(client, model, services):
    """Insere os serviços no Qdrant."""
    try:
        points = []
        
        for service in services:
            # Preparar o texto para embedding usando informações detalhadas
            professionals_text = ""
            if service['professionals']:
                professionals_text = "Profissionais: "
                for prof in service['professionals']:
                    professionals_text += f"{prof['first_name']} {prof['last_name']} ({prof['specialization']}), "
            
            text_for_embedding = f"""
                Serviço: {service['name']}
                Categoria: {service['category_name']}
                Descrição: {service['description'] or ''}
                Duração: {service['duration']} minutos
                Preparação: {service['preparation'] or ''}
                Cuidados pós-procedimento: {service['aftercare'] or ''}
                Contraindicações: {service['contraindications'] or ''}
                {professionals_text}
                Informações detalhadas: {service['detailed_information'] or ''}
            """
            
            # Gerar embedding
            embedding = model.encode(text_for_embedding)
            
            # Preparar payload
            payload = {
                "id": service['id'],
                "name": service['name'],
                "category": service['category_name'],
                "description": service['description'],
                "price": float(service['price']) if service['price'] else 0.0,
                "duration": service['duration'],
                "preparation": service['preparation'],
                "aftercare": service['aftercare'],
                "contraindications": service['contraindications'],
                "detailed_information": service['detailed_information'],
                "professionals": [dict(p) for p in service['professionals']],
                "prices": [dict(p) for p in service['prices']] if 'prices' in service else [],
                "text_for_search": text_for_embedding
            }
            
            # Adicionar ponto
            points.append(models.PointStruct(
                id=service['id'],
                vector=embedding.tolist(),
                payload=payload
            ))
        
        # Inserir pontos na coleção
        client.upsert(
            collection_name="services",
            points=points
        )
        
        print(f"✅ {len(points)} serviços inseridos no Qdrant")
    except Exception as e:
        print(f"❌ Erro ao inserir serviços: {e}")
        sys.exit(1)

def main():
    """Função principal do script."""
    print("🚀 Iniciando inicialização do Qdrant")
    
    # Aguardar serviços estarem disponíveis
    wait_for_services()
    
    # Carregar modelo de embeddings
    model = get_model()
    
    # Conectar ao Qdrant
    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    
    # Criar coleções
    create_collections(client)
    
    # Obter dados do PostgreSQL
    business_rules = get_business_rules_from_db()
    products = get_products_from_db()
    services = get_services_from_db()
    
    # Inserir dados no Qdrant
    insert_business_rules(client, model, business_rules)
    insert_products(client, model, products)
    insert_services(client, model, services)
    
    print("✅ Inicialização do Qdrant concluída com sucesso!")

if __name__ == "__main__":
    main()
