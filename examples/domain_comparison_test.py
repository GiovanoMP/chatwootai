#!/usr/bin/env python3
"""
Teste de comparação entre diferentes domínios de negócio.

Este script demonstra como o mesmo agente adaptável pode gerar
resultados diferentes dependendo do domínio de negócio ativo.
"""
import os
import sys
import logging
from typing import Dict, Any, List
import json
from tabulate import tabulate

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


def get_agent_config(domain_name: str, agent_type: str) -> Dict[str, Any]:
    """
    Cria uma configuração básica para o agente.
    
    Args:
        domain_name: Nome do domínio de negócio
        agent_type: Tipo de agente (sales, support, scheduling)
        
    Returns:
        Dict[str, Any]: Configuração do agente
    """
    return {
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


def compare_domains(query: str, domains: List[str], agent_type: str) -> Dict[str, Any]:
    """
    Compara as respostas do mesmo tipo de agente em diferentes domínios.
    
    Args:
        query: Consulta a ser processada
        domains: Lista de domínios a serem comparados
        agent_type: Tipo de agente a ser usado
        
    Returns:
        Dict[str, Any]: Resultados da comparação
    """
    results = {}
    domain_manager = DomainManager()
    plugin_manager = PluginManager()
    
    for domain in domains:
        logger.info(f"Processando consulta para o domínio: {domain}")
        
        # Altera para o domínio atual
        if not domain_manager.switch_domain(domain):
            logger.error(f"Não foi possível carregar o domínio: {domain}")
            results[domain] = {"error": f"Domínio não encontrado: {domain}"}
            continue
        
        # Cria o agente apropriado
        agent_config = get_agent_config(domain, agent_type)
        
        if agent_type == "sales":
            agent = SalesAgent(agent_config, domain_manager, plugin_manager)
            result = agent.process_product_inquiry(query)
        elif agent_type == "support":
            agent = SupportAgent(agent_config, domain_manager, plugin_manager)
            result = agent.process_support_query(query)
        elif agent_type == "scheduling":
            agent = SchedulingAgent(agent_config, domain_manager, plugin_manager)
            result = agent.get_services()
        else:
            result = {"error": f"Tipo de agente não suportado: {agent_type}"}
        
        results[domain] = result
    
    return results


def display_comparison_table(results: Dict[str, Any], query: str, agent_type: str):
    """
    Exibe uma tabela comparativa dos resultados.
    
    Args:
        results: Resultados da comparação
        query: Consulta processada
        agent_type: Tipo de agente usado
    """
    print(f"\n=== Comparação de Domínios para Agente: {agent_type} ===")
    print(f"Consulta: '{query}'\n")
    
    # Prepara os dados para a tabela
    table_data = []
    
    for domain, result in results.items():
        if "error" in result:
            table_data.append([domain, "ERRO", result["error"]])
        else:
            # Formata o resultado como JSON para exibição
            result_str = json.dumps(result, indent=2, ensure_ascii=False)
            table_data.append([domain, "OK", result_str])
    
    # Exibe a tabela
    headers = ["Domínio", "Status", "Resultado"]
    print(tabulate(table_data, headers=headers, tablefmt="grid"))


def main():
    """Função principal."""
    # Exemplos de consultas para diferentes tipos de agentes
    test_cases = [
        {
            "query": "Quais produtos vocês recomendam para pele sensível?",
            "agent_type": "sales",
            "domains": ["cosmetics", "healthcare", "retail"]
        },
        {
            "query": "Como faço para devolver um produto?",
            "agent_type": "support",
            "domains": ["cosmetics", "retail"]
        },
        {
            "query": "Quero agendar um serviço",
            "agent_type": "scheduling",
            "domains": ["cosmetics", "healthcare"]
        }
    ]
    
    # Processa cada caso de teste
    for i, test_case in enumerate(test_cases):
        print(f"\n\n{'='*80}")
        print(f"CASO DE TESTE #{i+1}")
        print(f"{'='*80}\n")
        
        try:
            results = compare_domains(
                test_case["query"],
                test_case["domains"],
                test_case["agent_type"]
            )
            
            display_comparison_table(
                results,
                test_case["query"],
                test_case["agent_type"]
            )
            
        except Exception as e:
            logger.exception(f"Erro ao processar caso de teste {i+1}")
            print(f"\nErro: {str(e)}")
    
    print("\n\nTestes concluídos!")


if __name__ == "__main__":
    main()
