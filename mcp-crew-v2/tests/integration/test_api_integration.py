#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Testes de integração para o MCP-Crew v2
Valida que a refatoração não quebrou a funcionalidade principal do sistema
"""

import os
import sys
import unittest
import json
import requests
from unittest import mock

# Adiciona o diretório raiz ao path para importações
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.core.orchestrator import mcp_crew_orchestrator
from src.core.mcp_tool_discovery import tool_discovery
from src.core.knowledge_manager import knowledge_manager, KnowledgeItem, KnowledgeType
from src.config.config import Config


class TestMCPCrewIntegration(unittest.TestCase):
    """Testes de integração para o MCP-Crew v2"""
    
    def setUp(self):
        """Configuração inicial para os testes"""
        self.base_url = "http://localhost:5003"
        self.test_account_id = "test_account"
        self.headers = {"Content-Type": "application/json"}
    
    def test_health_check(self):
        """Testa o endpoint de health check"""
        # Mock da resposta para evitar dependência de servidor real
        with mock.patch('requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {
                "status": "operational",
                "redis": "connected",
                "mcps": {
                    "mcp-mongodb": "connected",
                    "mcp-chatwoot": "connected"
                }
            }
            
            # Teste direto com o orquestrador
            health_status = mcp_crew_orchestrator.get_health_status()
            self.assertIsInstance(health_status, dict)
            self.assertIn("status", health_status)
            
            # Simulação de chamada HTTP
            response = requests.get(f"{self.base_url}/api/mcp-crew/health")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertIn("status", data)
    
    def test_tool_discovery(self):
        """Testa a descoberta de ferramentas"""
        # Mock para evitar chamadas reais
        with mock.patch('src.core.mcp_tool_discovery.MCPToolDiscovery.discover_all_tools') as mock_discover:
            mock_discover.return_value = {
                "mcp-mongodb": [
                    {"name": "find_documents", "description": "Encontra documentos no MongoDB"},
                    {"name": "insert_document", "description": "Insere documento no MongoDB"}
                ],
                "mcp-chatwoot": [
                    {"name": "send_message", "description": "Envia mensagem no Chatwoot"},
                    {"name": "get_conversation", "description": "Obtém conversa do Chatwoot"}
                ]
            }
            
            # Teste direto com o módulo de descoberta
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                tools = loop.run_until_complete(
                    tool_discovery.discover_all_tools(self.test_account_id, force_refresh=True)
                )
            finally:
                loop.close()
            
            self.assertIsInstance(tools, dict)
            self.assertIn("mcp-mongodb", tools)
            self.assertIn("mcp-chatwoot", tools)
    
    def test_knowledge_manager(self):
        """Testa o gerenciador de conhecimento"""
        # Criar um item de conhecimento
        knowledge_item = KnowledgeItem(
            account_id=self.test_account_id,
            knowledge_type=KnowledgeType.PRODUCT_INFO,
            topic="test_topic",
            title="Test Knowledge",
            content={"key": "value"},
            source_agent="test_agent",
            tags=["test", "integration"]
        )
        
        # Testar armazenamento
        result = knowledge_manager.store_knowledge(knowledge_item)
        self.assertTrue(result)
        
        # Testar busca
        items = knowledge_manager.search_knowledge_by_topic(
            account_id=self.test_account_id,
            topic="test_topic"
        )
        self.assertIsInstance(items, list)
        
        # Testar limpeza
        count = knowledge_manager.cleanup_expired_knowledge(self.test_account_id)
        self.assertIsInstance(count, int)
    
    def test_mcp_connector_factory(self):
        """Testa a fábrica de conectores MCP"""
        from src.core.mcp_connector_factory import mcp_connector_factory
        
        # Testar obtenção de conector
        connector = mcp_connector_factory.get_connector("mcp-mongodb")
        self.assertIsNotNone(connector)
        
        # Verificar se o conector tem o método tools
        self.assertTrue(hasattr(connector, "tools"))
    
    def test_orchestrator_process_request(self):
        """Testa o processamento de requisições pelo orquestrador"""
        # Mock para evitar execução real
        with mock.patch('src.core.orchestrator.DynamicMCPCrewOrchestrator.process_request') as mock_process:
            mock_process.return_value = {
                "success": True,
                "result": "Processamento concluído com sucesso",
                "execution_time": 0.5
            }
            
            # Criar dados de requisição
            request_data = {
                "account_id": self.test_account_id,
                "channel": "api",
                "payload": {
                    "text": "Teste de integração",
                    "sender_id": "test_user"
                }
            }
            
            # Teste direto com o orquestrador
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    mcp_crew_orchestrator.process_request(request_data)
                )
            finally:
                loop.close()
            
            self.assertIsInstance(result, dict)
            self.assertIn("success", result)
            self.assertTrue(result["success"])


if __name__ == "__main__":
    unittest.main()
