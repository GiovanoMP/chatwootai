#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para testar o envio de um webhook de mapeamento de canal.
"""

import requests
import json
import sys
import os

def send_mapping_webhook(webhook_url, account_id, chatwoot_account_id, chatwoot_inbox_id, internal_account_id, domain):
    """
    Envia um webhook de mapeamento de canal para o sistema.
    
    Args:
        webhook_url: URL do webhook
        account_id: ID da conta
        chatwoot_account_id: ID da conta no Chatwoot
        chatwoot_inbox_id: ID da caixa de entrada no Chatwoot
        internal_account_id: ID interno da conta
        domain: Domínio
    """
    # Preparar payload
    payload = {
        'source': 'channel_mapping',
        'event': 'mapping_sync',
        'account_id': account_id,
        'token': 'test_token',
        'mapping': {
            'chatwoot_account_id': chatwoot_account_id,
            'chatwoot_inbox_id': chatwoot_inbox_id,
            'internal_account_id': internal_account_id,
            'domain': domain,
            'is_fallback': False,
            'sequence': 10,
            'special_whatsapp_numbers': []
        }
    }
    
    # Enviar requisição
    headers = {'Content-Type': 'application/json'}
    response = requests.post(webhook_url, headers=headers, json=payload)
    
    # Verificar resposta
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.text}")
    
    return response

if __name__ == "__main__":
    # Verificar argumentos
    if len(sys.argv) < 6:
        print("Uso: python test_mapping_webhook.py <webhook_url> <account_id> <chatwoot_account_id> <chatwoot_inbox_id> <internal_account_id> <domain>")
        sys.exit(1)
    
    # Obter argumentos
    webhook_url = sys.argv[1]
    account_id = sys.argv[2]
    chatwoot_account_id = sys.argv[3]
    chatwoot_inbox_id = sys.argv[4]
    internal_account_id = sys.argv[5]
    domain = sys.argv[6]
    
    # Enviar webhook
    send_mapping_webhook(webhook_url, account_id, chatwoot_account_id, chatwoot_inbox_id, internal_account_id, domain)
