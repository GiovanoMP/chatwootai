#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Testes unitários para a GenericCrew.

Este script testa a funcionalidade da GenericCrew, verificando se ela pode ser
instanciada corretamente a partir de configurações YAML e se ela funciona como esperado
em diferentes cenários e domínios.
"""

import os
import sys
import logging
import unittest
from unittest.mock import MagicMock, patch
import json
import yaml
import tempfile
import redis
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
logger = logging.getLogger('GenericCrewTests')

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importar os módulos necessários
from src.core.crews.generic_crew import GenericCrew
from src.core.crews.crew_factory import CrewFactory
from src.core.domain.domain_manager import DomainManager
from src.core.data_proxy_agent import DataProxyAgent


class GenericCrewTester(unittest.TestCase):
    """
    Classe para testar a funcionalidade da GenericCrew.
    """

    def setUp(self):
        """Configuração inicial para os testes."""
        # Usar os diretórios de domínio reais
        self.domains_dir = Path("/home/giovano/Projetos/Chatwoot V4/config/domains")
        
        # Criar mocks para dependências
        self.mock_data_proxy_agent = MagicMock(spec=DataProxyAgent)
        
        # Inicializar o DomainManager com os diretórios reais
        self.mock_redis_client = MagicMock(spec=redis.Redis)
        self.mock_redis_client.get.return_value = None  # Simular cache vazio inicialmente
        
        # Usar o DomainManager real com o diretório de domínios real
        self.domain_manager = DomainManager(
            domains_dir=self.domains_dir,
            redis_client=self.mock_redis_client
        )
        
        # Inicializar o CrewFactory com o DomainManager real
        self.crew_factory = CrewFactory(
            domain_manager=self.domain_manager,
            data_proxy_agent=self.mock_data_proxy_agent
        )
        
    def tearDown(self):
        """Limpeza após os testes."""
        pass
    
    def test_generic_crew_initialization(self):
        """Testa se a GenericCrew pode ser inicializada corretamente a partir de uma configuração YAML."""
        # Criar uma GenericCrew usando o CrewFactory para o domínio de cosméticos
        crew = self.crew_factory.create_crew("sales_crew", "cosmetics")
        
        # Verificar se a crew foi criada corretamente
        self.assertIsNotNone(crew)
        self.assertIsInstance(crew, GenericCrew)
        self.assertEqual(crew.name, "CosmeticsSalesCrew")
        
        # Verificar se a crew tem agentes
        self.assertGreater(len(crew.agents), 0)
        
        # Verificar se a crew tem tarefas
        self.assertGreater(len(crew.tasks), 0)
        
        logger.info("✅ GenericCrew inicializada com sucesso a partir da configuração YAML")
    
    def test_generic_crew_run(self):
        """Testa se a GenericCrew pode executar tarefas corretamente."""
        # Configurar o mock para simular a execução da crew
        mock_crew_kickoff = MagicMock(return_value="Resposta personalizada para o cliente")
        
        # Criar uma GenericCrew usando o CrewFactory para o domínio de cosméticos
        with patch('src.core.crews.generic_crew.Crew.kickoff', mock_crew_kickoff):
            crew = self.crew_factory.create_crew("sales_crew", "cosmetics")
            
            # Executar a crew com uma consulta de teste
            result = crew.process_message("Você tem creme para as mãos?")
            
            # Verificar se a crew foi executada e retornou o resultado esperado
            self.assertEqual(result, "Resposta personalizada para o cliente")
            mock_crew_kickoff.assert_called_once()
            
        logger.info("✅ GenericCrew executou tarefas com sucesso")
    
    def test_generic_crew_with_different_domains(self):
        """Testa se a GenericCrew pode ser adaptada para diferentes domínios."""
        # Criar crews para diferentes domínios reais
        cosmetics_crew = self.crew_factory.create_crew("sales_crew", "cosmetics")
        health_crew = self.crew_factory.create_crew("sales_crew", "health")
        retail_crew = self.crew_factory.create_crew("sales_crew", "retail")
        
        # Verificar se as crews foram criadas corretamente
        self.assertIsNotNone(cosmetics_crew)
        self.assertIsNotNone(health_crew)
        self.assertIsNotNone(retail_crew)
        
        # Verificar se as crews têm nomes diferentes
        self.assertEqual(cosmetics_crew.name, "CosmeticsSalesCrew")
        self.assertEqual(health_crew.name, "HealthSalesCrew")
        self.assertEqual(retail_crew.name, "RetailSalesCrew")
        
        # Verificar se as crews têm agentes
        self.assertGreater(len(cosmetics_crew.agents), 0)
        self.assertGreater(len(health_crew.agents), 0)
        self.assertGreater(len(retail_crew.agents), 0)
        
        logger.info("✅ GenericCrew adaptada com sucesso para diferentes domínios")


# Ponto de entrada para execução direta
if __name__ == "__main__":
    unittest.main()
