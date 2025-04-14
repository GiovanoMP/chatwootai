# -*- coding: utf-8 -*-

"""
Testes de integração para a API do módulo Product Management.
"""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from odoo_api.modules.product_management.services import ProductManagementService
from odoo_api.modules.product_management.schemas import (
    ProductBatchSyncResponse,
    PriceUpdateResponse,
    SyncStatusResponse,
    ProductListResponse,
)

@pytest.mark.asyncio
async def test_sync_products_batch(
    test_client, mock_odoo_connector_factory, mock_vector_service
):
    """Testa a sincronização em massa de produtos."""
    # Configurar mock do OdooConnector
    mock_odoo_connector = await mock_odoo_connector_factory.create_connector("account_1")
    mock_odoo_connector.execute_kw.return_value = [
        {"id": 123, "name": "Test Product 1"},
        {"id": 456, "name": "Test Product 2"},
    ]

    # Configurar mock do serviço de produtos semânticos
    with patch("odoo_api.modules.product_management.services.get_semantic_product_service") as mock_get_service:
        mock_semantic_service = AsyncMock()
        mock_semantic_service.sync_product_to_vector_db.return_value = MagicMock(
            product_id=123,
            vector_id="account_1_123",
            sync_status="completed",
            timestamp=datetime.now(),
        )
        mock_get_service.return_value = mock_semantic_service

        # Fazer requisição
        response = test_client.post(
            "/api/v1/products/sync-batch?account_id=account_1",
            json={
                "product_ids": [123, 456, 789],
                "options": {
                    "generate_descriptions": True,
                    "skip_odoo_update": False,
                    "force_update": False,
                }
            },
        )

        # Verificar resposta
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["total"] == 3
        assert data["data"]["successful"] == 2
        assert data["data"]["failed"] == 1
        assert len(data["data"]["results"]) == 3

@pytest.mark.asyncio
async def test_update_prices_batch(
    test_client, mock_odoo_connector_factory
):
    """Testa a atualização de preços em massa."""
    # Configurar mock do OdooConnector
    mock_odoo_connector = await mock_odoo_connector_factory.create_connector("account_1")
    mock_odoo_connector.execute_kw.side_effect = [
        # Primeira chamada: search_read
        [
            {"id": 123, "name": "Test Product 1", "list_price": 100.0, "ai_price": 90.0},
            {"id": 456, "name": "Test Product 2", "list_price": 200.0, "ai_price": 180.0},
        ],
        # Segunda chamada: write para produto 123
        True,
        # Terceira chamada: write para produto 456
        True,
    ]

    # Fazer requisição
    response = test_client.post(
        "/api/v1/products/update-prices?account_id=account_1",
        json={
            "product_ids": [123, 456],
            "adjustment": {
                "type": "percentage",
                "value": -10.0,
                "field": "list_price",
            }
        },
    )

    # Verificar resposta
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["total"] == 2
    assert data["data"]["successful"] == 2
    assert data["data"]["failed"] == 0
    assert len(data["data"]["results"]) == 2

@pytest.mark.asyncio
async def test_get_sync_status(
    test_client, mock_odoo_connector_factory, mock_cache_service
):
    """Testa a verificação de status de sincronização."""
    # Configurar mock do OdooConnector
    mock_odoo_connector = await mock_odoo_connector_factory.create_connector("account_1")
    mock_odoo_connector.execute_kw.return_value = [
        {"id": 123, "name": "Test Product 1", "semantic_description_verified": True},
        {"id": 456, "name": "Test Product 2", "semantic_description_verified": False},
    ]

    # Configurar mock do cache
    mock_cache_service.get.side_effect = [
        # Primeira chamada: produto 123
        {
            "timestamp": datetime.now().isoformat(),
            "vector_id": "account_1_123",
        },
        # Segunda chamada: produto 456
        None,
    ]

    # Fazer requisição
    response = test_client.get(
        "/api/v1/products/sync-status?account_id=account_1&product_ids=123,456",
    )

    # Verificar resposta
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["total"] == 2
    assert data["data"]["synced"] == 1
    assert data["data"]["not_synced"] == 1
    assert len(data["data"]["products"]) == 2

@pytest.mark.asyncio
async def test_list_products(
    test_client, mock_odoo_connector_factory
):
    """Testa a listagem de produtos."""
    # Configurar mock do OdooConnector
    mock_odoo_connector = await mock_odoo_connector_factory.create_connector("account_1")
    mock_odoo_connector.execute_kw.side_effect = [
        # Primeira chamada: search_count
        10,
        # Segunda chamada: search_read
        [
            {
                "id": 123,
                "name": "Test Product 1",
                "default_code": "TP001",
                "list_price": 100.0,
                "ai_price": 90.0,
                "categ_id": [1, "Test Category"],
                "semantic_description_verified": True,
            },
            {
                "id": 456,
                "name": "Test Product 2",
                "default_code": "TP002",
                "list_price": 200.0,
                "ai_price": 180.0,
                "categ_id": [2, "Another Category"],
                "semantic_description_verified": False,
            },
        ],
    ]

    # Fazer requisição
    response = test_client.post(
        "/api/v1/products/list?account_id=account_1",
        json={
            "filter": {
                "category_ids": [1, 2],
                "price_range": [50.0, 250.0],
                "sync_status": "synced",
                "search_term": "Test",
            },
            "limit": 10,
            "offset": 0,
            "order_by": "name",
            "order_dir": "asc",
        },
    )

    # Verificar resposta
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["total"] == 10
    assert data["data"]["limit"] == 10
    assert data["data"]["offset"] == 0
    assert len(data["data"]["products"]) == 2

@pytest.mark.asyncio
async def test_sync_products_batch_validation_error(
    test_client
):
    """Testa a validação de parâmetros na sincronização em massa."""
    # Fazer requisição com parâmetros inválidos
    response = test_client.post(
        "/api/v1/products/sync-batch?account_id=account_1",
        json={
            "product_ids": [],  # Lista vazia é inválida
            "options": {
                "generate_descriptions": True,
                "skip_odoo_update": False,
            }
        },
    )

    # Verificar resposta
    assert response.status_code == 422  # Unprocessable Entity

@pytest.mark.asyncio
async def test_update_prices_batch_validation_error(
    test_client
):
    """Testa a validação de parâmetros na atualização de preços."""
    # Fazer requisição com parâmetros inválidos
    response = test_client.post(
        "/api/v1/products/update-prices?account_id=account_1",
        json={
            "product_ids": [123, 456],
            "adjustment": {
                "type": "invalid_type",  # Tipo inválido
                "value": -10.0,
                "field": "list_price",
            }
        },
    )

    # Verificar resposta
    assert response.status_code == 422  # Unprocessable Entity

@pytest.mark.asyncio
async def test_get_sync_status_missing_account_id(
    test_client
):
    """Testa a verificação de account_id na verificação de status."""
    # Fazer requisição sem account_id
    response = test_client.get(
        "/api/v1/products/sync-status",  # Sem account_id
    )

    # Verificar resposta
    assert response.status_code == 400  # Bad Request

@pytest.mark.asyncio
async def test_list_products_validation_error(
    test_client
):
    """Testa a validação de parâmetros na listagem de produtos."""
    # Fazer requisição com parâmetros inválidos
    response = test_client.post(
        "/api/v1/products/list?account_id=account_1",
        json={
            "limit": 0,  # Limite inválido
            "offset": 0,
            "order_by": "name",
            "order_dir": "asc",
        },
    )

    # Verificar resposta
    assert response.status_code == 422  # Unprocessable Entity
