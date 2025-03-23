#!/usr/bin/env python3
"""
Script para testar manualmente o fluxo de mensagens no ChatwootAI.

Este script simula uma mensagem chegando pelo webhook do Chatwoot e 
acompanha seu processamento completo na arquitetura hub-and-spoke.

Uso:
    python test_message_manually.py
    
    Ou para testar com mensagem personalizada:
    python test_message_manually.py "Vocês têm protetor solar fator 50?"
"""

import asyncio
import json
import logging
import sys
from datetime import datetime

# Configuração de logging colorido para facilitar a visualização
try:
    import coloredlogs
    coloredlogs.install(level=logging.INFO,
                      fmt='%(asctime)s %(name)s [%(levelname)s] %(message)s')
except ImportError:
    logging.basicConfig(level=logging.INFO,
                     format='%(asctime)s %(name)s [%(levelname)s] %(message)s')

logger = logging.getLogger("TESTE-MANUAL")

# Importações dos componentes do sistema
from src.webhook.webhook_handler import ChatwootWebhookHandler
from src.core.hub import HubCrew
from src.core.memory import MemorySystem
from src.core.data_service_hub import DataServiceHub
from src.core.domain.domain_manager import DomainManager
from src.crews.sales_crew import SalesCrew
from src.crews.functional_crew import FunctionalCrew
from src.plugins.core.plugin_manager import PluginManager


class MockChatwootAPI:
    """Simulação da API do Chatwoot para visualizar as respostas."""
    
    def __init__(self):
        self.messages = []
    
    async def send_message(self, conversation_id, content, message_type="outgoing", private=False):
        """Simula o envio de uma mensagem para o Chatwoot."""
        message = {
            "conversation_id": conversation_id,
            "content": content,
            "message_type": message_type,
            "private": private,
            "timestamp": datetime.now().isoformat()
        }
        self.messages.append(message)
        logger.info(f"🔵 CHATWOOT recebeu resposta: {content}")
        return message


async def setup_system():
    """Configura todos os componentes do sistema para teste."""
    logger.info("🚀 Inicializando componentes do sistema para teste...")
    
    # 1. Inicializar sistema de memória
    memory_system = MemorySystem()
    logger.info("✅ Sistema de memória inicializado")
    
    # 2. Inicializar gerenciador de domínio
    domain_manager = DomainManager()
    domain_manager.switch_domain("cosmetics")
    logger.info(f"✅ Gerenciador de domínio inicializado com domínio ativo: {domain_manager.get_active_domain_name()}")
    
    # 3. Inicializar gerenciador de plugins
    plugin_manager = PluginManager(config={})
    logger.info("✅ Gerenciador de plugins inicializado")
    
    # 4. Inicializar hub de serviços de dados
    data_service_hub = DataServiceHub()
    logger.info("✅ Hub de serviços de dados inicializado")
    
    # 5. Inicializar a SalesCrew
    sales_crew = SalesCrew(
        memory_system=memory_system,
        data_service_hub=data_service_hub,
        domain_manager=domain_manager,
        plugin_manager=plugin_manager
    )
    logger.info("✅ SalesCrew inicializada")
    
    # 6. Inicializar o HubCrew (centro da arquitetura hub-and-spoke)
    hub_crew = HubCrew(
        memory_system=memory_system,
        data_service_hub=data_service_hub
    )
    
    # 7. Conectar crews funcionais ao HubCrew
    functional_crews = {
        "sales": sales_crew
    }
    # Adicionar ao dict do HubCrew para que possa rotear mensagens
    setattr(hub_crew, "_functional_crews", functional_crews)
    logger.info("✅ HubCrew inicializado e conectado às crews funcionais")
    
    # 8. Inicializar o webhook handler com a API mock do Chatwoot
    mock_chatwoot = MockChatwootAPI()
    webhook_handler = ChatwootWebhookHandler(
        hub_crew=hub_crew,
        config={
            "channel_mapping": {"1": "whatsapp"},
            "chatwoot_api_key": "test_api_key",
            "chatwoot_base_url": "http://localhost:3000/api/v1",
            "chatwoot_account_id": 1
        }
    )
    # Substituir o método de envio para usar nosso mock
    webhook_handler._send_reply_to_chatwoot = mock_chatwoot.send_message
    logger.info("✅ Webhook handler inicializado com mock do Chatwoot")
    
    logger.info("🎉 Todos os componentes inicializados com sucesso!")
    
    return webhook_handler


async def test_message(webhook_handler, message_content):
    """Testa o processamento de uma mensagem específica."""
    # Criar uma mensagem de teste simulando webhook do Chatwoot
    test_webhook = {
        "event": "message_created",  # Tipo de evento esperado pelo webhook handler
        "message": {
            "id": 12345,
            "content": message_content,
            "message_type": "incoming",
            "created_at": datetime.now().isoformat()
        },
        "conversation": {
            "id": 67890,
            "inbox_id": 1
        },
        "contact": {
            "id": 54321,
            "name": "Cliente Teste"
        }
    }
    
    logger.info(f"📩 Simulando mensagem do cliente: '{message_content}'")
    
    # Processar a mensagem pelo webhook handler
    logger.info("⚙️ Iniciando processamento da mensagem...")
    result = await webhook_handler.process_webhook(test_webhook)
    
    # Exibir resultado do processamento
    logger.info("✅ Processamento concluído!")
    if result:
        logger.info(f"📊 Resultado: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    return result


async def main():
    """Função principal do script."""
    print("\n" + "="*70)
    print("🤖 TESTE MANUAL DO FLUXO DE MENSAGENS NO CHATWOOT AI")
    print("="*70 + "\n")
    
    # Obter mensagem dos argumentos ou usar padrão
    message = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Você tem creme para as mãos?"
    
    # Configurar o sistema
    webhook_handler = await setup_system()
    
    # Testar o processamento da mensagem
    print("\n" + "-"*70)
    print(f"📱 CLIENTE envia: '{message}'")
    print("-"*70 + "\n")
    
    await test_message(webhook_handler, message)
    
    print("\n" + "="*70)
    print("✅ TESTE CONCLUÍDO")
    print("="*70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
