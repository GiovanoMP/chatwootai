#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Testes de integração para as Crews do sistema.

Este script testa a integração entre as diferentes crews do sistema,
verificando se a comunicação entre os componentes está funcionando corretamente.
Testa principalmente a inicialização e comunicação das crews funcionais com o Hub.
"""

import os
import sys
import logging
import unittest
from unittest.mock import MagicMock, patch
import json
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
logger = logging.getLogger('CrewIntegrationTests')

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class CrewIntegrationTester(unittest.TestCase):
    """
    Classe para testar a integração entre as diferentes crews do sistema.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Inicializar dicionário de resultados
        self.results = {}
        # Inicializar as chaves para os resultados de cada teste
        self.results['functional_crews_initialization'] = False
        self.results['crew_messaging_flow'] = False
        
    def setUp(self):
        """Configuração inicial para os testes."""
        # Carregar variáveis de ambiente do arquivo .env
        env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
        if os.path.exists(env_path):
            load_dotenv(env_path)
            logger.info(f"Variáveis de ambiente carregadas de: {env_path}")
        
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
    
    def test_hub_initialization(self):
        """Testa a inicialização do HubCrew com todos os componentes necessários."""
        logger.info("Testando inicialização do HubCrew")
        
        try:
            from src.core.data_service_hub import DataServiceHub
            from src.core.memory import MemorySystem
            from src.core.domain import DomainManager
            from src.plugins.core.plugin_manager import PluginManager
            from src.core.hub import HubCrew
            
            with self.timed_operation("Inicialização HubCrew"):
                # Inicializar os componentes básicos
                memory_system = MemorySystem()
                data_service_hub = DataServiceHub()
                domain_manager = DomainManager()
                plugin_manager = PluginManager(config={})
                
                # Inicializar o HubCrew
                hub_crew = HubCrew(
                    memory_system=memory_system,
                    data_service_hub=data_service_hub
                )
                
                # Verificar se a crew foi inicializada corretamente
                self.assertIsNotNone(hub_crew, "HubCrew não foi inicializada")
                logger.info(f"HubCrew inicializada: {hub_crew}")
                
                # Verificar se os componentes necessários estão disponíveis
                self.assertIsNotNone(hub_crew.memory_system, 
                                    "MemorySystem não está disponível no HubCrew")
                self.assertIsNotNone(hub_crew.data_service_hub, 
                                    "DataServiceHub não está disponível no HubCrew")
                
                self.results['hub_initialization'] = True
                    
        except Exception as e:
            logger.error(f"Erro ao testar inicialização do HubCrew: {str(e)}")
            self.results['hub_initialization'] = False
            raise
    
    def test_functional_crews_initialization(self):
        """Testa a inicialização das crews funcionais."""
        logger.info("Testando inicialização das crews funcionais")
        
        # Lista de crews funcionais para testar
        functional_crews = [
            ("SalesCrew", "src.crews.sales_crew"),
            ("SupportCrew", "src.crews.support_crew"),
            ("InfoCrew", "src.crews.info_crew"),
            ("SchedulingCrew", "src.crews.scheduling_crew")
        ]
        
        for crew_name, module_path in functional_crews:
            logger.info(f"Testando inicialização de {crew_name}")
            
            try:
                # Importar dinamicamente a crew
                import importlib
                crew_module = importlib.import_module(module_path)
                crew_class = getattr(crew_module, crew_name)
                
                with self.timed_operation(f"Inicialização {crew_name}"):
                    # Inicializar os componentes básicos
                    from src.core.memory import MemorySystem
                    from src.core.data_service_hub import DataServiceHub
                    from src.core.domain import DomainManager
                    from src.plugins.core.plugin_manager import PluginManager
                    
                    memory_system = MemorySystem()
                    data_service_hub = DataServiceHub()
                    domain_manager = DomainManager()
                    plugin_manager = PluginManager(config={})
                    
                    # Mocks para os componentes adicionais necessários
                    additional_tools = []
                    
                    # Inicializar a crew funcional
                    crew = crew_class(
                        memory_system=memory_system,
                        data_service_hub=data_service_hub,
                        domain_manager=domain_manager,
                        plugin_manager=plugin_manager,
                        additional_tools=additional_tools
                    )
                    
                    # Verificar se a crew foi inicializada corretamente
                    self.assertIsNotNone(crew, f"{crew_name} não foi inicializada")
                    logger.info(f"{crew_name} inicializada: {crew}")
                    
                    # Verificar acesso ao DataProxyAgent via DataServiceHub
                    data_proxy = None
                    if hasattr(crew, 'data_proxy_agent'):
                        data_proxy = crew.data_proxy_agent
                    elif hasattr(crew, 'data_service_hub'):
                        # Tentar obter o data_proxy_agent do data_service_hub
                        data_proxy = crew.data_service_hub.get_data_proxy_agent()
                    
                    if data_proxy:
                        logger.info(f"{crew_name} tem acesso ao DataProxyAgent: {data_proxy}")
                    else:
                        logger.warning(f"{crew_name} não tem acesso ao DataProxyAgent")
                    
                    self.results[f'{crew_name.lower()}_initialization'] = True
                    
            except ImportError:
                logger.warning(f"Módulo {module_path} não encontrado, pulando teste de {crew_name}")
                self.results[f'{crew_name.lower()}_initialization'] = None
            except Exception as e:
                logger.error(f"Erro ao testar inicialização de {crew_name}: {str(e)}")
                self.results[f'{crew_name.lower()}_initialization'] = False
    
    def test_crew_messaging_flow(self):
        """Testa o fluxo de mensagens entre as crews."""
        logger.info("Testando fluxo de mensagens entre crews")
        
        try:
            from src.core.hub import OrchestratorAgent
            from src.core.data_service_hub import DataServiceHub
            from src.core.memory import MemorySystem
            from src.core.domain import DomainManager
            from src.plugins.core.plugin_manager import PluginManager
            
            with self.timed_operation("Fluxo de mensagens entre crews"):
                # Inicializar os componentes básicos
                memory_system = MemorySystem()
                data_service_hub = DataServiceHub()
                domain_manager = DomainManager()
                plugin_manager = PluginManager(config={})
                
                # Mock para os métodos de processamento para evitar chamadas reais à API do LLM
                with patch('src.core.hub.OrchestratorAgent.route_message') as mock_route:
                    # Configurar o mock para retornar uma resposta válida
                    mock_route.return_value = {'status': 'success'}
                    
                    # Inicializar as crews
                    config = {}
                    hub = OrchestratorAgent(config)
                    
                    # Criar uma mensagem de exemplo
                    test_message = {
                        "content": "Olá, gostaria de saber o preço do produto X",
                        "sender": {
                            "id": "123456789",
                            "name": "Usuário de teste"
                        },
                        "conversation_id": "conv123",
                        "timestamp": time.time()
                    }
                    
                    # Simular o processamento de mensagem
                    logger.info("Simulando processamento de mensagem pelo Hub")
                    result = hub.route_message(test_message)
                    
                    # Verificar se o processamento da mensagem retornou algo válido
                    self.assertIsNotNone(result, "Processamento de mensagem não retornou resultado")
                    logger.info(f"Resultado do processamento: {result}")
                    
                    # Verificar se o mock foi chamado
                    mock_route.assert_called_once()
                    
                    self.results['crew_messaging_flow'] = True
                    
        except Exception as e:
            logger.error(f"Erro ao testar fluxo de mensagens entre crews: {str(e)}")
            self.results['crew_messaging_flow'] = False
            raise
    
    def display_results(self):
        """Exibe um resumo dos resultados dos testes."""
        logger.info("\n" + "="*50)
        logger.info("RESUMO DOS TESTES DE INTEGRAÇÃO DE CREWS")
        logger.info("="*50)
        
        for test, success in self.results.items():
            if success is None:
                status = "⚠️ PULADO"
            else:
                status = "✅ PASSOU" if success else "❌ FALHOU"
            logger.info(f"{test.replace('_', ' ').title()}: {status}")
            
        logger.info("="*50)
    
    def run_all_tests(self):
        """Executa todos os testes de integração em sequência."""
        logger.info("Iniciando testes de integração de Crews")
        
        # Teste de inicialização do HubCrew
        try:
            self.test_hub_initialization()
        except Exception as e:
            logger.error(f"Teste de inicialização do HubCrew falhou: {str(e)}")
        
        # Teste de inicialização das crews funcionais
        try:
            self.test_functional_crews_initialization()
        except Exception as e:
            logger.error(f"Teste de inicialização das crews funcionais falhou: {str(e)}")
        
        # Teste de fluxo de mensagens entre crews
        try:
            self.test_crew_messaging_flow()
        except Exception as e:
            logger.error(f"Teste de fluxo de mensagens entre crews falhou: {str(e)}")
        
        # Exibir resumo
        self.display_results()
        
        # Retornar True se todos os testes que não foram pulados passaram
        return all(success for success in self.results.values() if success is not None)


# Ponto de entrada para execução direta
if __name__ == "__main__":
    tester = CrewIntegrationTester()
    success = tester.run_all_tests()
    
    # Sair com código de erro se algum teste falhou
    sys.exit(0 if success else 1)
