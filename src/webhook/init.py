"""
Inicialização do sistema de webhook.

Este módulo contém a lógica de inicialização do sistema de webhook,
incluindo a configuração do Hub e do ChatwootWebhookHandler.

Na nova arquitetura, todas as mensagens são direcionadas para a
customer_service_crew, que é configurada via YAML para cada account_id.
"""

import os
import logging
import json
import yaml

# Importa componentes necessários
from src.webhook.webhook_handler import ChatwootWebhookHandler
from src.core.hub import Hub

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

    # Importar o cliente do serviço de configuração
    try:
        from src.utils.config_service_client import config_service

        # Verificar a saúde do serviço de configuração
        if config_service.health_check():
            logger.info("✅ Serviço de configuração está saudável")
            # Obter mapeamento do serviço de configuração
            mapping_data = config_service.get_chatwoot_mapping()
            logger.info("✅ Mapeamento Chatwoot carregado do serviço de configuração")
        else:
            logger.warning("⚠️ Serviço de configuração não está saudável. Usando mapeamento padrão.")
            mapping_data = {}
    except ImportError:
        logger.warning("⚠️ Cliente do serviço de configuração não encontrado. Usando arquivo local.")
        # Fallback para o arquivo local (legado)
        json_path = os.getenv("CHATWOOT_MAPPING_PATH", "config/chatwoot_mapping.json")

        # Se o caminho terminar com .yaml, mudar para .json
        if json_path.endswith('.yaml'):
            json_path = os.path.splitext(json_path)[0] + ".json"

        # Carregar mapeamento do JSON
        mapping_data = {}

        if os.path.exists(json_path):
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    mapping_data = json.load(f) or {}
                logger.info(f"✅ Mapeamento Chatwoot carregado do JSON: {json_path}")
            except Exception as e:
                logger.warning(f"⚠️ Erro ao carregar mapeamento do JSON: {str(e)}")
                # Se houver erro, usar um mapeamento vazio
                mapping_data = {}
        else:
            logger.warning(f"⚠️ Arquivo de mapeamento {json_path} não encontrado. Usando padrão.")

    # Carregar mapeamentos no novo formato
    account_domain_mapping = mapping_data.get("account_domain_mapping", {})
    inbox_domain_mapping = mapping_data.get("inbox_domain_mapping", {})

    # Se não encontrar no novo formato, tentar o formato legado
    if not account_domain_mapping and "accounts" in mapping_data:
        logger.info("Usando formato legado para account_domain_mapping")
        legacy_accounts = mapping_data.get("accounts", {})
        # Converter do formato legado para o novo formato
        for account_id, account_info in legacy_accounts.items():
            if isinstance(account_info, dict) and "domain" in account_info:
                account_domain_mapping[account_id] = account_info["domain"]

    # Se não encontrar no novo formato, tentar o formato legado para inboxes
    if not inbox_domain_mapping and "inboxes" in mapping_data:
        logger.info("Usando formato legado para inbox_domain_mapping")
        inbox_domain_mapping = mapping_data.get("inboxes", {})

    logger.info(f"📊 Mapeamento de accounts: {json.dumps(account_domain_mapping)}")
    logger.info(f"📊 Mapeamento de inboxes: {json.dumps(inbox_domain_mapping)}")

    # Na nova arquitetura, não precisamos mais de componentes legados
    logger.info("✅ Usando nova arquitetura simplificada")

    # Inicializa o Hub central
    hub = Hub()
    logger.info("✅ Hub inicializado")

    # Na nova arquitetura, usamos diretamente o Hub

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

    # Inicializa o webhook handler diretamente com o Hub
    webhook_handler = ChatwootWebhookHandler(
        hub=hub,
        config=webhook_config
    )
    logger.info("✅ ChatwootWebhookHandler inicializado com o novo Hub")

    logger.info("🎉 Sistema inicializado com sucesso para receber webhooks!")
    logger.info("🔄 Sistema configurado com a nova arquitetura simplificada")
    logger.info("🔄 Todas as mensagens serão direcionadas para a customer_service_crew")
    return webhook_handler
