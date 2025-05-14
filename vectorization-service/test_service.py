#!/usr/bin/env python3
"""
Script para testar o serviço de vetorização.
"""

import argparse
import json
import requests
import sys
import time
from datetime import datetime

# Configurações padrão
DEFAULT_URL = "http://localhost:8004"
DEFAULT_API_KEY = "development-api-key"

def test_health(base_url):
    """Testa a rota de saúde do serviço."""
    url = f"{base_url}/health"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        print(f"✅ Teste de saúde: {response.json()}")
        return True
    except Exception as e:
        print(f"❌ Teste de saúde falhou: {str(e)}")
        return False

def test_business_rules_sync(base_url, api_key, account_id="test_account"):
    """Testa a sincronização de regras de negócio."""
    url = f"{base_url}/api/v1/business-rules/sync"
    
    # Dados de teste
    data = {
        "account_id": account_id,
        "business_rule_id": 1,
        "rules": {
            "permanent_rules": [
                {
                    "id": 1,
                    "name": "Regra de Teste Permanente",
                    "description": "Esta é uma regra de teste permanente para verificar a sincronização.",
                    "type": "informativa",
                    "last_updated": datetime.now().isoformat()
                }
            ],
            "temporary_rules": [
                {
                    "id": 2,
                    "name": "Regra de Teste Temporária",
                    "description": "Esta é uma regra de teste temporária para verificar a sincronização.",
                    "type": "promocional",
                    "start_date": "2023-01-01",
                    "end_date": "2023-12-31",
                    "last_updated": datetime.now().isoformat()
                }
            ]
        }
    }
    
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": api_key
    }
    
    try:
        start_time = time.time()
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        
        execution_time = time.time() - start_time
        result = response.json()
        
        print(f"✅ Teste de sincronização de regras de negócio: {result['message']} em {execution_time:.2f}s")
        print(f"   Detalhes: {json.dumps(result['data'], indent=2)}")
        return True
    except Exception as e:
        print(f"❌ Teste de sincronização de regras de negócio falhou: {str(e)}")
        if hasattr(e, "response") and e.response:
            print(f"   Resposta: {e.response.text}")
        return False

def test_scheduling_rules_sync(base_url, api_key, account_id="test_account"):
    """Testa a sincronização de regras de agendamento."""
    url = f"{base_url}/api/v1/scheduling-rules/sync"
    
    # Dados de teste
    data = {
        "account_id": account_id,
        "business_rule_id": 1,
        "scheduling_rules": [
            {
                "id": 1,
                "name": "Consulta Padrão",
                "description": "Agendamento de consulta padrão",
                "service_type": "consulta",
                "service_type_other": "",
                "duration": 60,
                "min_interval": 30,
                "min_advance_time": 24,
                "max_advance_time": 30,
                "days_available": {
                    "monday": True,
                    "tuesday": True,
                    "wednesday": True,
                    "thursday": True,
                    "friday": True,
                    "saturday": False,
                    "sunday": False
                },
                "hours": {
                    "morning_start": "08:00",
                    "morning_end": "12:00",
                    "afternoon_start": "14:00",
                    "afternoon_end": "18:00",
                    "has_lunch_break": True
                },
                "special_hours": {
                    "saturday": {
                        "morning_start": "09:00",
                        "morning_end": "12:00",
                        "has_afternoon": False
                    },
                    "sunday": {
                        "morning_start": "00:00",
                        "morning_end": "00:00",
                        "has_afternoon": False
                    }
                },
                "policies": {
                    "cancellation": "Cancelamentos devem ser feitos com 24h de antecedência",
                    "rescheduling": "Reagendamentos devem ser feitos com 24h de antecedência",
                    "required_information": "Nome completo, telefone e e-mail",
                    "confirmation_instructions": "Confirme seu agendamento por e-mail"
                },
                "last_updated": datetime.now().isoformat()
            }
        ]
    }
    
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": api_key
    }
    
    try:
        start_time = time.time()
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        
        execution_time = time.time() - start_time
        result = response.json()
        
        print(f"✅ Teste de sincronização de regras de agendamento: {result['message']} em {execution_time:.2f}s")
        print(f"   Detalhes: {json.dumps(result['data'], indent=2)}")
        return True
    except Exception as e:
        print(f"❌ Teste de sincronização de regras de agendamento falhou: {str(e)}")
        if hasattr(e, "response") and e.response:
            print(f"   Resposta: {e.response.text}")
        return False

def test_support_documents_sync(base_url, api_key, account_id="test_account"):
    """Testa a sincronização de documentos de suporte."""
    url = f"{base_url}/api/v1/support-documents/sync"
    
    # Dados de teste
    data = {
        "account_id": account_id,
        "business_rule_id": 1,
        "documents": [
            {
                "id": 1,
                "name": "FAQ",
                "document_type": "faq",
                "content": "Perguntas frequentes sobre o serviço:\n1. Como agendar?\nR: Através do site ou telefone.\n2. Como cancelar?\nR: Através do site ou telefone com 24h de antecedência.",
                "last_updated": datetime.now().isoformat()
            },
            {
                "id": 2,
                "name": "Termos de Uso",
                "document_type": "terms",
                "content": "Termos de uso do serviço: Ao utilizar nosso serviço, você concorda com os seguintes termos...",
                "last_updated": datetime.now().isoformat()
            }
        ]
    }
    
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": api_key
    }
    
    try:
        start_time = time.time()
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        
        execution_time = time.time() - start_time
        result = response.json()
        
        print(f"✅ Teste de sincronização de documentos de suporte: {result['message']} em {execution_time:.2f}s")
        print(f"   Detalhes: {json.dumps(result['data'], indent=2)}")
        return True
    except Exception as e:
        print(f"❌ Teste de sincronização de documentos de suporte falhou: {str(e)}")
        if hasattr(e, "response") and e.response:
            print(f"   Resposta: {e.response.text}")
        return False

def test_business_rules_search(base_url, api_key, account_id="test_account"):
    """Testa a busca de regras de negócio."""
    url = f"{base_url}/api/v1/business-rules/search"
    
    # Dados de teste
    data = {
        "account_id": account_id,
        "query": "regra teste",
        "limit": 5,
        "score_threshold": 0.5
    }
    
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": api_key
    }
    
    try:
        start_time = time.time()
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        
        execution_time = time.time() - start_time
        result = response.json()
        
        print(f"✅ Teste de busca de regras de negócio: {result['message']} em {execution_time:.2f}s")
        print(f"   Detalhes: {json.dumps(result['data'], indent=2)}")
        return True
    except Exception as e:
        print(f"❌ Teste de busca de regras de negócio falhou: {str(e)}")
        if hasattr(e, "response") and e.response:
            print(f"   Resposta: {e.response.text}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Testa o serviço de vetorização")
    parser.add_argument("--url", default=DEFAULT_URL, help=f"URL base do serviço (padrão: {DEFAULT_URL})")
    parser.add_argument("--api-key", default=DEFAULT_API_KEY, help=f"API key para autenticação (padrão: {DEFAULT_API_KEY})")
    parser.add_argument("--account-id", default="test_account", help="ID da conta para testes (padrão: test_account)")
    parser.add_argument("--test", choices=["all", "health", "business-rules", "scheduling-rules", "support-documents", "search"], default="all", help="Teste específico a ser executado (padrão: all)")
    
    args = parser.parse_args()
    
    print(f"🔍 Testando serviço de vetorização em {args.url}")
    
    success = True
    
    if args.test in ["all", "health"]:
        if not test_health(args.url):
            success = False
    
    if args.test in ["all", "business-rules"]:
        if not test_business_rules_sync(args.url, args.api_key, args.account_id):
            success = False
    
    if args.test in ["all", "scheduling-rules"]:
        if not test_scheduling_rules_sync(args.url, args.api_key, args.account_id):
            success = False
    
    if args.test in ["all", "support-documents"]:
        if not test_support_documents_sync(args.url, args.api_key, args.account_id):
            success = False
    
    if args.test in ["all", "search"]:
        if not test_business_rules_search(args.url, args.api_key, args.account_id):
            success = False
    
    if success:
        print("\n✅ Todos os testes executados com sucesso!")
        return 0
    else:
        print("\n❌ Alguns testes falharam. Verifique os logs para mais detalhes.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
