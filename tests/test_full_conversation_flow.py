import pytest
from fastapi.testclient import TestClient
from src.webhook.server import app
from src.core.hub import HubCrew
from src.services.data.data_proxy_agent import DataProxyAgent

@pytest.fixture
def test_client():
    return TestClient(app)

@pytest.fixture
def mock_data_proxy():
    proxy = DataProxyAgent()
    proxy.get_product_data = lambda domain, query: {
        'products': [
            {'name': 'Creme para Mãos', 'brand': 'Nivea', 'price': 25.90, 'in_stock': True}
        ]
    }
    return proxy

@pytest.fixture
def hub_crew(mock_data_proxy):
    return HubCrew(data_proxy_agent=mock_data_proxy)

def test_full_sales_conversation(test_client, hub_crew):
    # Simula payload do Chatwoot
    payload = {
        "content": "Você tem creme para as mãos?",
        "conversation": {"id": 123},
        "sender": {"phone_number": "+5511999999999"}
    }

    # Envia mensagem para o webhook
    response = test_client.post("/webhook/chatwoot", json=payload)

    # Verifica resposta
    assert response.status_code == 200
    response_data = response.json()
    
    assert "Creme para Mãos" in response_data['content']
    assert "Nivea" in response_data['content']
    assert "25,90" in response_data['content']
    
    # Verifica se passou por todos componentes
    assert hub_crew.context_manager.get_context(123) is not None
    assert hub_crew.orchestrator.last_intent == 'product_inquiry'
