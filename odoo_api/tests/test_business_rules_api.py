"""
Testes para a API de regras de negócio.

Este módulo contém testes para verificar o funcionamento da API de regras de negócio,
incluindo sincronização e busca semântica.
"""

import asyncio
import json
import logging
import os
import sys
import unittest
from typing import Dict, Any, List

# Adicionar o diretório raiz ao PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from odoo_api.modules.business_rules.services import BusinessRulesService
from odoo_api.services.vector_service import get_vector_service
from odoo_api.services.cache_service import get_cache_service
from odoo_api.embedding_agents.business_rules_agent import get_business_rules_agent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestBusinessRulesAPI(unittest.TestCase):
    """Testes para a API de regras de negócio."""

    def setUp(self):
        """Configuração inicial para os testes."""
        self.account_id = "account_test"
        self.loop = asyncio.get_event_loop()
        
        # Criar regras de teste
        self.test_rules = [
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
            },
            {
                "id": 3,
                "name": "Promoção de Aniversário",
                "description": "Em comemoração ao aniversário da loja, todos os produtos estão com 20% de desconto durante o mês de julho.",
                "type": "promotion",
                "is_temporary": True,
                "start_date": "2023-07-01T00:00:00",
                "end_date": "2023-07-31T23:59:59",
                "rule_data": {
                    "discount_percentage": 20,
                    "products": "all"
                }
            }
        ]

    async def _setup_async(self):
        """Configuração assíncrona para os testes."""
        # Obter serviços
        self.business_rules_service = BusinessRulesService()
        self.vector_service = await get_vector_service()
        self.cache_service = await get_cache_service()
        self.embedding_agent = await get_business_rules_agent()
        
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

    def test_sync_business_rules(self):
        """Testar sincronização de regras de negócio."""
        async def _test():
            await self._setup_async()
            
            # Criar mock para BusinessRuleResponse
            from odoo_api.modules.business_rules.schemas import BusinessRuleResponse
            
            class MockBusinessRuleResponse:
                def __init__(self, rule_data):
                    for key, value in rule_data.items():
                        setattr(self, key, value)
                
                def model_dump(self):
                    return {k: v for k, v in self.__dict__.items()}
            
            # Converter regras de teste para objetos MockBusinessRuleResponse
            mock_rules = [MockBusinessRuleResponse(rule) for rule in self.test_rules]
            
            # Monkey patch para o método list_active_rules
            original_method = self.business_rules_service.list_active_rules
            self.business_rules_service.list_active_rules = lambda account_id: asyncio.Future()
            self.business_rules_service.list_active_rules.set_result(mock_rules)
            
            try:
                # Sincronizar regras
                result = await self.business_rules_service.sync_business_rules(self.account_id)
                
                # Verificar resultado
                self.assertEqual(result.sync_status, "completed")
                self.assertEqual(result.permanent_rules, 2)
                self.assertEqual(result.temporary_rules, 1)
                self.assertEqual(result.vectorized_rules, 3)
                
                # Verificar se as regras foram armazenadas no Redis
                redis_rules = await self.cache_service.get(f"{self.account_id}:ai:rules:all")
                self.assertIsNotNone(redis_rules)
                self.assertEqual(len(redis_rules), 3)
                
                # Verificar se as regras foram vetorizadas no Qdrant
                collection_name = f"business_rules_{self.account_id}"
                collections = await self.vector_service.qdrant_client.get_collections()
                self.assertIn(collection_name, [c.name for c in collections.collections])
                
                # Testar busca semântica
                query = "Qual é o horário de funcionamento da loja?"
                search_results = await self.business_rules_service.search_business_rules(
                    account_id=self.account_id,
                    query=query,
                    limit=3,
                    score_threshold=0.7
                )
                
                self.assertIsNotNone(search_results)
                self.assertTrue(len(search_results) > 0)
                
                # A primeira regra deve ser sobre horário de funcionamento
                self.assertEqual(search_results[0]["rule_id"], 1)
                
                # Testar outra consulta
                query = "Posso devolver um produto após 5 dias?"
                search_results = await self.business_rules_service.search_business_rules(
                    account_id=self.account_id,
                    query=query,
                    limit=3,
                    score_threshold=0.7
                )
                
                self.assertIsNotNone(search_results)
                self.assertTrue(len(search_results) > 0)
                
                # A primeira regra deve ser sobre política de devolução
                self.assertEqual(search_results[0]["rule_id"], 2)
                
            finally:
                # Restaurar método original
                self.business_rules_service.list_active_rules = original_method
                
                # Limpar dados de teste
                await self._cleanup_test_data()
        
        self.loop.run_until_complete(_test())

    def test_embedding_agent(self):
        """Testar o agente de embeddings."""
        async def _test():
            await self._setup_async()
            
            # Testar processamento de regra
            rule_data = self.test_rules[0]
            business_area = "retail"
            
            processed_text = await self.embedding_agent.process_data(rule_data, business_area)
            
            # Verificar se o texto processado contém informações importantes
            self.assertIn("Horário de Funcionamento", processed_text)
            self.assertIn("segunda a sexta", processed_text)
            self.assertIn("9h às 18h", processed_text)
            self.assertIn("sábados", processed_text)
            
            # Verificar se o contexto da área de negócio foi considerado
            self.assertIn("retail", processed_text.lower())
            
            # Testar geração de embedding
            embedding = await self.vector_service.generate_embedding(processed_text)
            
            # Verificar se o embedding foi gerado corretamente
            self.assertIsNotNone(embedding)
            self.assertTrue(len(embedding) > 0)
            
            # Limpar dados de teste
            await self._cleanup_test_data()
        
        self.loop.run_until_complete(_test())

    def test_search_business_rules(self):
        """Testar busca semântica de regras de negócio."""
        async def _test():
            await self._setup_async()
            
            # Sincronizar regras primeiro
            # (Usando o mesmo código do teste de sincronização)
            
            # Criar mock para BusinessRuleResponse
            from odoo_api.modules.business_rules.schemas import BusinessRuleResponse
            
            class MockBusinessRuleResponse:
                def __init__(self, rule_data):
                    for key, value in rule_data.items():
                        setattr(self, key, value)
                
                def model_dump(self):
                    return {k: v for k, v in self.__dict__.items()}
            
            # Converter regras de teste para objetos MockBusinessRuleResponse
            mock_rules = [MockBusinessRuleResponse(rule) for rule in self.test_rules]
            
            # Monkey patch para o método list_active_rules
            original_method = self.business_rules_service.list_active_rules
            self.business_rules_service.list_active_rules = lambda account_id: asyncio.Future()
            self.business_rules_service.list_active_rules.set_result(mock_rules)
            
            try:
                # Sincronizar regras
                await self.business_rules_service.sync_business_rules(self.account_id)
                
                # Testar diferentes consultas
                test_queries = [
                    ("Qual é o horário de funcionamento?", 1),
                    ("Posso devolver um produto?", 2),
                    ("Tem alguma promoção acontecendo?", 3),
                    ("A loja abre aos sábados?", 1),
                    ("Quanto tempo tenho para devolver um produto?", 2),
                    ("Qual é o desconto da promoção de aniversário?", 3)
                ]
                
                for query, expected_rule_id in test_queries:
                    search_results = await self.business_rules_service.search_business_rules(
                        account_id=self.account_id,
                        query=query,
                        limit=3,
                        score_threshold=0.7
                    )
                    
                    self.assertIsNotNone(search_results)
                    self.assertTrue(len(search_results) > 0)
                    
                    # A primeira regra deve ser a esperada
                    self.assertEqual(search_results[0]["rule_id"], expected_rule_id)
                    
                    # Verificar score de similaridade
                    self.assertGreaterEqual(search_results[0]["similarity_score"], 0.7)
                
            finally:
                # Restaurar método original
                self.business_rules_service.list_active_rules = original_method
                
                # Limpar dados de teste
                await self._cleanup_test_data()
        
        self.loop.run_until_complete(_test())

if __name__ == "__main__":
    unittest.main()
