# -*- coding: utf-8 -*-

"""
Manipulador de eventos de mapeamento de canais.
Este módulo contém funções para processar eventos de mapeamento de canais
enviados pelo módulo ai_credentials_manager.
"""

import os
import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

def process_mapping_event(webhook_data: Dict[str, Any], credential_encryption=None) -> Dict[str, Any]:
    """
    Processa um evento de sincronização de mapeamento de canal.

    Este método recebe dados de um webhook enviado pelo módulo ai_credentials_manager
    e atualiza o arquivo de mapeamento JSON com as informações recebidas.

    Args:
        webhook_data: Dados do webhook contendo informações de mapeamento
        credential_encryption: Objeto para criptografia de credenciais (opcional)

    Returns:
        Dicionário com o resultado do processamento
    """
    try:
        logger.info("Processando evento de sincronização de mapeamento de canal")

        # Extrair informações do evento
        account_id = webhook_data.get("account_id")
        token = webhook_data.get("token")
        mapping = webhook_data.get("mapping", {})

        # Validar dados obrigatórios
        if not account_id or not mapping:
            logger.warning("Evento de mapeamento sem account_id ou mapping")
            return {"success": False, "error": "Dados incompletos: account_id e mapping são obrigatórios"}

        # Verificar token de autenticação
        if not token:
            logger.warning("Evento de mapeamento sem token de autenticação")
            return {"success": False, "error": "Token de autenticação não fornecido"}

        logger.info(f"Processando mapeamento para account_id: {account_id}")

        # Verificar se o diretório config existe
        config_dir = os.path.join(os.getcwd(), "config")
        if not os.path.exists(config_dir):
            os.makedirs(config_dir, exist_ok=True)

        # Caminho para o arquivo de mapeamento JSON
        json_path = os.path.join(config_dir, "chatwoot_mapping.json")

        # Carregar mapeamento existente ou criar novo
        if os.path.exists(json_path):
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    mapping_data = json.load(f) or {}
                logger.info(f"Mapeamento carregado do JSON: {json_path}")
            except Exception as e:
                logger.warning(f"Erro ao carregar mapeamento do JSON: {str(e)}")
                # Se houver erro, criar um novo mapeamento
                mapping_data = {
                    "accounts": {},
                    "inboxes": {},
                    "fallbacks": [],
                    "special_numbers": []
                }
        else:
            # Criar um novo mapeamento
            mapping_data = {
                "accounts": {},
                "inboxes": {},
                "fallbacks": [],
                "special_numbers": []
            }

        # Garantir que todas as seções existam
        if "accounts" not in mapping_data:
            mapping_data["accounts"] = {}
        if "inboxes" not in mapping_data:
            mapping_data["inboxes"] = {}
        if "fallbacks" not in mapping_data:
            mapping_data["fallbacks"] = []
        if "special_numbers" not in mapping_data:
            mapping_data["special_numbers"] = []

        # Extrair dados do mapeamento
        chatwoot_account_id = mapping.get("chatwoot_account_id")
        chatwoot_inbox_id = mapping.get("chatwoot_inbox_id")
        internal_account_id = mapping.get("internal_account_id")
        domain = mapping.get("domain")
        is_fallback = mapping.get("is_fallback", False)
        sequence = mapping.get("sequence", 10)
        special_whatsapp_numbers = mapping.get("special_whatsapp_numbers", [])

        # Validar dados obrigatórios do mapeamento
        if not chatwoot_account_id or not internal_account_id or not domain:
            logger.warning("Mapeamento sem chatwoot_account_id, internal_account_id ou domain")
            return {"success": False, "error": "Dados incompletos: chatwoot_account_id, internal_account_id e domain são obrigatórios"}

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
        if is_fallback:
            # Remover fallback existente para este account_id (se houver)
            mapping_data["fallbacks"] = [f for f in mapping_data["fallbacks"]
                                        if f.get("account_id") != internal_account_id]

            # Adicionar novo fallback
            mapping_data["fallbacks"].append({
                "domain": domain,
                "account_id": internal_account_id,
                "sequence": sequence
            })

            # Ordenar fallbacks por sequência
            mapping_data["fallbacks"].sort(key=lambda x: x.get("sequence", 10))
        else:
            # Remover fallback para este account_id (se existir)
            mapping_data["fallbacks"] = [f for f in mapping_data["fallbacks"]
                                        if f.get("account_id") != internal_account_id]

        # Atualizar números especiais de WhatsApp
        # Primeiro, remover números existentes para este account_id
        mapping_data["special_numbers"] = [n for n in mapping_data["special_numbers"]
                                          if n.get("account_id") != internal_account_id]

        # Adicionar novos números especiais
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

        # Salvar mapeamento atualizado no microserviço de configuração e em JSON local
        try:
            # Tentar salvar no microserviço de configuração primeiro
            from src.utils.config_service_client import config_service

            # Verificar se o serviço está saudável
            logger.info(f"Verificando saúde do serviço de configuração...")
            health_check = config_service.health_check()
            logger.info(f"Resultado do health check: {health_check}")

            if health_check:
                # Atualizar o mapeamento no microserviço
                logger.info(f"Tentando atualizar mapeamento no microserviço de configuração...")
                try:
                    success = config_service.update_chatwoot_mapping(mapping_data, partial=False)
                    logger.info(f"Resultado da atualização: {success}")

                    if success:
                        logger.info(f"Mapeamento salvo com sucesso no microserviço de configuração")
                    else:
                        logger.warning(f"Erro ao salvar mapeamento no microserviço. Usando fallback para arquivo local.")
                except Exception as e:
                    logger.error(f"Exceção ao atualizar mapeamento no microserviço: {str(e)}")
                    success = False
            else:
                logger.warning(f"Microserviço de configuração não está disponível. Usando fallback para arquivo local.")

            # Salvar o arquivo JSON localmente como fallback
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(mapping_data, f, indent=2, ensure_ascii=False)

            logger.info(f"Mapeamento salvo com sucesso em JSON local: {json_path}")

            # Criar uma cópia de backup
            backup_path = f"{json_path}.bak"
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(mapping_data, f, indent=2, ensure_ascii=False)

            logger.info(f"Backup do mapeamento criado: {backup_path}")
        except Exception as e:
            logger.error(f"Erro ao salvar mapeamento: {str(e)}")
            return {
                "success": False,
                "error": f"Erro ao salvar mapeamento: {str(e)}"
            }

        logger.info(f"Mapeamento atualizado com sucesso")

        return {
            "success": True,
            "message": "Mapeamento sincronizado com sucesso",
            "account_id": account_id,
            "mapping_path": json_path
        }

    except Exception as e:
        logger.error(f"Erro ao processar evento de mapeamento: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e)
        }
