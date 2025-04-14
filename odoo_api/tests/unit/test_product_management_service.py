# -*- coding: utf-8 -*-

"""
Testes unitários para o serviço de gerenciamento de produtos.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from odoo_api.modules.product_management.services import ProductManagementService
from odoo_api.modules.product_management.schemas import (
    ProductBatchSyncOptions,
    PriceAdjustment,
    ProductFilter,
)
from odoo_api.core.exceptions import ValidationError

@pytest.fixture
def service():
    """Fixture para o serviço de gerenciamento de produtos."""
    return ProductManagementService()

@pytest.mark.asyncio
async def test_sync_products_batch(service, mock_odoo_connector_factory, mock_cache_service):
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
        
        # Executar sincronização
        result = await service.sync_products_batch(
            account_id="account_1",
            product_ids=[123, 456, 789],
            options=ProductBatchSyncOptions(
                generate_descriptions=True,
                skip_odoo_update=False,
                force_update=False,
            ),
        )
        
        # Verificar resultado
        assert result.total == 3
        assert result.successful == 2
        assert result.failed == 1
        assert len(result.results) == 3
        
        # Verificar chamadas
        mock_odoo_connector.execute_kw.assert_called_once()
        assert mock_semantic_service.sync_product_to_vector_db.call_count == 2

@pytest.mark.asyncio
async def test_update_prices_batch(service, mock_odoo_connector_factory):
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
    
    # Executar atualização de preços
    result = await service.update_prices_batch(
        account_id="account_1",
        product_ids=[123, 456],
        adjustment=PriceAdjustment(
            type="percentage",
            value=-10.0,
            field="list_price",
        ),
    )
    
    # Verificar resultado
    assert result.total == 2
    assert result.successful == 2
    assert result.failed == 0
    assert len(result.results) == 2
    
    # Verificar valores
    assert result.results[0].product_id == 123
    assert result.results[0].old_price == 100.0
    assert result.results[0].new_price == 90.0
    
    assert result.results[1].product_id == 456
    assert result.results[1].old_price == 200.0
    assert result.results[1].new_price == 180.0
    
    # Verificar chamadas
    assert mock_odoo_connector.execute_kw.call_count == 3

@pytest.mark.asyncio
async def test_update_prices_batch_fixed(service, mock_odoo_connector_factory):
    """Testa a atualização de preços em massa com ajuste fixo."""
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
    
    # Executar atualização de preços
    result = await service.update_prices_batch(
        account_id="account_1",
        product_ids=[123, 456],
        adjustment=PriceAdjustment(
            type="fixed",
            value=-10.0,
            field="list_price",
        ),
    )
    
    # Verificar resultado
    assert result.total == 2
    assert result.successful == 2
    assert result.failed == 0
    assert len(result.results) == 2
    
    # Verificar valores
    assert result.results[0].product_id == 123
    assert result.results[0].old_price == 100.0
    assert result.results[0].new_price == 90.0
    
    assert result.results[1].product_id == 456
    assert result.results[1].old_price == 200.0
    assert result.results[1].new_price == 190.0
    
    # Verificar chamadas
    assert mock_odoo_connector.execute_kw.call_count == 3

@pytest.mark.asyncio
async def test_update_prices_batch_invalid_type(service):
    """Testa a atualização de preços em massa com tipo inválido."""
    with pytest.raises(ValidationError):
        await service.update_prices_batch(
            account_id="account_1",
            product_ids=[123, 456],
            adjustment=PriceAdjustment(
                type="invalid",
                value=-10.0,
                field="list_price",
            ),
        )

@pytest.mark.asyncio
async def test_update_prices_batch_invalid_field(service):
    """Testa a atualização de preços em massa com campo inválido."""
    with pytest.raises(ValidationError):
        await service.update_prices_batch(
            account_id="account_1",
            product_ids=[123, 456],
            adjustment=PriceAdjustment(
                type="percentage",
                value=-10.0,
                field="invalid_field",
            ),
        )

@pytest.mark.asyncio
async def test_get_sync_status(service, mock_odoo_connector_factory, mock_cache_service):
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
    
    # Executar verificação de status
    result = await service.get_sync_status(
        account_id="account_1",
        product_ids=[123, 456],
    )
    
    # Verificar resultado
    assert result.total == 2
    assert result.synced == 1
    assert result.not_synced == 1
    assert len(result.products) == 2
    
    # Verificar valores
    assert result.products[0].product_id == 123
    assert result.products[0].sync_status == "synced"
    assert result.products[0].vector_id == "account_1_123"
    
    assert result.products[1].product_id == 456
    assert result.products[1].sync_status == "not_synced"
    assert result.products[1].vector_id is None
    
    # Verificar chamadas
    mock_odoo_connector.execute_kw.assert_called_once()
    assert mock_cache_service.get.call_count == 2

@pytest.mark.asyncio
async def test_list_products(service, mock_odoo_connector_factory):
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
    
    # Executar listagem
    result = await service.list_products(
        account_id="account_1",
        filter=ProductFilter(
            category_ids=[1, 2],
            price_range=[50.0, 250.0],
            sync_status="synced",
            search_term="Test",
        ),
        limit=10,
        offset=0,
        order_by="name",
        order_dir="asc",
    )
    
    # Verificar resultado
    assert result.total == 10
    assert result.limit == 10
    assert result.offset == 0
    assert len(result.products) == 2
    
    # Verificar valores
    assert result.products[0].product_id == 123
    assert result.products[0].name == "Test Product 1"
    assert result.products[0].default_code == "TP001"
    assert result.products[0].list_price == 100.0
    assert result.products[0].ai_price == 90.0
    assert result.products[0].category_id == 1
    assert result.products[0].category_name == "Test Category"
    assert result.products[0].sync_status == "synced"
    
    assert result.products[1].product_id == 456
    assert result.products[1].name == "Test Product 2"
    assert result.products[1].default_code == "TP002"
    assert result.products[1].list_price == 200.0
    assert result.products[1].ai_price == 180.0
    assert result.products[1].category_id == 2
    assert result.products[1].category_name == "Another Category"
    assert result.products[1].sync_status == "not_synced"
    
    # Verificar chamadas
    assert mock_odoo_connector.execute_kw.call_count == 2

@pytest.mark.asyncio
async def test_list_products_invalid_limit(service):
    """Testa a listagem de produtos com limite inválido."""
    with pytest.raises(ValidationError):
        await service.list_products(
            account_id="account_1",
            limit=0,
        )
    
    with pytest.raises(ValidationError):
        await service.list_products(
            account_id="account_1",
            limit=1001,
        )

@pytest.mark.asyncio
async def test_list_products_invalid_offset(service):
    """Testa a listagem de produtos com offset inválido."""
    with pytest.raises(ValidationError):
        await service.list_products(
            account_id="account_1",
            offset=-1,
        )

@pytest.mark.asyncio
async def test_list_products_invalid_order_dir(service):
    """Testa a listagem de produtos com direção de ordenação inválida."""
    with pytest.raises(ValidationError):
        await service.list_products(
            account_id="account_1",
            order_dir="invalid",
        )

@pytest.mark.asyncio
async def test_list_products_invalid_order_by(service):
    """Testa a listagem de produtos com campo de ordenação inválido."""
    with pytest.raises(ValidationError):
        await service.list_products(
            account_id="account_1",
            order_by="invalid_field",
        )
