import pytest
from src.webhook.webhook_handler import process_webhook_event

@pytest.fixture
def mock_data_proxy():
    # Implementar mock do DataProxyAgent
    {{ ... }}

def test_processamento_mensagem_simples(mock_data_proxy):
    # Teste end-to-end do fluxo principal
    {{ ... }}
