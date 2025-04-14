# -*- coding: utf-8 -*-

"""
Configurações para testes.
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch

from odoo_api.main import app
from odoo_api.config.settings import settings
from odoo_api.services.cache_service import CacheService
from odoo_api.services.vector_service import VectorService
from odoo_api.core.odoo_connector import OdooConnector, OdooConnectorFactory

@pytest.fixture
def test_client():
    """Fixture para cliente de teste."""
    return TestClient(app)

@pytest.fixture
def mock_settings():
    """Fixture para configurações de teste."""
    settings.DEBUG = True
    settings.REDIS_HOST = "localhost"
    settings.REDIS_PORT = 6379
    settings.REDIS_DB = 0
    settings.QDRANT_HOST = "localhost"
    settings.QDRANT_PORT = 6333
    settings.EMBEDDING_MODEL = "text-embedding-ada-002"
    settings.EMBEDDING_DIMENSION = 1536
    settings.MCP_CONFIG_DIR = "./tests/fixtures/config"
    return settings

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
def mock_qdrant():
    """Fixture para mock do Qdrant."""
    with patch("qdrant_client.QdrantClient") as mock:
        # Configurar métodos mock
        mock_instance = MagicMock()
        mock.return_value = mock_instance
        
        # Configurar métodos específicos
        mock_instance.get_collections.return_value = MagicMock(collections=[])
        mock_instance.create_collection.return_value = None
        mock_instance.create_payload_index.return_value = None
        mock_instance.search.return_value = []
        mock_instance.upsert.return_value = None
        mock_instance.delete.return_value = None
        
        yield mock_instance

@pytest.fixture
def mock_odoo_connector():
    """Fixture para mock do OdooConnector."""
    with patch("odoo_api.core.odoo_connector.OdooConnector") as mock:
        # Configurar métodos mock
        mock_instance = AsyncMock()
        mock.return_value = mock_instance
        
        # Configurar métodos específicos
        mock_instance.connect.return_value = 1
        mock_instance.execute_kw.return_value = []
        mock_instance.search_read.return_value = []
        mock_instance.create.return_value = 1
        mock_instance.write.return_value = True
        mock_instance.unlink.return_value = True
        
        yield mock_instance

@pytest.fixture
def mock_odoo_connector_factory(mock_odoo_connector):
    """Fixture para mock do OdooConnectorFactory."""
    with patch("odoo_api.core.odoo_connector.OdooConnectorFactory") as mock:
        # Configurar métodos mock
        mock.create_connector = AsyncMock(return_value=mock_odoo_connector)
        
        yield mock

@pytest.fixture
def mock_cache_service(mock_redis):
    """Fixture para mock do CacheService."""
    with patch("odoo_api.services.cache_service.get_cache_service") as mock:
        # Criar instância do serviço
        service = CacheService()
        service.redis = mock_redis
        
        # Configurar mock para retornar a instância
        mock.return_value = service
        
        yield service

@pytest.fixture
def mock_vector_service(mock_qdrant):
    """Fixture para mock do VectorService."""
    with patch("odoo_api.services.vector_service.get_vector_service") as mock:
        # Criar instância do serviço
        service = VectorService()
        service.qdrant_client = mock_qdrant
        
        # Configurar métodos mock
        service.generate_embedding = AsyncMock(return_value=[0.1] * 1536)
        service.sync_product_to_vector_db = AsyncMock(return_value="account_1_123")
        service.search_products = AsyncMock(return_value=[])
        service.delete_product = AsyncMock(return_value=True)
        
        # Configurar mock para retornar a instância
        mock.return_value = service
        
        yield service

@pytest.fixture
def mock_openai():
    """Fixture para mock da API OpenAI."""
    with patch("httpx.AsyncClient") as mock:
        # Configurar métodos mock
        mock_instance = AsyncMock()
        mock.return_value.__aenter__.return_value = mock_instance
        
        # Configurar resposta para embeddings
        mock_instance.post.return_value.json.return_value = {
            "data": [{"embedding": [0.1] * 1536}]
        }
        mock_instance.post.return_value.raise_for_status = AsyncMock()
        
        yield mock_instance
