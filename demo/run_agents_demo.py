"""
Script de demonstração para testar os agentes do ChatwootAI em ação.

Este script configura e executa uma demonstração simples do sistema ChatwootAI,
mostrando como os diferentes componentes interagem entre si.
"""

import os
import sys
import logging
import json
from typing import Dict, Any

# Adiciona o diretório raiz ao path para importar os módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.hub import OrchestratorAgent, ContextManagerAgent, IntegrationAgent
from src.core.memory import MemorySystem, SharedMemory
from src.core.cache.agent_cache import RedisAgentCache
from src.core.hub import HubCrew
from src.crews.functional_crew import FunctionalCrew
from src.services.data.data_service_hub import DataServiceHub
from src.agents.data_proxy_agent import DataProxyAgent

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)


def create_data_service_hub():
    """Cria um DataServiceHub para a demonstração."""
    # Criar um DataServiceHub configurado para o ambiente de demonstração
    data_service_hub = DataServiceHub()
    
    # Aqui podemos registrar serviços adicionais ou configurar mock services se necessário
    
    return data_service_hub


def create_memory_system():
    """Cria e configura o sistema de memória."""
    # Em um ambiente real, você usaria um cliente Redis real
    # Para demonstração, usamos um mock que simula o comportamento
    memory = SharedMemory(redis_url="redis://localhost:6379/0")
    return MemorySystem(shared_memory=memory)


def create_agent_cache():
    """Cria e configura o cache de agentes."""
    # Em um ambiente real, você usaria um cliente Redis real
    # Para demonstração, usamos um mock que simula o comportamento
    return RedisAgentCache(prefix="demo_cache:", ttl=3600)


def create_hub_crew(memory_system, data_service_hub, agent_cache):
    """Cria e configura a crew do hub."""
    
    # Cria a crew do hub usando o DataServiceHub
    hub_crew = HubCrew(
        memory_system=memory_system,
        data_service_hub=data_service_hub,
        agent_cache=agent_cache
    )
    
    return hub_crew


def create_functional_crews(memory_system, data_service_hub, agent_cache):
    """Cria e configura as crews funcionais."""
    
    # Cria a crew de vendas usando o DataServiceHub
    sales_crew = FunctionalCrew(
        crew_type="sales",
        memory_system=memory_system,
        data_service_hub=data_service_hub,
        agent_cache=agent_cache
    )
    
    # Cria a crew de suporte usando o DataServiceHub
    support_crew = FunctionalCrew(
        crew_type="support",
        memory_system=memory_system,
        data_service_hub=data_service_hub,
        agent_cache=agent_cache
    )
    
    return {
        "sales": sales_crew,
        "support": support_crew
    }


def process_message(message: Dict[str, Any], context: Dict[str, Any], hub_crew, functional_crews):
    """Processa uma mensagem através do sistema."""
    logger.info(f"Processando mensagem: {message['content']}")
    
    # Passo 1: Roteamento da mensagem pelo hub
    routing_result = hub_crew.orchestrator.route_message(message, context)
    logger.info(f"Mensagem roteada para: {routing_result['crew']} (confiança: {routing_result['confidence']})")
    
    # Passo 2: Atualização do contexto
    context = hub_crew.context_manager.update_context(message, context)
    logger.info(f"Contexto atualizado: {len(context)} itens")
    
    # Passo 3: Processamento pela crew funcional apropriada
    crew_type = routing_result["crew"]
    if crew_type in functional_crews:
        crew = functional_crews[crew_type]
        response = crew.process_message(message, context)
        logger.info(f"Resposta da crew {crew_type}: {response}")
        return response
    else:
        logger.error(f"Crew não encontrada: {crew_type}")
        return {"error": f"Crew não encontrada: {crew_type}"}


def run_demo():
    """Executa a demonstração do sistema."""
    logger.info("Iniciando demonstração do ChatwootAI")
    
    # Cria os componentes necessários
    memory_system = create_memory_system()
    agent_cache = create_agent_cache()
    data_service_hub = create_data_service_hub()
    
    # Cria as crews
    hub_crew = create_hub_crew(memory_system, data_service_hub, agent_cache)
    functional_crews = create_functional_crews(memory_system, data_service_hub, agent_cache)
    
    # Configura o contexto inicial
    context = {
        "conversation_id": "demo-123",
        "customer": {
            "id": "cust-456",
            "name": "Cliente Demonstração",
            "history": []
        }
    }
    
    # Mensagens de exemplo
    messages = [
        {"content": "Olá, gostaria de saber mais sobre os produtos de skincare"},
        {"content": "Qual é o melhor produto para pele seca?"},
        {"content": "Estou com um problema no meu último pedido, não chegou ainda"},
        {"content": "Quero comprar o hidratante facial, como faço?"}
    ]
    
    # Processa cada mensagem
    for message in messages:
        response = process_message(message, context, hub_crew, functional_crews)
        print("\n" + "-"*50)
        print(f"Mensagem: {message['content']}")
        print(f"Resposta: {response}")
        print("-"*50 + "\n")
    
    logger.info("Demonstração concluída")


if __name__ == "__main__":
    # Executa a demonstração
    run_demo()
