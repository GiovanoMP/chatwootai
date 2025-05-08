# -*- coding: utf-8 -*-

"""
Cliente para o serviço de configuração.

Este módulo fornece um cliente para interagir com o microserviço de configuração,
permitindo obter e atualizar configurações do sistema.
"""

import requests
import logging
import json
import os
import traceback
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

class ConfigServiceClient:
    """
    Cliente para o serviço de configuração.

    Attributes:
        base_url: URL base do serviço de configuração
        api_key: Chave de API para autenticação
        headers: Cabeçalhos HTTP para as requisições
    """

    def __init__(self):
        """Inicializa o cliente com as configurações do ambiente."""
        self.base_url = os.getenv("CONFIG_SERVICE_URL", "http://localhost:8002")
        self.api_key = os.getenv("CONFIG_SERVICE_API_KEY", "development-api-key")
        self.headers = {
            "Content-Type": "application/json",
            "X-API-Key": self.api_key
        }
        logger.info(f"Cliente do serviço de configuração inicializado: {self.base_url}")

    def get_chatwoot_mapping(self) -> Dict[str, Any]:
        """
        Obtém o mapeamento Chatwoot do serviço de configuração.

        Returns:
            Dados do mapeamento ou um mapeamento vazio em caso de erro
        """
        try:
            response = requests.get(
                f"{self.base_url}/mapping/",
                headers=self.headers,
                timeout=5
            )

            if response.status_code == 200:
                mapping_data = response.json()
                logger.info(f"✅ Mapeamento Chatwoot carregado do serviço de configuração")
                return mapping_data
            else:
                logger.warning(f"⚠️ Erro ao carregar mapeamento: {response.status_code} - {response.text}")
                return self._get_default_mapping()
        except Exception as e:
            logger.error(f"⚠️ Erro ao conectar ao serviço de configuração: {str(e)}")
            return self._get_default_mapping()

    def update_chatwoot_mapping(self, mapping_data: Dict[str, Any], partial: bool = True) -> bool:
        """
        Atualiza o mapeamento Chatwoot no serviço de configuração.

        Args:
            mapping_data: Dados do mapeamento
            partial: Se True, faz uma atualização parcial (PATCH); se False, substitui o mapeamento (POST)

        Returns:
            True se a atualização foi bem-sucedida, False caso contrário
        """
        try:
            url = f"{self.base_url}/mapping/"
            method = requests.patch if partial else requests.post

            logger.info(f"Enviando requisição para {url} usando método {'PATCH' if partial else 'POST'}")
            logger.info(f"Dados do mapeamento: {json.dumps(mapping_data, indent=2, ensure_ascii=False)}")

            response = method(
                url,
                json={"mapping_data": mapping_data},
                headers=self.headers,
                timeout=10  # Aumentando o timeout para 10 segundos
            )

            logger.info(f"Resposta do serviço de configuração: Status {response.status_code}")

            if response.status_code in (200, 201):
                logger.info(f"✅ Mapeamento Chatwoot atualizado com sucesso")
                logger.info(f"Resposta: {response.text}")
                return True
            else:
                logger.warning(f"⚠️ Erro ao atualizar mapeamento: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"⚠️ Erro ao conectar ao serviço de configuração: {str(e)}")
            logger.error(f"Detalhes do erro: {traceback.format_exc()}")
            return False

    def _get_default_mapping(self) -> Dict[str, Any]:
        """
        Retorna um mapeamento padrão vazio.

        Returns:
            Mapeamento padrão vazio
        """
        return {
            "accounts": {},
            "inboxes": {},
            "fallbacks": [],
            "special_numbers": []
        }

    def get_config(self, tenant_id: str, domain: str, config_type: str) -> Optional[Dict[str, Any]]:
        """
        Obtém a configuração do serviço de configuração.

        Args:
            tenant_id: ID do tenant
            domain: Domínio do tenant (retail, healthcare, etc.)
            config_type: Tipo de configuração (config, credentials, crew_whatsapp, etc.)

        Returns:
            Dados da configuração ou None em caso de erro
        """
        try:
            response = requests.get(
                f"{self.base_url}/configs/{tenant_id}/{domain}/{config_type}",
                headers=self.headers,
                timeout=5
            )

            if response.status_code == 200:
                config_data = response.json()
                logger.info(f"✅ Configuração {config_type} carregada para {tenant_id}/{domain}")
                return config_data
            else:
                logger.warning(f"⚠️ Erro ao carregar configuração: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"⚠️ Erro ao conectar ao serviço de configuração: {str(e)}")
            return None

    def get_config_yaml(self, tenant_id: str, domain: str, config_type: str) -> Optional[str]:
        """
        Obtém a configuração como YAML do serviço de configuração.

        Args:
            tenant_id: ID do tenant
            domain: Domínio do tenant (retail, healthcare, etc.)
            config_type: Tipo de configuração (config, credentials, crew_whatsapp, etc.)

        Returns:
            Conteúdo YAML da configuração ou None em caso de erro
        """
        try:
            response = requests.get(
                f"{self.base_url}/configs/{tenant_id}/{domain}/{config_type}/yaml",
                headers=self.headers,
                timeout=5
            )

            if response.status_code == 200:
                yaml_content = response.text
                logger.info(f"✅ Configuração YAML {config_type} carregada para {tenant_id}/{domain}")
                return yaml_content
            else:
                logger.warning(f"⚠️ Erro ao carregar configuração YAML: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"⚠️ Erro ao conectar ao serviço de configuração: {str(e)}")
            return None

    def update_config(self, tenant_id: str, domain: str, config_type: str, yaml_content: str) -> bool:
        """
        Atualiza a configuração no serviço de configuração.

        Args:
            tenant_id: ID do tenant
            domain: Domínio do tenant (retail, healthcare, etc.)
            config_type: Tipo de configuração (config, credentials, crew_whatsapp, etc.)
            yaml_content: Conteúdo YAML da configuração

        Returns:
            True se a atualização foi bem-sucedida, False caso contrário
        """
        try:
            response = requests.post(
                f"{self.base_url}/configs/{tenant_id}/{domain}/{config_type}",
                json={"yaml_content": yaml_content},
                headers=self.headers,
                timeout=5
            )

            if response.status_code in (200, 201):
                logger.info(f"✅ Configuração {config_type} atualizada com sucesso para {tenant_id}/{domain}")
                return True
            else:
                logger.warning(f"⚠️ Erro ao atualizar configuração: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"⚠️ Erro ao conectar ao serviço de configuração: {str(e)}")
            return False

    def list_configs(self, tenant_id: str, domain: str = None) -> Optional[List[Dict[str, Any]]]:
        """
        Lista as configurações disponíveis para um tenant.

        Args:
            tenant_id: ID do tenant
            domain: Domínio do tenant (opcional)

        Returns:
            Lista de configurações ou None em caso de erro
        """
        try:
            url = f"{self.base_url}/configs/{tenant_id}"
            if domain:
                url += f"?domain={domain}"

            response = requests.get(
                url,
                headers=self.headers,
                timeout=5
            )

            if response.status_code == 200:
                configs = response.json()
                logger.info(f"✅ Lista de configurações carregada para {tenant_id}")
                return configs
            else:
                logger.warning(f"⚠️ Erro ao carregar lista de configurações: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"⚠️ Erro ao conectar ao serviço de configuração: {str(e)}")
            return None

    def health_check(self) -> bool:
        """
        Verifica a saúde do serviço de configuração.

        Returns:
            True se o serviço está saudável, False caso contrário
        """
        try:
            response = requests.get(
                f"{self.base_url}/health",
                headers=self.headers,
                timeout=2
            )

            return response.status_code == 200
        except Exception:
            return False

# Instância global para uso em todo o sistema
config_service = ConfigServiceClient()
