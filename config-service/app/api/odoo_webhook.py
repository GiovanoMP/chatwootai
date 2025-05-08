"""
Endpoint para receber webhooks do Odoo.

Este módulo implementa um endpoint dedicado para receber webhooks do Odoo,
processando atualizações de configurações e credenciais diretamente no banco de dados.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_api_key
from app.services.config_service import ConfigService
from app.services.mapping_service import MappingService
from typing import Dict, Any, Optional
import yaml
import json
import logging
import traceback
from datetime import datetime

router = APIRouter(prefix="/odoo-webhook", tags=["odoo"])
logger = logging.getLogger(__name__)

@router.post("/", response_model=Dict[str, Any])
async def process_odoo_webhook(
    webhook_data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """
    Processa webhook do Odoo com atualizações de configuração.

    Args:
        webhook_data: Dados do webhook
        db: Sessão do banco de dados
        api_key: Chave de API para autenticação

    Returns:
        Resultado do processamento
    """
    logger.info("Recebendo webhook do Odoo")
    logger.debug(f"Dados do webhook: {json.dumps(webhook_data, indent=2)}")

    # Extrair informações do webhook
    event_type = webhook_data.get("event_type")

    # Se event_type não estiver definido, tentar determinar pelo conteúdo
    if not event_type:
        if "credentials" in webhook_data:
            event_type = "credentials_sync"
            logger.info("Tipo de evento determinado como 'credentials_sync' pelo conteúdo")
        elif "mapping" in webhook_data:
            event_type = "mapping_sync"
            logger.info("Tipo de evento determinado como 'mapping_sync' pelo conteúdo")
        elif webhook_data.get("source") == "credentials":
            event_type = "credentials_sync"
            logger.info("Tipo de evento determinado como 'credentials_sync' pelo campo 'source'")
        elif webhook_data.get("source") == "channel_mapping":
            event_type = "mapping_sync"
            logger.info("Tipo de evento determinado como 'mapping_sync' pelo campo 'source'")

    if event_type == "credentials_sync":
        return await process_credentials_sync(webhook_data, db)
    elif event_type == "mapping_sync":
        return await process_mapping_sync(webhook_data, db)
    elif event_type == "company_metadata_sync":
        return await process_company_metadata_sync(webhook_data, db)
    else:
        logger.warning(f"Tipo de evento desconhecido: {event_type}")
        logger.warning(f"Conteúdo do webhook: {json.dumps(webhook_data, indent=2)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tipo de evento não suportado ou não identificado"
        )

async def process_credentials_sync(webhook_data: Dict[str, Any], db: Session) -> Dict[str, Any]:
    """
    Processa evento de sincronização de credenciais.

    Args:
        webhook_data: Dados do webhook
        db: Sessão do banco de dados

    Returns:
        Resultado do processamento
    """
    try:
        # Extrair informações do evento
        account_id = webhook_data.get("account_id")
        credentials = webhook_data.get("credentials", {})
        token = webhook_data.get("token")

        # Validar dados obrigatórios
        if not account_id:
            logger.warning("Evento de credenciais sem account_id")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Dados incompletos: account_id é obrigatório"
            )

        # Verificar token de autenticação
        if not token:
            logger.warning("Evento de credenciais sem token de autenticação")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token de autenticação não fornecido"
            )

        logger.info(f"Processando credenciais para account_id: {account_id}")

        # Extrair informações das credenciais
        domain = webhook_data.get("domain", "default")

        # Processar o arquivo de configuração
        config = {
            "account_id": account_id,
            "name": webhook_data.get("name", f"Cliente {account_id}"),
            "description": webhook_data.get("description", f"Configuração para {account_id}"),
        }

        # Adicionar integrações se fornecidas
        if "integrations" in webhook_data:
            config["integrations"] = webhook_data.get("integrations", {})
        else:
            # Criar seção de integrações padrão
            config["integrations"] = {}

            # Adicionar configuração MCP
            if "odoo_url" in webhook_data or "odoo_db" in webhook_data or "odoo_username" in webhook_data:
                config["integrations"]["mcp"] = {
                    "type": "odoo-mcp",
                    "config": {}
                }

                if webhook_data.get("odoo_url"):
                    config["integrations"]["mcp"]["config"]["url"] = webhook_data.get("odoo_url")
                if webhook_data.get("odoo_db"):
                    config["integrations"]["mcp"]["config"]["db"] = webhook_data.get("odoo_db")
                if webhook_data.get("odoo_username"):
                    config["integrations"]["mcp"]["config"]["username"] = webhook_data.get("odoo_username")
                if token:
                    config["integrations"]["mcp"]["config"]["credential_ref"] = token

            # Adicionar configuração Qdrant
            if webhook_data.get("qdrant_collection"):
                config["integrations"]["qdrant"] = {
                    "collection": webhook_data.get("qdrant_collection")
                }
            else:
                config["integrations"]["qdrant"] = {
                    "collection": f"business_rules_{account_id}"
                }

            # Adicionar configuração Redis
            if webhook_data.get("redis_prefix"):
                config["integrations"]["redis"] = {
                    "prefix": webhook_data.get("redis_prefix")
                }
            else:
                config["integrations"]["redis"] = {
                    "prefix": account_id
                }

        # Adicionar enabled_collections se fornecido
        if "enabled_collections" in webhook_data:
            config["enabled_collections"] = webhook_data.get("enabled_collections", [])

        # Processar o arquivo de credenciais
        creds_config = {
            "account_id": account_id,
            "credentials": {}
        }

        # Adicionar credenciais sensíveis
        if "odoo_password" in webhook_data and token:
            creds_config["credentials"][token] = f"ENC:{webhook_data.get('odoo_password')}"

        # Converter para YAML
        config_yaml = yaml.dump(config, default_flow_style=False)
        creds_yaml = yaml.dump(creds_config, default_flow_style=False)

        logger.debug(f"Config YAML: {config_yaml}")
        logger.debug(f"Credentials YAML: {creds_yaml}")

        # Salvar no banco de dados
        config_service = ConfigService(db)

        # Salvar configuração
        config_result = config_service.create_or_update_config(
            tenant_id=account_id,
            domain=domain,
            config_type="config",
            yaml_content=config_yaml
        )

        # Salvar credenciais
        creds_result = config_service.create_or_update_config(
            tenant_id=account_id,
            domain=domain,
            config_type="credentials",
            yaml_content=creds_yaml
        )

        logger.info(f"Configuração atualizada com sucesso para {account_id}/{domain}, versão {config_result.version}")
        logger.info(f"Credenciais atualizadas com sucesso para {account_id}/{domain}, versão {creds_result.version}")

        return {
            "success": True,
            "message": "Credenciais sincronizadas com sucesso",
            "tenant_id": account_id,
            "domain": domain,
            "config_version": config_result.version,
            "credentials_version": creds_result.version,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Erro ao processar evento de credenciais: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao processar evento de credenciais: {str(e)}"
        )

async def process_company_metadata_sync(webhook_data: Dict[str, Any], db: Session) -> Dict[str, Any]:
    """
    Processa evento de sincronização de metadados da empresa.

    Args:
        webhook_data: Dados do webhook
        db: Sessão do banco de dados

    Returns:
        Resultado do processamento
    """
    try:
        # Extrair informações do evento
        account_id = webhook_data.get("account_id")
        domain = webhook_data.get("domain", "default")

        # Validar dados obrigatórios
        if not account_id:
            logger.warning("Evento de metadados sem account_id")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Dados incompletos: account_id é obrigatório"
            )

        logger.info(f"Processando metadados da empresa para account_id: {account_id}")

        # Construir o objeto de metadados
        metadata = {
            "account_id": account_id,
            "name": webhook_data.get("name", f"Empresa {account_id}"),
            "description": webhook_data.get("description", f"Metadados para {account_id}"),
            "business_area": webhook_data.get("business_area", "default"),
            "business_area_other": webhook_data.get("business_area_other", ""),
            "company_values": webhook_data.get("company_values", ""),
            "online_presence": {
                "website": webhook_data.get("website", ""),
                "facebook_url": webhook_data.get("facebook_url", ""),
                "instagram_url": webhook_data.get("instagram_url", ""),
                "mention_website_at_end": webhook_data.get("mention_website_at_end", False),
                "mention_facebook_at_end": webhook_data.get("mention_facebook_at_end", False),
                "mention_instagram_at_end": webhook_data.get("mention_instagram_at_end", False)
            },
            "communication": {
                "greeting_message": webhook_data.get("greeting_message", ""),
                "communication_style": webhook_data.get("communication_style", "friendly"),
                "emoji_usage": webhook_data.get("emoji_usage", "moderate")
            }
        }

        # Adicionar endereço se fornecido
        if "address" in webhook_data:
            metadata["address"] = webhook_data.get("address", {})

        # Adicionar horários de funcionamento se fornecidos
        if "business_hours" in webhook_data:
            metadata["business_hours"] = webhook_data.get("business_hours", {})

        # Adicionar coleções habilitadas se fornecidas
        if "enabled_collections" in webhook_data:
            metadata["enabled_collections"] = webhook_data.get("enabled_collections", [])

        # Converter para YAML
        metadata_yaml = yaml.dump(metadata, default_flow_style=False)

        logger.debug(f"Metadata YAML: {metadata_yaml}")

        # Salvar no banco de dados
        config_service = ConfigService(db)

        # Salvar metadados
        metadata_result = config_service.create_or_update_config(
            tenant_id=account_id,
            domain=domain,
            config_type="metadata",
            yaml_content=metadata_yaml
        )

        logger.info(f"Metadados atualizados com sucesso para {account_id}/{domain}, versão {metadata_result.version}")

        return {
            "success": True,
            "message": "Metadados da empresa sincronizados com sucesso",
            "tenant_id": account_id,
            "domain": domain,
            "metadata_version": metadata_result.version,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Erro ao processar evento de metadados: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao processar evento de metadados: {str(e)}"
        )

async def process_mapping_sync(webhook_data: Dict[str, Any], db: Session) -> Dict[str, Any]:
    """
    Processa evento de sincronização de mapeamento.

    Args:
        webhook_data: Dados do webhook
        db: Sessão do banco de dados

    Returns:
        Resultado do processamento
    """
    try:
        # Extrair informações do evento
        mapping = webhook_data.get("mapping", {})

        # Validar dados obrigatórios
        if not mapping:
            logger.warning("Evento de mapeamento sem dados de mapeamento")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Dados incompletos: mapping é obrigatório"
            )

        # Extrair dados do mapeamento
        chatwoot_account_id = mapping.get("chatwoot_account_id")
        chatwoot_inbox_id = mapping.get("chatwoot_inbox_id")
        internal_account_id = mapping.get("internal_account_id")
        domain = mapping.get("domain")

        # Validar dados obrigatórios do mapeamento
        if not chatwoot_account_id or not internal_account_id or not domain:
            logger.warning("Mapeamento sem chatwoot_account_id, internal_account_id ou domain")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Dados incompletos: chatwoot_account_id, internal_account_id e domain são obrigatórios"
            )

        # Construir o objeto de mapeamento
        mapping_data = {
            "accounts": {},
            "inboxes": {},
            "fallbacks": [],
            "special_numbers": []
        }

        # Atualizar mapeamento de accounts
        mapping_data["accounts"][str(chatwoot_account_id)] = {
            "domain": domain,
            "account_id": internal_account_id
        }

        # Atualizar mapeamento de inboxes se especificado
        if chatwoot_inbox_id:
            mapping_data["inboxes"][str(chatwoot_inbox_id)] = {
                "domain": domain,
                "account_id": internal_account_id
            }

        # Atualizar fallbacks
        is_fallback = mapping.get("is_fallback", False)
        sequence = mapping.get("sequence", 10)

        if is_fallback:
            mapping_data["fallbacks"].append({
                "domain": domain,
                "account_id": internal_account_id,
                "sequence": sequence
            })

        # Atualizar números especiais de WhatsApp
        special_whatsapp_numbers = mapping.get("special_whatsapp_numbers", [])

        for number_data in special_whatsapp_numbers:
            number = number_data.get("number")
            crew = number_data.get("crew", "analytics")

            if number:
                mapping_data["special_numbers"].append({
                    "number": number,
                    "crew": crew,
                    "domain": domain,
                    "account_id": internal_account_id
                })

        # Salvar no banco de dados
        mapping_service = MappingService(db)
        result = mapping_service.create_or_update_mapping(mapping_data)

        logger.info(f"Mapeamento atualizado com sucesso, versão {result.version}")

        return {
            "success": True,
            "message": "Mapeamento sincronizado com sucesso",
            "version": result.version,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Erro ao processar evento de mapeamento: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao processar evento de mapeamento: {str(e)}"
        )
