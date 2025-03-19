#!/usr/bin/env python
"""
Script para simular eventos de webhook do Chatwoot.

Este script permite simular diferentes tipos de eventos de webhook
que seriam enviados pelo Chatwoot, facilitando o teste do sistema
sem depender de uma instância real do Chatwoot.
"""

import os
import sys
import json
import logging
import requests
import argparse
from dotenv import load_dotenv
from datetime import datetime

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Adiciona o diretório raiz ao path para importar os módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

# Tipos de eventos suportados pelo webhook do Chatwoot
EVENT_TYPES = [
    "message_created",
    "conversation_created",
    "conversation_status_changed",
    "contact_created",
    "contact_updated"
]

def generate_webhook_payload(event_type, content=None, **kwargs):
    """
    Gera um payload de webhook do Chatwoot para o tipo de evento especificado.
    
    Args:
        event_type: Tipo de evento (message_created, conversation_created, etc.)
        content: Conteúdo da mensagem (para message_created)
        **kwargs: Parâmetros adicionais específicos para cada tipo de evento
        
    Returns:
        Dict: Payload do webhook no formato esperado pelo servidor
    """
    # Base do payload
    payload = {
        "event": event_type,
        "account": {
            "id": kwargs.get("account_id", 1),
            "name": "Conta de Teste"
        }
    }
    
    # Timestamp padrão (agora)
    now = datetime.now().isoformat()
    
    # Específico para cada tipo de evento
    if event_type == "message_created":
        payload["message"] = {
            "id": kwargs.get("message_id", 12345),
            "content": content or "Olá, gostaria de saber mais sobre os produtos",
            "message_type": kwargs.get("message_type", 1),  # 1 para mensagem de entrada (do cliente)
            "created_at": kwargs.get("created_at", now),
            "conversation": {
                "id": kwargs.get("conversation_id", 6789),
                "inbox_id": kwargs.get("inbox_id", 1)
            },
            "sender": {
                "id": kwargs.get("sender_id", 4321),
                "name": kwargs.get("sender_name", "Cliente Teste"),
                "email": kwargs.get("sender_email", "cliente@teste.com"),
                "phone_number": kwargs.get("sender_phone", "+5511999999999"),
                "account_id": kwargs.get("account_id", 1)
            }
        }
    
    elif event_type == "conversation_created":
        payload["conversation"] = {
            "id": kwargs.get("conversation_id", 6789),
            "inbox_id": kwargs.get("inbox_id", 1),
            "status": "open",
            "created_at": kwargs.get("created_at", now),
            "contact": {
                "id": kwargs.get("contact_id", 4321),
                "name": kwargs.get("contact_name", "Cliente Teste"),
                "email": kwargs.get("contact_email", "cliente@teste.com"),
                "phone_number": kwargs.get("contact_phone", "+5511999999999"),
                "account_id": kwargs.get("account_id", 1)
            }
        }
    
    elif event_type == "conversation_status_changed":
        payload["conversation"] = {
            "id": kwargs.get("conversation_id", 6789),
            "inbox_id": kwargs.get("inbox_id", 1),
            "status": kwargs.get("status", "resolved"),
            "created_at": kwargs.get("created_at", now),
            "contact": {
                "id": kwargs.get("contact_id", 4321),
                "name": kwargs.get("contact_name", "Cliente Teste"),
                "account_id": kwargs.get("account_id", 1)
            }
        }
    
    return payload

def send_webhook(webhook_url, payload, api_token=None):
    """
    Envia um payload de webhook para o servidor.
    
    Args:
        webhook_url: URL do webhook
        payload: Payload a ser enviado
        api_token: Token de API para autenticação (opcional)
        
    Returns:
        Response: Resposta do servidor
    """
    headers = {
        "Content-Type": "application/json"
    }
    
    if api_token:
        headers["api_access_token"] = api_token
    
    logger.info(f"Enviando webhook para {webhook_url}")
    logger.debug(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(webhook_url, json=payload, headers=headers)
        response.raise_for_status()
        
        logger.info(f"Webhook enviado com sucesso: {response.status_code}")
        if response.content:
            logger.info(f"Resposta: {response.text}")
        
        return response
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Erro ao enviar webhook: {e}")
        if hasattr(e, 'response') and e.response:
            logger.error(f"Status Code: {e.response.status_code}")
            logger.error(f"Resposta: {e.response.text}")
        return None

def simulate_conversation(webhook_url, api_token=None):
    """
    Simula uma conversa completa, enviando vários webhooks em sequência.
    
    Args:
        webhook_url: URL do webhook
        api_token: Token de API para autenticação (opcional)
    """
    # Definir IDs consistentes para a simulação
    account_id = 1
    conversation_id = 6789
    inbox_id = 1
    contact_id = 4321
    contact_name = "Maria Silva"
    contact_phone = "+5511987654321"
    
    logger.info("Iniciando simulação de conversa...")
    
    # 1. Criar nova conversa
    conversation_payload = generate_webhook_payload(
        "conversation_created",
        account_id=account_id,
        conversation_id=conversation_id,
        inbox_id=inbox_id,
        contact_id=contact_id,
        contact_name=contact_name,
        contact_phone=contact_phone
    )
    send_webhook(webhook_url, conversation_payload, api_token)
    
    # 2. Primeira mensagem do cliente
    message1_payload = generate_webhook_payload(
        "message_created",
        content="Olá! Estou procurando um hidratante para pele oleosa. Vocês têm alguma recomendação?",
        account_id=account_id,
        conversation_id=conversation_id,
        inbox_id=inbox_id,
        sender_id=contact_id,
        sender_name=contact_name,
        sender_phone=contact_phone
    )
    send_webhook(webhook_url, message1_payload, api_token)
    
    # 3. Segunda mensagem do cliente (depois de receber a resposta)
    message2_payload = generate_webhook_payload(
        "message_created",
        content="Quais são os preços desses produtos?",
        account_id=account_id,
        conversation_id=conversation_id,
        inbox_id=inbox_id,
        sender_id=contact_id,
        sender_name=contact_name,
        sender_phone=contact_phone
    )
    send_webhook(webhook_url, message2_payload, api_token)
    
    # 4. Terceira mensagem do cliente
    message3_payload = generate_webhook_payload(
        "message_created",
        content="Vocês entregam em São Paulo?",
        account_id=account_id,
        conversation_id=conversation_id,
        inbox_id=inbox_id,
        sender_id=contact_id,
        sender_name=contact_name,
        sender_phone=contact_phone
    )
    send_webhook(webhook_url, message3_payload, api_token)
    
    # 5. Finalização da conversa
    closing_payload = generate_webhook_payload(
        "conversation_status_changed",
        status="resolved",
        account_id=account_id,
        conversation_id=conversation_id,
        inbox_id=inbox_id,
        contact_id=contact_id,
        contact_name=contact_name
    )
    send_webhook(webhook_url, closing_payload, api_token)
    
    logger.info("Simulação de conversa completa!")

def main():
    """Função principal do script."""
    parser = argparse.ArgumentParser(description="Simulador de webhook do Chatwoot")
    
    # Grupos de argumentos
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--single", action="store_true", help="Enviar um único webhook")
    group.add_argument("--conversation", action="store_true", help="Simular uma conversa completa")
    
    # Argumentos para webhook único
    parser.add_argument("--event", choices=EVENT_TYPES, help="Tipo de evento do webhook")
    parser.add_argument("--content", help="Conteúdo da mensagem (para message_created)")
    
    # Argumentos para URL e autenticação
    parser.add_argument("--url", help="URL do webhook")
    parser.add_argument("--token", help="Token de API para autenticação (opcional)")
    
    args = parser.parse_args()
    
    # Determinar URL do webhook
    webhook_url = args.url
    if not webhook_url:
        webhook_domain = os.getenv("WEBHOOK_DOMAIN", "localhost")
        webhook_port = os.getenv("WEBHOOK_PORT", "8001")
        use_https = os.getenv("WEBHOOK_USE_HTTPS", "false").lower() == "true"
        
        protocol = "https" if use_https else "http"
        port_str = f":{webhook_port}" if (not use_https and webhook_port != "80") or (use_https and webhook_port != "443") else ""
        
        webhook_url = f"{protocol}://{webhook_domain}{port_str}/webhook"
    
    # Obter token de API
    api_token = args.token or os.getenv("CHATWOOT_API_KEY")
    
    if args.single:
        if not args.event:
            parser.error("--event é obrigatório quando --single é usado")
        
        # Enviar webhook único
        payload = generate_webhook_payload(args.event, args.content)
        send_webhook(webhook_url, payload, api_token)
    
    elif args.conversation:
        # Simular conversa completa
        simulate_conversation(webhook_url, api_token)

if __name__ == "__main__":
    main()
