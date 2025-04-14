# -*- coding: utf-8 -*-

"""
Testes de integração para a API de regras de negócio.
"""

import pytest
import json
from datetime import date, timedelta
from unittest.mock import patch, AsyncMock

from fastapi.testclient import TestClient
from odoo_api.main import app
from odoo_api.modules.business_rules.schemas import RuleType, RulePriority


@pytest.fixture
def client():
    """Fixture para o cliente de teste."""
    return TestClient(app)


@pytest.fixture
def mock_business_rules_service():
    """Fixture para o serviço de regras de negócio mockado."""
    with patch('odoo_api.modules.business_rules.routes.get_business_rules_service') as mock_get_service:
        service = AsyncMock()
        mock_get_service.return_value = service
        yield service


def test_create_business_rule(client, mock_business_rules_service):
    """Testa a criação de uma regra de negócio."""
    # Configurar mock
    mock_business_rules_service.create_business_rule.return_value = {
        "id": 123,
        "name": "Horário de Funcionamento",
        "description": "Horário de funcionamento da loja",
        "type": "business_hours",
        "priority": 2,
        "active": True,
        "rule_data": {
            "days": [0, 1, 2, 3, 4],
            "start_time": "09:00",
            "end_time": "18:00",
            "timezone": "America/Sao_Paulo"
        },
        "is_temporary": False,
        "start_date": None,
        "end_date": None,
        "created_at": "2023-06-15T10:30:00",
        "updated_at": "2023-06-15T10:30:00"
    }
    
    # Dados da requisição
    data = {
        "name": "Horário de Funcionamento",
        "description": "Horário de funcionamento da loja",
        "type": "business_hours",
        "priority": 2,
        "active": True,
        "rule_data": {
            "days": [0, 1, 2, 3, 4],
            "start_time": "09:00",
            "end_time": "18:00",
            "timezone": "America/Sao_Paulo"
        }
    }
    
    # Fazer requisição
    response = client.post(
        "/api/v1/business-rules?account_id=account_1",
        json=data
    )
    
    # Verificar resposta
    assert response.status_code == 200
    assert response.json()["success"] == True
    assert response.json()["data"]["id"] == 123
    assert response.json()["data"]["name"] == "Horário de Funcionamento"
    
    # Verificar chamada ao serviço
    mock_business_rules_service.create_business_rule.assert_called_once()
    call_args = mock_business_rules_service.create_business_rule.call_args[1]
    assert call_args["account_id"] == "account_1"
    assert call_args["rule_data"].name == "Horário de Funcionamento"
    assert call_args["rule_data"].type == RuleType.BUSINESS_HOURS
    assert call_args["rule_data"].priority == RulePriority.MEDIUM


def test_create_temporary_rule(client, mock_business_rules_service):
    """Testa a criação de uma regra temporária."""
    # Configurar mock
    tomorrow = date.today() + timedelta(days=1)
    next_week = date.today() + timedelta(days=7)
    
    mock_business_rules_service.create_temporary_rule.return_value = {
        "id": 456,
        "name": "Promoção de Verão",
        "description": "Desconto de 20% em produtos de verão",
        "type": "promotion",
        "priority": 3,
        "active": True,
        "rule_data": {
            "name": "Promoção de Verão",
            "description": "Desconto de 20% em produtos de verão",
            "discount_type": "percentage",
            "discount_value": 20.0,
            "product_categories": [5, 6]
        },
        "is_temporary": True,
        "start_date": tomorrow.isoformat(),
        "end_date": next_week.isoformat(),
        "created_at": "2023-06-15T10:30:00",
        "updated_at": "2023-06-15T10:30:00"
    }
    
    # Dados da requisição
    data = {
        "name": "Promoção de Verão",
        "description": "Desconto de 20% em produtos de verão",
        "type": "promotion",
        "priority": 3,
        "active": True,
        "rule_data": {
            "name": "Promoção de Verão",
            "description": "Desconto de 20% em produtos de verão",
            "discount_type": "percentage",
            "discount_value": 20.0,
            "product_categories": [5, 6]
        },
        "start_date": tomorrow.isoformat(),
        "end_date": next_week.isoformat()
    }
    
    # Fazer requisição
    response = client.post(
        "/api/v1/business-rules/temporary?account_id=account_1",
        json=data
    )
    
    # Verificar resposta
    assert response.status_code == 200
    assert response.json()["success"] == True
    assert response.json()["data"]["id"] == 456
    assert response.json()["data"]["name"] == "Promoção de Verão"
    assert response.json()["data"]["is_temporary"] == True
    
    # Verificar chamada ao serviço
    mock_business_rules_service.create_temporary_rule.assert_called_once()
    call_args = mock_business_rules_service.create_temporary_rule.call_args[1]
    assert call_args["account_id"] == "account_1"
    assert call_args["rule_data"].name == "Promoção de Verão"
    assert call_args["rule_data"].type == RuleType.PROMOTION
    assert call_args["rule_data"].priority == RulePriority.HIGH


def test_get_business_rule(client, mock_business_rules_service):
    """Testa a obtenção de uma regra de negócio."""
    # Configurar mock
    mock_business_rules_service.get_business_rule.return_value = {
        "id": 123,
        "name": "Horário de Funcionamento",
        "description": "Horário de funcionamento da loja",
        "type": "business_hours",
        "priority": 2,
        "active": True,
        "rule_data": {
            "days": [0, 1, 2, 3, 4],
            "start_time": "09:00",
            "end_time": "18:00",
            "timezone": "America/Sao_Paulo"
        },
        "is_temporary": False,
        "start_date": None,
        "end_date": None,
        "created_at": "2023-06-15T10:30:00",
        "updated_at": "2023-06-15T10:30:00"
    }
    
    # Fazer requisição
    response = client.get(
        "/api/v1/business-rules/123?account_id=account_1"
    )
    
    # Verificar resposta
    assert response.status_code == 200
    assert response.json()["success"] == True
    assert response.json()["data"]["id"] == 123
    assert response.json()["data"]["name"] == "Horário de Funcionamento"
    
    # Verificar chamada ao serviço
    mock_business_rules_service.get_business_rule.assert_called_once_with(
        account_id="account_1",
        rule_id=123
    )


def test_list_active_rules(client, mock_business_rules_service):
    """Testa a listagem de regras ativas."""
    # Configurar mock
    mock_business_rules_service.list_active_rules.return_value = [
        {
            "id": 123,
            "name": "Horário de Funcionamento",
            "description": "Horário de funcionamento da loja",
            "type": "business_hours",
            "priority": 2,
            "active": True,
            "rule_data": {
                "days": [0, 1, 2, 3, 4],
                "start_time": "09:00",
                "end_time": "18:00",
                "timezone": "America/Sao_Paulo"
            },
            "is_temporary": False,
            "start_date": None,
            "end_date": None,
            "created_at": "2023-06-15T10:30:00",
            "updated_at": "2023-06-15T10:30:00"
        },
        {
            "id": 456,
            "name": "Promoção de Verão",
            "description": "Desconto de 20% em produtos de verão",
            "type": "promotion",
            "priority": 3,
            "active": True,
            "rule_data": {
                "name": "Promoção de Verão",
                "description": "Desconto de 20% em produtos de verão",
                "discount_type": "percentage",
                "discount_value": 20.0,
                "product_categories": [5, 6]
            },
            "is_temporary": True,
            "start_date": "2023-06-15",
            "end_date": "2023-06-30",
            "created_at": "2023-06-15T10:30:00",
            "updated_at": "2023-06-15T10:30:00"
        }
    ]
    
    # Fazer requisição
    response = client.get(
        "/api/v1/business-rules/active?account_id=account_1"
    )
    
    # Verificar resposta
    assert response.status_code == 200
    assert response.json()["success"] == True
    assert len(response.json()["data"]) == 2
    assert response.json()["data"][0]["id"] == 123
    assert response.json()["data"][1]["id"] == 456
    
    # Verificar chamada ao serviço
    mock_business_rules_service.list_active_rules.assert_called_once_with(
        account_id="account_1",
        rule_type=None
    )


def test_sync_business_rules(client, mock_business_rules_service):
    """Testa a sincronização de regras com o sistema de IA."""
    # Configurar mock
    mock_business_rules_service.sync_business_rules.return_value = {
        "permanent_rules": 1,
        "temporary_rules": 1,
        "sync_status": "completed",
        "timestamp": "2023-06-15T10:30:00"
    }
    
    # Fazer requisição
    response = client.post(
        "/api/v1/business-rules/sync?account_id=account_1"
    )
    
    # Verificar resposta
    assert response.status_code == 200
    assert response.json()["success"] == True
    assert response.json()["data"]["permanent_rules"] == 1
    assert response.json()["data"]["temporary_rules"] == 1
    assert response.json()["data"]["sync_status"] == "completed"
    
    # Verificar chamada ao serviço
    mock_business_rules_service.sync_business_rules.assert_called_once_with(
        account_id="account_1"
    )
