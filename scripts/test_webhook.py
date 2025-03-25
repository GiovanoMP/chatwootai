#!/usr/bin/env python
"""
Script para testar o webhook do Chatwoot com mensagens simuladas.

Este script simula o envio de webhooks do Chatwoot para o servidor local,
permitindo testar a integração sem precisar de um Chatwoot real.
"""

import os
import sys
import json
import requests
import argparse
from datetime import datetime

# Adiciona o diretório raiz ao path para importar os módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importa o sistema de debug_logger
from src.utils.debug_logger import get_logger

# Configura o logger
logger = get_logger('webhook_test', level='DEBUG')

def create_conversation_webhook(account_id, inbox_id, conversation_id=None, contact_id=None):
    """
    Cria um webhook simulado para o evento conversation_created.
    
    Args:
        account_id: ID da conta no Chatwoot
        inbox_id: ID da caixa de entrada no Chatwoot
        conversation_id: ID da conversa (opcional, será gerado se não fornecido)
        contact_id: ID do contato (opcional, será gerado se não fornecido)
        
    Returns:
        dict: Dados do webhook
    """
    if not conversation_id:
        # Gera um ID de conversa baseado no timestamp atual
        conversation_id = f"test_{int(datetime.now().timestamp())}"
    
    if not contact_id:
        # Gera um ID de contato baseado no timestamp atual
        contact_id = f"contact_{int(datetime.now().timestamp())}"
    
    # Cria o webhook simulado
    webhook_data = {
        "event": "conversation_created",
        "id": conversation_id,
        "account": {
            "id": account_id,
            "name": "Empresa Teste"
        },
        "inbox": {
            "id": inbox_id,
            "name": "WhatsApp"
        },
        "conversation": {
            "id": conversation_id,
            "inbox_id": inbox_id,
            "status": "open",
            "timestamp": datetime.now().isoformat(),
            "contact_last_seen_at": datetime.now().isoformat(),
            "agent_last_seen_at": datetime.now().isoformat(),
            "messages": []
        },
        "contact": {
            "id": contact_id,
            "name": "Cliente Teste",
            "email": "cliente@teste.com",
            "phone_number": "+5511999999999"
        },
        "meta": {
            "sender": {
                "id": contact_id,
                "type": "contact"
            },
            "assignee": None
        }
    }
    
    return webhook_data

def create_message_webhook(account_id, inbox_id, conversation_id, contact_id, message_content):
    """
    Cria um webhook simulado para o evento message_created.
    
    Args:
        account_id: ID da conta no Chatwoot
        inbox_id: ID da caixa de entrada no Chatwoot
        conversation_id: ID da conversa
        contact_id: ID do contato
        message_content: Conteúdo da mensagem
        
    Returns:
        dict: Dados do webhook
    """
    # Cria o webhook simulado
    webhook_data = {
        "event": "message_created",
        "id": f"msg_{int(datetime.now().timestamp())}",
        "account": {
            "id": account_id,
            "name": "Empresa Teste"
        },
        "inbox": {
            "id": inbox_id,
            "name": "WhatsApp"
        },
        "conversation": {
            "id": conversation_id,
            "inbox_id": inbox_id,
            "status": "open",
            "timestamp": datetime.now().isoformat(),
            "contact_last_seen_at": datetime.now().isoformat(),
            "agent_last_seen_at": datetime.now().isoformat()
        },
        "message": {
            "id": f"msg_{int(datetime.now().timestamp())}",
            "content": message_content,
            "message_type": "incoming",
            "content_type": "text",
            "created_at": datetime.now().isoformat(),
            "sender": {
                "id": contact_id,
                "type": "contact"
            }
        },
        "contact": {
            "id": contact_id,
            "name": "Cliente Teste",
            "email": "cliente@teste.com",
            "phone_number": "+5511999999999"
        }
    }
    
    return webhook_data

def send_webhook(webhook_data, webhook_url):
    """
    Envia um webhook para o servidor.
    
    Args:
        webhook_data: Dados do webhook
        webhook_url: URL do servidor webhook
        
    Returns:
        requests.Response: Resposta do servidor
    """
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(webhook_url, json=webhook_data, headers=headers)
        return response
    except Exception as e:
        logger.error(f"Erro ao enviar webhook: {str(e)}")
        return None

def test_conversation_flow(account_id, inbox_id, webhook_url, message):
    """
    Testa o fluxo completo de uma conversa.
    
    Args:
        account_id: ID da conta no Chatwoot
        inbox_id: ID da caixa de entrada no Chatwoot
        webhook_url: URL do servidor webhook
        message: Mensagem a ser enviada
        
    Returns:
        bool: True se o teste foi bem-sucedido, False caso contrário
    """
    logger.info(f"Iniciando teste de fluxo de conversa para account_id={account_id}, inbox_id={inbox_id}")
    
    # Gera IDs para a conversa e o contato
    conversation_id = f"test_{int(datetime.now().timestamp())}"
    contact_id = f"contact_{int(datetime.now().timestamp())}"
    
    # 1. Cria a conversa
    logger.info("Passo 1: Criando conversa...")
    conversation_webhook = create_conversation_webhook(account_id, inbox_id, conversation_id, contact_id)
    conversation_response = send_webhook(conversation_webhook, webhook_url)
    
    if not conversation_response or conversation_response.status_code != 200:
        logger.error(f"Falha ao criar conversa: {conversation_response.text if conversation_response else 'Sem resposta'}")
        return False
    
    logger.info(f"Conversa criada com sucesso: {conversation_id}")
    
    # 2. Envia a mensagem
    logger.info(f"Passo 2: Enviando mensagem: '{message}'...")
    message_webhook = create_message_webhook(account_id, inbox_id, conversation_id, contact_id, message)
    message_response = send_webhook(message_webhook, webhook_url)
    
    if not message_response or message_response.status_code != 200:
        logger.error(f"Falha ao enviar mensagem: {message_response.text if message_response else 'Sem resposta'}")
        return False
    
    logger.info("Mensagem enviada com sucesso")
    logger.info(f"Resposta do servidor: {message_response.text}")
    
    return True

def main():
    """Função principal do script."""
    parser = argparse.ArgumentParser(description='Teste de webhook do Chatwoot')
    parser.add_argument('--account', type=int, required=True, help='ID da conta no Chatwoot')
    parser.add_argument('--inbox', type=int, required=True, help='ID da caixa de entrada no Chatwoot')
    parser.add_argument('--url', type=str, default='http://localhost:8000/webhook', help='URL do servidor webhook')
    parser.add_argument('--message', type=str, default='Olá, gostaria de informações sobre produtos de beleza.', 
                        help='Mensagem a ser enviada')
    
    args = parser.parse_args()
    
    # Executa o teste
    success = test_conversation_flow(args.account, args.inbox, args.url, args.message)
    
    if success:
        logger.info("✅ Teste concluído com sucesso!")
        sys.exit(0)
    else:
        logger.error("❌ Teste falhou!")
        sys.exit(1)

if __name__ == "__main__":
    main()
