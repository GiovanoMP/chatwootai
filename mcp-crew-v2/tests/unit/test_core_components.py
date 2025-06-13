#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Testes unitários para os componentes principais do MCP-Crew v2
Valida que os componentes individuais funcionam corretamente após a refatoração
"""

import os
import sys
import unittest
from unittest import mock
import asyncio
import json
import redis

# Adiciona o diretório raiz ao path para importações
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.core.orchestrator import DynamicMCPCrewOrchestrator
from src.core.knowledge_manager import KnowledgeManager, KnowledgeItem, KnowledgeType
from src.core.mcp_tool_discovery import MCPToolDiscovery
from src.core.mcp_connector_factory import MCPConnectorFactory
from src.core.tool_metadata import ToolMetadata
from src.config.config import Config


class TestOrchestrator(unittest.TestCase):
    """Testes unitários para o orquestrador"""
    
    def setUp(self):
        """Configuração inicial para os testes"""
        self.orchestrator = DynamicMCPCrewOrchestrator()
        self.test_account_id = "test_account"
    
    def test_initialization(self):
        """Testa a inicialização do orquestrador"""
        self.assertIsInstance(self.orchestrator.active_crews, dict)
        self.assertIsInstance(self.orchestrator.mcp_adapters, dict)
        self.assertIsInstance(self.orchestrator.execution_metrics, dict)
    
    def test_get_health_status(self):
        """Testa a obtenção do status de saúde"""
        health_status = self.orchestrator.get_health_status()
        self.assertIsInstance(health_status, dict)
        self.assertIn("status", health_status)
    
    @mock.patch('src.core.mcp_tool_discovery.tool_discovery.discover_all_tools')
    @mock.patch('src.core.knowledge_manager.knowledge_manager.store_knowledge')
    async def test_process_request_async(self, mock_store_knowledge, mock_discover_tools):
        """Testa o processamento assíncrono de requisições"""
        # Configurar mocks
        mock_discover_tools.return_value = {
            "mcp-mongodb": [
                ToolMetadata(name="find_documents", description="Encontra documentos")
            ]
        }
        mock_store_knowledge.return_value = True
        
        # Dados de teste
        request_data = {
            "account_id": self.test_account_id,
            "channel": "api",
            "payload": {
                "text": "Teste unitário",
                "sender_id": "test_user"
            }
        }
        
        # Executar método
        result = await self.orchestrator.process_request(request_data)
        
        # Verificar resultado
        self.assertIsInstance(result, dict)
        self.assertIn("success", result)


class TestKnowledgeManager(unittest.TestCase):
    """Testes unitários para o gerenciador de conhecimento"""
    
    def setUp(self):
        """Configuração inicial para os testes"""
        self.knowledge_manager = KnowledgeManager()
        self.test_account_id = "test_account"
        
        # Criar item de conhecimento para testes
        self.test_item = KnowledgeItem(
            account_id=self.test_account_id,
            knowledge_type=KnowledgeType.GENERAL,
            topic="test_topic",
            title="Test Knowledge",
            content={"key": "value"},
            source_agent="test_agent",
            tags=["test", "unit"]
        )
    
    def test_store_and_retrieve_knowledge(self):
        """Testa armazenamento e recuperação de conhecimento"""
        # Armazenar conhecimento
        result = self.knowledge_manager.store_knowledge(self.test_item)
        self.assertTrue(result)
        
        # Recuperar por ID
        retrieved_item = self.knowledge_manager.retrieve_knowledge(
            self.test_account_id, 
            self.test_item.knowledge_id
        )
        self.assertIsNotNone(retrieved_item)
        self.assertEqual(retrieved_item.title, "Test Knowledge")
    
    def test_search_knowledge(self):
        """Testa busca de conhecimento"""
        # Armazenar conhecimento primeiro
        self.knowledge_manager.store_knowledge(self.test_item)
        
        # Buscar por tópico
        items_by_topic = self.knowledge_manager.search_knowledge_by_topic(
            self.test_account_id,
            "test_topic"
        )
        self.assertIsInstance(items_by_topic, list)
        self.assertTrue(len(items_by_topic) > 0)
        
        # Buscar por conteúdo
        items_by_content = self.knowledge_manager.search_knowledge_by_content(
            self.test_account_id,
            "value"
        )
        self.assertIsInstance(items_by_content, list)
    
    def test_subscribe_and_notify(self):
        """Testa subscrição e notificação de conhecimento"""
        # Subscrever a um tópico
        self.knowledge_manager.subscribe_to_topic(
            subscriber_id="test_subscriber",
            topic="test_topic"
        )
        
        # Verificar subscrição
        subscribers = self.knowledge_manager.get_topic_subscribers("test_topic")
        self.assertIn("test_subscriber", subscribers)
        
        # Notificar (sem verificar resultado, apenas que não falha)
        self.knowledge_manager.notify_subscribers(self.test_item)


class TestMCPToolDiscovery(unittest.TestCase):
    """Testes unitários para a descoberta de ferramentas"""
    
    def setUp(self):
        """Configuração inicial para os testes"""
        self.tool_discovery = MCPToolDiscovery()
        self.test_account_id = "test_account"
    
    @mock.patch('src.core.mcp_connector_factory.mcp_connector_factory.get_connector')
    async def test_discover_tools_async(self, mock_get_connector):
        """Testa descoberta assíncrona de ferramentas"""
        # Configurar mock
        mock_connector = mock.MagicMock()
        mock_connector.tools = [
            ToolMetadata(name="test_tool", description="Test tool")
        ]
        mock_get_connector.return_value = mock_connector
        
        # Executar descoberta
        tools = await self.tool_discovery.discover_all_tools(
            self.test_account_id,
            force_refresh=True
        )
        
        # Verificar resultado
        self.assertIsInstance(tools, dict)
    
    def test_get_tools_summary(self):
        """Testa obtenção de resumo de ferramentas"""
        # Configurar ferramentas descobertas
        self.tool_discovery.discovered_tools = {
            self.test_account_id: {
                "mcp-mongodb": [
                    ToolMetadata(name="find", description="Find documents")
                ],
                "mcp-chatwoot": [
                    ToolMetadata(name="send", description="Send message")
                ]
            }
        }
        
        # Obter resumo
        summary = self.tool_discovery.get_tools_summary(self.test_account_id)
        
        # Verificar resultado
        self.assertIsInstance(summary, dict)
        self.assertIn("total_tools", summary)
        self.assertIn("mcps", summary)


class TestMCPConnectorFactory(unittest.TestCase):
    """Testes unitários para a fábrica de conectores"""
    
    def setUp(self):
        """Configuração inicial para os testes"""
        self.connector_factory = MCPConnectorFactory()
    
    def test_get_mongodb_connector(self):
        """Testa obtenção de conector MongoDB"""
        connector = self.connector_factory.get_connector("mcp-mongodb")
        self.assertIsNotNone(connector)
        self.assertTrue(hasattr(connector, "tools"))
    
    def test_get_chatwoot_connector(self):
        """Testa obtenção de conector Chatwoot"""
        connector = self.connector_factory.get_connector("mcp-chatwoot")
        self.assertIsNotNone(connector)
        self.assertTrue(hasattr(connector, "tools"))
    
    def test_get_invalid_connector(self):
        """Testa obtenção de conector inválido"""
        connector = self.connector_factory.get_connector("invalid-mcp")
        self.assertIsNone(connector)


if __name__ == "__main__":
    # Para testes assíncronos
    def run_async_test(test_func):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(test_func())
        finally:
            loop.close()
    
    unittest.main()
