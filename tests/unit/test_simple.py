"""
Testes unitários simples para verificar a configuração básica do ambiente de testes.
"""

import pytest
from unittest.mock import MagicMock

def test_basic_mock():
    """Teste básico para verificar se os mocks funcionam corretamente."""
    # Criar um mock
    mock_obj = MagicMock()
    mock_obj.method.return_value = 42
    
    # Verificar se o mock funciona
    assert mock_obj.method() == 42
    mock_obj.method.assert_called_once()

def test_fixture_usage(mock_redis_client):
    """Teste para verificar se as fixtures estão funcionando corretamente."""
    # Configurar o mock
    mock_redis_client.get.return_value = "test_value"
    
    # Verificar se o mock funciona
    assert mock_redis_client.get("test_key") == "test_value"
    mock_redis_client.get.assert_called_once_with("test_key")

def test_redis_client_set(mock_redis_client):
    """Teste para verificar se o método set do Redis funciona corretamente."""
    # Chamar o método set
    result = mock_redis_client.set("test_key", "test_value")
    
    # Verificar se o método foi chamado corretamente
    mock_redis_client.set.assert_called_once_with("test_key", "test_value")
    assert result is True

def test_redis_client_exists(mock_redis_client):
    """Teste para verificar se o método exists do Redis funciona corretamente."""
    # Configurar o mock
    mock_redis_client.exists.return_value = True
    
    # Verificar se o mock funciona
    assert mock_redis_client.exists("test_key") is True
    mock_redis_client.exists.assert_called_once_with("test_key")

def test_redis_client_delete(mock_redis_client):
    """Teste para verificar se o método delete do Redis funciona corretamente."""
    # Configurar o mock
    mock_redis_client.delete.return_value = 1
    
    # Verificar se o mock funciona
    assert mock_redis_client.delete("test_key") == 1
    mock_redis_client.delete.assert_called_once_with("test_key")
