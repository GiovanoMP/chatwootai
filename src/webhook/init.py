"""
Inicialização do sistema de webhook.

Este módulo contém a lógica de inicialização do sistema de webhook,
incluindo a configuração do HubCrew e do ChatwootWebhookHandler.
"""

import os
import sys
import logging
import json
import yaml
import traceback
from typing import Dict, Any, Optional

# Importa componentes necessários
from src.webhook.webhook_handler import ChatwootWebhookHandler
from src.core.hub import HubCrew
from src.core.data_service_hub import DataServiceHub
from src.core.domain import DomainManager
from src.core.data_proxy_agent import DataProxyAgent
from src.core.crews.crew_factory import get_crew_factory

# Configurar logging
logger = logging.getLogger(__name__)

# Variáveis globais
webhook_handler = None

def get_webhook_handler():
    """Obtém ou inicializa o webhook handler"""
    global webhook_handler
    if webhook_handler is None:
        webhook_handler = initialize_system()
    return webhook_handler

def initialize_system():
    """
    Inicializa o sistema de webhook, incluindo o HubCrew e o ChatwootWebhookHandler.
    
    Returns:
        ChatwootWebhookHandler: Handler inicializado para processar webhooks
    """
    logger.info("🔄 Inicializando sistema de webhook...")

    # Carrega configurações do Chatwoot
    chatwoot_base_url = os.getenv("CHATWOOT_BASE_URL", "")
    chatwoot_api_key = os.getenv("CHATWOOT_API_KEY", "")

    if not chatwoot_base_url or not chatwoot_api_key:
        logger.warning("⚠️ Variáveis de ambiente CHATWOOT_BASE_URL ou CHATWOOT_API_KEY não definidas")

    # Carrega configurações adicionais do webhook
    webhook_settings = {}
    webhook_config_path = os.getenv("WEBHOOK_CONFIG_PATH", "config/webhook_config.yaml")
    
    if os.path.exists(webhook_config_path):
        try:
            with open(webhook_config_path, 'r') as f:
                webhook_settings = yaml.safe_load(f) or {}
            logger.info(f"✅ Configurações do webhook carregadas de {webhook_config_path}")
        except Exception as e:
            logger.warning(f"⚠️ Erro ao carregar configurações do webhook: {str(e)}")

    # Carrega mapeamento de account_id para domínio
    account_domain_mapping = {}
    inbox_domain_mapping = {}
    mapping_path = os.getenv("CHATWOOT_MAPPING_PATH", "config/chatwoot_mapping.yaml")
    
    if os.path.exists(mapping_path):
        try:
            with open(mapping_path, 'r') as f:
                mapping_data = yaml.safe_load(f) or {}
                account_domain_mapping = mapping_data.get("account_domain_mapping", {})
                inbox_domain_mapping = mapping_data.get("inbox_domain_mapping", {})
            logger.info(f"✅ Mapeamento Chatwoot carregado de {mapping_path}")
            logger.info(f"📊 Mapeamento de accounts: {json.dumps(account_domain_mapping)}")
            logger.info(f"📊 Mapeamento de inboxes: {json.dumps(inbox_domain_mapping)}")
        except Exception as e:
            logger.warning(f"⚠️ Erro ao carregar mapeamento Chatwoot: {str(e)}")
    else:
        logger.warning(f"⚠️ Arquivo de mapeamento {mapping_path} não encontrado")

    # Inicializa o gerenciador de domínios
    domain_manager = DomainManager()
    logger.info("✅ DomainManager inicializado")

    # Inicializa o DataServiceHub
    data_service_hub = DataServiceHub()
    logger.info("✅ DataServiceHub inicializado")

    # Inicializa o DataProxyAgent
    data_proxy_agent = DataProxyAgent(
        domain_manager=domain_manager,
        data_service_hub=data_service_hub
    )
    logger.info("✅ DataProxyAgent inicializado")

    # Inicializa o CrewFactory
    crew_factory = get_crew_factory(
        domain_manager=domain_manager,
        data_proxy_agent=data_proxy_agent
    )
    logger.info("✅ CrewFactory inicializado")

    # Inicializa o HubCrew central
    hub_crew = HubCrew(
        domain_manager=domain_manager,
        data_proxy_agent=data_proxy_agent,
        crew_factory=crew_factory
    )
    logger.info("✅ HubCrew inicializado")

    # Configura o webhook handler
    webhook_config = {
        "chatwoot_base_url": chatwoot_base_url,
        "chatwoot_api_key": chatwoot_api_key,
        # Mapeamento dinâmico de canais - será expandido conforme necessário
        "channel_mapping": json.loads(os.getenv('CHANNEL_MAPPING', '{"1": "whatsapp"}')),
        # Adiciona os mapeamentos carregados do YAML
        "account_domain_mapping": account_domain_mapping,
        "inbox_domain_mapping": inbox_domain_mapping,
        # Adiciona configurações adicionais do webhook
        **webhook_settings
    }

    # Inicializa o webhook handler com o HubCrew central
    webhook_handler = ChatwootWebhookHandler(
        hub_crew=hub_crew,
        config=webhook_config
    )
    logger.info("✅ ChatwootWebhookHandler inicializado")
    
    logger.info("🎉 Sistema inicializado com sucesso para receber webhooks!")
    logger.info("🔄 Sistema configurado para determinar domínios dinamicamente por conversa")
    return webhook_handler
