"""
Testes de integração para o fluxo de mensagens do webhook.

Estes testes verificam se o webhook processa corretamente as mensagens do Chatwoot,
incluindo a extração de metadados, o roteamento para o HubCrew e o retorno de respostas.
"""

import pytest
import json
from unittest.mock import patch, MagicMock, AsyncMock

@pytest.mark.asyncio
async def test_webhook_message_flow(mock_webhook_handler, sample_chatwoot_message):
    """
    Testa o fluxo básico de processamento de mensagens do Chatwoot.
    
    Este teste verifica se:
    1. O webhook extrai corretamente os metadados da mensagem
    2. A mensagem é encaminhada para o HubCrew
    3. A resposta é retornada corretamente
    """
    handler, mock_hub = mock_webhook_handler
    
    # Configurar o mock para _send_reply_to_chatwoot
    handler._send_reply_to_chatwoot = AsyncMock()
    handler._send_reply_to_chatwoot.return_value = {"id": "test_reply_id"}
    
    # Processar a mensagem
    response = await handler.process_webhook(sample_chatwoot_message)
    
    # Verificar se a mensagem foi processada
    assert response["status"] == "processed"
    assert "conversation_id" in response
    assert response["conversation_id"] == "test_conversation_id"
    assert response["has_response"] == True
    
    # Verificar se o HubCrew foi chamado com os parâmetros corretos
    mock_hub.process_message.assert_called_once()
    call_args = mock_hub.process_message.call_args[1]
    
    assert call_args["conversation_id"] == "test_conversation_id"
    assert call_args["domain_name"] == "test_domain"
    assert call_args["account_id"] == "account_test"
    assert call_args["message"]["content"] == "Olá, preciso de ajuda"
    
    # Verificar se a resposta foi enviada para o Chatwoot
    handler._send_reply_to_chatwoot.assert_called_once()
    reply_args = handler._send_reply_to_chatwoot.call_args[1]
    
    assert reply_args["conversation_id"] == "test_conversation_id"
    assert reply_args["content"] == "Resposta de teste"
    assert reply_args["private"] == False
    assert reply_args["message_type"] == "outgoing"

@pytest.mark.asyncio
async def test_webhook_ignores_outgoing_messages(mock_webhook_handler, sample_chatwoot_message):
    """
    Testa se o webhook ignora corretamente mensagens de saída (enviadas pelo sistema).
    """
    handler, mock_hub = mock_webhook_handler
    
    # Modificar a mensagem para ser de saída
    outgoing_message = sample_chatwoot_message.copy()
    outgoing_message["message"] = outgoing_message["message"].copy()
    outgoing_message["message"]["message_type"] = "outgoing"
    
    # Processar a mensagem
    response = await handler.process_webhook(outgoing_message)
    
    # Verificar se a mensagem foi ignorada
    assert response["status"] == "ignored"
    assert "reason" in response
    assert "Not an incoming message" in response["reason"]
    
    # Verificar se o HubCrew não foi chamado
    mock_hub.process_message.assert_not_called()

@pytest.mark.asyncio
async def test_webhook_handles_empty_content(mock_webhook_handler, sample_chatwoot_message):
    """
    Testa se o webhook lida corretamente com mensagens sem conteúdo.
    """
    handler, mock_hub = mock_webhook_handler
    
    # Modificar a mensagem para não ter conteúdo
    empty_message = sample_chatwoot_message.copy()
    empty_message["message"] = empty_message["message"].copy()
    empty_message["message"]["content"] = ""
    
    # Processar a mensagem
    response = await handler.process_webhook(empty_message)
    
    # Verificar se a mensagem foi ignorada
    assert response["status"] == "ignored"
    assert "reason" in response
    assert "Empty message content" in response["reason"]
    
    # Verificar se o HubCrew não foi chamado
    mock_hub.process_message.assert_not_called()

@pytest.mark.asyncio
async def test_webhook_handles_error_in_processing(mock_webhook_handler, sample_chatwoot_message):
    """
    Testa se o webhook lida corretamente com erros durante o processamento.
    """
    handler, mock_hub = mock_webhook_handler
    
    # Configurar o HubCrew para lançar uma exceção
    mock_hub.process_message.side_effect = Exception("Erro de teste")
    
    # Configurar o mock para _send_reply_to_chatwoot
    handler._send_reply_to_chatwoot = AsyncMock()
    
    # Processar a mensagem
    response = await handler.process_webhook(sample_chatwoot_message)
    
    # Verificar se a resposta indica erro
    assert response["status"] == "error"
    assert "error" in response
    assert "Erro de teste" in response["error"]
    
    # Verificar se uma mensagem de erro foi enviada para o Chatwoot
    handler._send_reply_to_chatwoot.assert_called_once()
    reply_args = handler._send_reply_to_chatwoot.call_args[1]
    
    assert reply_args["conversation_id"] == "test_conversation_id"
    assert "Desculpe" in reply_args["content"]
    assert reply_args["private"] == False
