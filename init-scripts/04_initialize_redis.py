#!/usr/bin/env python3
"""
Script para inicializar o Redis com configurações e dados iniciais
para o sistema ChatwootAI.

Este script configura o sistema de cache em dois níveis e armazena
algumas informações úteis para o funcionamento do sistema.
"""

import os
import sys
import time
import json
import redis

# Configurações
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)

def wait_for_redis():
    """Aguarda o Redis estar disponível antes de prosseguir."""
    redis_available = False
    for _ in range(30):  # Tenta por 30 segundos
        try:
            r = redis.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                db=REDIS_DB,
                password=REDIS_PASSWORD,
                socket_timeout=1
            )
            r.ping()
            redis_available = True
            print("✅ Redis está disponível")
            break
        except Exception as e:
            print(f"Aguardando Redis... ({e})")
            time.sleep(1)
    
    if not redis_available:
        print("❌ Redis não está disponível após 30 tentativas")
        sys.exit(1)
    
    return r

def initialize_cache_settings(r):
    """Inicializa as configurações do sistema de cache."""
    try:
        # Configurações do cache de primeiro nível (memória rápida)
        cache_l1_settings = {
            "max_size": 1000,  # Número máximo de itens no cache L1
            "ttl": 300,        # Tempo de vida em segundos (5 minutos)
            "enabled": True    # Se o cache L1 está habilitado
        }
        
        # Configurações do cache de segundo nível (Redis)
        cache_l2_settings = {
            "ttl": 3600,       # Tempo de vida em segundos (1 hora)
            "enabled": True    # Se o cache L2 está habilitado
        }
        
        # Armazenar configurações no Redis
        r.set("chatwootai:cache:l1:settings", json.dumps(cache_l1_settings))
        r.set("chatwootai:cache:l2:settings", json.dumps(cache_l2_settings))
        
        print("✅ Configurações de cache inicializadas com sucesso")
    except Exception as e:
        print(f"❌ Erro ao inicializar configurações de cache: {e}")
        sys.exit(1)

def initialize_domain_settings(r):
    """Inicializa as configurações do domínio de negócio."""
    try:
        # Configurações do domínio de cosméticos
        cosmetics_domain = {
            "name": "cosmetics",
            "display_name": "Empresa de Cosméticos",
            "description": "Domínio de negócio para empresa de cosméticos e procedimentos estéticos",
            "active": True,
            "settings": {
                "default_response_time": 120,  # Tempo de resposta padrão em segundos
                "business_hours": {
                    "monday": {"start": "09:00", "end": "18:00"},
                    "tuesday": {"start": "09:00", "end": "18:00"},
                    "wednesday": {"start": "09:00", "end": "18:00"},
                    "thursday": {"start": "09:00", "end": "18:00"},
                    "friday": {"start": "09:00", "end": "18:00"},
                    "saturday": {"start": "09:00", "end": "13:00"},
                    "sunday": {"start": None, "end": None}
                },
                "auto_response_outside_hours": True,
                "outside_hours_message": "Olá! Nosso horário de atendimento é de segunda a sexta das 9h às 18h, e aos sábados das 9h às 13h. Retornaremos o seu contato no próximo dia útil. Obrigado pela compreensão!"
            }
        }
        
        # Armazenar configurações no Redis
        r.set("chatwootai:domain:cosmetics", json.dumps(cosmetics_domain))
        r.set("chatwootai:active_domain", "cosmetics")
        
        print("✅ Configurações de domínio inicializadas com sucesso")
    except Exception as e:
        print(f"❌ Erro ao inicializar configurações de domínio: {e}")
        sys.exit(1)

def initialize_chatwoot_settings(r):
    """Inicializa as configurações de integração com o Chatwoot."""
    try:
        # Configurações do Chatwoot
        chatwoot_settings = {
            "api_endpoint": os.getenv("CHATWOOT_API_ENDPOINT", "https://chatwoot.example.com/api/v1"),
            "api_access_token": os.getenv("CHATWOOT_API_ACCESS_TOKEN", "dummy_token"),
            "account_id": int(os.getenv("CHATWOOT_ACCOUNT_ID", "1")),
            "inbox_ids": [int(id) for id in os.getenv("CHATWOOT_INBOX_IDS", "1,2").split(",")],
            "webhook_url": os.getenv("CHATWOOT_WEBHOOK_URL", "http://crewai:8000/webhooks/chatwoot"),
            "auto_assign_conversations": True,
            "auto_resolve_after_hours": 24,  # Auto resolver conversas após 24 horas de inatividade
            "greeting_message": "Olá! Sou o assistente virtual da Empresa de Cosméticos. Como posso ajudar você hoje?",
            "away_message": "Estamos analisando sua mensagem e um de nossos especialistas irá atendê-lo em breve!"
        }
        
        # Armazenar configurações no Redis
        r.set("chatwootai:chatwoot:settings", json.dumps(chatwoot_settings))
        
        print("✅ Configurações do Chatwoot inicializadas com sucesso")
    except Exception as e:
        print(f"❌ Erro ao inicializar configurações do Chatwoot: {e}")
        sys.exit(1)

def initialize_agent_settings(r):
    """Inicializa as configurações dos agentes de IA."""
    try:
        # Configurações gerais dos agentes
        agent_settings = {
            "default_model": "gpt-4o-mini",
            "fallback_model": "gpt-3.5-turbo",
            "temperature": 0.7,
            "max_tokens": 1000,
            "timeout": 30,  # Timeout em segundos
            "retry_attempts": 3,
            "memory_window": 10,  # Número de mensagens anteriores a considerar
            "enable_semantic_memory": True,
            "enable_tool_use": True
        }
        
        # Configurações específicas para cada tipo de agente
        sales_agent_settings = {
            "name": "Agente de Vendas",
            "description": "Especializado em auxiliar clientes na escolha de produtos e finalização de compras",
            "model": "gpt-4o-mini",
            "temperature": 0.6,
            "max_tokens": 800,
            "tools": ["product_search", "price_check", "inventory_check", "create_order"],
            "prompt_template": "Você é um assistente de vendas especializado em produtos de cosméticos. Seu objetivo é ajudar os clientes a encontrar os produtos ideais para suas necessidades e finalizar a compra."
        }
        
        support_agent_settings = {
            "name": "Agente de Suporte",
            "description": "Especializado em resolver dúvidas e problemas dos clientes",
            "model": "gpt-4o-mini",
            "temperature": 0.5,
            "max_tokens": 800,
            "tools": ["order_status", "return_policy", "faq_search", "escalate_issue"],
            "prompt_template": "Você é um assistente de suporte especializado em produtos de cosméticos. Seu objetivo é ajudar os clientes a resolver suas dúvidas e problemas de forma eficiente e amigável."
        }
        
        scheduling_agent_settings = {
            "name": "Agente de Agendamento",
            "description": "Especializado em agendar procedimentos estéticos e consultas",
            "model": "gpt-4o-mini",
            "temperature": 0.5,
            "max_tokens": 800,
            "tools": ["check_availability", "create_appointment", "reschedule_appointment", "cancel_appointment"],
            "prompt_template": "Você é um assistente de agendamento especializado em procedimentos estéticos. Seu objetivo é ajudar os clientes a agendar, remarcar ou cancelar seus procedimentos de forma eficiente."
        }
        
        # Armazenar configurações no Redis
        r.set("chatwootai:agents:settings", json.dumps(agent_settings))
        r.set("chatwootai:agents:sales:settings", json.dumps(sales_agent_settings))
        r.set("chatwootai:agents:support:settings", json.dumps(support_agent_settings))
        r.set("chatwootai:agents:scheduling:settings", json.dumps(scheduling_agent_settings))
        
        print("✅ Configurações dos agentes inicializadas com sucesso")
    except Exception as e:
        print(f"❌ Erro ao inicializar configurações dos agentes: {e}")
        sys.exit(1)

def initialize_api_keys(r):
    """Inicializa as chaves de API de serviços externos."""
    try:
        # Chaves de API (valores fictícios, devem ser substituídos pelos reais)
        api_keys = {
            "openai": os.getenv("OPENAI_API_KEY", "dummy_openai_key"),
            "serper": os.getenv("SERPER_API_KEY", "dummy_serper_key"),
            "anthropic": os.getenv("ANTHROPIC_API_KEY", "dummy_anthropic_key")
        }
        
        # Armazenar chaves no Redis
        for key, value in api_keys.items():
            r.set(f"chatwootai:api_keys:{key}", value)
        
        print("✅ Chaves de API inicializadas com sucesso")
    except Exception as e:
        print(f"❌ Erro ao inicializar chaves de API: {e}")
        sys.exit(1)

def initialize_metrics(r):
    """Inicializa contadores e métricas para monitoramento."""
    try:
        # Contadores iniciais
        metrics = {
            "total_conversations": 0,
            "total_messages": 0,
            "successful_responses": 0,
            "failed_responses": 0,
            "average_response_time": 0,
            "total_products_sold": 0,
            "total_appointments_scheduled": 0
        }
        
        # Armazenar métricas no Redis
        for key, value in metrics.items():
            r.set(f"chatwootai:metrics:{key}", value)
        
        print("✅ Métricas inicializadas com sucesso")
    except Exception as e:
        print(f"❌ Erro ao inicializar métricas: {e}")
        sys.exit(1)

def main():
    """Função principal do script."""
    print("🚀 Iniciando inicialização do Redis")
    
    # Aguardar Redis estar disponível
    r = wait_for_redis()
    
    # Inicializar configurações
    initialize_cache_settings(r)
    initialize_domain_settings(r)
    initialize_chatwoot_settings(r)
    initialize_agent_settings(r)
    initialize_api_keys(r)
    initialize_metrics(r)
    
    print("✅ Inicialização do Redis concluída com sucesso!")

if __name__ == "__main__":
    main()
