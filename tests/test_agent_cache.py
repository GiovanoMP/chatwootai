"""
Testes para a implementação de cache de agentes.

Este módulo contém testes para verificar o funcionamento da implementação
de RedisAgentCache e sua integração com os agentes do sistema.
"""

import unittest
from unittest.mock import MagicMock, patch
import json
import redis

from src.core.cache.agent_cache import RedisAgentCache


class TestRedisAgentCache(unittest.TestCase):
    """Testes para a classe RedisAgentCache."""

    def setUp(self):
        """Configura o ambiente de teste."""
        # Mock do cliente Redis
        self.redis_mock = MagicMock(spec=redis.Redis)
        self.cache = RedisAgentCache(redis_client=self.redis_mock, prefix="test:", ttl=60)

    def test_get_key(self):
        """Testa a geração de chaves de cache."""
        agent_id = "test_agent"
        input_data = "test_input"
        key = self.cache._get_key(agent_id, input_data)
        
        self.assertTrue(key.startswith("test:test_agent:"))
        self.assertIn(str(hash(input_data)), key)

    def test_get_cache_hit(self):
        """Testa a recuperação de dados do cache (hit)."""
        # Configura o mock para retornar dados
        cached_data = {"result": "cached_response"}
        self.redis_mock.get.return_value = json.dumps(cached_data)
        
        # Tenta recuperar do cache
        result = self.cache.get("test_agent", "test_input")
        
        # Verifica se o método get do Redis foi chamado com a chave correta
        self.redis_mock.get.assert_called_once()
        # Verifica se os dados retornados são os esperados
        self.assertEqual(result, cached_data)

    def test_get_cache_miss(self):
        """Testa a recuperação de dados do cache (miss)."""
        # Configura o mock para retornar None (cache miss)
        self.redis_mock.get.return_value = None
        
        # Tenta recuperar do cache
        result = self.cache.get("test_agent", "test_input")
        
        # Verifica se o método get do Redis foi chamado
        self.redis_mock.get.assert_called_once()
        # Verifica se o resultado é None
        self.assertIsNone(result)

    def test_set_cache(self):
        """Testa o armazenamento de dados no cache."""
        # Dados a serem armazenados
        output_data = {"result": "agent_response"}
        
        # Tenta armazenar no cache
        result = self.cache.set("test_agent", "test_input", output_data)
        
        # Verifica se o método setex do Redis foi chamado com os parâmetros corretos
        self.redis_mock.setex.assert_called_once()
        args, kwargs = self.redis_mock.setex.call_args
        self.assertEqual(args[1], 60)  # TTL
        self.assertEqual(json.loads(args[2]), output_data)  # Dados
        
        # Verifica se o resultado é True (sucesso)
        self.assertTrue(result)

    def test_delete_cache(self):
        """Testa a remoção de dados do cache."""
        # Tenta remover do cache
        result = self.cache.delete("test_agent", "test_input")
        
        # Verifica se o método delete do Redis foi chamado
        self.redis_mock.delete.assert_called_once()
        
        # Verifica se o resultado é True (sucesso)
        self.assertTrue(result)

    def test_clear_cache_specific_agent(self):
        """Testa a limpeza do cache para um agente específico."""
        # Configura o mock para retornar uma lista de chaves
        self.redis_mock.keys.return_value = ["test:test_agent:1", "test:test_agent:2"]
        
        # Tenta limpar o cache
        result = self.cache.clear("test_agent")
        
        # Verifica se o método keys do Redis foi chamado com o padrão correto
        self.redis_mock.keys.assert_called_once_with("test:test_agent:*")
        
        # Verifica se o método delete do Redis foi chamado com as chaves corretas
        self.redis_mock.delete.assert_called_once_with("test:test_agent:1", "test:test_agent:2")
        
        # Verifica se o resultado é True (sucesso)
        self.assertTrue(result)

    def test_clear_cache_all_agents(self):
        """Testa a limpeza do cache para todos os agentes."""
        # Configura o mock para retornar uma lista de chaves
        self.redis_mock.keys.return_value = ["test:agent1:1", "test:agent2:1"]
        
        # Tenta limpar o cache
        result = self.cache.clear()
        
        # Verifica se o método keys do Redis foi chamado com o padrão correto
        self.redis_mock.keys.assert_called_once_with("test:*")
        
        # Verifica se o método delete do Redis foi chamado com as chaves corretas
        self.redis_mock.delete.assert_called_once_with("test:agent1:1", "test:agent2:1")
        
        # Verifica se o resultado é True (sucesso)
        self.assertTrue(result)


@patch('redis.Redis')
class TestRedisAgentCacheIntegration(unittest.TestCase):
    """Testes de integração para a classe RedisAgentCache com o OrchestratorAgent."""

    def setUp(self):
        """Configura o ambiente de teste."""
        # Importações necessárias para os testes
        from src.core.hub import OrchestratorAgent
        from src.core.memory import MemorySystem
        
        # Mock do sistema de memória
        self.memory_mock = MagicMock(spec=MemorySystem)
        
        # Configuração do agente orquestrador
        self.agent = OrchestratorAgent(
            memory_system=self.memory_mock,
            crew_registry={"sales": MagicMock(), "support": MagicMock()},
            llm_config={"model": "gpt-3.5-turbo"}
        )

    def test_orchestrator_with_cache(self, redis_mock):
        """Testa o OrchestratorAgent com cache."""
        # Configura o mock do Redis
        redis_instance = redis_mock.return_value
        # Configura o mock para simular um cache hit
        redis_instance.get.return_value = json.dumps({
            "crew": "sales",
            "confidence": 0.8,
            "reasoning": "Mensagem relacionada a vendas"
        })
        
        # Cria o cache
        cache = RedisAgentCache(redis_client=redis_instance)
        
        # Configura o agente para usar o cache
        self.agent.__dict__["agent_cache"] = cache
        
        # Mensagem e contexto de teste
        message = {"content": "Quero comprar um produto"}
        context = {"conversation_id": "test_conv"}
        
        # Chama o método de roteamento
        with patch.object(self.agent, '_route_with_llm') as route_mock:
            result = self.agent.route_message(message, context)
            
            # Verifica se o método _route_with_llm não foi chamado (cache hit)
            route_mock.assert_not_called()
            
            # Verifica se o resultado é o esperado
            self.assertEqual(result["crew"], "sales")
            self.assertEqual(result["confidence"], 0.8)
            
            # Verifica se o método get do Redis foi chamado
            self.assertTrue(redis_instance.get.called)

    def test_orchestrator_without_cache(self, redis_mock):
        """Testa o OrchestratorAgent sem cache (cache miss)."""
        # Configura o mock do Redis
        redis_instance = redis_mock.return_value
        # Configura o mock para simular um cache miss
        redis_instance.get.return_value = None
        
        # Cria o cache
        cache = RedisAgentCache(redis_client=redis_instance)
        
        # Configura o agente para usar o cache
        self.agent.__dict__["agent_cache"] = cache
        
        # Mensagem e contexto de teste
        message = {"content": "Tenho um problema com meu pedido"}
        context = {"conversation_id": "test_conv"}
        
        # Mock do resultado do roteamento
        route_result = {
            "crew": "support",
            "confidence": 0.9,
            "reasoning": "Mensagem relacionada a suporte"
        }
        
        # Chama o método de roteamento
        with patch.object(self.agent, '_route_with_llm', return_value=route_result) as route_mock:
            result = self.agent.route_message(message, context)
            
            # Verifica se o método _route_with_llm foi chamado (cache miss)
            route_mock.assert_called_once()
            
            # Verifica se o resultado é o esperado
            self.assertEqual(result["crew"], "support")
            self.assertEqual(result["confidence"], 0.9)
            
            # Verifica se o método set do RedisAgentCache foi chamado (armazenamento no cache)
            # Não podemos verificar exatamente os argumentos, mas podemos verificar se foi chamado
            self.assertTrue(redis_instance.setex.called)


if __name__ == '__main__':
    unittest.main()
