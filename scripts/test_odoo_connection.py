#!/usr/bin/env python3
"""
Script para testar a conexão com o Odoo.
"""

import requests
import json
import sys

# Configurações
SERVER_URL = "http://localhost:8001"
API_ENDPOINT = f"{SERVER_URL}/api/v1/business-rules/sync"

# Dados de teste
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": "Bearer account_1-00bfe67a"
}

def main():
    """Função principal."""
    print("======================================================================")
    print("🔄 TESTANDO CONEXÃO COM O ODOO")
    print("======================================================================")
    
    # Enviar requisição para a API
    print(f"📡 Enviando requisição para {API_ENDPOINT}...")
    
    try:
        response = requests.post(
            API_ENDPOINT,
            headers=HEADERS,
            params={"account_id": "account_1"},
            timeout=30
        )
        
        # Verificar resposta
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Requisição bem-sucedida: {json.dumps(result, indent=2)}")
        else:
            print(f"❌ Erro na requisição: {response.status_code} - {response.text}")
    
    except Exception as e:
        print(f"❌ Erro ao enviar requisição: {str(e)}")
        return 1
    
    print("======================================================================")
    return 0

if __name__ == "__main__":
    sys.exit(main())
