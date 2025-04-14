# -*- coding: utf-8 -*-

"""
Testes de integração para a API do módulo Semantic Product.
"""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from odoo_api.modules.semantic_product.services import SemanticProductService
from odoo_api.modules.semantic_product.schemas import (
    ProductDescriptionResponse,
    ProductSyncResponse,
    ProductSearchResponse,
)

@pytest.mark.asyncio
async def test_generate_product_description(
    test_client, mock_odoo_connector_factory, mock_openai
):
    """Testa a geração de descrição de produto."""
    # Configurar mock do OdooConnector
    mock_odoo_connector = await mock_odoo_connector_factory.create_connector("account_1")
    mock_odoo_connector.execute_kw.side_effect = [
        # Primeira chamada: product.template.read
        [{
            "id": 123,
            "name": "Test Product",
            "categ_id": [1, "Test Category"],
            "description_sale": "Short description",
            "description": "Long description",
            "list_price": 100.0,
            "default_code": "TP001",
        }],
        # Segunda chamada: product.category.read
        [{
            "id": 1,
            "name": "Test Category",
        }],
        # Terceira chamada: product.template.attribute.line.search_read
        [],
        # Quarta chamada: product.template.read (campos semânticos)
        [{
            "semantic_description": "",
            "key_features": "",
            "use_cases": "",
            "ai_generated_description": "",
            "semantic_description_verified": False,
        }],
    ]
    
    # Configurar mock do OpenAI
    mock_openai.post.return_value.json.return_value = {
        "choices": [{
            "message": {
                "content": """
                DESCRIPTION:
                This is a test product description.
                
                KEY FEATURES:
                - Feature 1
                - Feature 2
                - Feature 3
                
                USE CASES:
                - Use case 1
                - Use case 2
                """
            }
        }]
    }
    
    # Fazer requisição
    response = test_client.post(
        "/api/v1/products/123/description?account_id=account_1",
        json={"options": {"include_features": True, "include_use_cases": True, "tone": "professional"}},
    )
    
    # Verificar resposta
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["product_id"] == 123
    assert "description" in data["data"]
    assert "key_features" in data["data"]
    assert "use_cases" in data["data"]

@pytest.mark.asyncio
async def test_sync_product(
    test_client, mock_odoo_connector_factory, mock_vector_service
):
    """Testa a sincronização de produto."""
    # Configurar mock do OdooConnector
    mock_odoo_connector = await mock_odoo_connector_factory.create_connector("account_1")
    mock_odoo_connector.execute_kw.side_effect = [
        # Primeira chamada: product.template.read
        [{
            "id": 123,
            "name": "Test Product",
            "categ_id": [1, "Test Category"],
            "description_sale": "Short description",
            "description": "Long description",
            "list_price": 100.0,
            "default_code": "TP001",
        }],
        # Segunda chamada: product.category.read
        [{
            "id": 1,
            "name": "Test Category",
        }],
        # Terceira chamada: product.template.attribute.line.search_read
        [],
        # Quarta chamada: product.template.read (campos semânticos)
        [{
            "semantic_description": "Semantic description",
            "key_features": "Key features",
            "use_cases": "Use cases",
            "ai_generated_description": "",
            "semantic_description_verified": False,
        }],
        # Quinta chamada: product.template.write
        True,
    ]
    
    # Configurar mock do VectorService
    mock_vector_service.sync_product_to_vector_db.return_value = "account_1_123"
    
    # Fazer requisição
    response = test_client.post(
        "/api/v1/products/123/sync?account_id=account_1",
        json={"description": "Custom description", "skip_odoo_update": False},
    )
    
    # Verificar resposta
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["product_id"] == 123
    assert data["data"]["vector_id"] == "account_1_123"
    assert data["data"]["sync_status"] == "completed"

@pytest.mark.asyncio
async def test_search_products(
    test_client, mock_odoo_connector_factory, mock_vector_service
):
    """Testa a busca semântica de produtos."""
    # Configurar mock do VectorService
    mock_vector_service.search_products.return_value = [
        {"product_id": 123, "score": 0.95},
        {"product_id": 456, "score": 0.85},
    ]
    
    # Configurar mock do OdooConnector
    mock_odoo_connector = await mock_odoo_connector_factory.create_connector("account_1")
    mock_odoo_connector.execute_kw.return_value = [
        {
            "id": 123,
            "name": "Test Product 1",
            "description": "Description 1",
            "list_price": 100.0,
            "categ_id": [1, "Test Category"],
        },
        {
            "id": 456,
            "name": "Test Product 2",
            "description": "Description 2",
            "list_price": 200.0,
            "categ_id": [2, "Another Category"],
        },
    ]
    
    # Fazer requisição
    response = test_client.post(
        "/api/v1/products/search?account_id=account_1",
        json={
            "query": "test product",
            "limit": 10,
            "filters": {
                "category_id": 1,
                "price_range": [50.0, 150.0]
            }
        },
    )
    
    # Verificar resposta
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["data"]["results"]) == 2
    assert data["data"]["total"] == 2
    assert data["data"]["results"][0]["product_id"] == 123
    assert data["data"]["results"][0]["name"] == "Test Product 1"
    assert data["data"]["results"][0]["score"] == 0.95
