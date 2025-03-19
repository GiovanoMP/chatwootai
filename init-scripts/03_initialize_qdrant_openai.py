#!/usr/bin/env python3
"""
Script simplificado de inicialização do Qdrant usando embeddings da OpenAI.

Este script:
1. Conecta ao PostgreSQL para obter dados de produtos e regras de serviço
2. Cria coleções no Qdrant para produtos e regras de serviço
3. Gera embeddings usando a API da OpenAI
4. Insere os embeddings no Qdrant

Uso:
    python3 03_initialize_qdrant_openai.py

Requisitos:
    - Variáveis de ambiente:
        - OPENAI_API_KEY: Chave de API da OpenAI
        - DATABASE_URL: URL de conexão com o PostgreSQL
        - QDRANT_URL: URL do Qdrant (padrão: http://localhost:6333)
    - Pacotes Python:
        - openai
        - psycopg2-binary
        - qdrant-client
"""
import os
import sys
import logging
import time
from typing import List, Dict, Any

import psycopg2
import psycopg2.extras
from qdrant_client import QdrantClient
from qdrant_client.http import models
from openai import OpenAI

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configurações
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    logger.error("OPENAI_API_KEY não definida. Defina esta variável de ambiente.")
    sys.exit(1)

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    logger.error("DATABASE_URL não definida. Defina esta variável de ambiente.")
    sys.exit(1)

QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "text-embedding-3-small")

# Dimensões do embedding para o modelo text-embedding-3-small da OpenAI
EMBEDDING_DIM = 1536

def get_openai_embedding(text: str) -> List[float]:
    """
    Gera um embedding para o texto usando a API da OpenAI.
    
    Args:
        text: Texto para gerar o embedding.
        
    Returns:
        Lista de floats representando o embedding.
    """
    client = OpenAI(api_key=OPENAI_API_KEY)
    
    try:
        response = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"Erro ao gerar embedding: {str(e)}")
        raise

def get_batch_openai_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Gera embeddings para múltiplos textos em uma única chamada de API.
    
    Args:
        texts: Lista de textos para gerar embeddings.
        
    Returns:
        Lista de embeddings.
    """
    client = OpenAI(api_key=OPENAI_API_KEY)
    
    try:
        response = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=texts
        )
        return [item.embedding for item in response.data]
    except Exception as e:
        logger.error(f"Erro ao gerar embeddings em lote: {str(e)}")
        raise

def get_db_connection():
    """
    Estabelece uma conexão com o banco de dados PostgreSQL.
    
    Returns:
        Conexão com o PostgreSQL.
    """
    try:
        return psycopg2.connect(DATABASE_URL)
    except Exception as e:
        logger.error(f"Erro ao conectar ao PostgreSQL: {str(e)}")
        raise

def get_products_from_db() -> List[Dict[str, Any]]:
    """
    Obtém todos os produtos do banco de dados.
    
    Returns:
        Lista de produtos.
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                cursor.execute("""
                    SELECT p.id, p.name, p.description, p.detailed_information,
                           p.price, p.active, pc.name as category_name,
                           COALESCE(i.quantity, 0) as stock
                    FROM products p
                    LEFT JOIN product_categories pc ON p.category_id = pc.id
                    LEFT JOIN inventory i ON p.id = i.product_id
                    WHERE p.active = TRUE
                """)
                return [dict(row) for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"Erro ao obter produtos do PostgreSQL: {str(e)}")
        raise

def get_business_rules_from_db() -> List[Dict[str, Any]]:
    """
    Obtém todas as regras de negócio do banco de dados.
    
    Returns:
        Lista de regras de negócio.
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                cursor.execute("""
                    SELECT id, name as title, description, rule_text as content,
                           category, active
                    FROM business_rules
                    WHERE active = TRUE AND category = 'service'
                """)
                return [dict(row) for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"Erro ao obter regras de negócio do PostgreSQL: {str(e)}")
        raise

def prepare_product_text(product: Dict[str, Any]) -> str:
    """
    Prepara o texto de um produto para geração de embedding.
    
    Args:
        product: Dicionário com os dados do produto.
        
    Returns:
        Texto preparado para geração de embedding.
    """
    text_parts = []
    
    # Adicionar nome e categoria
    text_parts.append(product['name'])
    if product.get('category_name'):
        text_parts.append(f"Categoria: {product['category_name']}")
    
    # Adicionar descrição
    if product.get('description'):
        text_parts.append(product['description'])
        
    # Adicionar informações detalhadas
    if product.get('detailed_information'):
        text_parts.append(product['detailed_information'])
        
    return ". ".join(text_parts)

def prepare_business_rule_text(rule: Dict[str, Any]) -> str:
    """
    Prepara o texto de uma regra de negócio para geração de embedding.
    
    Args:
        rule: Dicionário com os dados da regra de negócio.
        
    Returns:
        Texto preparado para geração de embedding.
    """
    text_parts = []
    
    # Adicionar título e categoria
    text_parts.append(rule['title'])
    if rule.get('category'):
        text_parts.append(f"Categoria: {rule['category']}")
    
    # Adicionar descrição
    if rule.get('description'):
        text_parts.append(rule['description'])
        
    # Adicionar conteúdo detalhado da regra
    if rule.get('content'):
        text_parts.append(rule['content'])
        
    return ". ".join(text_parts)

def initialize_qdrant():
    """
    Inicializa o Qdrant criando coleções e inserindo dados.
    """
    logger.info(f"Conectando ao Qdrant em {QDRANT_URL}")
    qdrant_client = QdrantClient(url=QDRANT_URL)
    
    # Criar coleção para produtos
    try:
        logger.info("Criando coleção 'products' no Qdrant")
        qdrant_client.recreate_collection(
            collection_name="products",
            vectors_config=models.VectorParams(
                size=EMBEDDING_DIM,
                distance=models.Distance.COSINE
            )
        )
        logger.info("Coleção 'products' criada com sucesso")
    except Exception as e:
        logger.error(f"Erro ao criar coleção 'products': {str(e)}")
        raise
    
    # Criar coleção para regras de negócio
    try:
        logger.info("Criando coleção 'business_rules' no Qdrant")
        qdrant_client.recreate_collection(
            collection_name="business_rules",
            vectors_config=models.VectorParams(
                size=EMBEDDING_DIM,
                distance=models.Distance.COSINE
            )
        )
        logger.info("Coleção 'business_rules' criada com sucesso")
    except Exception as e:
        logger.error(f"Erro ao criar coleção 'business_rules': {str(e)}")
        raise
    
    # Obter produtos e regras de negócio do PostgreSQL
    logger.info("Obtendo produtos do PostgreSQL")
    products = get_products_from_db()
    logger.info(f"Obtidos {len(products)} produtos")
    
    logger.info("Obtendo regras de negócio do PostgreSQL")
    business_rules = get_business_rules_from_db()
    logger.info(f"Obtidas {len(business_rules)} regras de negócio")
    
    # Processar produtos em lotes para economizar chamadas de API
    BATCH_SIZE = 50
    
    # Processar produtos
    for i in range(0, len(products), BATCH_SIZE):
        batch = products[i:i+BATCH_SIZE]
        logger.info(f"Processando lote de produtos {i+1} a {i+len(batch)} de {len(products)}")
        
        # Preparar textos para embeddings
        texts = [prepare_product_text(product) for product in batch]
        
        # Gerar embeddings em lote
        logger.info(f"Gerando {len(texts)} embeddings para produtos")
        embeddings = get_batch_openai_embeddings(texts)
        
        # Preparar pontos para o Qdrant
        points = []
        for j, product in enumerate(batch):
            points.append(models.PointStruct(
                id=product['id'],
                vector=embeddings[j],
                payload={
                    "id": product['id'],
                    "name": product['name'],
                    "description": product.get('description', ''),
                    "category": product.get('category_name', ''),
                    "price": float(product['price']) if product.get('price') else None,
                    "stock": product.get('stock', 0),
                    "active": product.get('active', True)
                }
            ))
        
        # Inserir no Qdrant
        logger.info(f"Inserindo {len(points)} produtos no Qdrant")
        qdrant_client.upsert(
            collection_name="products",
            points=points
        )
        
        # Pequena pausa para não sobrecarregar a API
        time.sleep(1)
    
    # Processar regras de negócio
    for i in range(0, len(business_rules), BATCH_SIZE):
        batch = business_rules[i:i+BATCH_SIZE]
        logger.info(f"Processando lote de regras de negócio {i+1} a {i+len(batch)} de {len(business_rules)}")
        
        # Preparar textos para embeddings
        texts = [prepare_business_rule_text(rule) for rule in batch]
        
        # Gerar embeddings em lote
        logger.info(f"Gerando {len(texts)} embeddings para regras de negócio")
        embeddings = get_batch_openai_embeddings(texts)
        
        # Preparar pontos para o Qdrant
        points = []
        for j, rule in enumerate(batch):
            points.append(models.PointStruct(
                id=rule['id'],
                vector=embeddings[j],
                payload={
                    "id": rule['id'],
                    "title": rule['title'],
                    "description": rule.get('description', ''),
                    "content": rule.get('content', ''),
                    "category": rule.get('category', 'service'),
                    "active": rule.get('active', True)
                }
            ))
        
        # Inserir no Qdrant
        logger.info(f"Inserindo {len(points)} regras de negócio no Qdrant")
        qdrant_client.upsert(
            collection_name="business_rules",
            points=points
        )
        
        # Pequena pausa para não sobrecarregar a API
        time.sleep(1)
    
    logger.info("Inicialização do Qdrant concluída com sucesso")

if __name__ == "__main__":
    try:
        initialize_qdrant()
    except Exception as e:
        logger.error(f"Erro durante a inicialização do Qdrant: {str(e)}")
        sys.exit(1)
