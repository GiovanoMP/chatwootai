"""
Testes unitários para o cliente Redis.

Estes testes verificam se o cliente Redis está funcionando corretamente,
incluindo a conexão, armazenamento e recuperação de dados.
"""

import pytest
from unittest.mock import patch, MagicMock
import os
import json

# Importar o módulo a ser testado
from src.utils.redis_client import get_redis_client, RedisCache

class TestRedisClient:
    """Testes para o cliente Redis."""

    @patch('redis.Redis')
    def test_get_redis_client_success(self, mock_redis):
        """Testa se o cliente Redis é criado corretamente quando a conexão é bem-sucedida."""
        # Configurar o mock
        mock_instance = MagicMock()
        mock_redis.return_value = mock_instance
        
        # Chamar a função
        client = get_redis_client(force_new=True)
        
        # Verificar se o Redis foi chamado com os parâmetros corretos
        mock_redis.assert_called_once()
        assert client is mock_instance
        
        # Verificar se ping foi chamado para testar a conexão
        mock_instance.ping.assert_called_once()

    @patch('redis.Redis')
    def test_get_redis_client_exception(self, mock_redis):
        """Testa se a função lida corretamente com exceções ao conectar ao Redis."""
        # Configurar o mock para lançar uma exceção
        mock_redis.side_effect = Exception("Erro de conexão")
        
        # Chamar a função
        client = get_redis_client(force_new=True)
        
        # Verificar se a função retornou None
        assert client is None

    @patch('redis.Redis')
    def test_get_redis_client_singleton(self, mock_redis):
        """Testa se a função retorna o mesmo cliente quando chamada múltiplas vezes."""
        # Configurar o mock
        mock_instance = MagicMock()
        mock_redis.return_value = mock_instance
        
        # Chamar a função duas vezes
        client1 = get_redis_client(force_new=True)
        client2 = get_redis_client(force_new=False)
        
        # Verificar se o Redis foi chamado apenas uma vez
        mock_redis.assert_called_once()
        
        # Verificar se os clientes são o mesmo objeto
        assert client1 is client2

    @patch('redis.Redis')
    def test_get_redis_client_env_vars(self, mock_redis):
        """Testa se a função usa corretamente as variáveis de ambiente."""
        # Configurar variáveis de ambiente
        os.environ['REDIS_HOST'] = 'test-host'
        os.environ['REDIS_PORT'] = '1234'
        os.environ['REDIS_DB'] = '5'
        os.environ['REDIS_PASSWORD'] = 'test-password'
        
        # Configurar o mock
        mock_instance = MagicMock()
        mock_redis.return_value = mock_instance
        
        # Chamar a função
        client = get_redis_client(force_new=True)
        
        # Verificar se o Redis foi chamado com os parâmetros corretos
        mock_redis.assert_called_once_with(
            host='test-host',
            port=1234,
            db=5,
            password='test-password',
            decode_responses=True,
            socket_timeout=2.0
        )
        
        # Limpar variáveis de ambiente
        del os.environ['REDIS_HOST']
        del os.environ['REDIS_PORT']
        del os.environ['REDIS_DB']
        del os.environ['REDIS_PASSWORD']

class TestRedisCache:
    """Testes para a classe RedisCache."""

    def test_init_with_client(self):
        """Testa se a classe é inicializada corretamente com um cliente fornecido."""
        # Criar um mock para o cliente Redis
        mock_client = MagicMock()
        
        # Inicializar a classe
        cache = RedisCache(redis_client=mock_client)
        
        # Verificar se o cliente foi armazenado corretamente
        assert cache.redis_client is mock_client

    @patch('src.utils.redis_client.get_redis_client')
    def test_init_without_client(self, mock_get_client):
        """Testa se a classe é inicializada corretamente sem um cliente fornecido."""
        # Configurar o mock
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        # Inicializar a classe
        cache = RedisCache()
        
        # Verificar se get_redis_client foi chamado
        mock_get_client.assert_called_once()
        
        # Verificar se o cliente foi armazenado corretamente
        assert cache.redis_client is mock_client

    def test_store_domain_config(self):
        """Testa se a função store_domain_config funciona corretamente."""
        # Criar um mock para o cliente Redis
        mock_client = MagicMock()
        
        # Inicializar a classe
        cache = RedisCache(redis_client=mock_client)
        
        # Chamar a função
        config = {"key": "value"}
        result = cache.store_domain_config("test-domain", config, ttl=3600)
        
        # Verificar se o Redis foi chamado com os parâmetros corretos
        mock_client.set.assert_called_once_with(
            "domain:config:test-domain",
            json.dumps(config),
            ex=3600
        )
        
        # Verificar se a função retornou True
        assert result is True

    def test_get_domain_config(self):
        """Testa se a função get_domain_config funciona corretamente."""
        # Criar um mock para o cliente Redis
        mock_client = MagicMock()
        
        # Configurar o mock para retornar um valor
        config = {"key": "value"}
        mock_client.get.return_value = json.dumps(config)
        
        # Inicializar a classe
        cache = RedisCache(redis_client=mock_client)
        
        # Chamar a função
        result = cache.get_domain_config("test-domain")
        
        # Verificar se o Redis foi chamado com os parâmetros corretos
        mock_client.get.assert_called_once_with("domain:config:test-domain")
        
        # Verificar se a função retornou o valor correto
        assert result == config

    def test_set_conversation_domain(self):
        """Testa se a função set_conversation_domain funciona corretamente."""
        # Criar um mock para o cliente Redis
        mock_client = MagicMock()
        
        # Inicializar a classe
        cache = RedisCache(redis_client=mock_client)
        
        # Chamar a função
        result = cache.set_conversation_domain("conv-123", "test-domain", ttl=86400)
        
        # Verificar se o Redis foi chamado com os parâmetros corretos
        mock_client.set.assert_called_once_with(
            "domain:conversation:conv-123",
            "test-domain",
            ex=86400
        )
        
        # Verificar se a função retornou True
        assert result is True

    def test_get_conversation_domain(self):
        """Testa se a função get_conversation_domain funciona corretamente."""
        # Criar um mock para o cliente Redis
        mock_client = MagicMock()
        
        # Configurar o mock para retornar um valor
        mock_client.get.return_value = "test-domain"
        
        # Inicializar a classe
        cache = RedisCache(redis_client=mock_client)
        
        # Chamar a função
        result = cache.get_conversation_domain("conv-123")
        
        # Verificar se o Redis foi chamado com os parâmetros corretos
        mock_client.get.assert_called_once_with("domain:conversation:conv-123")
        
        # Verificar se a função retornou o valor correto
        assert result == "test-domain"

    def test_store_agent_state(self):
        """Testa se a função store_agent_state funciona corretamente."""
        # Criar um mock para o cliente Redis
        mock_client = MagicMock()
        
        # Inicializar a classe
        cache = RedisCache(redis_client=mock_client)
        
        # Chamar a função
        state = {"memory": "test-memory"}
        result = cache.store_agent_state("agent-123", "test-domain", "conv-123", state, ttl=86400)
        
        # Verificar se o Redis foi chamado com os parâmetros corretos
        mock_client.set.assert_called_once_with(
            "agent:state:test-domain:agent-123:conv-123",
            json.dumps(state),
            ex=86400
        )
        
        # Verificar se a função retornou True
        assert result is True

    def test_get_agent_state(self):
        """Testa se a função get_agent_state funciona corretamente."""
        # Criar um mock para o cliente Redis
        mock_client = MagicMock()
        
        # Configurar o mock para retornar um valor
        state = {"memory": "test-memory"}
        mock_client.get.return_value = json.dumps(state)
        
        # Inicializar a classe
        cache = RedisCache(redis_client=mock_client)
        
        # Chamar a função
        result = cache.get_agent_state("agent-123", "test-domain", "conv-123")
        
        # Verificar se o Redis foi chamado com os parâmetros corretos
        mock_client.get.assert_called_once_with("agent:state:test-domain:agent-123:conv-123")
        
        # Verificar se a função retornou o valor correto
        assert result == state

    def test_invalidate_domain_config(self):
        """Testa se a função invalidate_domain_config funciona corretamente."""
        # Criar um mock para o cliente Redis
        mock_client = MagicMock()
        
        # Inicializar a classe
        cache = RedisCache(redis_client=mock_client)
        
        # Chamar a função
        result = cache.invalidate_domain_config("test-domain")
        
        # Verificar se o Redis foi chamado com os parâmetros corretos
        mock_client.delete.assert_called_once_with("domain:config:test-domain")
        
        # Verificar se a função retornou True
        assert result is True
