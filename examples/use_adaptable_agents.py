#!/usr/bin/env python3
"""
Exemplo de uso dos agentes adaptáveis para diferentes domínios de negócio.

Este script demonstra como utilizar os agentes adaptáveis do ChatwootAI
para processar mensagens em diferentes domínios de negócio.
"""
import os
import sys
import logging
from typing import Dict, Any

# Adiciona o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.domain import DomainManager
from src.plugins.plugin_manager import PluginManager
from src.agents.adaptable import SalesAgent, SupportAgent, SchedulingAgent


# Configura o logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def process_message(message: str, domain_name: str, agent_type: str) -> Dict[str, Any]:
    """
    Processa uma mensagem usando o agente adaptável apropriado.
    
    Args:
        message: Mensagem a ser processada
        domain_name: Nome do domínio de negócio
        agent_type: Tipo de agente (sales, support, scheduling)
        
    Returns:
        Dict[str, Any]: Resultado do processamento
    """
    # Inicializa o gerenciador de domínios
    domain_manager = DomainManager()
    
    # Altera para o domínio especificado
    if not domain_manager.switch_domain(domain_name):
        logger.error(f"Não foi possível carregar o domínio: {domain_name}")
        return {"error": f"Domínio não encontrado: {domain_name}"}
    
    # Inicializa o gerenciador de plugins
    plugin_manager = PluginManager()
    
    # Configuração básica do agente
    agent_config = {
        "name": f"{domain_name}_{agent_type}_agent",
        "erp": {
            "type": "odoo",
            "api_url": os.environ.get("ODOO_API_URL", "http://localhost:8000/api"),
            "api_key": os.environ.get("ODOO_API_KEY", "test_key")
        },
        "vector_db": {
            "url": os.environ.get("QDRANT_URL", "http://localhost:6333"),
            "api_key": os.environ.get("QDRANT_API_KEY", "")
        }
    }
    
    # Cria o agente apropriado
    if agent_type == "sales":
        agent = SalesAgent(agent_config, domain_manager, plugin_manager)
    elif agent_type == "support":
        agent = SupportAgent(agent_config, domain_manager, plugin_manager)
    elif agent_type == "scheduling":
        agent = SchedulingAgent(agent_config, domain_manager, plugin_manager)
    else:
        logger.error(f"Tipo de agente não suportado: {agent_type}")
        return {"error": f"Tipo de agente não suportado: {agent_type}"}
    
    # Processa a mensagem de acordo com o tipo de agente
    if agent_type == "sales":
        # Simula uma consulta sobre produtos
        return agent.process_product_inquiry(message)
    
    elif agent_type == "support":
        # Simula uma consulta de suporte
        return agent.process_support_query(message)
    
    elif agent_type == "scheduling":
        # Simula uma consulta sobre serviços disponíveis
        return agent.get_services()
    
    return {"error": "Processamento não implementado para este tipo de agente"}


def main():
    """Função principal."""
    # Exemplos de mensagens para diferentes domínios e agentes
    examples = [
        {
            "message": "Quais são os produtos para pele oleosa?",
            "domain": "cosmetics",
            "agent_type": "sales"
        },
        {
            "message": "Como posso devolver um produto que não gostei?",
            "domain": "retail",
            "agent_type": "support"
        },
        {
            "message": "Quero agendar uma consulta dermatológica",
            "domain": "healthcare",
            "agent_type": "scheduling"
        }
    ]
    
    # Processa cada exemplo
    for i, example in enumerate(examples):
        print(f"\n--- Exemplo {i+1} ---")
        print(f"Domínio: {example['domain']}")
        print(f"Tipo de agente: {example['agent_type']}")
        print(f"Mensagem: {example['message']}")
        print("\nProcessando...")
        
        try:
            result = process_message(
                example["message"],
                example["domain"],
                example["agent_type"]
            )
            
            print("\nResultado:")
            print(result)
            
        except Exception as e:
            logger.exception(f"Erro ao processar exemplo {i+1}")
            print(f"\nErro: {str(e)}")
    
    print("\nExecução concluída!")


if __name__ == "__main__":
    main()
