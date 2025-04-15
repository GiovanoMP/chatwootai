"""
Configurações e fixtures para testes.

Este arquivo contém configurações e fixtures compartilhadas entre os testes.
"""

import pytest
import os
import yaml
import tempfile
import shutil
import json
from unittest.mock import MagicMock, patch

@pytest.fixture
def test_config_dir():
    """Cria um diretório temporário para configurações de teste."""
    temp_dir = tempfile.mkdtemp()
    os.makedirs(os.path.join(temp_dir, "config", "domains", "test_domain"), exist_ok=True)
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def mock_webhook_handler(test_config_dir):
    """Cria um webhook handler para testes."""
    # Importar aqui para evitar problemas de importação circular
    with patch('src.webhook.webhook_handler.ChatwootClient'):
        from src.webhook.webhook_handler import ChatwootWebhookHandler

        # Criar mock para o HubCrew
        mock_hub = MagicMock()
        mock_hub.domain_manager = MagicMock()
        mock_hub.domain_manager.get_domain_by_account_id.return_value = "test_domain"
        mock_hub.domain_manager.get_internal_account_id.return_value = "account_test"

        # Mock para o processamento de mensagens
        mock_hub.process_message = MagicMock()
        mock_hub.process_message.return_value = {
            "response": {
                "content": "Resposta de teste"
            },
            "routing": {
                "crew": "test_crew",
                "confidence": 0.9
            }
        }

        # Configurar o handler com o diretório de configuração de teste
        handler = ChatwootWebhookHandler(
            hub_crew=mock_hub,
            config={
                "config_dir": os.path.join(test_config_dir, "config"),
                "chatwoot_base_url": "http://test.chatwoot.local",
                "chatwoot_api_key": "test_api_key",
                "account_domain_mapping": {"1": "test_domain"},
                "inbox_domain_mapping": {"1": "test_domain"}
            }
        )

        return handler, mock_hub

@pytest.fixture
def mock_vector_service():
    """Cria um mock para o serviço de vetorização."""
    mock_service = MagicMock()

    # Configurar comportamento para perform_hybrid_search
    def mock_hybrid_search(query, filters=None, limit=10):
        # Retornar resultados simulados
        return [
            {
                "id": 1,
                "name": "Produto Teste 1",
                "description": "Descrição do produto teste 1",
                "list_price": 100.0,
                "qty_available": 10,
                "combined_score": 0.95
            },
            {
                "id": 2,
                "name": "Produto Teste 2",
                "description": "Descrição do produto teste 2",
                "list_price": 150.0,
                "qty_available": 5,
                "combined_score": 0.85
            },
            {
                "id": 3,
                "name": "Produto Teste 3",
                "description": "Descrição do produto teste 3",
                "list_price": 200.0,
                "qty_available": 2,
                "combined_score": 0.75
            }
        ][:limit]

    mock_service.perform_hybrid_search = mock_hybrid_search

    return mock_service

@pytest.fixture
def sample_credentials_payload():
    """Retorna um payload de exemplo para sincronização de credenciais."""
    return {
        "source": "credentials",
        "event": "credentials_sync",
        "account_id": "account_test",
        "token": "valid_test_token",
        "credentials": {
            "domain": "test_domain",
            "name": "Test Client",
            "odoo_url": "http://test.odoo.local",
            "odoo_db": "test_db",
            "odoo_username": "test_user",
            "token": "valid_test_token",
            "facebook_app_id": "fb_app_123",
            "facebook_app_secret": "fb_secret_123",
            "facebook_access_token": "fb_token_123"
        }
    }

@pytest.fixture
def sample_chatwoot_message():
    """Retorna uma mensagem de exemplo do Chatwoot."""
    return {
        "event": "message_created",
        "message": {
            "id": "test_message_id",
            "content": "Olá, preciso de ajuda",
            "message_type": "incoming"
        },
        "conversation": {
            "id": "test_conversation_id",
            "inbox_id": "1"
        },
        "account": {
            "id": "1"
        },
        "contact": {
            "id": "test_contact_id"
        }
    }

@pytest.fixture
def mock_redis_client():
    """Cria um mock para o cliente Redis."""
    mock_client = MagicMock()

    # Configurar comportamento padrão para os métodos
    mock_client.get.return_value = None
    mock_client.set.return_value = True
    mock_client.exists.return_value = False
    mock_client.delete.return_value = 0

    return mock_client
