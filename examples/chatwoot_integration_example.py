"""
Exemplo de integração com o Chatwoot.

Este script demonstra como integrar o sistema com o Chatwoot,
monitorando conversas e respondendo a mensagens.
"""

import os
import time
import logging
import argparse
from dotenv import load_dotenv

from src.api.chatwoot_client import ChatwootClient
from src.services.chatwoot_monitor import ChatwootMonitor, ChatwootResponseHandler
from src.services.context import CRMContextService

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Carrega variáveis de ambiente
load_dotenv()

def get_env_or_exit(var_name):
    """Obtém uma variável de ambiente ou encerra o script."""
    value = os.getenv(var_name)
    if not value:
        logger.error(f"Variável de ambiente {var_name} não definida")
        exit(1)
    return value

def message_handler(message_data):
    """
    Função de exemplo para processar mensagens do Chatwoot.
    
    Args:
        message_data: Dados da mensagem com contexto
    """
    message = message_data.get('message', {})
    context = message_data.get('context', {})
    
    conversation_id = context.get('conversation', {}).get('id')
    contact = context.get('contact', {})
    content = message.get('content', '')
    
    logger.info(f"Nova mensagem de {contact.get('name', 'Desconhecido')}: {content}")
    
    # Aqui você integraria com o sistema de agentes da CrewAI
    # Por enquanto, apenas enviamos uma resposta de exemplo
    
    # Obtém ou cria o cliente no CRM
    contact_info = {
        'name': contact.get('name', 'Cliente'),
        'email': contact.get('email'),
        'phone': contact.get('phone_number')
    }
    
    try:
        # Armazena o contexto da conversa no CRM
        customer = crm_context.get_or_create_customer(contact_info)
        
        # Armazena a thread da conversa
        messages = [
            {
                'role': 'user',
                'content': content
            }
        ]
        
        crm_context.store_conversation_thread(
            customer_id=customer['id'],
            conversation_id=conversation_id,
            messages=messages
        )
        
        # Gera uma resposta simples
        response_text = f"Olá! Recebemos sua mensagem: '{content}'. Um agente irá atendê-lo em breve."
        
        # Envia a resposta
        response_handler.send_response(conversation_id, response_text)
        
        # Adiciona etiquetas para classificação
        response_handler.add_labels(conversation_id, ['automatico', 'em_processamento'])
        
    except Exception as e:
        logger.error(f"Erro ao processar mensagem: {e}")
        # Em caso de erro, envia uma mensagem genérica
        response_handler.send_response(
            conversation_id, 
            "Desculpe, tivemos um problema ao processar sua mensagem. Um agente humano irá atendê-lo em breve."
        )

def main():
    """Função principal."""
    parser = argparse.ArgumentParser(description='Exemplo de integração com o Chatwoot')
    parser.add_argument('--poll-interval', type=int, default=30,
                        help='Intervalo de polling em segundos')
    parser.add_argument('--inbox-id', type=int, default=None,
                        help='ID da inbox para monitorar (opcional)')
    args = parser.parse_args()
    
    # Obtém variáveis de ambiente necessárias
    chatwoot_base_url = get_env_or_exit('CHATWOOT_BASE_URL')
    chatwoot_api_key = get_env_or_exit('CHATWOOT_API_KEY')
    chatwoot_account_id = int(get_env_or_exit('CHATWOOT_ACCOUNT_ID'))
    
    # Inicializa o cliente do Chatwoot
    chatwoot_client = ChatwootClient(
        base_url=chatwoot_base_url,
        api_key=chatwoot_api_key
    )
    
    # Inicializa o manipulador de respostas
    global response_handler
    response_handler = ChatwootResponseHandler(
        chatwoot_client=chatwoot_client,
        account_id=chatwoot_account_id
    )
    
    # Inicializa o serviço de contexto do CRM
    global crm_context
    crm_context = CRMContextService()
    
    # Inicializa e inicia o monitor de conversas
    monitor = ChatwootMonitor(
        chatwoot_client=chatwoot_client,
        account_id=chatwoot_account_id,
        message_handler=message_handler,
        poll_interval=args.poll_interval,
        inbox_id=args.inbox_id
    )
    
    try:
        logger.info("Iniciando monitoramento de conversas do Chatwoot...")
        monitor.start()
        
        # Mantém o script em execução
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Encerrando monitoramento...")
        monitor.stop()
        logger.info("Monitoramento encerrado")

if __name__ == "__main__":
    main()
