"""
Exemplo de uso do serviço de contexto CRM.

Este script demonstra como usar o CRMContextService para gerenciar o contexto
das conversas em uma simulação do CRM.
"""
import os
import sys
import json
import logging
import psycopg2
import redis
from datetime import datetime
from dotenv import load_dotenv

# Adiciona o diretório raiz ao path para importar os módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Carrega as variáveis de ambiente
load_dotenv()

# Configura o logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Importa o serviço de contexto
from src.services.context import CRMContextService

def main():
    """Função principal do exemplo."""
    print("=== Exemplo de uso do serviço de contexto CRM ===")
    
    # Configura a conexão com o banco de dados
    try:
        # Obtém as credenciais do banco de dados das variáveis de ambiente
        db_host = os.getenv("POSTGRES_HOST", "postgres")
        db_port = os.getenv("POSTGRES_PORT", "5432")
        db_name = os.getenv("POSTGRES_DB", "chatwootai")
        db_user = os.getenv("POSTGRES_USER", "postgres")
        db_password = os.getenv("POSTGRES_PASSWORD", "postgres")
        
        print(f"Conectando ao banco de dados: {db_host}:{db_port}/{db_name}")
        
        # Cria a conexão
        db_connection = psycopg2.connect(
            host=db_host,
            port=db_port,
            dbname=db_name,
            user=db_user,
            password=db_password
        )
        
        # Configura o cliente Redis (opcional)
        redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
        redis_client = redis.from_url(redis_url) if redis_url else None
        
        # Inicializa o serviço de contexto
        print("\n1. Inicializando o serviço de contexto CRM...")
        crm_service = CRMContextService(db_connection=db_connection, redis_client=redis_client)
    except Exception as e:
        print(f"Erro ao conectar ao banco de dados: {str(e)}")
        return
    
    # Exemplo de informações de contato
    contact_info = {
        'name': 'Ana Souza',
        'email': 'ana.souza@example.com',
        'phone': '11922223333'
    }
    
    # Busca ou cria um cliente
    print(f"\n2. Buscando ou criando cliente com as informações: {contact_info}")
    customer = crm_service.get_or_create_customer(contact_info)
    print(f"Cliente encontrado/criado: ID={customer['id']}, Nome={customer['name']}")
    
    # ID da conversa (normalmente viria do Chatwoot)
    conversation_id = f"conv_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    print(f"\n3. ID da conversa para teste: {conversation_id}")
    
    # Exemplo de mensagens de conversa
    messages = [
        {
            'role': 'system',
            'content': 'Conversa iniciada',
            'metadata': {'timestamp': datetime.now().isoformat()}
        },
        {
            'role': 'customer',
            'content': 'Olá, gostaria de informações sobre produtos de skincare.',
            'metadata': {'timestamp': datetime.now().isoformat()}
        },
        {
            'role': 'agent',
            'content': 'Olá Ana! Claro, temos várias opções de skincare. Você está procurando algo específico?',
            'metadata': {'timestamp': datetime.now().isoformat()}
        },
        {
            'role': 'customer',
            'content': 'Estou procurando um hidratante para pele seca.',
            'metadata': {'timestamp': datetime.now().isoformat()}
        }
    ]
    
    # Armazena a thread de conversa
    print(f"\n4. Armazenando thread de conversa com {len(messages)} mensagens...")
    success = crm_service.store_conversation_thread(
        customer_id=customer['id'],
        conversation_id=conversation_id,
        messages=messages,
        domain_id='cosmetics'  # Domínio de negócio (opcional)
    )
    
    if success:
        print("Thread de conversa armazenada com sucesso!")
    else:
        print("Erro ao armazenar thread de conversa.")
        return
    
    # Atualiza o contexto da conversa
    print("\n5. Atualizando o contexto da conversa...")
    context_data = {
        'last_product_category': 'skincare',
        'customer_skin_type': 'dry',
        'product_preferences': ['hidratante', 'natural'],
        'conversation_summary': 'Cliente procurando hidratante para pele seca'
    }
    
    success = crm_service.update_conversation_context(
        conversation_id=conversation_id,
        customer_id=customer['id'],
        context_data=context_data
    )
    
    if success:
        print("Contexto da conversa atualizado com sucesso!")
    else:
        print("Erro ao atualizar contexto da conversa.")
        return
    
    # Recupera o contexto da conversa
    print("\n6. Recuperando o contexto da conversa...")
    context = crm_service.get_conversation_context(conversation_id)
    print("Contexto recuperado:")
    print(json.dumps(context, indent=2))
    
    # Recupera o histórico de conversas do cliente
    print(f"\n7. Recuperando histórico de conversas do cliente ID={customer['id']}...")
    history = crm_service.get_customer_conversation_history(customer['id'])
    print(f"Encontradas {len(history)} threads de conversa.")
    
    if history:
        print("\nDetalhes da primeira thread:")
        print(f"ID da thread: {history[0]['id']}")
        print(f"ID da conversa: {history[0]['conversation_id']}")
        print(f"Número de mensagens: {len(history[0]['messages'])}")
        
        print("\nMensagens da conversa:")
        for i, msg in enumerate(history[0]['messages']):
            print(f"[{i+1}] {msg['sender_type']}: {msg['content']}")
    
    print("\n=== Exemplo concluído com sucesso! ===")

if __name__ == "__main__":
    main()
