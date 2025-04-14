"""
Testes de integração para o serviço de Business Rules.

Este módulo contém testes para verificar o funcionamento do serviço de Business Rules,
incluindo a integração com o agente de embedding e os serviços de vetorização e cache.
"""

import asyncio
import os
import sys
import unittest
from typing import Dict, Any, List
from datetime import date
from unittest.mock import patch, MagicMock

# Adicionar o diretório raiz ao PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from odoo_api.modules.business_rules.services_new import BusinessRulesService
from odoo_api.modules.business_rules.schemas import BusinessRuleResponse, RuleType
from odoo_api.core.services.vector_service import get_vector_service
from odoo_api.core.services.cache_service import get_cache_service
from odoo_api.embedding_agents.business_rules_agent import get_business_rules_agent

class TestBusinessRulesService(unittest.TestCase):
    """Testes para o serviço de Business Rules."""

    def setUp(self):
        """Configuração inicial para os testes."""
        self.loop = asyncio.get_event_loop()
        self.account_id = "account_test"
        
        # Criar serviço
        self.service = BusinessRulesService()
        
        # Dados de teste
        self.test_rules = [
            BusinessRuleResponse(
                id=1,
                name="Horário de Funcionamento",
                description="Nossa loja funciona de segunda a sexta, das 9h às 18h, e aos sábados das 9h às 13h.",
                type=RuleType.BUSINESS_HOURS,
                is_temporary=False,
                rule_data={
                    "days": [0, 1, 2, 3, 4, 5],
                    "start_time": "09:00",
                    "end_time": "18:00",
                    "saturday_hours": {
                        "start_time": "09:00",
                        "end_time": "13:00"
                    }
                }
            ),
            BusinessRuleResponse(
                id=2,
                name="Política de Devolução",
                description="Aceitamos devoluções em até 7 dias após a compra, desde que o produto esteja em perfeito estado e com a embalagem original.",
                type=RuleType.RETURN_POLICY,
                is_temporary=False,
                rule_data={
                    "days": 7,
                    "conditions": ["produto em perfeito estado", "embalagem original"]
                }
            ),
            BusinessRuleResponse(
                id=3,
                name="Promoção de Aniversário",
                description="Em comemoração ao aniversário da loja, todos os produtos estão com 20% de desconto durante o mês de julho.",
                type=RuleType.PROMOTION,
                is_temporary=True,
                start_date=date(2023, 7, 1),
                end_date=date(2023, 7, 31),
                rule_data={
                    "discount_percentage": 20,
                    "products": "all"
                }
            )
        ]
    
    async def _setup_async(self):
        """Configuração assíncrona para os testes."""
        # Obter serviços
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
                await self.vector_service.delete_collection(collection_name)
        except Exception as e:
            print(f"Erro ao limpar coleção do Qdrant: {e}")
    
    def test_sync_business_rules(self):
        """Testar sincronização de regras de negócio."""
        async def _test():
            await self._setup_async()
            
            # Patch para o método list_active_rules
            with patch.object(BusinessRulesService, 'list_active_rules') as mock_list:
                # Configurar o mock para retornar as regras de teste
                mock_list.return_value = self.test_rules
                
                # Patch para o método _get_business_area
                with patch.object(BusinessRulesService, '_get_business_area') as mock_area:
                    # Configurar o mock para retornar uma área de negócio
                    mock_area.return_value = "varejo de móveis"
                    
                    # Chamar o método de sincronização
                    result = await self.service.sync_business_rules(self.account_id)
                    
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
            
            # Limpar dados de teste
            await self._cleanup_test_data()
        
        self.loop.run_until_complete(_test())
    
    def test_search_business_rules(self):
        """Testar busca semântica de regras de negócio."""
        async def _test():
            await self._setup_async()
            
            # Patch para o método list_active_rules
            with patch.object(BusinessRulesService, 'list_active_rules') as mock_list:
                # Configurar o mock para retornar as regras de teste
                mock_list.return_value = self.test_rules
                
                # Patch para o método _get_business_area
                with patch.object(BusinessRulesService, '_get_business_area') as mock_area:
                    # Configurar o mock para retornar uma área de negócio
                    mock_area.return_value = "varejo de móveis"
                    
                    # Sincronizar regras
                    await self.service.sync_business_rules(self.account_id)
                    
                    # Testar busca semântica
                    query = "Qual é o horário de funcionamento da loja?"
                    search_results = await self.service.search_business_rules(
                        account_id=self.account_id,
                        query=query,
                        limit=3,
                        score_threshold=0.7
                    )
                    
                    # Verificar resultados
                    self.assertIsNotNone(search_results)
                    self.assertTrue(len(search_results) > 0)
                    
                    # A primeira regra deve ser sobre horário de funcionamento
                    self.assertEqual(search_results[0]["rule_id"], 1)
                    
                    # Testar outra consulta
                    query = "Posso devolver um produto após 5 dias?"
                    search_results = await self.service.search_business_rules(
                        account_id=self.account_id,
                        query=query,
                        limit=3,
                        score_threshold=0.7
                    )
                    
                    # Verificar resultados
                    self.assertIsNotNone(search_results)
                    self.assertTrue(len(search_results) > 0)
                    
                    # A primeira regra deve ser sobre política de devolução
                    self.assertEqual(search_results[0]["rule_id"], 2)
            
            # Limpar dados de teste
            await self._cleanup_test_data()
        
        self.loop.run_until_complete(_test())
    
    def test_sync_single_rule(self):
        """Testar sincronização de uma única regra."""
        async def _test():
            await self._setup_async()
            
            # Patch para o método _get_business_area
            with patch.object(BusinessRulesService, '_get_business_area') as mock_area:
                # Configurar o mock para retornar uma área de negócio
                mock_area.return_value = "varejo de móveis"
                
                # Sincronizar uma única regra
                rule = self.test_rules[0]
                result = await self.service._sync_single_rule(self.account_id, rule)
                
                # Verificar resultado
                self.assertTrue(result)
                
                # Verificar se a regra foi armazenada no Redis
                redis_rules = await self.cache_service.get(f"{self.account_id}:ai:rules:all")
                self.assertIsNotNone(redis_rules)
                self.assertEqual(len(redis_rules), 1)
                self.assertEqual(redis_rules[0]["id"], rule.id)
                
                # Verificar se a regra foi vetorizada no Qdrant
                collection_name = f"business_rules_{self.account_id}"
                collections = await self.vector_service.qdrant_client.get_collections()
                self.assertIn(collection_name, [c.name for c in collections.collections])
                
                # Buscar a regra no Qdrant
                query_embedding = await self.vector_service.generate_embedding(rule.name)
                search_results = await self.vector_service.search_vectors(
                    collection_name=collection_name,
                    query_vector=query_embedding,
                    limit=1,
                    score_threshold=0.7
                )
                
                # Verificar resultado
                self.assertIsNotNone(search_results)
                self.assertEqual(len(search_results), 1)
                self.assertEqual(search_results[0]["rule_id"], rule.id)
            
            # Limpar dados de teste
            await self._cleanup_test_data()
        
        self.loop.run_until_complete(_test())
    
    def test_remove_rule_from_ai(self):
        """Testar remoção de uma regra do sistema de IA."""
        async def _test():
            await self._setup_async()
            
            # Patch para o método _get_business_area
            with patch.object(BusinessRulesService, '_get_business_area') as mock_area:
                # Configurar o mock para retornar uma área de negócio
                mock_area.return_value = "varejo de móveis"
                
                # Sincronizar uma única regra
                rule = self.test_rules[0]
                await self.service._sync_single_rule(self.account_id, rule)
                
                # Verificar se a regra foi armazenada
                redis_rules = await self.cache_service.get(f"{self.account_id}:ai:rules:all")
                self.assertEqual(len(redis_rules), 1)
                
                # Remover a regra
                result = await self.service._remove_rule_from_ai(self.account_id, rule.id)
                
                # Verificar resultado
                self.assertTrue(result)
                
                # Verificar se a regra foi removida do Redis
                redis_rules = await self.cache_service.get(f"{self.account_id}:ai:rules:all")
                self.assertEqual(len(redis_rules), 0)
                
                # Verificar se a regra foi removida do Qdrant
                collection_name = f"business_rules_{self.account_id}"
                query_embedding = await self.vector_service.generate_embedding(rule.name)
                search_results = await self.vector_service.search_vectors(
                    collection_name=collection_name,
                    query_vector=query_embedding,
                    limit=1,
                    score_threshold=0.7
                )
                
                # Verificar resultado
                self.assertEqual(len(search_results), 0)
            
            # Limpar dados de teste
            await self._cleanup_test_data()
        
        self.loop.run_until_complete(_test())

if __name__ == "__main__":
    unittest.main()
