#!/usr/bin/env python3
"""
Script para testar os serviços de dados do ChatwootAI.

Este script demonstra o uso dos serviços de dados implementados,
permitindo validar o funcionamento correto da camada de serviços de dados.
"""

import os
import sys
import json
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("DataServicesTest")

# Adicionar diretório pai ao path para importar os módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importar os serviços de dados
from services.data.data_service_hub import DataServiceHub
from services.data.product_data_service import ProductDataService
from services.data.customer_data_service import CustomerDataService
from services.data.conversation_context_service import ConversationContextService
from services.data.conversation_analytics_service import ConversationAnalyticsService

def print_separator(title):
    """Imprime um separador com título para melhor visualização."""
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, "="))
    print("=" * 80 + "\n")

def test_data_service_hub():
    """Testa as funcionalidades básicas do DataServiceHub."""
    print_separator("Testando DataServiceHub")
    
    # Inicializar o hub
    hub = DataServiceHub()
    
    # Testar conexão com PostgreSQL
    if hub.pg_conn:
        logger.info("Conexão com PostgreSQL estabelecida com sucesso!")
        
        # Testar consulta simples
        result = hub.execute_query("SELECT 1 as test")
        logger.info(f"Resultado da consulta de teste: {result}")
    else:
        logger.error("Falha na conexão com PostgreSQL!")
    
    # Testar conexão com Redis
    if hub.redis_client:
        logger.info("Conexão com Redis estabelecida com sucesso!")
        
        # Testar operações básicas de cache
        hub.cache_set("test_key", "test_value")
        value = hub.cache_get("test_key")
        logger.info(f"Valor recuperado do cache: {value}")
        
        hub.cache_invalidate("test_key")
        value = hub.cache_get("test_key")
        logger.info(f"Valor após invalidação: {value}")
    else:
        logger.error("Falha na conexão com Redis!")
    
    return hub

def test_product_service(hub):
    """Testa as funcionalidades do ProductDataService."""
    print_separator("Testando ProductDataService")
    
    # Inicializar o serviço de produtos
    product_service = ProductDataService(hub)
    
    # Testar criação de produto
    try:
        new_product = product_service.create({
            "name": "Produto de Teste",
            "description": "Este é um produto para testar o serviço de dados",
            "price": 99.99,
            "sku": f"TEST-{int(datetime.now().timestamp())}"
        })
        
        if new_product:
            logger.info(f"Produto criado com sucesso: {new_product}")
            product_id = new_product['id']
            
            # Testar busca por ID
            product = product_service.get_by_id(product_id)
            logger.info(f"Produto recuperado por ID: {product}")
            
            # Testar atualização
            updated = product_service.update(product_id, {
                "price": 129.99,
                "description": "Descrição atualizada para o produto de teste"
            })
            logger.info(f"Produto atualizado: {updated}")
            
            # Testar busca por texto
            search_results = product_service.search_by_text("Teste")
            logger.info(f"Resultados da busca por 'Teste': {len(search_results)} produto(s)")
            
            # Testar exclusão (opcional - comentado para preservar o produto para testes futuros)
            # deleted = product_service.delete(product_id)
            # logger.info(f"Produto excluído: {deleted}")
        else:
            logger.error("Falha ao criar produto de teste!")
    except Exception as e:
        logger.error(f"Erro ao testar serviço de produtos: {str(e)}")
    
    return product_service

def test_customer_service(hub):
    """Testa as funcionalidades do CustomerDataService."""
    print_separator("Testando CustomerDataService")
    
    # Inicializar o serviço de clientes
    customer_service = CustomerDataService(hub)
    
    # Testar criação de cliente
    try:
        timestamp = int(datetime.now().timestamp())
        new_customer = customer_service.create({
            "first_name": "Cliente",
            "last_name": "Teste",
            "email": f"teste{timestamp}@example.com",
            "phone": f"+5511999{timestamp % 1000000:06d}",
            "external_id": f"EXT-{timestamp}"
        })
        
        if new_customer:
            logger.info(f"Cliente criado com sucesso: {new_customer}")
            customer_id = new_customer['id']
            
            # Testar busca por ID
            customer = customer_service.get_by_id(customer_id)
            logger.info(f"Cliente recuperado por ID: {customer}")
            
            # Testar adição de endereço
            address = customer_service.add_address(customer_id, {
                "address_line1": "Rua de Teste, 123",
                "city": "São Paulo",
                "state": "SP",
                "postal_code": "01234-567",
                "country": "Brasil",
                "is_default": True,
                "address_type": "both"
            })
            logger.info(f"Endereço adicionado: {address}")
            
            # Testar definição de preferência
            pref_set = customer_service.set_preference(customer_id, "preferred_contact", "email")
            logger.info(f"Preferência definida: {pref_set}")
            
            # Testar obtenção de perfil completo
            profile = customer_service.get_full_profile(customer_id)
            logger.info(f"Perfil completo: {json.dumps(profile, indent=2)}")
            
            # Testar exclusão (opcional - comentado para preservar o cliente para testes futuros)
            # deleted = customer_service.delete(customer_id)
            # logger.info(f"Cliente excluído: {deleted}")
        else:
            logger.error("Falha ao criar cliente de teste!")
    except Exception as e:
        logger.error(f"Erro ao testar serviço de clientes: {str(e)}")
    
    return customer_service

def test_conversation_context_service(hub):
    """Testa as funcionalidades do ConversationContextService."""
    print_separator("Testando ConversationContextService")
    
    # Inicializar o serviço de contexto de conversas
    context_service = ConversationContextService(hub)
    
    # Gerar ID de conversa único
    conversation_id = f"conv-{int(datetime.now().timestamp())}"
    
    try:
        # Testar obtenção de contexto (deve criar um novo)
        context = context_service.get_context(conversation_id)
        logger.info(f"Contexto inicial criado: {context}")
        
        # Testar atualização de contexto
        updated = context_service.update_context(conversation_id, {
            "customer_id": 1,  # Assumindo que existe um cliente com ID 1
            "status": "active",
            "metadata": {
                "channel": "whatsapp",
                "initiated_by": "customer"
            }
        })
        logger.info(f"Contexto atualizado: {updated}")
        
        # Testar adição de mensagens
        message1 = context_service.add_message(conversation_id, {
            "sender_id": "customer-1",
            "sender_type": "customer",
            "content": "Olá, preciso de ajuda com meu pedido"
        })
        logger.info(f"Mensagem 1 adicionada: {message1}")
        
        message2 = context_service.add_message(conversation_id, {
            "sender_id": "agent-1",
            "sender_type": "agent",
            "content": "Olá! Em que posso ajudar com seu pedido?"
        })
        logger.info(f"Mensagem 2 adicionada: {message2}")
        
        # Testar definição de variáveis
        var_set = context_service.set_variable(conversation_id, "last_order_id", 12345)
        logger.info(f"Variável definida: {var_set}")
        
        var_set = context_service.set_variable(conversation_id, "product_interest", "Smartphone")
        logger.info(f"Variável definida: {var_set}")
        
        # Obter contexto completo atualizado
        updated_context = context_service.get_context(conversation_id)
        logger.info(f"Contexto final: {json.dumps(updated_context, indent=2)}")
    
    except Exception as e:
        logger.error(f"Erro ao testar serviço de contexto: {str(e)}")
    
    return context_service

def test_conversation_analytics_service(hub):
    """Testa as funcionalidades do ConversationAnalyticsService."""
    print_separator("Testando ConversationAnalyticsService")
    
    # Inicializar o serviço de análise de conversas
    analytics_service = ConversationAnalyticsService(hub)
    
    # Gerar ID de conversa único para teste
    conversation_id = f"analytics-conv-{int(datetime.now().timestamp())}"
    customer_id = 1  # Assumindo que existe um cliente com ID 1
    
    try:
        # Criar mensagens de teste
        messages = [
            {
                "sender_id": f"customer-{customer_id}",
                "sender_type": "customer",
                "content": "Olá, estou tendo um problema com meu smartphone que comprei semana passada",
                "created_at": (datetime.now() - datetime.timedelta(minutes=30)).isoformat()
            },
            {
                "sender_id": "agent-1",
                "sender_type": "agent",
                "content": "Olá! Sinto muito pelo inconveniente. Poderia me descrever o problema?",
                "created_at": (datetime.now() - datetime.timedelta(minutes=29)).isoformat()
            },
            {
                "sender_id": f"customer-{customer_id}",
                "sender_type": "customer",
                "content": "Ele não carrega mais. Tentei diferentes carregadores, mas não funciona.",
                "created_at": (datetime.now() - datetime.timedelta(minutes=28)).isoformat()
            },
            {
                "sender_id": "agent-1",
                "sender_type": "agent",
                "content": "Entendi. Vamos iniciar um processo de suporte técnico. Você tem a nota fiscal?",
                "created_at": (datetime.now() - datetime.timedelta(minutes=26)).isoformat()
            },
            {
                "sender_id": f"customer-{customer_id}",
                "sender_type": "customer",
                "content": "Sim, comprei na loja em São Paulo. Tenho a nota fiscal aqui.",
                "created_at": (datetime.now() - datetime.timedelta(minutes=25)).isoformat()
            }
        ]
        
        # Testar armazenamento de resumo de conversa
        summary = analytics_service.store_conversation_summary(
            conversation_id=conversation_id,
            customer_id=customer_id,
            channel="whatsapp",
            messages=messages,
            metadata={"source": "test"}
        )
        
        logger.info(f"Resumo de conversa armazenado: {json.dumps(summary, indent=2)}")
        
        # Testar recuperação de análise
        analysis = analytics_service.get_conversation_analysis(conversation_id)
        logger.info(f"Análise recuperada: {json.dumps(analysis, indent=2)}")
        
        # Testar extração de tópicos comuns
        common_topics = analytics_service.get_common_topics_for_customer(customer_id)
        logger.info(f"Tópicos comuns para o cliente: {json.dumps(common_topics, indent=2)}")
        
        # Testar extração de entidades preferidas
        entity_prefs = analytics_service.get_entity_preferences(customer_id)
        logger.info(f"Preferências de entidades: {json.dumps(entity_prefs, indent=2)}")
    
    except Exception as e:
        logger.error(f"Erro ao testar serviço de análise de conversas: {str(e)}")
    
    return analytics_service

def main():
    """Função principal que executa todos os testes."""
    try:
        # Testar DataServiceHub
        hub = test_data_service_hub()
        
        if hub.pg_conn and hub.redis_client:
            # Testar serviços específicos
            product_service = test_product_service(hub)
            customer_service = test_customer_service(hub)
            context_service = test_conversation_context_service(hub)
            analytics_service = test_conversation_analytics_service(hub)
            
            print_separator("Testes Concluídos")
            logger.info("Todos os testes foram executados!")
        else:
            logger.error("Não foi possível inicializar completamente o DataServiceHub. Abortando testes.")
        
        # Fechar conexões
        hub.close()
    
    except Exception as e:
        logger.error(f"Erro durante os testes: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
