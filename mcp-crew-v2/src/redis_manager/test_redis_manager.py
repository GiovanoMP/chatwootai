"""
Testes para o RedisManager do MCP-Crew v2.

Este módulo contém testes unitários para o RedisManager.
"""

import unittest
import time
from unittest.mock import MagicMock, patch

from src.redis_manager.redis_manager import RedisManager, DataType


class TestRedisManager(unittest.TestCase):
    """Testes para o RedisManager."""

    @patch('redis.Redis')
    @patch('redis.ConnectionPool')
    def setUp(self, mock_connection_pool, mock_redis):
        """Configura o ambiente de teste."""
        self.mock_connection_pool = mock_connection_pool
        self.mock_redis = mock_redis
        self.redis_manager = RedisManager(
            host="localhost",
            port=6379,
            prefix="test-mcp-crew",
        )
        self.tenant_id = "test-tenant"
        
    def test_get_key(self):
        """Testa a geração de chaves."""
        key = self.redis_manager._get_key(
            tenant_id="tenant1",
            data_type="tool_discovery",
            identifier="mongodb"
        )
        self.assertEqual(key, "test-mcp-crew:tenant1:tool_discovery:mongodb")
        
    def test_circuit_breaker(self):
        """Testa o funcionamento do circuit breaker."""
        # Configura o circuit breaker
        self.redis_manager.circuit_breaker.failure_threshold = 2
        self.redis_manager.circuit_breaker.reset_timeout = 1
        
        # Registra falhas
        self.redis_manager.circuit_breaker.record_failure()
        self.assertFalse(self.redis_manager.circuit_breaker.is_open)
        
        self.redis_manager.circuit_breaker.record_failure()
        self.assertTrue(self.redis_manager.circuit_breaker.is_open)
        
        # Verifica se o circuit breaker está aberto
        self.assertFalse(self.redis_manager.circuit_breaker.allow_request())
        
        # Espera o timeout
        time.sleep(1.1)
        
        # Verifica se o circuit breaker permite requisições após o timeout
        self.assertTrue(self.redis_manager.circuit_breaker.allow_request())
        
    @patch('redis_manager.redis_manager.RedisManager._execute_with_circuit_breaker')
    def test_set(self, mock_execute):
        """Testa o método set."""
        mock_execute.return_value = True
        
        result = self.redis_manager.set(
            tenant_id=self.tenant_id,
            data_type=DataType.TOOL_DISCOVERY,
            identifier="mongodb",
            value={"name": "test"}
        )
        
        self.assertTrue(result)
        mock_execute.assert_called_once()
        
    @patch('redis_manager.redis_manager.RedisManager._execute_with_circuit_breaker')
    def test_get(self, mock_execute):
        """Testa o método get."""
        mock_execute.return_value = '{"name": "test"}'
        
        result = self.redis_manager.get(
            tenant_id=self.tenant_id,
            data_type=DataType.TOOL_DISCOVERY,
            identifier="mongodb"
        )
        
        self.assertEqual(result, {"name": "test"})
        mock_execute.assert_called_once()
        
    @patch('redis_manager.redis_manager.RedisManager._execute_with_circuit_breaker')
    def test_get_none(self, mock_execute):
        """Testa o método get quando o valor não existe."""
        mock_execute.return_value = None
        
        result = self.redis_manager.get(
            tenant_id=self.tenant_id,
            data_type=DataType.TOOL_DISCOVERY,
            identifier="mongodb"
        )
        
        self.assertIsNone(result)
        mock_execute.assert_called_once()
        
    @patch('redis_manager.redis_manager.RedisManager._execute_with_circuit_breaker')
    def test_delete(self, mock_execute):
        """Testa o método delete."""
        mock_execute.return_value = 1
        
        result = self.redis_manager.delete(
            tenant_id=self.tenant_id,
            data_type=DataType.TOOL_DISCOVERY,
            identifier="mongodb"
        )
        
        self.assertTrue(result)
        mock_execute.assert_called_once()
        
    @patch('redis_manager.redis_manager.RedisManager._execute_with_circuit_breaker')
    def test_exists(self, mock_execute):
        """Testa o método exists."""
        mock_execute.return_value = 1
        
        result = self.redis_manager.exists(
            tenant_id=self.tenant_id,
            data_type=DataType.TOOL_DISCOVERY,
            identifier="mongodb"
        )
        
        self.assertTrue(result)
        mock_execute.assert_called_once()
        
    @patch('redis_manager.redis_manager.RedisManager.set_conversation_context')
    @patch('redis_manager.redis_manager.RedisManager.get_conversation_context')
    def test_update_conversation_context(self, mock_get, mock_set):
        """Testa o método update_conversation_context."""
        # Configura os mocks
        mock_get.return_value = {"count": 1}
        mock_set.return_value = True
        
        # Define a função de atualização
        def update_func(context):
            context["count"] += 1
            return context
        
        # Chama o método
        result = self.redis_manager.update_conversation_context(
            tenant_id=self.tenant_id,
            conversation_id="conv123",
            update_func=update_func
        )
        
        # Verifica o resultado
        self.assertTrue(result)
        mock_get.assert_called_once_with(self.tenant_id, "conv123")
        mock_set.assert_called_once_with(self.tenant_id, "conv123", {"count": 2})
        
    @patch('redis_manager.redis_manager.RedisManager._execute_with_circuit_breaker')
    def test_get_keys_by_pattern(self, mock_execute):
        """Testa o método get_keys_by_pattern."""
        mock_execute.return_value = ["key1", "key2"]
        
        result = self.redis_manager.get_keys_by_pattern(
            tenant_id=self.tenant_id,
            data_type=DataType.TOOL_DISCOVERY,
            pattern="*"
        )
        
        self.assertEqual(result, ["key1", "key2"])
        mock_execute.assert_called_once()
        
    @patch('redis_manager.redis_manager.RedisManager._execute_with_circuit_breaker')
    def test_get_stats(self, mock_execute):
        """Testa o método get_stats."""
        mock_execute.return_value = {
            "used_memory_human": "1M",
            "connected_clients": 10,
            "uptime_in_days": 5,
            "db0": {"keys": 100},
            "db1": {"keys": 200},
        }
        
        result = self.redis_manager.get_stats()
        
        self.assertEqual(result["used_memory"], "1M")
        self.assertEqual(result["clients_connected"], 10)
        self.assertEqual(result["uptime_days"], 5)
        self.assertEqual(result["total_keys"], 300)
        mock_execute.assert_called_once()


if __name__ == '__main__':
    unittest.main()
