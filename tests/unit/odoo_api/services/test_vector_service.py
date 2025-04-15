"""
Testes unitários para o serviço de vetorização.

Estes testes verificam se o serviço de vetorização está funcionando corretamente,
incluindo a geração de embeddings, armazenamento e busca de vetores.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import json
import os
import sys

# Mock para settings antes de importar o módulo
sys.modules['odoo_api.config.settings'] = MagicMock()
sys.modules['odoo_api.config.settings'].settings = MagicMock(
    EMBEDDING_DIMENSION=1536,
    EMBEDDING_MODEL="text-embedding-3-small",
    QDRANT_HOST="localhost",
    QDRANT_PORT=6333,
    QDRANT_API_KEY=None,
    OPENAI_API_KEY="test_key",
    TIMEOUT_DEFAULT=30,
    RETRY_MAX_ATTEMPTS=3,
    RETRY_MIN_SECONDS=1,
    RETRY_MAX_SECONDS=10
)

# Importar o módulo a ser testado
from odoo_api.services.vector_service import VectorService, get_vector_service

class TestVectorService:
    """Testes para o serviço de vetorização."""

    @pytest.fixture
    def vector_service(self):
        """Cria uma instância do serviço de vetorização para testes."""
        # Criar o serviço
        service = VectorService()

        # Configurar mocks para os clientes
        service.qdrant_client = MagicMock()
        service.openai_client = MagicMock()
        service.openai_client.embeddings = MagicMock()
        service.openai_client.embeddings.create = AsyncMock()

        # Configurar o mock para o método connect
        service.connect = AsyncMock()

        return service

    @pytest.mark.asyncio
    async def test_ensure_collection_exists_new_collection(self, vector_service):
        """Testa se o método ensure_collection_exists cria uma nova coleção quando ela não existe."""
        # Configurar o mock para retornar que a coleção não existe
        collections_mock = MagicMock()
        collections_mock.collections = [MagicMock(name="other_collection")]
        vector_service.qdrant_client.get_collections.return_value = collections_mock

        # Chamar o método
        await vector_service.ensure_collection_exists("test_collection", 1536)

        # Verificar se o método create_collection foi chamado com os parâmetros corretos
        vector_service.qdrant_client.create_collection.assert_called_once()
        call_args = vector_service.qdrant_client.create_collection.call_args[1]
        assert call_args["collection_name"] == "test_collection"
        assert call_args["vectors_config"].size == 1536

    @pytest.mark.asyncio
    async def test_ensure_collection_exists_existing_collection(self, vector_service):
        """Testa se o método ensure_collection_exists não cria uma coleção quando ela já existe."""
        # Configurar o mock para retornar que a coleção já existe
        collections_mock = MagicMock()
        collection_mock = MagicMock()
        collection_mock.name = "test_collection"
        collections_mock.collections = [collection_mock]
        vector_service.qdrant_client.get_collections.return_value = collections_mock

        # Chamar o método
        await vector_service.ensure_collection_exists("test_collection", 1536)

        # Verificar se o método create_collection não foi chamado
        vector_service.qdrant_client.create_collection.assert_not_called()

    @pytest.mark.asyncio
    async def test_generate_embedding(self, vector_service):
        """Testa se o método generate_embedding gera um embedding corretamente."""
        # Configurar o mock para retornar um embedding
        embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
        response_mock = MagicMock()
        response_mock.data = [MagicMock(embedding=embedding)]
        vector_service.openai_client.embeddings.create.return_value = response_mock

        # Chamar o método
        result = await vector_service.generate_embedding("test text")

        # Verificar se o método create foi chamado com os parâmetros corretos
        vector_service.openai_client.embeddings.create.assert_called_once()

        # Verificar se o resultado é o esperado
        assert result == embedding

    @pytest.mark.asyncio
    async def test_generate_embedding_empty_text(self, vector_service):
        """Testa se o método generate_embedding lida corretamente com texto vazio."""
        # Configurar o mock para settings.EMBEDDING_DIMENSION
        with patch("odoo_api.services.vector_service.settings") as mock_settings:
            mock_settings.EMBEDDING_DIMENSION = 5

            # Chamar o método com texto vazio
            result = await vector_service.generate_embedding("")

            # Verificar se o método create não foi chamado
            vector_service.openai_client.embeddings.create.assert_not_called()

            # Verificar se o resultado é um vetor de zeros
            assert result == [0.0, 0.0, 0.0, 0.0, 0.0]

    @pytest.mark.asyncio
    async def test_store_vector(self, vector_service):
        """Testa se o método store_vector armazena um vetor corretamente."""
        # Configurar o mock para ensure_collection_exists
        vector_service.ensure_collection_exists = AsyncMock()

        # Chamar o método
        vector = [0.1, 0.2, 0.3, 0.4, 0.5]
        payload = {"key": "value"}
        await vector_service.store_vector("test_collection", "test_id", vector, payload)

        # Verificar se o método ensure_collection_exists foi chamado
        vector_service.ensure_collection_exists.assert_called_once_with("test_collection")

        # Verificar se o método upsert foi chamado com os parâmetros corretos
        vector_service.qdrant_client.upsert.assert_called_once()
        call_args = vector_service.qdrant_client.upsert.call_args[1]
        assert call_args["collection_name"] == "test_collection"
        assert len(call_args["points"]) == 1
        assert call_args["points"][0].id == "test_id"
        assert call_args["points"][0].vector == vector
        assert call_args["points"][0].payload == payload

    @pytest.mark.asyncio
    async def test_search_vectors(self, vector_service):
        """Testa se o método search_vectors busca vetores corretamente."""
        # Configurar o mock para retornar resultados de busca
        hit1 = MagicMock(payload={"id": 1, "name": "Product 1"}, score=0.9)
        hit2 = MagicMock(payload={"id": 2, "name": "Product 2"}, score=0.8)
        vector_service.qdrant_client.search.return_value = [hit1, hit2]

        # Chamar o método
        query_vector = [0.1, 0.2, 0.3, 0.4, 0.5]
        results = await vector_service.search_vectors("test_collection", query_vector, 10, 0.7)

        # Verificar se o método search foi chamado com os parâmetros corretos
        vector_service.qdrant_client.search.assert_called_once_with(
            collection_name="test_collection",
            query_vector=query_vector,
            limit=10,
            score_threshold=0.7
        )

        # Verificar se os resultados são os esperados
        assert len(results) == 2
        assert results[0]["id"] == 1
        assert results[0]["name"] == "Product 1"
        assert results[0]["score"] == 0.9
        assert results[1]["id"] == 2
        assert results[1]["name"] == "Product 2"
        assert results[1]["score"] == 0.8

    @pytest.mark.asyncio
    async def test_delete_vector(self, vector_service):
        """Testa se o método delete_vector remove um vetor corretamente."""
        # Chamar o método
        await vector_service.delete_vector("test_collection", "test_id")

        # Verificar se o método delete foi chamado com os parâmetros corretos
        vector_service.qdrant_client.delete.assert_called_once()
        call_args = vector_service.qdrant_client.delete.call_args[1]
        assert call_args["collection_name"] == "test_collection"
        assert call_args["points_selector"].points == ["test_id"]

    @pytest.mark.asyncio
    async def test_delete_collection(self, vector_service):
        """Testa se o método delete_collection remove uma coleção corretamente."""
        # Chamar o método
        await vector_service.delete_collection("test_collection")

        # Verificar se o método delete_collection foi chamado com os parâmetros corretos
        vector_service.qdrant_client.delete_collection.assert_called_once_with(
            collection_name="test_collection"
        )

    @pytest.mark.asyncio
    async def test_sync_product_to_vector_db(self, vector_service):
        """Testa se o método sync_product_to_vector_db sincroniza um produto corretamente."""
        # Configurar mocks
        vector_service._prepare_product_for_embedding = MagicMock(return_value="product text")
        vector_service.generate_embedding = AsyncMock(return_value=[0.1, 0.2, 0.3, 0.4, 0.5])
        vector_service.ensure_collection_exists = AsyncMock()
        vector_service.store_vector = AsyncMock()

        # Chamar o método
        product_data = {
            "name": "Test Product",
            "description": "Test Description",
            "default_code": "TP001",
            "barcode": "123456789",
            "categ_id": [1, "Test Category"],
            "list_price": 100.0,
            "standard_price": 80.0,
            "qty_available": 10.0,
            "attributes": {"color": "red", "size": "M"}
        }
        result = await vector_service.sync_product_to_vector_db("account_1", 123, product_data)

        # Verificar se os métodos foram chamados corretamente
        vector_service._prepare_product_for_embedding.assert_called_once_with(product_data)
        vector_service.generate_embedding.assert_called_once_with("product text")
        vector_service.ensure_collection_exists.assert_called_once_with("products_account_1")
        vector_service.store_vector.assert_called_once()

        # Verificar os parâmetros do store_vector
        call_args = vector_service.store_vector.call_args[1]
        assert call_args["collection_name"] == "products_account_1"
        assert call_args["vector_id"] == "product_123"
        assert call_args["vector"] == [0.1, 0.2, 0.3, 0.4, 0.5]

        # Verificar o payload
        payload = call_args["payload"]
        assert payload["product_id"] == 123
        assert payload["name"] == "Test Product"
        assert payload["description"] == "Test Description"
        assert payload["default_code"] == "TP001"
        assert payload["barcode"] == "123456789"
        assert payload["categ_id"] == [1, "Test Category"]
        assert payload["list_price"] == 100.0
        assert payload["standard_price"] == 80.0
        assert payload["qty_available"] == 10.0
        assert payload["attributes"] == {"color": "red", "size": "M"}

        # Verificar o resultado
        assert result is True

    @pytest.mark.asyncio
    async def test_delete_product_from_vector_db(self, vector_service):
        """Testa se o método delete_product_from_vector_db remove um produto corretamente."""
        # Configurar mock
        vector_service.delete_vector = AsyncMock()

        # Chamar o método
        result = await vector_service.delete_product_from_vector_db("account_1", 123)

        # Verificar se o método delete_vector foi chamado corretamente
        vector_service.delete_vector.assert_called_once_with(
            collection_name="products_account_1",
            vector_id="product_123"
        )

        # Verificar o resultado
        assert result is True

    @pytest.mark.asyncio
    async def test_prepare_product_for_embedding(self, vector_service):
        """Testa se o método _prepare_product_for_embedding formata os dados corretamente."""
        # Chamar o método
        product_data = {
            "name": "Test Product",
            "description": "Test Description",
            "default_code": "TP001",
            "barcode": "123456789",
            "categ_id": [1, "Test Category"],
            "list_price": 100.0,
            "standard_price": 80.0,
            "attributes": {"color": "red", "size": "M"}
        }
        result = vector_service._prepare_product_for_embedding(product_data)

        # Verificar se o resultado contém as informações esperadas
        assert "Nome: Test Product" in result
        assert "Código: TP001" in result
        assert "Código de Barras: 123456789" in result
        assert "Categoria: Test Category" in result
        assert "Preço de Venda: 100.0" in result
        assert "Preço de Custo: 80.0" in result
        assert "Descrição:\n        Test Description" in result
        assert "Atributos:\n        color: red\nsize: M" in result

    @pytest.mark.asyncio
    async def test_get_vector_service(self):
        """Testa se a função get_vector_service retorna uma instância do serviço."""
        # Configurar mock para VectorService
        with patch("odoo_api.services.vector_service.VectorService") as mock_service_class:
            # Configurar o mock para o método connect
            mock_service = MagicMock()
            mock_service.connect = AsyncMock()
            mock_service_class.return_value = mock_service

            # Chamar a função
            service = await get_vector_service()

            # Verificar se o serviço foi criado e conectado
            mock_service_class.assert_called_once()
            mock_service.connect.assert_called_once()

            # Verificar se a função retorna o serviço
            assert service == mock_service

            # Chamar a função novamente
            service2 = await get_vector_service()

            # Verificar se o serviço não foi criado novamente
            assert mock_service_class.call_count == 1
            assert service2 == service
