#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Testes de integração para a arquitetura multi-tenant.

Este script testa a integração entre os componentes da arquitetura multi-tenant,
verificando se o CrewFactory e a GenericCrew funcionam corretamente com diferentes
configurações de domínio e se o mapeamento de customer_id para domain_name está
funcionando como esperado.
"""

import os
import sys
import logging
import unittest
from unittest.mock import MagicMock, patch
import json
import redis
import yaml
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Criar logger específico para estes testes
logger = logging.getLogger('MultiTenantIntegrationTests')

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importar os módulos necessários
from src.core.crews.generic_crew import GenericCrew
from src.core.crews.crew_factory import CrewFactory
from src.core.domain.domain_manager import DomainManager
from src.core.data_proxy_agent import DataProxyAgent
from src.core.data_service_hub import DataServiceHub
from src.core.hub import HubCrew


class MultiTenantIntegrationTester(unittest.TestCase):
    """
    Classe para testar a integração da arquitetura multi-tenant.
    """

    def setUp(self):
        """Configuração inicial para os testes."""
        # Criar mocks para dependências
        self.mock_redis_client = MagicMock(spec=redis.Redis)
        self.mock_redis_client.get.return_value = None  # Simular cache vazio inicialmente
        
        # Mock para DataServiceHub
        self.mock_data_service_hub = MagicMock(spec=DataServiceHub)
        
        # Configurar o mock do DataProxyAgent
        self.mock_data_proxy_agent = MagicMock(spec=DataProxyAgent)
        self.mock_data_proxy_agent.query_customer_data.return_value = {
            "customer_id": "customer123",
            "domain": "cosmetics",
            "name": "Cliente Teste",
            "preferences": {
                "product_categories": ["skincare", "makeup"]
            }
        }
        
        # Configurar o DomainManager com os diretórios reais de configuração
        self.domain_manager = DomainManager(
            domains_dir=Path("/home/giovano/Projetos/Chatwoot V4/config/domains"),
            redis_client=self.mock_redis_client
        )
        
        # Patch para o método load_domain_config para usar os arquivos reais
        self.original_load_domain_config = self.domain_manager.load_domain_config
        self.domain_manager.load_domain_config = self._mock_load_domain_config
        
        # Inicializar o CrewFactory
        self.crew_factory = CrewFactory(
            domain_manager=self.domain_manager,
            data_proxy_agent=self.mock_data_proxy_agent
        )
        
        # Inicializar o HubCrew
        self.hub_crew = HubCrew(
            crew_factory=self.crew_factory,
            domain_manager=self.domain_manager,
            data_proxy_agent=self.mock_data_proxy_agent
        )
        
    def tearDown(self):
        """Limpeza após os testes."""
        # Restaurar o método original
        if hasattr(self, 'original_load_domain_config'):
            self.domain_manager.load_domain_config = self.original_load_domain_config
    
    def _mock_load_domain_config(self, domain_name):
        """Mock para carregar configurações de domínio dos arquivos reais."""
        config_path = Path(f"/home/giovano/Projetos/Chatwoot V4/config/domains/{domain_name}/config.yaml")
        if not config_path.exists():
            return None
        
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        return config
    
    def test_domain_manager_load_config(self):
        """Testa se o DomainManager carrega corretamente as configurações dos domínios."""
        # Carregar configurações para diferentes domínios
        cosmetics_config = self.domain_manager.get_domain_config("cosmetics")
        health_config = self.domain_manager.get_domain_config("health")
        retail_config = self.domain_manager.get_domain_config("retail")
        
        # Verificar se as configurações foram carregadas corretamente
        self.assertIsNotNone(cosmetics_config)
        self.assertIsNotNone(health_config)
        self.assertIsNotNone(retail_config)
        
        # Verificar se as configurações contêm as seções esperadas
        self.assertIn("crew", cosmetics_config)
        self.assertIn("agents", cosmetics_config)
        self.assertIn("crew", health_config)
        self.assertIn("agents", health_config)
        self.assertIn("crew", retail_config)
        self.assertIn("agents", retail_config)
        
        logger.info("✅ DomainManager carregou configurações corretamente")
    
    def test_crew_factory_create_crew(self):
        """Testa se o CrewFactory cria corretamente crews para diferentes domínios."""
        # Criar crews para diferentes domínios
        cosmetics_sales_crew = self.crew_factory.create_crew("sales_crew", "cosmetics")
        health_sales_crew = self.crew_factory.create_crew("sales_crew", "health")
        retail_sales_crew = self.crew_factory.create_crew("sales_crew", "retail")
        
        # Verificar se as crews foram criadas corretamente
        self.assertIsNotNone(cosmetics_sales_crew)
        self.assertIsNotNone(health_sales_crew)
        self.assertIsNotNone(retail_sales_crew)
        
        # Verificar se as crews são instâncias de GenericCrew
        self.assertIsInstance(cosmetics_sales_crew, GenericCrew)
        self.assertIsInstance(health_sales_crew, GenericCrew)
        self.assertIsInstance(retail_sales_crew, GenericCrew)
        
        # Verificar se as crews têm os nomes corretos
        self.assertEqual(cosmetics_sales_crew.name, "CosmeticsSalesCrew")
        self.assertEqual(health_sales_crew.name, "HealthSalesCrew")
        self.assertEqual(retail_sales_crew.name, "RetailSalesCrew")
        
        logger.info("✅ CrewFactory criou crews corretamente para diferentes domínios")
    
    def test_hub_crew_register_conversation(self):
        """Testa se o HubCrew registra corretamente uma conversa e determina o domínio baseado no customer_id."""
        # Configurar o mock do DataProxyAgent para retornar dados de cliente com domínio específico
        self.mock_data_proxy_agent.query_customer_data.return_value = {
            "customer_id": "customer123",
            "domain": "cosmetics",
            "name": "Cliente Teste",
            "preferences": {
                "product_categories": ["skincare", "makeup"]
            }
        }
        
        # Registrar uma conversa
        conversation_context = self.hub_crew.register_conversation(
            conversation_id="conv123",
            customer_id="customer123"
        )
        
        # Verificar se o contexto da conversa foi criado corretamente
        self.assertIsNotNone(conversation_context)
        self.assertEqual(conversation_context.get("domain"), "cosmetics")
        
        # Verificar se o DataProxyAgent foi chamado para obter os dados do cliente
        self.mock_data_proxy_agent.query_customer_data.assert_called_once_with("customer123")
        
        logger.info("✅ HubCrew registrou conversa e determinou domínio corretamente")
    
    def test_multi_tenant_message_processing(self):
        """Testa o processamento de mensagens em um ambiente multi-tenant."""
        # Configurar o mock para simular a execução da crew
        mock_crew_run = MagicMock(return_value="Resposta personalizada para o cliente")
        
        # Configurar o mock do DataProxyAgent para retornar dados de cliente com domínio específico
        self.mock_data_proxy_agent.query_customer_data.return_value = {
            "customer_id": "customer123",
            "domain": "cosmetics",
            "name": "Cliente Teste",
            "preferences": {
                "product_categories": ["skincare", "makeup"]
            }
        }
        
        # Registrar uma conversa
        self.hub_crew.register_conversation(
            conversation_id="conv123",
            customer_id="customer123"
        )
        
        # Processar uma mensagem
        with patch('src.core.crews.generic_crew.Crew.run', mock_crew_run):
            response = self.hub_crew.process_message(
                conversation_id="conv123",
                message="Você tem creme para as mãos?"
            )
            
            # Verificar se a resposta foi gerada corretamente
            self.assertEqual(response, "Resposta personalizada para o cliente")
            
        logger.info("✅ Processamento de mensagens em ambiente multi-tenant funcionou corretamente")
    
    def test_domain_switching(self):
        """Testa a capacidade de mudar de domínio para um cliente."""
        # Configurar o mock do DataProxyAgent para retornar dados de cliente com domínio específico
        self.mock_data_proxy_agent.query_customer_data.return_value = {
            "customer_id": "customer123",
            "domain": "cosmetics",
            "name": "Cliente Teste",
            "preferences": {
                "product_categories": ["skincare", "makeup"]
            }
        }
        
        # Registrar uma conversa
        conversation_context = self.hub_crew.register_conversation(
            conversation_id="conv123",
            customer_id="customer123"
        )
        
        # Verificar se o domínio inicial é "cosmetics"
        self.assertEqual(conversation_context.get("domain"), "cosmetics")
        
        # Mudar o mock para retornar um domínio diferente
        self.mock_data_proxy_agent.query_customer_data.return_value = {
            "customer_id": "customer123",
            "domain": "health",
            "name": "Cliente Teste",
            "preferences": {
                "product_categories": ["supplements", "wellness"]
            }
        }
        
        # Atualizar o contexto da conversa
        updated_context = self.hub_crew.update_conversation_context(
            conversation_id="conv123",
            customer_id="customer123"
        )
        
        # Verificar se o domínio foi atualizado para "health"
        self.assertEqual(updated_context.get("domain"), "health")
        
        logger.info("✅ Mudança de domínio para um cliente funcionou corretamente")


# Ponto de entrada para execução direta
if __name__ == "__main__":
    unittest.main()
