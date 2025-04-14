"""
Testes para a integração entre o módulo Odoo e a API.

Este módulo contém testes para verificar a integração entre o módulo Odoo e a API,
incluindo sincronização de regras de negócio.
"""

import asyncio
import json
import logging
import os
import sys
import unittest
from typing import Dict, Any, List
from unittest.mock import patch, MagicMock

# Adicionar o diretório raiz ao PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from odoo_api.modules.business_rules.routes import sync_business_rules
from odoo_api.modules.business_rules.services import BusinessRulesService
from odoo_api.services.vector_service import get_vector_service
from odoo_api.services.cache_service import get_cache_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestOdooIntegration(unittest.TestCase):
    """Testes para a integração entre o módulo Odoo e a API."""

    def setUp(self):
        """Configuração inicial para os testes."""
        self.account_id = "account_test"
        self.loop = asyncio.get_event_loop()
        
        # Dados de teste para simular a requisição do Odoo
        self.test_request = {
            "metadata": {
                "source": "odoo",
                "account_id": self.account_id,
                "action": "sync_business_rules"
            },
            "params": {
                "business_rule_id": 1,
                "rules": [
                    {
                        "id": 1,
                        "name": "Horário de Funcionamento",
                        "description": "Nossa loja funciona de segunda a sexta, das 9h às 18h, e aos sábados das 9h às 13h.",
                        "type": "business_hours",
                        "is_temporary": False,
                        "rule_data": {
                            "days": [0, 1, 2, 3, 4, 5],
                            "start_time": "09:00",
                            "end_time": "18:00",
                            "saturday_hours": {
                                "start_time": "09:00",
                                "end_time": "13:00"
                            }
                        }
                    },
                    {
                        "id": 2,
                        "name": "Política de Devolução",
                        "description": "Aceitamos devoluções em até 7 dias após a compra, desde que o produto esteja em perfeito estado e com a embalagem original.",
                        "type": "return_policy",
                        "is_temporary": False,
                        "rule_data": {
                            "days": 7,
                            "conditions": ["produto em perfeito estado", "embalagem original"]
                        }
                    }
                ]
            }
        }

    async def _setup_async(self):
        """Configuração assíncrona para os testes."""
        # Obter serviços
        self.business_rules_service = BusinessRulesService()
        self.vector_service = await get_vector_service()
        self.cache_service = await get_cache_service()
        
        # Limpar dados de testes anteriores
        await self._cleanup_test_data()

    async def _cleanup_test_data(self):
        """Limpar dados de testes anteriores."""
        # Limpar cache do Redis
        redis_keys = await self.cache_service.keys(f"{self.account_id}:*")
        if redis_keys:
            await self.cache_service.delete(*redis_keys)
        
        # Limpar coleção do Qdrant
        collection_name = f"business_rules_{self.account_id}"
        try:
            collections = await self.vector_service.qdrant_client.get_collections()
            if collection_name in [c.name for c in collections.collections]:
                await self.vector_service.qdrant_client.delete_collection(collection_name)
        except Exception as e:
            logger.warning(f"Erro ao limpar coleção do Qdrant: {e}")

    def test_sync_endpoint(self):
        """Testar o endpoint de sincronização."""
        async def _test():
            await self._setup_async()
            
            # Criar mock para a requisição
            mock_request = MagicMock()
            mock_request.query_params = {"account_id": self.account_id}
            
            # Patch para o método sync_business_rules do serviço
            with patch.object(BusinessRulesService, 'sync_business_rules') as mock_sync:
                # Configurar o mock para retornar um resultado de sucesso
                mock_result = MagicMock()
                mock_result.permanent_rules = 2
                mock_result.temporary_rules = 0
                mock_result.vectorized_rules = 2
                mock_result.sync_status = "completed"
                mock_sync.return_value = mock_result
                
                # Chamar o endpoint
                response = await sync_business_rules(mock_request)
                
                # Verificar se o método foi chamado com os parâmetros corretos
                mock_sync.assert_called_once_with(self.account_id)
                
                # Verificar a resposta
                self.assertTrue(response.get("success"))
                self.assertEqual(response.get("data").get("permanent_rules"), 2)
                self.assertEqual(response.get("data").get("temporary_rules"), 0)
                self.assertEqual(response.get("data").get("vectorized_rules"), 2)
                self.assertEqual(response.get("data").get("sync_status"), "completed")
            
            # Limpar dados de teste
            await self._cleanup_test_data()
        
        self.loop.run_until_complete(_test())

    def test_integration_flow(self):
        """Testar o fluxo completo de integração."""
        async def _test():
            await self._setup_async()
            
            # Simular o fluxo completo
            # 1. Módulo Odoo envia requisição para a API
            # 2. API processa a requisição e sincroniza as regras
            # 3. API retorna o resultado da sincronização
            
            # Criar mock para a requisição
            mock_request = MagicMock()
            mock_request.query_params = {"account_id": self.account_id}
            
            # Patch para o método list_active_rules do serviço
            with patch.object(BusinessRulesService, 'list_active_rules') as mock_list:
                # Configurar o mock para retornar as regras de teste
                from odoo_api.modules.business_rules.schemas import BusinessRuleResponse
                
                class MockBusinessRuleResponse:
                    def __init__(self, rule_data):
                        for key, value in rule_data.items():
                            setattr(self, key, value)
                    
                    def model_dump(self):
                        return {k: v for k, v in self.__dict__.items()}
                
                # Converter regras de teste para objetos MockBusinessRuleResponse
                mock_rules = [MockBusinessRuleResponse(rule) for rule in self.test_request["params"]["rules"]]
                mock_list.return_value = mock_rules
                
                # Chamar o endpoint
                response = await sync_business_rules(mock_request)
                
                # Verificar se o método foi chamado com os parâmetros corretos
                mock_list.assert_called_once_with(self.account_id)
                
                # Verificar a resposta
                self.assertTrue(response.get("success"))
                self.assertEqual(response.get("data").get("permanent_rules"), 2)
                self.assertEqual(response.get("data").get("temporary_rules"), 0)
                
                # Verificar se as regras foram armazenadas no Redis
                redis_rules = await self.cache_service.get(f"{self.account_id}:ai:rules:all")
                self.assertIsNotNone(redis_rules)
                self.assertEqual(len(redis_rules), 2)
                
                # Verificar se as regras foram vetorizadas no Qdrant
                collection_name = f"business_rules_{self.account_id}"
                collections = await self.vector_service.qdrant_client.get_collections()
                self.assertIn(collection_name, [c.name for c in collections.collections])
            
            # Limpar dados de teste
            await self._cleanup_test_data()
        
        self.loop.run_until_complete(_test())

if __name__ == "__main__":
    unittest.main()
