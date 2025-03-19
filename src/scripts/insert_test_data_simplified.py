#!/usr/bin/env python3
"""
Insert test data script - Versão simplificada para inserir dados de teste para o sistema.
"""
import os
import sys
import logging
import random
from datetime import datetime, timedelta
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_connection():
    """
    Cria uma conexão com o banco de dados PostgreSQL.
    
    Returns:
        Conexão com PostgreSQL.
    """
    # Carregar variáveis de ambiente
    env_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
    load_dotenv(env_path)
    print(f"Carregando variáveis de ambiente de: {env_path}")
    
    conn_params = {
        'host': os.environ.get('POSTGRES_HOST', 'localhost'),
        'port': os.environ.get('POSTGRES_PORT', '5433'),
        'user': os.environ.get('POSTGRES_USER', 'postgres'),
        'password': os.environ.get('POSTGRES_PASSWORD', 'postgres'),
        'database': os.environ.get('POSTGRES_DB', 'chatwootai')
    }
    
    print(f"Conectando ao PostgreSQL: {conn_params['host']}:{conn_params['port']}/{conn_params['database']}")
    
    # Conectar ao banco de dados
    conn = psycopg2.connect(**conn_params)
    conn.autocommit = True  # Importante para evitar transações abertas
    return conn

def insert_product_descriptions():
    """
    Atualiza as descrições detalhadas dos produtos.
    
    Returns:
        bool: True se bem-sucedido, False caso contrário.
    """
    print("\n### Atualizando descrições de produtos ###")
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # Verificar se a coluna existe
    cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'products' 
        AND column_name = 'detailed_description';
    """)
    
    if not cursor.fetchone():
        print("Coluna 'detailed_description' não existe. Criando...")
        cursor.execute("""
            ALTER TABLE products 
            ADD COLUMN detailed_description TEXT;
        """)
        print("✅ Coluna 'detailed_description' adicionada.")
    
    # Obter produtos existentes
    cursor.execute("SELECT id, name FROM products ORDER BY id LIMIT 10")
    products = cursor.fetchall()
    
    if not products:
        print("⚠️ Nenhum produto encontrado para atualizar.")
        conn.close()
        return False
    
    descrições = [
        "Este produto é perfeito para peles sensíveis. Sua fórmula suave limpa profundamente sem ressecar a pele.",
        "Ideal para todos os tipos de pele, este produto hidrata intensamente e protege contra os danos do sol.",
        "Com fórmula exclusiva, este produto combate os sinais de envelhecimento e melhora a elasticidade da pele.",
        "Desenvolvido com ingredientes naturais, este produto nutre a pele e proporciona uma sensação de frescor.",
        "Este produto é essencial para quem busca uma rotina de cuidados completa, pois limpa e hidrata ao mesmo tempo.",
        "Com textura leve e de rápida absorção, este produto é perfeito para uso diário em qualquer estação do ano.",
        "Este produto contém vitaminas essenciais para a saúde da pele, garantindo um aspecto saudável e radiante.",
        "Indicado para peles oleosas, este produto controla a oleosidade sem ressecar, equilibrando a produção de sebo.",
        "Com ação antioxidante, este produto protege a pele contra os radicais livres e previne o envelhecimento precoce.",
        "Este produto possui fórmula hipoalergênica, perfeita para peles sensíveis e propensas a alergias."
    ]
    
    produtos_atualizados = 0
    
    for i, product in enumerate(products):
        try:
            product_id = product['id']
            description = descrições[i % len(descrições)]
            
            # Atualizar descrição detalhada
            cursor.execute(
                "UPDATE products SET detailed_description = %s WHERE id = %s",
                (description, product_id)
            )
            produtos_atualizados += 1
            print(f"✅ Produto ID {product_id} ({product['name']}) atualizado com sucesso")
        except Exception as e:
            print(f"❌ Erro ao atualizar produto ID {product_id}: {str(e)}")
    
    conn.close()
    print(f"\nTotal de produtos atualizados: {produtos_atualizados}")
    return produtos_atualizados > 0

def insert_conversation_contexts():
    """
    Insere dados de teste para contextos de conversa.
    
    Returns:
        bool: True se bem-sucedido, False caso contrário.
    """
    print("\n### Inserindo dados de teste para contextos de conversa ###")
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # Verificar se a tabela existe
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_name = 'conversation_contexts';
    """)
    
    if not cursor.fetchone():
        print("❌ Tabela 'conversation_contexts' não existe.")
        conn.close()
        return False
    
    # Verificar se já existem contextos de conversa
    cursor.execute("SELECT COUNT(*) as count FROM conversation_contexts")
    result = cursor.fetchone()
    
    if result and result['count'] > 0:
        print(f"⚠️ Já existem {result['count']} contextos de conversa. Pulando inserção.")
        conn.close()
        return True
    
    # Obter ids de clientes existentes
    cursor.execute("SELECT id FROM customers ORDER BY RANDOM() LIMIT 5")
    customers = cursor.fetchall()
    
    if not customers:
        print("❌ Nenhum cliente encontrado para criar contextos de conversa")
        conn.close()
        return False
    
    status_options = ['active', 'resolved', 'pending']
    agent_ids = ['agent_001', 'agent_002', 'agent_003', 'agent_004', 'agent_005']
    
    contexts_created = 0
    messages_created = 0
    variables_created = 0
    
    for customer in customers:
        try:
            customer_id = customer['id']
            conversation_id = f"conv_{customer_id}_{int(datetime.now().timestamp())}"
            status = random.choice(status_options)
            agent_id = random.choice(agent_ids)
            created_at = datetime.now() - timedelta(days=random.randint(1, 30))
            updated_at = created_at + timedelta(hours=random.randint(1, 48))
            
            metadata = {
                'source': random.choice(['whatsapp', 'facebook', 'instagram', 'web']),
                'channel': random.choice(['messaging', 'chat', 'direct']),
                'priority': random.choice(['low', 'medium', 'high']),
                'tags': random.sample(['atendimento', 'vendas', 'suporte', 'informações', 'reclamação'], k=random.randint(1, 3))
            }
            
            # Inserir contexto
            cursor.execute(
                """
                INSERT INTO conversation_contexts 
                (conversation_id, customer_id, agent_id, status, metadata, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (conversation_id, customer_id, agent_id, status, json.dumps(metadata), created_at, updated_at)
            )
            contexts_created += 1
            
            # Criar algumas mensagens para a conversa
            num_messages = random.randint(3, 10)
            message_time = created_at
            
            customer_messages = [
                "Olá, gostaria de informações sobre produtos para pele sensível",
                "Tenho alergia a alguns componentes, vocês podem me ajudar?",
                "Quais são os ingredientes desse produto?",
                "Esse produto é testado em animais?",
                "Qual o prazo de entrega para minha região?",
                "Vocês têm amostras grátis?",
                "Esse produto serve para pele oleosa?",
                "Posso usar este produto durante o dia?",
                "Quanto custa o frete?",
                "Vocês têm alguma promoção neste momento?"
            ]
            
            agent_messages = [
                "Olá! Como posso ajudar você hoje?",
                "Claro, posso te ajudar com informações sobre nossos produtos.",
                "Vou verificar essa informação para você.",
                "Este produto é hipoalergênico e não contém parabenos.",
                "Não fazemos testes em animais em nenhuma etapa de produção.",
                "O prazo de entrega para sua região é de 3 a 5 dias úteis.",
                "Sim, temos amostras grátis em compras acima de R$ 150,00.",
                "Este produto é ideal para peles oleosas, pois controla a oleosidade.",
                "O frete é grátis para compras acima de R$ 200,00.",
                "Sim, temos uma promoção de 20% de desconto em todos os produtos da linha facial."
            ]
            
            for i in range(num_messages):
                is_customer = i % 2 == 0
                sender_id = str(customer_id) if is_customer else agent_id
                sender_type = 'customer' if is_customer else 'agent'
                content = random.choice(customer_messages if is_customer else agent_messages)
                
                message_time += timedelta(minutes=random.randint(1, 15))
                
                cursor.execute(
                    """
                    INSERT INTO conversation_messages
                    (conversation_id, sender_id, sender_type, content, metadata, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        conversation_id, 
                        sender_id, 
                        sender_type, 
                        content, 
                        json.dumps({'read': True, 'source_device': 'mobile' if is_customer else 'web'}), 
                        message_time
                    )
                )
                messages_created += 1
            
            # Adicionar algumas variáveis de contexto
            variable_keys = ['last_product_viewed', 'cart_value', 'preferred_payment', 'utm_source', 'last_page_visited']
            variable_values = ['produto-hidratante-facial', '157.90', 'credit_card', 'google', '/produtos/pele']
            
            for i in range(min(len(variable_keys), len(variable_values))):
                cursor.execute(
                    """
                    INSERT INTO conversation_variables
                    (conversation_id, variable_key, variable_value, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (conversation_id, variable_keys[i], variable_values[i], created_at, updated_at)
                )
                variables_created += 1
            
            print(f"✅ Contexto de conversa criado para o cliente ID {customer_id} (ID da conversa: {conversation_id})")
            
        except Exception as e:
            print(f"❌ Erro ao criar contexto de conversa para o cliente ID {customer_id}: {str(e)}")
    
    conn.close()
    print(f"\nTotal inserido: {contexts_created} contextos, {messages_created} mensagens, {variables_created} variáveis")
    return contexts_created > 0

def insert_conversation_analytics():
    """
    Insere dados de teste para análise de conversas.
    
    Returns:
        bool: True se bem-sucedido, False caso contrário.
    """
    print("\n### Inserindo dados de teste para análise de conversas ###")
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # Verificar se a tabela existe
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_name = 'conversation_analytics';
    """)
    
    if not cursor.fetchone():
        print("❌ Tabela 'conversation_analytics' não existe.")
        conn.close()
        return False
    
    # Verificar se já existem dados de análise
    cursor.execute("SELECT COUNT(*) as count FROM conversation_analytics")
    result = cursor.fetchone()
    
    if result and result['count'] > 0:
        print(f"⚠️ Já existem {result['count']} análises de conversa. Pulando inserção.")
        conn.close()
        return True
    
    # Obter contextos de conversa
    cursor.execute("""
        SELECT cc.conversation_id, cc.customer_id, COUNT(cm.id) as message_count
        FROM conversation_contexts cc
        JOIN conversation_messages cm ON cc.conversation_id = cm.conversation_id
        GROUP BY cc.conversation_id, cc.customer_id
    """)
    
    contexts = cursor.fetchall()
    
    if not contexts:
        print("❌ Nenhum contexto de conversa encontrado para criar análises")
        conn.close()
        return False
    
    analytics_created = 0
    
    for context in contexts:
        try:
            conversation_id = context['conversation_id']
            customer_id = context['customer_id']
            message_count = context['message_count']
            
            # Gerar dados aleatórios para análise
            sentiment_score = round(random.uniform(-1.0, 1.0), 2)
            
            topics = json.dumps([
                {"name": "produto", "confidence": round(random.uniform(0.7, 0.98), 2)},
                {"name": "preço", "confidence": round(random.uniform(0.6, 0.95), 2)},
                {"name": "entrega", "confidence": round(random.uniform(0.5, 0.9), 2)}
            ])
            
            entities = json.dumps([
                {"type": "product", "name": "hidratante facial", "mentions": random.randint(1, 3)},
                {"type": "brand", "name": "dermacare", "mentions": random.randint(1, 2)},
                {"type": "attribute", "name": "hipoalergênico", "mentions": random.randint(1, 2)}
            ])
            
            key_points = json.dumps([
                "Cliente interessado em produtos para pele sensível",
                "Cliente mencionou preocupação com ingredientes",
                "Cliente perguntou sobre prazos de entrega"
            ])
            
            duration = random.randint(300, 1800)  # duração em segundos (5-30 minutos)
            created_at = datetime.now() - timedelta(hours=random.randint(1, 24))
            
            # Inserir análise
            cursor.execute(
                """
                INSERT INTO conversation_analytics
                (conversation_id, customer_id, sentiment_score, topics, entities, key_points, duration, message_count, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    conversation_id, 
                    customer_id, 
                    sentiment_score, 
                    topics, 
                    entities, 
                    key_points, 
                    duration, 
                    message_count, 
                    created_at, 
                    created_at
                )
            )
            
            analytics_created += 1
            print(f"✅ Análise criada para a conversa ID {conversation_id}")
            
        except Exception as e:
            print(f"❌ Erro ao criar análise para a conversa ID {conversation_id}: {str(e)}")
    
    conn.close()
    print(f"\nTotal de análises criadas: {analytics_created}")
    return analytics_created > 0

def main():
    """
    Função principal que executa a inserção de dados de teste.
    """
    print("\n================================================================================")
    print("INSERÇÃO DE DADOS DE TESTE (VERSÃO SIMPLIFICADA)")
    print("================================================================================\n")
    
    success_count = 0
    
    if insert_product_descriptions():
        success_count += 1
        
    if insert_conversation_contexts():
        success_count += 1
        
    if insert_conversation_analytics():
        success_count += 1
        
    print("\n================================================================================")
    print(f"RESULTADO DA INSERÇÃO: {success_count}/3 categorias de dados inseridas com sucesso")
    print("================================================================================")
    
    return 0 if success_count == 3 else 1

if __name__ == "__main__":
    sys.exit(main())
