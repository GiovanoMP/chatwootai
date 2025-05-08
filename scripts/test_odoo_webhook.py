#!/usr/bin/env python3
"""
Script para testar o webhook do Odoo no serviço de configuração.

Este script simula o envio de um webhook do Odoo para o serviço de configuração,
permitindo testar a funcionalidade sem precisar do Odoo.

Uso:
    python scripts/test_odoo_webhook.py
"""

import requests
import json
import argparse
import sys
import os
from datetime import datetime

# Configurações padrão
DEFAULT_CONFIG_SERVICE_URL = "http://localhost:8002"
DEFAULT_API_KEY = "development-api-key"
DEFAULT_ACCOUNT_ID = "123456"
DEFAULT_DOMAIN = "default"

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Teste do webhook do Odoo para o serviço de configuração")
    parser.add_argument("--url", default=DEFAULT_CONFIG_SERVICE_URL, help="URL do serviço de configuração")
    parser.add_argument("--api-key", default=DEFAULT_API_KEY, help="Chave de API para autenticação")
    parser.add_argument("--account-id", default=DEFAULT_ACCOUNT_ID, help="ID da conta")
    parser.add_argument("--domain", default=DEFAULT_DOMAIN, help="Domínio da conta")
    parser.add_argument("--type", choices=["credentials", "mapping", "metadata"], default="credentials", help="Tipo de webhook")

    return parser.parse_args()

def create_credentials_payload(account_id, domain):
    """Cria payload para teste de sincronização de credenciais."""
    return {
        "event_type": "credentials_sync",
        "account_id": account_id,
        "domain": domain,
        "name": f"Cliente Teste {account_id}",
        "description": f"Configuração de teste para {account_id}",
        "odoo_url": "https://odoo.example.com",
        "odoo_db": "odoo_db",
        "odoo_username": "admin",
        "odoo_password": "admin_password",
        "token": "odoo_token_123",
        "enabled_collections": [
            "business_rules",
            "products_informations",
            "scheduling_rules",
            "support_documents"
        ],
        "timestamp": datetime.now().isoformat()
    }

def create_mapping_payload(account_id, domain):
    """Cria payload para teste de sincronização de mapeamento."""
    return {
        "event_type": "mapping_sync",
        "mapping": {
            "chatwoot_account_id": "987654",
            "chatwoot_inbox_id": "12345",
            "internal_account_id": account_id,
            "domain": domain,
            "is_fallback": True,
            "sequence": 10,
            "special_whatsapp_numbers": [
                {
                    "number": "5511999999999",
                    "crew": "analytics"
                },
                {
                    "number": "5511888888888",
                    "crew": "support"
                }
            ]
        },
        "timestamp": datetime.now().isoformat()
    }

def create_metadata_payload(account_id, domain):
    """Cria payload para teste de sincronização de metadados da empresa."""
    return {
        "event_type": "company_metadata_sync",
        "account_id": account_id,
        "domain": domain,
        "name": f"Empresa Teste {account_id}",
        "description": f"Descrição da empresa teste {account_id}",
        "business_area": "retail",
        "business_area_other": "",
        "company_values": "Qualidade, Inovação, Atendimento",
        "website": "https://www.empresa-teste.com",
        "facebook_url": "https://www.facebook.com/empresa-teste",
        "instagram_url": "https://www.instagram.com/empresa-teste",
        "mention_website_at_end": True,
        "mention_facebook_at_end": False,
        "mention_instagram_at_end": True,
        "greeting_message": "Olá! Como posso ajudar?",
        "communication_style": "friendly",
        "emoji_usage": "moderate",
        "address": {
            "street": "Rua Teste, 123",
            "street2": "Sala 45",
            "city": "São Paulo",
            "state": "SP",
            "zip": "01234-567",
            "country": "Brasil",
            "share_address": True
        },
        "business_hours": {
            "monday": True,
            "tuesday": True,
            "wednesday": True,
            "thursday": True,
            "friday": True,
            "saturday": False,
            "sunday": False,
            "business_hours_start": 9.0,
            "business_hours_end": 18.0,
            "has_lunch_break": True,
            "lunch_break_start": 12.0,
            "lunch_break_end": 13.0,
            "saturday_hours_start": 9.0,
            "saturday_hours_end": 13.0,
            "sunday_hours_start": 0.0,
            "sunday_hours_end": 0.0
        },
        "enabled_collections": [
            "business_rules",
            "products_informations",
            "scheduling_rules",
            "support_documents"
        ],
        "timestamp": datetime.now().isoformat()
    }

def send_webhook(url, api_key, payload):
    """Envia webhook para o serviço de configuração."""
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": api_key
    }

    print(f"Enviando webhook para {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")

    try:
        response = requests.post(url, json=payload, headers=headers)

        print(f"Status: {response.status_code}")
        print(f"Resposta: {json.dumps(response.json(), indent=2) if response.status_code < 400 else response.text}")

        return response.status_code < 400
    except Exception as e:
        print(f"Erro ao enviar webhook: {str(e)}")
        return False

def main():
    """Função principal."""
    args = parse_args()

    # Construir URL do webhook
    webhook_url = f"{args.url}/odoo-webhook"

    # Criar payload de acordo com o tipo
    if args.type == "credentials":
        payload = create_credentials_payload(args.account_id, args.domain)
        payload_type = "credenciais"
    elif args.type == "mapping":
        payload = create_mapping_payload(args.account_id, args.domain)
        payload_type = "mapeamento"
    elif args.type == "metadata":
        payload = create_metadata_payload(args.account_id, args.domain)
        payload_type = "metadados da empresa"

    print(f"Enviando payload de {payload_type} para {webhook_url}")

    # Enviar webhook
    success = send_webhook(webhook_url, args.api_key, payload)

    # Verificar resultado
    if success:
        print(f"Webhook de {payload_type} enviado com sucesso!")
        sys.exit(0)
    else:
        print(f"Falha ao enviar webhook de {payload_type}!")
        sys.exit(1)

if __name__ == "__main__":
    main()
