#!/usr/bin/env python3
"""
Script para testar a conexão entre o Odoo e o webhook-mongo.

Este script simula o envio de dados do módulo company_services para o webhook-mongo,
permitindo verificar se a conexão está funcionando corretamente.

Uso:
    python test_connection.py [--url URL] [--account-id ACCOUNT_ID] [--api-key API_KEY]
"""

import argparse
import requests
import json
import sys
import os
from datetime import datetime

# Configurações padrão
DEFAULT_WEBHOOK_URL = "http://localhost:8003"
DEFAULT_API_KEY = "development-api-key"
DEFAULT_ACCOUNT_ID = "account_1"
DEFAULT_SECURITY_TOKEN = "abc123"

def parse_args():
    """Analisa os argumentos da linha de comando."""
    parser = argparse.ArgumentParser(description="Testa a conexão com o webhook-mongo")
    parser.add_argument("--url", default=DEFAULT_WEBHOOK_URL,
                        help=f"URL do webhook-mongo (padrão: {DEFAULT_WEBHOOK_URL})")
    parser.add_argument("--account-id", default=DEFAULT_ACCOUNT_ID,
                        help=f"ID da conta (padrão: {DEFAULT_ACCOUNT_ID})")
    parser.add_argument("--api-key", default=DEFAULT_API_KEY,
                        help=f"Chave de API (padrão: {DEFAULT_API_KEY})")
    parser.add_argument("--security-token", default=DEFAULT_SECURITY_TOKEN,
                        help=f"Token de segurança (padrão: {DEFAULT_SECURITY_TOKEN})")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Exibir informações detalhadas")
    
    return parser.parse_args()

def create_test_yaml(account_id, security_token):
    """Cria um YAML de teste para enviar ao webhook."""
    yaml_content = f"""account_id: {account_id}
security_token: {security_token}
name: Empresa Teste
description: Configuração de teste para {account_id}
version: 1
updated_at: {datetime.now().isoformat()}
enabled_modules:
  - company_info
  - service_settings
  - enabled_services
  - mcp
  - channels
modules:
  company_info:
    name: Empresa Teste
    description: Descrição da empresa teste
    address:
      street: Rua Teste, 123
      city: Cidade Teste
      state: Estado Teste
      zip: 12345-678
      country: Brasil
      share_with_customers: true
  service_settings:
    business_hours:
      days:
        monday: {{ open: true, start: "08:00", end: "18:00" }}
        tuesday: {{ open: true, start: "08:00", end: "18:00" }}
        wednesday: {{ open: true, start: "08:00", end: "18:00" }}
        thursday: {{ open: true, start: "08:00", end: "18:00" }}
        friday: {{ open: true, start: "08:00", end: "18:00" }}
        saturday: {{ open: false }}
        sunday: {{ open: false }}
    greeting_message: Olá! Como posso ajudar você hoje?
    farewell_message: Obrigado por entrar em contato. Tenha um ótimo dia!
  enabled_services:
    collections:
      - products_informations
      - scheduling_rules
      - support_documents
    services:
      sales:
        enabled: true
        promotions:
          inform_at_start: true
      scheduling:
        enabled: true
      delivery:
        enabled: false
      support:
        enabled: true
  mcp:
    type: odoo
    version: 14.0
    connection:
      url: http://localhost:8069
      database: {account_id}
      username: admin
      password_ref: {account_id}_db_pwd
      access_level: read
  channels:
    whatsapp:
      enabled: true
      services:
        - sales
        - scheduling
        - support
"""
    return yaml_content

def test_health(url, verbose=False):
    """Testa o endpoint de saúde do webhook."""
    health_url = f"{url}/health"
    
    if verbose:
        print(f"\n🔍 Testando endpoint de saúde: {health_url}")
    
    try:
        response = requests.get(health_url, timeout=10)
        
        if verbose:
            print(f"📊 Status: {response.status_code}")
            print(f"📄 Resposta: {json.dumps(response.json(), indent=2) if response.status_code < 400 else response.text}")
        
        if response.status_code == 200:
            print("✅ Endpoint de saúde está funcionando!")
            return True
        else:
            print(f"❌ Endpoint de saúde retornou status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erro ao acessar endpoint de saúde: {str(e)}")
        return False

def test_webhook(url, account_id, api_key, security_token, verbose=False):
    """Testa o envio de dados para o webhook."""
    endpoint = f"{url}/company-services/{account_id}/metadata"
    
    if verbose:
        print(f"\n🔍 Testando endpoint do webhook: {endpoint}")
    
    # Criar payload
    yaml_content = create_test_yaml(account_id, security_token)
    payload = {
        "yaml_content": yaml_content
    }
    
    # Preparar headers
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": api_key,
        "X-Security-Token": security_token
    }
    
    if verbose:
        print(f"📤 Enviando dados para o webhook...")
        print(f"🔑 Headers: {json.dumps(headers, indent=2)}")
        print(f"📦 Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(
            endpoint,
            json=payload,
            headers=headers,
            timeout=30
        )
        
        if verbose:
            print(f"📊 Status: {response.status_code}")
            print(f"📄 Resposta: {json.dumps(response.json(), indent=2) if response.status_code < 400 else response.text}")
        
        if response.status_code in (200, 201):
            print("✅ Dados enviados com sucesso para o webhook!")
            return True
        else:
            print(f"❌ Erro ao enviar dados para o webhook: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Erro ao enviar dados para o webhook: {str(e)}")
        return False

def test_connection_from_odoo(url, account_id, api_key, security_token, verbose=False):
    """Testa a conexão a partir do contêiner do Odoo."""
    if verbose:
        print("\n🔍 Testando conexão a partir do contêiner do Odoo...")
    
    # Verificar se o contêiner do Odoo está rodando
    try:
        import subprocess
        result = subprocess.run(["docker", "ps", "--filter", "name=odoo", "--format", "{{.Names}}"], 
                               capture_output=True, text=True, check=True)
        odoo_containers = result.stdout.strip().split('\n')
        
        if not odoo_containers or odoo_containers[0] == '':
            print("❌ Nenhum contêiner do Odoo encontrado!")
            return False
        
        odoo_container = odoo_containers[0]
        
        if verbose:
            print(f"🐳 Contêiner do Odoo encontrado: {odoo_container}")
        
        # Testar conexão a partir do contêiner do Odoo
        test_command = f"""
        curl -s -X POST \\
          '{url}/company-services/{account_id}/metadata' \\
          -H 'Content-Type: application/json' \\
          -H 'X-API-Key: {api_key}' \\
          -H 'X-Security-Token: {security_token}' \\
          -d '{{"yaml_content": "account_id: {account_id}\\nsecurity_token: {security_token}\\nname: Teste"}}'
        """
        
        if verbose:
            print(f"🧪 Executando comando de teste no contêiner do Odoo:")
            print(test_command)
        
        result = subprocess.run(["docker", "exec", odoo_container, "bash", "-c", test_command], 
                               capture_output=True, text=True)
        
        if verbose:
            print(f"📊 Saída: {result.stdout}")
            print(f"❗ Erro: {result.stderr}")
        
        if "success" in result.stdout.lower():
            print("✅ Conexão a partir do contêiner do Odoo bem-sucedida!")
            return True
        else:
            print(f"❌ Erro na conexão a partir do contêiner do Odoo: {result.stderr}")
            
            # Sugerir soluções
            print("\n🔧 Possíveis soluções:")
            print("1. Verifique se o webhook-mongo está acessível a partir do contêiner do Odoo")
            print("2. Use o IP do host em vez de 'localhost' na URL do webhook")
            print("3. Certifique-se de que os contêineres estão na mesma rede Docker")
            print("4. Verifique se não há regras de firewall bloqueando a conexão")
            
            return False
    except Exception as e:
        print(f"❌ Erro ao testar conexão a partir do contêiner do Odoo: {str(e)}")
        return False

def main():
    """Função principal."""
    args = parse_args()
    
    print("="*80)
    print("🚀 TESTE DE CONEXÃO COM O WEBHOOK-MONGO")
    print("="*80)
    print(f"🌐 URL: {args.url}")
    print(f"👤 Account ID: {args.account_id}")
    print(f"🔑 API Key: {'*'*(len(args.api_key)-4) + args.api_key[-4:]}")
    print(f"🔒 Security Token: {'*'*(len(args.security_token)-4) + args.security_token[-4:]}")
    print("="*80)
    
    # Testar endpoint de saúde
    health_ok = test_health(args.url, args.verbose)
    
    if not health_ok:
        print("\n⚠️ O endpoint de saúde não está funcionando. Continuando com os testes...")
    
    # Testar webhook
    webhook_ok = test_webhook(args.url, args.account_id, args.api_key, args.security_token, args.verbose)
    
    if not webhook_ok:
        print("\n⚠️ O teste do webhook falhou. Verifique as configurações e tente novamente.")
    
    # Testar conexão a partir do contêiner do Odoo
    odoo_ok = test_connection_from_odoo(args.url, args.account_id, args.api_key, args.security_token, args.verbose)
    
    # Resumo dos testes
    print("\n"+"="*80)
    print("📋 RESUMO DOS TESTES")
    print("="*80)
    print(f"✅ Endpoint de saúde: {'OK' if health_ok else 'FALHOU'}")
    print(f"✅ Teste do webhook: {'OK' if webhook_ok else 'FALHOU'}")
    print(f"✅ Conexão a partir do Odoo: {'OK' if odoo_ok else 'FALHOU'}")
    print("="*80)
    
    if health_ok and webhook_ok and odoo_ok:
        print("\n🎉 Todos os testes passaram! A conexão está funcionando corretamente.")
        return 0
    else:
        print("\n⚠️ Alguns testes falharam. Verifique as mensagens acima para mais detalhes.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
