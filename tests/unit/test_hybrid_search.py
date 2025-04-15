"""
Testes unitários para o sistema de busca híbrida (BM42).

Estes testes verificam se o sistema de busca híbrida está funcionando corretamente,
incluindo a combinação de busca densa, esparsa e verificação no Odoo.
"""

import pytest
from unittest.mock import patch, MagicMock

@pytest.fixture
def mock_search_components():
    """Cria mocks para os componentes de busca."""
    # Mock para o serviço de embedding
    mock_embedding_service = MagicMock()
    mock_embedding_service.generate_embedding.return_value = [0.1, 0.2, 0.3, 0.4, 0.5]
    
    # Mock para o codificador esparso
    mock_sparse_encoder = MagicMock()
    mock_sparse_encoder.encode.return_value = {"term1": 0.8, "term2": 0.6, "term3": 0.4}
    
    # Mock para o cliente Qdrant
    mock_qdrant_client = MagicMock()
    mock_qdrant_client.search.return_value = [
        MagicMock(id=1, score=0.95),
        MagicMock(id=2, score=0.85),
        MagicMock(id=3, score=0.75),
        MagicMock(id=4, score=0.65),
    ]
    
    # Mock para a busca esparsa
    mock_sparse_search = MagicMock()
    mock_sparse_search.search.return_value = [
        MagicMock(id=2, score=0.9),
        MagicMock(id=3, score=0.8),
        MagicMock(id=5, score=0.7),
        MagicMock(id=6, score=0.6),
    ]
    
    # Mock para o cliente Odoo
    mock_odoo_client = MagicMock()
    mock_odoo_client.search_read.return_value = [
        {
            "id": 1,
            "name": "Produto 1",
            "description": "Descrição do produto 1",
            "list_price": 100.0,
            "qty_available": 10,
        },
        {
            "id": 2,
            "name": "Produto 2",
            "description": "Descrição do produto 2",
            "list_price": 150.0,
            "qty_available": 5,
        },
        {
            "id": 3,
            "name": "Produto 3",
            "description": "Descrição do produto 3",
            "list_price": 200.0,
            "qty_available": 2,
        },
    ]
    
    return {
        "embedding_service": mock_embedding_service,
        "sparse_encoder": mock_sparse_encoder,
        "qdrant_client": mock_qdrant_client,
        "sparse_search": mock_sparse_search,
        "odoo_client": mock_odoo_client
    }

def test_hybrid_search_basic_functionality(mock_search_components):
    """
    Testa a funcionalidade básica da busca híbrida.
    
    Este teste verifica se:
    1. A busca híbrida combina corretamente os resultados da busca densa e esparsa
    2. Os resultados são filtrados corretamente pelo Odoo
    3. Os resultados são ordenados por score combinado
    """
    # Importar a classe VectorService
    from odoo_api.services.vector_service import VectorService
    
    # Criar uma instância da classe com os mocks
    vector_service = VectorService(
        embedding_service=mock_search_components["embedding_service"],
        sparse_encoder=mock_search_components["sparse_encoder"],
        qdrant_client=mock_search_components["qdrant_client"],
        sparse_search=mock_search_components["sparse_search"],
        odoo_client=mock_search_components["odoo_client"],
        redis_client=None
    )
    
    # Executar a busca híbrida
    results = vector_service._perform_hybrid_search(
        query="camisa azul algodão",
        filters=None,
        limit=10
    )
    
    # Verificar se os componentes foram chamados corretamente
    mock_search_components["embedding_service"].generate_embedding.assert_called_once_with("camisa azul algodão")
    mock_search_components["sparse_encoder"].encode.assert_called_once_with("camisa azul algodão")
    mock_search_components["qdrant_client"].search.assert_called_once()
    mock_search_components["sparse_search"].search.assert_called_once()
    
    # Verificar se o Odoo foi consultado com os IDs corretos
    mock_search_components["odoo_client"].search_read.assert_called_once()
    odoo_call_args = mock_search_components["odoo_client"].search_read.call_args[0]
    
    assert odoo_call_args[0] == 'product.template'
    assert ('id', 'in', [1, 2, 3, 4, 5, 6]) in odoo_call_args[1]
    assert ('active', '=', True) in odoo_call_args[1]
    assert ('qty_available', '>', 0) in odoo_call_args[1]
    
    # Verificar os resultados
    assert len(results) == 3  # Número de produtos retornados pelo mock do Odoo
    
    # Verificar se os scores combinados foram calculados corretamente
    assert all("combined_score" in product for product in results)
    
    # Verificar se os resultados estão ordenados por score combinado
    scores = [product["combined_score"] for product in results]
    assert scores == sorted(scores, reverse=True)

def test_hybrid_search_with_filters(mock_search_components):
    """
    Testa a busca híbrida com filtros adicionais.
    """
    # Importar a classe VectorService
    from odoo_api.services.vector_service import VectorService
    
    # Criar uma instância da classe com os mocks
    vector_service = VectorService(
        embedding_service=mock_search_components["embedding_service"],
        sparse_encoder=mock_search_components["sparse_encoder"],
        qdrant_client=mock_search_components["qdrant_client"],
        sparse_search=mock_search_components["sparse_search"],
        odoo_client=mock_search_components["odoo_client"],
        redis_client=None
    )
    
    # Executar a busca híbrida com filtros
    results = vector_service._perform_hybrid_search(
        query="camisa azul algodão",
        filters={"categ_id": 5},  # Filtro adicional por categoria
        limit=10
    )
    
    # Verificar se o Odoo foi consultado com os filtros corretos
    mock_search_components["odoo_client"].search_read.assert_called_once()
    odoo_call_args = mock_search_components["odoo_client"].search_read.call_args[0]
    
    assert ('categ_id', '=', 5) in odoo_call_args[1]

def test_hybrid_search_with_cache(mock_search_components, mock_redis_client):
    """
    Testa a busca híbrida com cache Redis.
    """
    # Importar a classe VectorService
    from odoo_api.services.vector_service import VectorService
    import json
    
    # Configurar o mock do Redis para simular um cache hit
    cached_results = [
        {
            "id": 1,
            "name": "Produto Cached 1",
            "description": "Descrição do produto cached 1",
            "list_price": 100.0,
            "qty_available": 10,
            "combined_score": 0.95
        },
        {
            "id": 2,
            "name": "Produto Cached 2",
            "description": "Descrição do produto cached 2",
            "list_price": 150.0,
            "qty_available": 5,
            "combined_score": 0.85
        }
    ]
    
    # Configurar o mock do Redis para retornar resultados em cache
    mock_redis_client.exists.return_value = True
    mock_redis_client.get.return_value = json.dumps(cached_results)
    
    # Criar uma instância da classe com os mocks
    vector_service = VectorService(
        embedding_service=mock_search_components["embedding_service"],
        sparse_encoder=mock_search_components["sparse_encoder"],
        qdrant_client=mock_search_components["qdrant_client"],
        sparse_search=mock_search_components["sparse_search"],
        odoo_client=mock_search_components["odoo_client"],
        redis_client=mock_redis_client
    )
    
    # Executar a busca híbrida
    results = vector_service.search_products(
        query="camisa azul algodão",
        filters=None,
        limit=10
    )
    
    # Verificar se os resultados vieram do cache
    assert results == cached_results
    
    # Verificar se os componentes de busca não foram chamados
    mock_search_components["embedding_service"].generate_embedding.assert_not_called()
    mock_search_components["sparse_encoder"].encode.assert_not_called()
    mock_search_components["qdrant_client"].search.assert_not_called()
    mock_search_components["sparse_search"].search.assert_not_called()
    mock_search_components["odoo_client"].search_read.assert_not_called()

def test_hybrid_search_cache_miss(mock_search_components, mock_redis_client):
    """
    Testa a busca híbrida com cache miss no Redis.
    """
    # Importar a classe VectorService
    from odoo_api.services.vector_service import VectorService
    import json
    
    # Configurar o mock do Redis para simular um cache miss
    mock_redis_client.exists.return_value = False
    
    # Criar uma instância da classe com os mocks
    vector_service = VectorService(
        embedding_service=mock_search_components["embedding_service"],
        sparse_encoder=mock_search_components["sparse_encoder"],
        qdrant_client=mock_search_components["qdrant_client"],
        sparse_search=mock_search_components["sparse_search"],
        odoo_client=mock_search_components["odoo_client"],
        redis_client=mock_redis_client
    )
    
    # Executar a busca híbrida
    results = vector_service.search_products(
        query="camisa azul algodão",
        filters=None,
        limit=10
    )
    
    # Verificar se os componentes de busca foram chamados
    mock_search_components["embedding_service"].generate_embedding.assert_called_once()
    mock_search_components["sparse_encoder"].encode.assert_called_once()
    mock_search_components["qdrant_client"].search.assert_called_once()
    mock_search_components["sparse_search"].search.assert_called_once()
    mock_search_components["odoo_client"].search_read.assert_called_once()
    
    # Verificar se os resultados foram armazenados no cache
    mock_redis_client.set.assert_called_once()
    cache_args = mock_redis_client.set.call_args[0]
    
    assert isinstance(cache_args[0], str)  # Chave de cache
    assert isinstance(cache_args[1], str)  # Valor serializado em JSON
    assert isinstance(json.loads(cache_args[1]), list)  # Valor é uma lista de resultados
