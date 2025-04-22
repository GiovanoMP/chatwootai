#!/usr/bin/env python3
"""
Script para testar a sincronização de credenciais.
"""

import requests
import json
import os
import sys

# Configurações
SERVER_URL = "http://localhost:8001"
WEBHOOK_ENDPOINT = f"{SERVER_URL}/webhook"

# Dados de teste
TEST_DATA = {
    "source": "credentials",
    "event": "credentials_sync",
    "account_id": "account_1",
    "token": "account_1-00bfe67a",
    "credentials": {
        "domain": "retail",
        "name": "Sandra Cosmeticos",
        "odoo_url": "http://localhost:8069",
        "odoo_db": "account_1",
        "odoo_username": "giovano@sprintia.com.br",
        "odoo_password": "admin123",  # Senha de teste
        "token": "account_1-00bfe67a",
        "qdrant_collection": "business_rules_account_1",
        "redis_prefix": "account_1",
        "facebook_app_id": "12345678910",
        "facebook_app_secret": "facebook_secret_123",
        "facebook_access_token": "facebook_token_456",
        "instagram_client_id": "12345678910",
        "instagram_client_secret": "instagram_secret_123",
        "instagram_access_token": "instagram_token_456",
        "mercado_livre_app_id": "123456",
        "mercado_livre_client_secret": "ml_secret_123",
        "mercado_livre_access_token": "ml_token_456"
    }
}

def main():
    """Função principal."""
    print("======================================================================")
    print("🔄 TESTANDO SINCRONIZAÇÃO DE CREDENCIAIS")
    print("======================================================================")
    
    # Enviar requisição para o webhook
    print(f"📡 Enviando requisição para {WEBHOOK_ENDPOINT}...")
    
    try:
        response = requests.post(
            WEBHOOK_ENDPOINT,
            json=TEST_DATA,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        # Verificar resposta
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Requisição bem-sucedida: {json.dumps(result, indent=2)}")
            
            # Verificar se os arquivos foram criados
            if "config_path" in result and "credentials_path" in result:
                config_path = result["config_path"]
                credentials_path = result["credentials_path"]
                
                print(f"📄 Arquivo de configuração: {config_path}")
                print(f"📄 Arquivo de credenciais: {credentials_path}")
                
                # Verificar se os arquivos existem
                if os.path.exists(config_path):
                    print(f"✅ Arquivo de configuração existe")
                else:
                    print(f"❌ Arquivo de configuração não existe")
                
                if os.path.exists(credentials_path):
                    print(f"✅ Arquivo de credenciais existe")
                else:
                    print(f"❌ Arquivo de credenciais não existe")
            else:
                print(f"⚠️ Caminhos dos arquivos não retornados na resposta")
        else:
            print(f"❌ Erro na requisição: {response.status_code} - {response.text}")
    
    except Exception as e:
        print(f"❌ Erro ao enviar requisição: {str(e)}")
        return 1
    
    print("======================================================================")
    return 0

if __name__ == "__main__":
    sys.exit(main())
