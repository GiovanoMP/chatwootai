"""
Testes para a integração do webhook com o sistema de agentes.

Este script contém casos de teste para verificar se a integração
entre o webhook do Chatwoot e o sistema de agentes está funcionando corretamente.
"""

import os
import sys
import json
import pytest
import requests
from typing import Dict, Any, Optional
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# URL do servidor webhook (local ou remoto)
WEBHOOK_URL = os.environ.get("TEST_WEBHOOK_URL", "http://localhost:8001")

# Dados de teste
TEST_CONVERSATION_ID = "123456"
TEST_MESSAGE_ID = "789012"
TEST_CONTACT_ID = "345678"
TEST_INBOX_ID = "1"  # Assumindo que este é mapeado para "whatsapp"

def create_test_message_payload(message_content: str) -> Dict[str, Any]:
    """
    Cria um payload de teste para uma mensagem do Chatwoot.
    
    Args:
        message_content: Conteúdo da mensagem
        
    Returns:
        Dict[str, Any]: Payload de teste
    """
    return {
        "event": "message_created",
        "id": 123,
        "account": {
            "id": 1,
            "name": "Test Account"
        },
        "inbox": {
            "id": int(TEST_INBOX_ID),
            "name": "WhatsApp"
        },
        "conversation": {
            "id": int(TEST_CONVERSATION_ID),
            "inbox_id": int(TEST_INBOX_ID),
            "status": "open",
            "created_at": "2023-01-01T00:00:00Z",
            "contact_last_seen_at": "2023-01-01T00:00:00Z",
            "agent_last_seen_at": "2023-01-01T00:00:00Z"
        },
        "message": {
            "id": int(TEST_MESSAGE_ID),
            "content": message_content,
            "message_type": "incoming",
            "content_type": "text",
            "created_at": datetime.now().isoformat(),
            "private": False
        },
        "contact": {
            "id": int(TEST_CONTACT_ID),
            "name": "Test User",
            "email": "test@example.com",
            "phone_number": "5511999999999"
        }
    }

def test_webhook_server_running():
    """Verifica se o servidor webhook está rodando."""
    try:
        response = requests.get(f"{WEBHOOK_URL}/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "online"
        logger.info("✅ Servidor webhook está rodando")
        return True
    except Exception as e:
        logger.error(f"❌ Erro ao verificar servidor webhook: {str(e)}")
        return False

def test_health_endpoint():
    """Verifica se o endpoint de saúde está funcionando."""
    try:
        response = requests.get(f"{WEBHOOK_URL}/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        logger.info(f"✅ Endpoint de saúde respondeu: {data['status']}")
        return True
    except Exception as e:
        logger.error(f"❌ Erro ao verificar endpoint de saúde: {str(e)}")
        return False

def test_webhook_endpoint_message_processing(message_content: str = "Olá, preciso de ajuda"):
    """
    Verifica se o endpoint webhook consegue processar uma mensagem.
    
    Args:
        message_content: Conteúdo da mensagem de teste
    """
    try:
        payload = create_test_message_payload(message_content)
        
        # Log detalhado do payload
        logger.info(f"Enviando payload de teste: {json.dumps(payload, indent=2)}")
        
        # Envia o payload para o endpoint webhook
        response = requests.post(f"{WEBHOOK_URL}/webhook", json=payload)
        
        # Verifica o status HTTP
        assert response.status_code in [200, 202]
        
        # Obtém os dados da resposta
        data = response.json()
        
        # Log da resposta
        logger.info(f"Resposta do webhook: {json.dumps(data, indent=2)}")
        
        # Verifica se a resposta contém campos esperados
        assert "status" in data
        
        # Verifica se a mensagem foi processada (ou ignorada, se for um teste)
        assert data["status"] in ["processed", "processed_no_response", "ignored"]
        
        # Se a mensagem foi processada, verifica detalhes adicionais
        if data["status"] == "processed":
            assert "crew" in data
            logger.info(f"✅ Mensagem processada pela crew: {data['crew']}")
            
            # Verifica se foi gerada uma resposta
            if data.get("has_response", False):
                logger.info("✅ Resposta gerada com sucesso")
        
        # Verifica tempos de processamento
        if "processing_time" in data:
            logger.info(f"⏱️ Tempo de processamento: {data['processing_time']}")
        
        # Verifica estatísticas, se disponíveis
        if "stats" in data:
            logger.info(f"📊 Estatísticas: {json.dumps(data['stats'], indent=2)}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Erro ao testar processamento de mensagem: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def run_all_tests():
    """Executa todos os testes em sequência."""
    print("\n==== Teste de Integração Webhook-Agentes ====\n")
    
    # Verifica se o servidor está rodando
    if not test_webhook_server_running():
        print("\n❌ ERRO: O servidor webhook não está rodando. Execute-o antes de executar os testes.\n")
        return
    
    # Verifica o endpoint de saúde
    test_health_endpoint()
    
    # Testa o processamento de mensagem de vendas
    print("\n==== Teste de Processamento de Mensagem de Vendas ====")
    test_webhook_endpoint_message_processing("Quero comprar um hidratante facial")
    
    # Testa o processamento de mensagem de suporte
    print("\n==== Teste de Processamento de Mensagem de Suporte ====")
    test_webhook_endpoint_message_processing("Tenho um problema com meu pedido #12345")
    
    # Testa o processamento de mensagem de informações
    print("\n==== Teste de Processamento de Mensagem de Informações ====")
    test_webhook_endpoint_message_processing("Quais são os horários de funcionamento da loja?")
    
    print("\n==== Testes Concluídos ====\n")

if __name__ == "__main__":
    run_all_tests()
