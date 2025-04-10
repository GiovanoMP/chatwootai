#!/usr/bin/env python3
"""
Simulador de Webhook do Chatwoot

Este script envia webhooks simulados para o webhook handler do ChatwootAI,
permitindo testar o sistema com diferentes account_ids sem depender do Chatwoot real.
O payload é construído para ser idêntico ao que seria enviado pelo Chatwoot real.
"""

import requests
import json
import time
import logging
import argparse
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

# Adicionar diretório raiz ao path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(Path(__file__).parent.parent.parent / 'logs' / f'{datetime.now().strftime("%Y%m%d")}_webhook_simulator.log')
    ]
)
logger = logging.getLogger("webhook_simulator")

def create_message_created_payload(account_id: int, inbox_id: int = 1, 
                                  conversation_id: int = 1, message: str = "Olá, isso é um teste") -> Dict[str, Any]:
    """
    Cria um payload para o evento message_created do Chatwoot.
    
    Args:
        account_id: ID da conta do Chatwoot
        inbox_id: ID da caixa de entrada
        conversation_id: ID da conversa
        message: Conteúdo da mensagem
        
    Returns:
        Dict[str, Any]: Payload do webhook
    """
    # Gerar IDs únicos
    message_id = int(time.time() * 1000) % 10000
    contact_id = account_id * 100 + inbox_id
    user_id = None  # Mensagem do cliente, não do agente
    
    # Criar dados do contato
    contact_data = {
        "id": contact_id,
        "name": f"Cliente Teste {contact_id}",
        "email": f"cliente{contact_id}@teste.com",
        "phone_number": f"+5511999999{contact_id % 1000:03d}",
        "account_id": account_id,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "additional_attributes": {},
        "custom_attributes": {},
        "identifier": None,
        "thumbnail": "",
        "type": "contact"
    }
    
    # Criar dados da mensagem
    message_data = {
        "id": message_id,
        "content": message,
        "inbox_id": inbox_id,
        "conversation_id": conversation_id,
        "message_type": "incoming",  # Deve ser 'incoming' e não 0
        "content_type": "text",
        "content_attributes": {},
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "private": False,
        "sender_type": "contact",
        "sender_id": contact_id
    }
    
    # Criar dados da conversa
    conversation_data = {
        "id": conversation_id,
        "account_id": account_id,
        "inbox_id": inbox_id,
        "status": "open",
        "assignee_id": None,
        "contact_inbox": {
            "source_id": None
        },
        "contact": contact_data
    }
    
    # Criar payload completo no formato esperado pelo webhook handler
    payload = {
        "event": "message_created",
        "account": {
            "id": account_id
        },
        "message": message_data,
        "conversation": conversation_data,
        "contact": contact_data
    }
    
    return payload

def send_webhook(payload: Dict[str, Any], webhook_url: str = "http://localhost:8001/webhook") -> bool:
    """
    Envia um webhook para o webhook handler.
    
    Args:
        payload: Payload do webhook
        webhook_url: URL do webhook handler
        
    Returns:
        bool: True se o webhook foi enviado com sucesso, False caso contrário
    """
    try:
        # Adicionar headers que o Chatwoot enviaria
        headers = {
            "Content-Type": "application/json",
            "X-Chatwoot-Signature": "simulado",
            "X-Chatwoot-Event": payload.get("event", "message_created")
        }
        
        # Enviar webhook
        response = requests.post(webhook_url, json=payload, headers=headers)
        
        # Verificar resposta
        if response.status_code == 200:
            logger.info(f"Webhook enviado com sucesso: account_id={payload.get('account_id')}, status={response.status_code}")
            return True
        else:
            logger.error(f"Erro ao enviar webhook: status={response.status_code}, resposta={response.text}")
            return False
    except Exception as e:
        logger.error(f"Exceção ao enviar webhook: {e}")
        return False

def test_client_mapping(webhook_url: str = "http://localhost:8000/webhook", 
                        account_ids: List[int] = [1, 2, 3],
                        delay: int = 2) -> None:
    """
    Testa o mapeamento de clientes enviando webhooks para diferentes account_ids.
    
    Args:
        webhook_url: URL do webhook handler
        account_ids: Lista de account_ids para testar
        delay: Atraso entre os webhooks em segundos
    """
    logger.info(f"Iniciando teste de mapeamento de clientes com account_ids: {account_ids}")
    
    for account_id in account_ids:
        # Criar payload
        payload = create_message_created_payload(
            account_id=account_id,
            inbox_id=account_id * 100,
            conversation_id=account_id * 1000,
            message=f"Teste para account_id={account_id}. Por favor, me diga quais produtos vocês têm."
        )
        
        # Enviar webhook
        success = send_webhook(payload, webhook_url)
        
        if success:
            logger.info(f"Webhook para account_id={account_id} enviado com sucesso")
        else:
            logger.error(f"Falha ao enviar webhook para account_id={account_id}")
        
        # Aguardar antes de enviar o próximo webhook
        if delay > 0 and account_id != account_ids[-1]:
            logger.info(f"Aguardando {delay} segundos antes do próximo webhook...")
            time.sleep(delay)
    
    logger.info("Teste de mapeamento de clientes concluído")

def main():
    """
    Função principal.
    """
    # Configurar parser de argumentos
    parser = argparse.ArgumentParser(description="Simulador de Webhook do Chatwoot")
    parser.add_argument("--url", type=str, default="http://localhost:8001/webhook",
                        help="URL do webhook handler (default: http://localhost:8001/webhook)")
    parser.add_argument("--accounts", type=int, nargs="+", default=[1, 2, 3],
                        help="Lista de account_ids para testar (default: 1 2 3)")
    parser.add_argument("--delay", type=int, default=2,
                        help="Atraso entre os webhooks em segundos (default: 2)")
    parser.add_argument("--verbose", action="store_true",
                        help="Exibir logs detalhados")
    
    # Parsear argumentos
    args = parser.parse_args()
    
    # Configurar nível de log
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    # Executar teste
    test_client_mapping(args.url, args.accounts, args.delay)

if __name__ == "__main__":
    main()
