# -*- coding: utf-8 -*-

"""
Testes unitários para o serviço de cache.
"""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch

from odoo_api.services.cache_service import CacheService
from odoo_api.core.exceptions import CacheError

@pytest.fixture
def mock_redis():
    """Fixture para mock do Redis."""
    with patch("redis.asyncio.Redis") as mock:
        # Configurar métodos mock
        mock_instance = AsyncMock()
        mock.return_value = mock_instance
        
        # Configurar métodos específicos
        mock_instance.get.return_value = None
        mock_instance.set.return_value = True
        mock_instance.delete.return_value = True
        mock_instance.exists.return_value = 0
        mock_instance.ttl.return_value = -2
        mock_instance.keys.return_value = []
        mock_instance.flushall.return_value = True
        mock_instance.ping.return_value = True
        
        yield mock_instance

@pytest.fixture
def cache_service(mock_redis):
    """Fixture para o serviço de cache."""
    service = CacheService()
    service.redis = mock_redis
    return service

@pytest.mark.asyncio
async def test_connect(mock_redis):
    """Testa a conexão com o Redis."""
    service = CacheService()
    await service.connect()
    mock_redis.ping.assert_called_once()

@pytest.mark.asyncio
async def test_get_not_found(cache_service, mock_redis):
    """Testa a obtenção de um valor não encontrado."""
    mock_redis.get.return_value = None
    result = await cache_service.get("test_key")
    assert result is None
    mock_redis.get.assert_called_once_with("test_key")

@pytest.mark.asyncio
async def test_get_found(cache_service, mock_redis):
    """Testa a obtenção de um valor encontrado."""
    mock_redis.get.return_value = json.dumps({"test": "value"})
    result = await cache_service.get("test_key")
    assert result == {"test": "value"}
    mock_redis.get.assert_called_once_with("test_key")

@pytest.mark.asyncio
async def test_set(cache_service, mock_redis):
    """Testa a definição de um valor."""
    result = await cache_service.set("test_key", {"test": "value"}, 60)
    assert result is True
    mock_redis.set.assert_called_once_with("test_key", json.dumps({"test": "value"}), ex=60)

@pytest.mark.asyncio
async def test_delete(cache_service, mock_redis):
    """Testa a remoção de um valor."""
    result = await cache_service.delete("test_key")
    assert result is True
    mock_redis.delete.assert_called_once_with("test_key")

@pytest.mark.asyncio
async def test_exists_not_found(cache_service, mock_redis):
    """Testa a verificação de existência de um valor não encontrado."""
    mock_redis.exists.return_value = 0
    result = await cache_service.exists("test_key")
    assert result is False
    mock_redis.exists.assert_called_once_with("test_key")

@pytest.mark.asyncio
async def test_exists_found(cache_service, mock_redis):
    """Testa a verificação de existência de um valor encontrado."""
    mock_redis.exists.return_value = 1
    result = await cache_service.exists("test_key")
    assert result is True
    mock_redis.exists.assert_called_once_with("test_key")

@pytest.mark.asyncio
async def test_get_ttl_not_found(cache_service, mock_redis):
    """Testa a obtenção do TTL de um valor não encontrado."""
    mock_redis.ttl.return_value = -2
    result = await cache_service.get_ttl("test_key")
    assert result is None
    mock_redis.ttl.assert_called_once_with("test_key")

@pytest.mark.asyncio
async def test_get_ttl_found(cache_service, mock_redis):
    """Testa a obtenção do TTL de um valor encontrado."""
    mock_redis.ttl.return_value = 30
    result = await cache_service.get_ttl("test_key")
    assert result == 30
    mock_redis.ttl.assert_called_once_with("test_key")

@pytest.mark.asyncio
async def test_keys(cache_service, mock_redis):
    """Testa a obtenção de chaves."""
    mock_redis.keys.return_value = ["key1", "key2"]
    result = await cache_service.keys("test_*")
    assert result == ["key1", "key2"]
    mock_redis.keys.assert_called_once_with("test_*")

@pytest.mark.asyncio
async def test_flush_all(cache_service, mock_redis):
    """Testa a limpeza de todos os valores."""
    result = await cache_service.flush_all()
    assert result is True
    mock_redis.flushall.assert_called_once()

@pytest.mark.asyncio
async def test_get_account_config(cache_service):
    """Testa a obtenção da configuração de uma conta."""
    with patch.object(cache_service, "get") as mock_get:
        mock_get.return_value = {"database": "test_db"}
        result = await cache_service.get_account_config("account_1")
        assert result == {"database": "test_db"}
        mock_get.assert_called_once_with("account_1:config")

@pytest.mark.asyncio
async def test_set_account_config(cache_service):
    """Testa a definição da configuração de uma conta."""
    with patch.object(cache_service, "set") as mock_set:
        mock_set.return_value = True
        result = await cache_service.set_account_config("account_1", {"database": "test_db"}, 3600)
        assert result is True
        mock_set.assert_called_once_with("account_1:config", {"database": "test_db"}, 3600)

@pytest.mark.asyncio
async def test_get_product(cache_service):
    """Testa a obtenção de um produto."""
    with patch.object(cache_service, "get") as mock_get:
        mock_get.return_value = {"name": "Test Product"}
        result = await cache_service.get_product("account_1", 123)
        assert result == {"name": "Test Product"}
        mock_get.assert_called_once_with("account_1:product:123")

@pytest.mark.asyncio
async def test_set_product(cache_service):
    """Testa a definição de um produto."""
    with patch.object(cache_service, "set") as mock_set:
        mock_set.return_value = True
        result = await cache_service.set_product("account_1", 123, {"name": "Test Product"}, 3600)
        assert result is True
        mock_set.assert_called_once_with("account_1:product:123", {"name": "Test Product"}, 3600)

@pytest.mark.asyncio
async def test_invalidate_product(cache_service):
    """Testa a invalidação de um produto."""
    with patch.object(cache_service, "delete") as mock_delete:
        mock_delete.return_value = True
        result = await cache_service.invalidate_product("account_1", 123)
        assert result is True
        mock_delete.assert_called_once_with("account_1:product:123")
