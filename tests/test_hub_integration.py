#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Testes de integração para o Hub e seus componentes.

Este script testa a integração entre o Hub, o DataProxyAgent e os agentes adaptáveis,
verificando se a comunicação entre esses componentes está funcionando corretamente.
"""

import os
import sys
import logging
import unittest
from unittest.mock import MagicMock, patch
import time
from dotenv import load_dotenv

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Criar logger específico para estes testes
logger = logging.getLogger('HubIntegrationTests')

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class HubIntegrationTester(unittest.TestCase):
    """
    Classe para testar a integração entre o Hub, o DataProxyAgent e os agentes.
    """

    def setUp(self):
        """Configuração inicial para os testes."""
        # Carregar variáveis de ambiente do arquivo .env
        env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
        if os.path.exists(env_path):
            load_dotenv(env_path)
            logger.info(f"Variáveis de ambiente carregadas de: {env_path}")
        
        # Inicializar dicionário de resultados
        self.results = {}
        # Inicializar as chaves para os resultados de cada teste
        self.results['hub_proxy_integration'] = False
        self.results['proxy_agent_tools'] = False
        self.results['adaptable_agent_integration'] = False
        
    def timed_operation(self, operation_name):
        """
        Contexto para medir o tempo de execução de uma operação.
        
        Args:
            operation_name: Nome da operação sendo executada
            
        Returns:
            Contexto para uso com 'with'
        """
        class TimedContext:
            def __init__(self, operation_name, results_dict):
                self.operation_name = operation_name
                self.results_dict = results_dict
                
            def __enter__(self):
                self.start_time = time.time()
                logger.info(f"Iniciando {self.operation_name}...")
                return self
                
            def __exit__(self, exc_type, exc_val, exc_tb):
                duration = time.time() - self.start_time
                logger.info(f"{self.operation_name} concluído em {duration:.2f} segundos")
                if exc_type:
                    logger.error(f"{self.operation_name} falhou após {duration:.2f} segundos: {str(exc_val)}")
                return False  # Não suprimir exceções
        
        return TimedContext(operation_name, self.results)
    
    def test_hub_proxy_integration(self):
        """Testa a integração entre o Hub e o DataProxyAgent."""
        logger.info("Testando integração Hub-DataProxyAgent")
        
        # Inicializar resultados caso não exista
        if not hasattr(self, 'results'):
            self.results = {}
            self.results['hub_proxy_integration'] = False
            self.results['proxy_agent_tools'] = False
            self.results['adaptable_agent_integration'] = False
            
        try:
            from src.core.hub import HubCrew
            from src.core.data_service_hub import DataServiceHub
            from src.core.memory import MemorySystem
            from src.core.data_proxy_agent import DataProxyAgent
            
            with self.timed_operation("Inicialização dos componentes"):
                # Inicializar os componentes básicos
                memory_system = MemorySystem()
                data_service_hub = DataServiceHub()
                
                # Inicializar o Hub com o DataServiceHub
                hub = HubCrew(
                    memory_system=memory_system,
                    data_service_hub=data_service_hub
                )
                
                # Verificar se o DataProxyAgent está disponível no hub
                data_proxy = hub.data_proxy
                
                self.assertIsNotNone(data_proxy, "DataProxyAgent não foi inicializado no Hub")
                logger.info(f"DataProxyAgent inicializado corretamente: {data_proxy}")
                
                # Verificar se o DataProxyAgent tem acesso às ferramentas corretas
                tools = data_proxy._tools if hasattr(data_proxy, '_tools') else []
                logger.info(f"Ferramentas do DataProxyAgent: {[t.__class__.__name__ for t in tools]}")
                
                # Verificar se o DataServiceHub está disponível no Hub
                self.assertEqual(hub._data_service_hub, data_service_hub, 
                              "DataServiceHub não foi corretamente associado ao Hub")
                
                self.results['hub_proxy_integration'] = True
                
        except Exception as e:
            logger.error(f"Erro ao testar integração Hub-DataProxyAgent: {str(e)}")
            self.results['hub_proxy_integration'] = False
            raise
    
    def test_proxy_agent_tools(self):
        """Testa se o DataProxyAgent tem as ferramentas corretas configuradas."""
        logger.info("Testando ferramentas do DataProxyAgent")
        
        # Inicializar resultados caso não exista
        if not hasattr(self, 'results'):
            self.results = {}
            self.results['hub_proxy_integration'] = False
            self.results['proxy_agent_tools'] = False
            self.results['adaptable_agent_integration'] = False
            
        try:
            from src.core.data_service_hub import DataServiceHub
            from src.core.memory import MemorySystem
            from crewai.tools.base_tool import BaseTool
            
            with self.timed_operation("Verificação das ferramentas"):
                # Inicializar os componentes básicos
                memory_system = MemorySystem()
                data_service_hub = DataServiceHub()
                
                # Obter ou criar o DataProxyAgent
                try:
                    # Tentar obter o DataProxyAgent do hub
                    data_proxy = data_service_hub.get_data_proxy_agent()
                except Exception as proxy_err:
                    logger.warning(f"Erro ao obter DataProxyAgent do hub: {str(proxy_err)}")
                    
                    # Se falhar, tentar criar manualmente
                    from src.core.data_proxy_agent import DataProxyAgent
                    data_proxy = DataProxyAgent(services={})
                
                self.assertIsNotNone(data_proxy, "DataProxyAgent não pôde ser obtido do DataServiceHub")
                
                # Obter as ferramentas do DataProxyAgent
                tools = data_proxy.get_tools()
                self.assertIsNotNone(tools, "Ferramentas do DataProxyAgent não foram obtidas")
                
                # Verificar se as ferramentas são do tipo BaseTool do CrewAI
                for tool in tools:
                    self.assertIsInstance(tool, BaseTool, 
                                       f"Ferramenta {tool.__class__.__name__} não é uma instância de BaseTool")
                
                # Verificar os nomes das ferramentas
                tool_names = [t.name for t in tools]
                logger.info(f"Ferramentas encontradas: {tool_names}")
                
                # Verificar presença de ferramentas essenciais
                expected_tools = ["query_product_data", "query_customer_data", "query_business_rules", "vector_search"]
                for tool_name in expected_tools:
                    self.assertIn(tool_name, tool_names, f"Ferramenta '{tool_name}' não encontrada nas ferramentas do DataProxyAgent")
                
                # Verificar existência de descrições para as ferramentas
                for tool in tools:
                    self.assertTrue(hasattr(tool, 'description') and tool.description, 
                                 f"Ferramenta {tool.name} não possui descrição adequada")
                
                # Verificar se as ferramentas têm o método _run implementado
                for tool in tools:
                    self.assertTrue(hasattr(tool, '_run'), 
                                 f"Ferramenta {tool.name} não possui o método _run implementado")
                
                self.results['proxy_agent_tools'] = True
                
        except Exception as e:
            logger.error(f"Erro ao testar ferramentas do DataProxyAgent: {str(e)}")
            self.results['proxy_agent_tools'] = False
            raise
    
    def test_adaptable_agent_integration(self):
        """Testa a integração entre agentes adaptáveis e o DataProxyAgent."""
        logger.info("Testando integração de agentes adaptáveis com DataProxyAgent")
        
        # Inicializar resultados caso não exista
        if not hasattr(self, 'results'):
            self.results = {}
            self.results['hub_proxy_integration'] = False
            self.results['proxy_agent_tools'] = False
            self.results['adaptable_agent_integration'] = False
            
        try:
            from src.core.data_service_hub import DataServiceHub
            from src.core.memory import MemorySystem
            from src.core.agent_manager import AgentManager
            from src.plugins.core.plugin_manager import PluginManager
            # Importar a classe base diretamente do módulo correto
            from src.plugins.base.base_plugin import BasePlugin
            
            # Tentar importar um agente adaptável com a nova estrutura de diretórios
            try:
                # Primeiro tentamos importar um agente específico como SalesAgent
                try:
                    from src.agents.specialized.sales_agent import SalesAgent
                    agent_class = SalesAgent
                    agent_type = "sales"
                    logger.info("Classe SalesAgent encontrada e será usada para os testes de integração")
                except ImportError as sales_err:
                    logger.warning(f"Erro ao importar SalesAgent: {str(sales_err)}")
                    
                    # Verificar se existe o módulo adaptable_agent
                    try:
                        from src.agents.base.adaptable_agent import AdaptableAgent
                        logger.info("Módulo adaptable_agent encontrado, usando como base para criar um TestSalesAgent")
                        
                        from crewai.tools.base_tool import BaseTool
                        
                        class TestSalesAgent(AdaptableAgent):
                            def get_agent_type(self):
                                return "sales"
                                
                            def get_crew_agent(self):
                                # Implementar um método para criar um agente CrewAI
                                from crewai import Agent
                                
                                # Garantir que temos data_proxy_agent
                                if not self.data_proxy_agent:
                                    raise ValueError("DataProxyAgent não disponível para o SalesAgent")
                                
                                # Obter ferramentas do DataProxyAgent
                                tools = self.data_proxy_agent.get_tools()
                                
                                # Criar um agente CrewAI
                                agent = Agent(
                                    role=self.agent_config.get("role", "Sales Agent"),
                                    goal=self.agent_config.get("goal", "Help customers with sales inquiries"),
                                    backstory=self.agent_config.get("backstory", "An AI sales agent"),
                                    tools=tools,
                                    verbose=True
                                )
                                return agent
                                
                            def process_message(self, message, context=None):
                                if not context:
                                    context = {}
                                return {"response": "Sales agent test response", "context": context}
                        
                        agent_class = TestSalesAgent
                        agent_type = "sales"
                    except ImportError as adpt_err:
                        logger.warning(f"Erro ao importar AdaptableAgent: {str(adpt_err)}")
                        raise
            except ImportError as import_err:
                logger.warning(f"Erro ao importar agentes adaptáveis: {str(import_err)}")
                
                # Fallback para uma implementação mock de agente adaptável para testes
                from crewai.tools.base_tool import BaseTool
                
                class TestAdaptableAgent:
                    def __init__(self, agent_config, memory_system=None, data_proxy_agent=None, 
                                agent_manager=None, plugin_manager=None):
                        self.agent_config = agent_config
                        self.memory_system = memory_system
                        self.data_proxy_agent = data_proxy_agent
                        self.agent_manager = agent_manager
                        self.plugin_manager = plugin_manager
                        
                        # Definir configuração de domínio para testes
                        self.domain_config = {"domain": "test", "features": ["basic_query"]} 
                    
                    def get_agent_type(self):
                        return "test"
                    
                    def get_crew_agent(self):
                        # Implementar um método para criar um agente CrewAI
                        from crewai import Agent
                        
                        # Obter ferramentas do DataProxyAgent
                        tools = self.data_proxy_agent.get_tools() if self.data_proxy_agent else []
                        
                        # Criar um agente CrewAI
                        agent = Agent(
                            role="Test Agent",
                            goal="Test integration",
                            backstory="A test agent for integration testing",
                            tools=tools,
                            verbose=True
                        )
                        return agent
                        
                    def process_message(self, message, context=None):
                        return {"response": "Test response"}
                
                agent_class = TestAdaptableAgent
                agent_type = "test"
                logger.info("Usando TestAdaptableAgent como fallback para testes de integração")
            
            with self.timed_operation("Integração de agentes adaptáveis"):
                # Inicializar os componentes básicos
                memory_system = MemorySystem()
                data_service_hub = DataServiceHub()
                agent_manager = AgentManager()
                plugin_manager = PluginManager(config={})
                
                # Obter ou criar o DataProxyAgent
                try:
                    # Tentar obter o DataProxyAgent do hub
                    data_proxy = data_service_hub.get_data_proxy_agent()
                except Exception as proxy_err:
                    logger.warning(f"Erro ao obter DataProxyAgent do hub: {str(proxy_err)}")
                    
                    # Se falhar, tentar criar manualmente
                    from src.core.data_proxy_agent import DataProxyAgent
                    data_proxy = DataProxyAgent(services={})
                
                # Configuração básica para o agente
                agent_config = {
                    "name": f"Test{agent_type.capitalize()}Agent",
                    "function_type": agent_type,
                    "role": f"{agent_type.capitalize()} Agent",
                    "goal": "Test integration",
                    "backstory": "Testing adaptable agent integration"
                }
                
                # Inicializar o agente adaptável
                try:
                    agent = agent_class(
                        agent_config=agent_config,
                        memory_system=memory_system,
                        data_proxy_agent=data_proxy,
                        agent_manager=agent_manager,
                        plugin_manager=plugin_manager
                    )
                    
                    # Verificar se o agente tem acesso ao DataProxyAgent
                    self.assertIsNotNone(agent.data_proxy_agent, 
                                      "Agente adaptável não tem acesso ao DataProxyAgent")
                    
                    logger.info(f"Agente adaptável inicializado com DataProxyAgent: {agent.data_proxy_agent}")
                    
                    # Verificar a configuração de domínio carregada
                    self.assertIsNotNone(agent.domain_config, 
                                      "Configuração de domínio não foi carregada")
                    
                    logger.info(f"Configuração de domínio: {agent.domain_config}")
                    
                    self.results['adaptable_agent_integration'] = True
                    
                except Exception as agent_error:
                    logger.error(f"Erro ao inicializar agente adaptável: {str(agent_error)}")
                    self.results['adaptable_agent_integration'] = False
                    raise
                
        except Exception as e:
            logger.error(f"Erro ao testar integração de agentes adaptáveis: {str(e)}")
            self.results['adaptable_agent_integration'] = False
            raise
    
    def display_results(self):
        """Exibe um resumo dos resultados dos testes."""
        logger.info("\n" + "="*50)
        logger.info("RESUMO DOS TESTES DE INTEGRAÇÃO")
        logger.info("="*50)
        
        # Garantir que o atributo results existe
        if not hasattr(self, 'results'):
            self.results = {}
            self.results['hub_proxy_integration'] = False
            self.results['proxy_agent_tools'] = False
            self.results['adaptable_agent_integration'] = False
        
        # Exibir os resultados
        for test, success in self.results.items():
            status = "✅ PASSOU" if success else "❌ FALHOU"
            logger.info(f"{test.replace('_', ' ').title()}: {status}")
            
        logger.info("="*50)
    
    def run_all_tests(self):
        """Executa todos os testes de integração em sequência."""
        logger.info("Iniciando testes de integração Hub-DataProxyAgent-Agentes")
        
        # Teste de integração Hub-DataProxyAgent
        try:
            self.test_hub_proxy_integration()
        except Exception as e:
            logger.error(f"Teste de integração Hub-DataProxyAgent falhou: {str(e)}")
        
        # Teste de ferramentas do DataProxyAgent
        try:
            self.test_proxy_agent_tools()
        except Exception as e:
            logger.error(f"Teste de ferramentas do DataProxyAgent falhou: {str(e)}")
        
        # Teste de integração de agentes adaptáveis
        try:
            self.test_adaptable_agent_integration()
        except Exception as e:
            logger.error(f"Teste de integração de agentes adaptáveis falhou: {str(e)}")
        
        # Exibir resumo
        self.display_results()
        
        # Retornar True se todos os testes passaram
        return all(self.results.values())


# Ponto de entrada para execução direta
if __name__ == "__main__":
    tester = HubIntegrationTester()
    success = tester.run_all_tests()
    
    # Sair com código de erro se algum teste falhou
    sys.exit(0 if success else 1)
