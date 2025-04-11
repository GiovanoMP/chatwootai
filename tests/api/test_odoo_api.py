"""
Testes para a API REST de integração com o Odoo.

Este módulo contém testes para os endpoints da API REST de integração com o Odoo.

Autor: Augment Agent
Data: 26/03/2025
"""

import pytest
import json
from fastapi.testclient import TestClient
from src.api.odoo import app

# Cliente de teste
client = TestClient(app)

def test_root_endpoint():
    """Teste para o endpoint raiz."""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()

def test_product_sync_endpoint_without_token():
    """Teste para o endpoint de sincronização de produtos sem token."""
    payload = {
        "metadata": {
            "source": "odoo",
            "action": "sync_product"
        },
        "params": {
            "product_id": 1
        }
    }
    response = client.post("/api/v1/webhook/product/sync", json=payload)
    assert response.status_code == 401  # Unauthorized

def test_product_sync_endpoint_with_token():
    """Teste para o endpoint de sincronização de produtos com token."""
    payload = {
        "metadata": {
            "source": "odoo",
            "action": "sync_product"
        },
        "params": {
            "product_id": 1
        }
    }
    headers = {
        "Authorization": "Bearer test_token"
    }
    response = client.post("/api/v1/webhook/product/sync", json=payload, headers=headers)
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert "request_id" in response.json()

def test_product_description_endpoint():
    """Teste para o endpoint de geração de descrição de produto."""
    payload = {
        "metadata": {
            "source": "odoo",
            "action": "generate_description"
        },
        "params": {
            "product_id": 1
        }
    }
    headers = {
        "Authorization": "Bearer test_token"
    }
    response = client.post("/api/v1/webhook/product/description", json=payload, headers=headers)
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert "request_id" in response.json()

def test_status_endpoint():
    """Teste para o endpoint de verificação de status."""
    headers = {
        "Authorization": "Bearer test_token"
    }
    response = client.get("/api/v1/webhook/status/test_123", headers=headers)
    assert response.status_code == 200
    assert "request_id" in response.json()
    assert response.json()["request_id"] == "test_123"

def test_invalid_payload():
    """Teste para payload inválido."""
    payload = {
        "invalid": "payload"
    }
    headers = {
        "Authorization": "Bearer test_token"
    }
    response = client.post("/api/v1/webhook/product/sync", json=payload, headers=headers)
    assert response.status_code == 422  # Unprocessable Entity
