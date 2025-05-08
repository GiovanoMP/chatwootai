#!/usr/bin/env python3
"""
Teste da nova arquitetura do ChatwootAI.

Este script testa os componentes principais da nova arquitetura:
- ConfigRegistry e ConfigLoader
- BaseCrew e crews específicas por canal
- CrewFactory
- Hub
"""

import asyncio
import logging
import os
import sys

# Adicionar o diretório raiz ao PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.config import get_config_registry
from src.core.crews import get_crew_factory
from src.core.hub import get_hub

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_config_registry():
    """Testa o ConfigRegistry."""
    logger.info("=== Testando ConfigRegistry ===")
    
    # Obter instância do ConfigRegistry
    config_registry = get_config_registry()
    
    # Testar carregamento de configuração
    domain_name = "furniture"
    account_id = "account_2"
    
    config = await config_registry.get_config(domain_name, account_id)
    
    if config:
        logger.info(f"Configuração carregada com sucesso para {domain_name}/{account_id}")
        logger.info(f"Nome da empresa: {config.get('name', 'N/A')}")
        logger.info(f"Integrações: {list(config.get('integrations', {}).keys())}")
    else:
        logger.error(f"Falha ao carregar configuração para {domain_name}/{account_id}")
    
    return config is not None

async def test_crew_factory(domain_name, account_id):
    """Testa o CrewFactory."""
    logger.info("=== Testando CrewFactory ===")
    
    # Obter instância do CrewFactory
    crew_factory = get_crew_factory()
    
    # Testar criação de crew para WhatsApp
    crew = await crew_factory.create_crew(
        crew_type="customer_service",
        domain_name=domain_name,
        account_id=account_id,
        channel_type="whatsapp"
    )
    
    if crew:
        logger.info(f"Crew criada com sucesso: {crew.__class__.__name__}")
        logger.info(f"Agentes: {len(crew.agents)}")
        logger.info(f"Tarefas: {len(getattr(crew.crew, 'tasks', []))}")
    else:
        logger.error("Falha ao criar crew")
    
    return crew is not None

async def test_hub(domain_name, account_id):
    """Testa o Hub."""
    logger.info("=== Testando Hub ===")
    
    # Obter instância do Hub
    hub = get_hub()
    
    # Criar mensagem de teste
    message = {
        "content": "Olá, gostaria de informações sobre produtos",
        "sender_id": "test_user",
        "source_id": "whatsapp"
    }
    
    # Testar processamento de mensagem
    result = await hub.process_message(
        message=message,
        conversation_id="test_conversation",
        channel_type="chatwoot",
        domain_name=domain_name,
        account_id=account_id
    )
    
    if result:
        logger.info(f"Mensagem processada com sucesso")
        logger.info(f"Status: {result.get('status', 'N/A')}")
        logger.info(f"Roteamento: {result.get('routing', {})}")
        if "content" in result:
            logger.info(f"Resposta: {result.get('content')[:100]}...")
    else:
        logger.error("Falha ao processar mensagem")
    
    return result is not None

async def main():
    """Função principal."""
    logger.info("Iniciando testes da nova arquitetura")
    
    # Definir domínio e account_id para testes
    domain_name = "furniture"
    account_id = "account_2"
    
    # Testar ConfigRegistry
    config_ok = await test_config_registry()
    if not config_ok:
        logger.error("Teste do ConfigRegistry falhou, abortando")
        return
    
    # Testar CrewFactory
    crew_ok = await test_crew_factory(domain_name, account_id)
    if not crew_ok:
        logger.error("Teste do CrewFactory falhou, abortando")
        return
    
    # Testar Hub
    hub_ok = await test_hub(domain_name, account_id)
    if not hub_ok:
        logger.error("Teste do Hub falhou")
        return
    
    logger.info("Todos os testes concluídos com sucesso!")

if __name__ == "__main__":
    asyncio.run(main())
