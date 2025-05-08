# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import requests
import logging
import yaml
import json
import os

_logger = logging.getLogger(__name__)

class ConfigServiceClient:
    """Cliente para o microserviço de configuração."""

    def __init__(self, env):
        """
        Inicializa o cliente.

        Args:
            env: Ambiente Odoo
        """
        self.env = env
        self._load_config()

    def _load_config(self):
        """Carrega as configurações do microserviço."""
        config_param = self.env['ir.config_parameter'].sudo()
        self.enabled = config_param.get_param('config_service_enabled', 'True') == 'True'

        # Tentar obter a URL do serviço de configuração
        self.url = config_param.get_param('config_service.url', '')

        # Se não encontrar, tentar o parâmetro antigo
        if not self.url:
            self.url = config_param.get_param('config_service_url', 'http://localhost:8002')

        # Tentar obter a chave de API do serviço de configuração
        self.api_key = config_param.get_param('config_service.api_key', '')

        # Se não encontrar, tentar o parâmetro antigo
        if not self.api_key:
            self.api_key = config_param.get_param('config_service_api_key', 'development-api-key')

        _logger.info(f"Configuração do serviço de configuração: URL={self.url}, API Key={self.api_key[:5]}...")

    def health_check(self):
        """
        Verifica se o microserviço está disponível.

        Returns:
            True se o microserviço está disponível, False caso contrário
        """
        if not self.enabled:
            _logger.info("Microserviço de configuração desativado")
            return False

        try:
            response = requests.get(
                f"{self.url}/health",
                headers={"X-API-Key": self.api_key},
                timeout=2
            )
            return response.status_code == 200
        except Exception as e:
            _logger.error(f"Erro ao verificar saúde do microserviço: {str(e)}")
            return False

    def sync_config(self, tenant_id, domain, config_type, yaml_content):
        """
        Sincroniza uma configuração com o microserviço.

        Args:
            tenant_id: ID do tenant
            domain: Domínio do tenant
            config_type: Tipo de configuração
            yaml_content: Conteúdo YAML da configuração

        Returns:
            True se a sincronização foi bem-sucedida, False caso contrário
        """
        if not self.enabled:
            _logger.info(f"Microserviço desativado. Usando método legado para sincronizar configuração para tenant_id={tenant_id}, domain={domain}, config_type={config_type}")
            return self._sync_config_legacy(tenant_id, domain, config_type, yaml_content)

        try:
            url = f"{self.url}/configs/{tenant_id}/{domain}/{config_type}"
            headers = {
                "Content-Type": "application/json",
                "X-API-Key": self.api_key
            }

            response = requests.post(
                url,
                json={"yaml_content": yaml_content},
                headers=headers,
                timeout=5
            )

            if response.status_code in (200, 201):
                _logger.info(f"Configuração sincronizada com sucesso: {tenant_id}/{domain}/{config_type}")
                return True
            else:
                _logger.error(f"Erro ao sincronizar configuração: {response.status_code} - {response.text}")
                # Fallback para o método legado
                return self._sync_config_legacy(tenant_id, domain, config_type, yaml_content)
        except Exception as e:
            _logger.error(f"Erro ao sincronizar configuração: {str(e)}")
            # Fallback para o método legado
            return self._sync_config_legacy(tenant_id, domain, config_type, yaml_content)

    def get_config(self, tenant_id, domain, config_type):
        """
        Obtém uma configuração do microserviço.

        Args:
            tenant_id: ID do tenant
            domain: Domínio do tenant
            config_type: Tipo de configuração

        Returns:
            Dicionário com a configuração ou None se não encontrada
        """
        if not self.enabled:
            _logger.info(f"Microserviço desativado. Usando método legado para obter configuração para tenant_id={tenant_id}, domain={domain}, config_type={config_type}")
            return self._get_config_legacy(tenant_id, domain, config_type)

        try:
            url = f"{self.url}/configs/{tenant_id}/{domain}/{config_type}"
            headers = {"X-API-Key": self.api_key}

            response = requests.get(
                url,
                headers=headers,
                timeout=5
            )

            if response.status_code == 200:
                _logger.info(f"Configuração obtida com sucesso: {tenant_id}/{domain}/{config_type}")
                return response.json()
            else:
                _logger.error(f"Erro ao obter configuração: {response.status_code} - {response.text}")
                # Fallback para o método legado
                return self._get_config_legacy(tenant_id, domain, config_type)
        except Exception as e:
            _logger.error(f"Erro ao obter configuração: {str(e)}")
            # Fallback para o método legado
            return self._get_config_legacy(tenant_id, domain, config_type)

    def _sync_config_legacy(self, tenant_id, domain, config_type, yaml_content):
        """
        Método legado para sincronizar a configuração.

        Args:
            tenant_id: ID do tenant
            domain: Domínio do tenant
            config_type: Tipo de configuração
            yaml_content: Conteúdo YAML da configuração

        Returns:
            True se a sincronização foi bem-sucedida, False caso contrário
        """
        try:
            # Determinar o caminho do arquivo YAML
            config_dir = os.path.join("config", "domains", domain, tenant_id)

            # Criar diretório se não existir
            os.makedirs(config_dir, exist_ok=True)

            # Caminho para o arquivo de configuração
            config_file = os.path.join(config_dir, f"{config_type}.yaml")

            # Salvar configuração
            with open(config_file, 'w') as f:
                f.write(yaml_content)

            _logger.info(f"Configuração salva com sucesso em {config_file}")
            return True
        except Exception as e:
            _logger.error(f"Erro ao sincronizar configuração: {str(e)}")
            return False

    def _get_config_legacy(self, tenant_id, domain, config_type):
        """
        Método legado para obter a configuração.

        Args:
            tenant_id: ID do tenant
            domain: Domínio do tenant
            config_type: Tipo de configuração

        Returns:
            Dicionário com a configuração ou None se não encontrada
        """
        try:
            # Determinar o caminho do arquivo YAML
            config_file = os.path.join("config", "domains", domain, tenant_id, f"{config_type}.yaml")

            # Verificar se o arquivo existe
            if not os.path.exists(config_file):
                _logger.warning(f"Arquivo de configuração não encontrado: {config_file}")
                return None

            # Carregar configuração
            with open(config_file, 'r') as f:
                yaml_content = f.read()
                config_data = yaml.safe_load(yaml_content) or {}

            # Retornar configuração no mesmo formato que o microserviço
            return {
                "id": 1,  # ID fictício
                "tenant_id": tenant_id,
                "domain": domain,
                "config_type": config_type,
                "yaml_content": yaml_content,
                "json_data": config_data,
                "version": 1,  # Versão fictícia
                "created_at": "2023-01-01T00:00:00",  # Data fictícia
                "updated_at": "2023-01-01T00:00:00"   # Data fictícia
            }
        except Exception as e:
            _logger.error(f"Erro ao obter configuração: {str(e)}")
            return None
