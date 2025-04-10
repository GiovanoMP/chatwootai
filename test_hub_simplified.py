#!/usr/bin/env python3
"""
Script para testar o hub_simplified.py
"""

import asyncio
import logging
import sys
import os
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Adicionar o diretório atual ao path para importar os módulos locais
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    # Importar os módulos necessários
    from src.core.hub_simplified import HubCrew
    from src.core.data_proxy_agent import DataProxyAgent
    from src.core.domain.domain_manager import DomainManager

    # Função principal assíncrona
    async def main():
        logger.info("Iniciando teste do HubCrew simplificado...")

        # Criar componentes necessários
        domain_manager = DomainManager(domains_dir="@config", default_domain="furniture")
        data_proxy_agent = DataProxyAgent(domain_manager=domain_manager)

        # Criar o HubCrew simplificado
        hub_crew = HubCrew(
            data_proxy_agent=data_proxy_agent,
            domain_manager=domain_manager
        )

        # Criar uma mensagem de teste
        message = {
            "id": "test_message_1",
            "content": "Olá, gostaria de informações sobre móveis para sala de estar",
            "sender_id": "user_123",
            "recipient_id": "bot_456",
            "timestamp": datetime.now().isoformat()
        }

        # Processar a mensagem
        logger.info("Processando mensagem de teste...")
        result = await hub_crew.process_message(
            message=message,
            conversation_id="test_conversation_1",
            channel_type="whatsapp",
            domain_name="furniture",  # Fornecer o domínio diretamente para teste
            account_id="account_2"    # Fornecer o account_id diretamente para teste
        )

        # Exibir o resultado
        logger.info(f"Resultado do processamento: {result}")

        # Finalizar a conversa
        logger.info("Finalizando conversa de teste...")
        finalize_result = await hub_crew.finalize_conversation("test_conversation_1")

        # Exibir o resultado da finalização
        logger.info(f"Resultado da finalização: {finalize_result}")

        logger.info("Teste concluído!")

    # Executar a função principal
    if __name__ == "__main__":
        asyncio.run(main())

except ImportError as e:
    logger.error(f"Erro ao importar os módulos necessários: {e}")
    logger.error("Verifique se todas as dependências estão instaladas.")
    sys.exit(1)
except Exception as e:
    logger.error(f"Erro ao testar o HubCrew simplificado: {e}")
    sys.exit(1)
