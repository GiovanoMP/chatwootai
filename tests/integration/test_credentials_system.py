"""
Testes de integração para o sistema de referências de credenciais.

Estes testes verificam se o sistema de referências de credenciais está funcionando corretamente,
incluindo a sincronização de credenciais, a substituição de credenciais sensíveis por referências
e a recuperação de credenciais usando referências.
"""

import pytest
import os
import yaml
import json
from unittest.mock import patch, MagicMock

@pytest.mark.asyncio
async def test_credentials_endpoint_with_valid_token(mock_webhook_handler, test_config_dir, sample_credentials_payload):
    """
    Testa se o endpoint de credenciais processa corretamente um payload com token válido.
    
    Este teste verifica se:
    1. O endpoint retorna sucesso
    2. O arquivo YAML é criado corretamente
    3. As credenciais sensíveis são substituídas por referências
    """
    handler, mock_hub = mock_webhook_handler
    
    # Processar o payload de credenciais
    response = await handler.process_credentials_event(sample_credentials_payload)
    
    # Verificar se a resposta foi bem-sucedida
    assert response["success"] == True
    assert "config_path" in response
    
    # Verificar se o arquivo YAML foi criado corretamente
    config_path = response["config_path"]
    assert os.path.exists(config_path)
    
    # Verificar se as credenciais sensíveis foram substituídas por referências
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Verificar estrutura básica
    assert "account_id" in config
    assert config["account_id"] == "account_test"
    assert "integrations" in config
    assert "mcp" in config["integrations"]
    
    # Verificar se as credenciais sensíveis foram substituídas por referências
    assert "credential_ref" in config["integrations"]["mcp"]["config"]
    assert config["integrations"]["mcp"]["config"]["credential_ref"] == "valid_test_token"
    
    # Verificar se as credenciais do Facebook foram processadas corretamente
    assert "facebook" in config["integrations"]
    assert "app_id" in config["integrations"]["facebook"]
    assert "app_secret_ref" in config["integrations"]["facebook"]
    assert "access_token_ref" in config["integrations"]["facebook"]
    assert config["integrations"]["facebook"]["app_id"] == "fb_app_123"
    assert config["integrations"]["facebook"]["app_secret_ref"] == "fb_secret_account_test"
    assert config["integrations"]["facebook"]["access_token_ref"] == "fb_token_account_test"

@pytest.mark.asyncio
async def test_credentials_endpoint_with_invalid_token(mock_webhook_handler, sample_credentials_payload):
    """
    Testa se o endpoint de credenciais rejeita corretamente um payload com token inválido.
    """
    handler, mock_hub = mock_webhook_handler
    
    # Modificar o payload para ter um token inválido
    invalid_payload = sample_credentials_payload.copy()
    invalid_payload["token"] = "invalid_token"
    
    # Processar o payload de credenciais
    response = await handler.process_credentials_event(invalid_payload)
    
    # Verificar se a resposta indica falha
    assert response["success"] == False
    assert "error" in response
    assert "Token de autenticação inválido" in response["error"]

@pytest.mark.asyncio
async def test_credentials_endpoint_with_missing_data(mock_webhook_handler):
    """
    Testa se o endpoint de credenciais rejeita corretamente um payload com dados faltando.
    """
    handler, mock_hub = mock_webhook_handler
    
    # Criar payload incompleto
    incomplete_payload = {
        "source": "credentials",
        "event": "credentials_sync"
        # Faltando account_id e credentials
    }
    
    # Processar o payload de credenciais
    response = await handler.process_credentials_event(incomplete_payload)
    
    # Verificar se a resposta indica falha
    assert response["success"] == False
    assert "error" in response
    assert "Dados incompletos" in response["error"]

@pytest.mark.asyncio
async def test_credentials_endpoint_updates_existing_config(mock_webhook_handler, test_config_dir, sample_credentials_payload):
    """
    Testa se o endpoint de credenciais atualiza corretamente um arquivo de configuração existente.
    """
    handler, mock_hub = mock_webhook_handler
    
    # Criar um arquivo de configuração existente
    account_dir = os.path.join(test_config_dir, "config", "domains", "test_domain", "account_test")
    os.makedirs(account_dir, exist_ok=True)
    config_path = os.path.join(account_dir, "config.yaml")
    
    existing_config = {
        "account_id": "account_test",
        "name": "Existing Client",
        "description": "Configuração existente",
        "integrations": {
            "mcp": {
                "type": "odoo-mcp",
                "config": {
                    "url": "http://existing.odoo.local",
                    "db": "existing_db",
                    "username": "existing_user",
                    "credential_ref": "existing_token"
                }
            },
            "qdrant": {
                "collection": "existing_collection",
                "custom_setting": "custom_value"
            }
        }
    }
    
    with open(config_path, 'w') as f:
        yaml.dump(existing_config, f)
    
    # Processar o payload de credenciais
    response = await handler.process_credentials_event(sample_credentials_payload)
    
    # Verificar se a resposta foi bem-sucedida
    assert response["success"] == True
    
    # Verificar se o arquivo YAML foi atualizado corretamente
    with open(config_path, 'r') as f:
        updated_config = yaml.safe_load(f)
    
    # Verificar se os campos foram atualizados
    assert updated_config["name"] == "Test Client"  # Atualizado
    assert "description" in updated_config  # Mantido do original
    
    # Verificar se as configurações MCP foram atualizadas
    assert updated_config["integrations"]["mcp"]["config"]["url"] == "http://test.odoo.local"  # Atualizado
    assert updated_config["integrations"]["mcp"]["config"]["db"] == "test_db"  # Atualizado
    assert updated_config["integrations"]["mcp"]["config"]["credential_ref"] == "valid_test_token"  # Atualizado
    
    # Verificar se as configurações personalizadas foram mantidas
    assert "qdrant" in updated_config["integrations"]
    assert "custom_setting" in updated_config["integrations"]["qdrant"]
    assert updated_config["integrations"]["qdrant"]["custom_setting"] == "custom_value"
