# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
import yaml
import json
import os

_logger = logging.getLogger(__name__)

class ConfigServiceAdapter:
    """Adaptador para o serviço de configuração."""

    def __init__(self, env):
        """
        Inicializa o adaptador.

        Args:
            env: Ambiente Odoo
        """
        self.env = env
        self._load_config()

    def _load_config(self):
        """Carrega as configurações do adaptador."""
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

        _logger.info(f"Configuração do adaptador do serviço de configuração: URL={self.url}, API Key={self.api_key[:5]}...")

    def sync_business_rules(self, tenant_id, domain, rules_data):
        """
        Sincroniza as regras de negócio com o serviço de configuração.

        Args:
            tenant_id: ID do tenant
            domain: Domínio do tenant
            rules_data: Dados das regras de negócio

        Returns:
            True se a sincronização foi bem-sucedida, False caso contrário
        """
        try:
            # Converter para YAML
            yaml_content = yaml.dump(rules_data, default_flow_style=False)

            # Verificar se o módulo ai_credentials_manager está instalado
            ai_module = self.env['ir.module.module'].sudo().search([('name', '=', 'ai_credentials_manager'), ('state', '=', 'installed')])
            if not ai_module:
                _logger.warning("Módulo ai_credentials_manager não está instalado")
                return self._sync_business_rules_legacy(tenant_id, domain, yaml_content)

            # Tentar usar o cliente do módulo ai_credentials_manager
            try:
                config_service = self.env['ai.config.service'].sudo()
                success = config_service.sync_config(tenant_id, domain, "config", yaml_content)

                if success:
                    _logger.info(f"Regras de negócio sincronizadas com sucesso para tenant_id={tenant_id}, domain={domain}")
                    return True
                else:
                    _logger.error("Erro ao sincronizar regras de negócio com o serviço de configuração")
                    # Tentar usar o endpoint direto do config-service
                    return self._sync_business_rules_direct(tenant_id, domain, yaml_content)
            except Exception as e:
                _logger.error(f"Erro ao usar cliente do módulo ai_credentials_manager: {str(e)}")
                # Tentar usar o endpoint direto do config-service
                return self._sync_business_rules_direct(tenant_id, domain, yaml_content)
        except Exception as e:
            _logger.error(f"Erro ao sincronizar regras de negócio: {str(e)}")
            return False

    def _sync_business_rules_direct(self, tenant_id, domain, yaml_content):
        """
        Sincroniza as regras de negócio diretamente com o serviço de configuração.

        Args:
            tenant_id: ID do tenant
            domain: Domínio do tenant
            yaml_content: Conteúdo YAML das regras de negócio

        Returns:
            True se a sincronização foi bem-sucedida, False caso contrário
        """
        try:
            import requests

            # Construir a URL para o endpoint do config-service
            config_type = "config"  # Tipo de configuração para regras de negócio
            url = f"{self.url}/configs/{tenant_id}/{domain}/{config_type}"

            # Preparar os headers com a chave de API
            headers = {
                "Content-Type": "application/json",
                "X-API-Key": self.api_key
            }

            # Preparar o payload
            payload = {
                "yaml_content": yaml_content
            }

            _logger.info(f"Enviando regras de negócio para o config-service: URL={url}")

            # Fazer a requisição POST
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=10
            )

            # Verificar o status da resposta
            if response.status_code in (200, 201):
                _logger.info(f"Regras de negócio sincronizadas com sucesso: {tenant_id}/{domain}/{config_type}")
                return True
            else:
                _logger.error(f"Erro ao sincronizar regras de negócio: {response.status_code} - {response.text}")
                # Fallback para o método legado
                return self._sync_business_rules_legacy(tenant_id, domain, yaml_content)
        except Exception as e:
            _logger.error(f"Erro ao sincronizar regras de negócio diretamente: {str(e)}")
            # Fallback para o método legado
            return self._sync_business_rules_legacy(tenant_id, domain, yaml_content)

    def _sync_business_rules_legacy(self, tenant_id, domain, yaml_content):
        """
        Método legado para sincronizar as regras de negócio.

        Args:
            tenant_id: ID do tenant
            domain: Domínio do tenant
            yaml_content: Conteúdo YAML das regras de negócio

        Returns:
            True se a sincronização foi bem-sucedida, False caso contrário
        """
        try:
            # Determinar o caminho do arquivo YAML
            config_dir = os.path.join("config", "domains", domain, tenant_id)

            # Criar diretório se não existir
            os.makedirs(config_dir, exist_ok=True)

            # Caminho para o arquivo de configuração
            config_file = os.path.join(config_dir, "config.yaml")

            # Salvar configuração
            with open(config_file, 'w') as f:
                f.write(yaml_content)

            _logger.info(f"Regras de negócio salvas com sucesso em {config_file}")
            return True
        except Exception as e:
            _logger.error(f"Erro ao sincronizar regras de negócio: {str(e)}")
            return False

    def get_business_rules(self, tenant_id, domain):
        """
        Obtém as regras de negócio do serviço de configuração.

        Args:
            tenant_id: ID do tenant
            domain: Domínio do tenant

        Returns:
            Dicionário com as regras de negócio ou None se não encontradas
        """
        try:
            # Verificar se o módulo ai_credentials_manager está instalado
            ai_module = self.env['ir.module.module'].sudo().search([('name', '=', 'ai_credentials_manager'), ('state', '=', 'installed')])
            if not ai_module:
                _logger.warning("Módulo ai_credentials_manager não está instalado")
                return self._get_business_rules_legacy(tenant_id, domain)

            # Tentar usar o cliente do módulo ai_credentials_manager
            try:
                config_service = self.env['ai.config.service'].sudo()
                config_data = config_service.get_config(tenant_id, domain, "config")

                if config_data:
                    _logger.info(f"Regras de negócio obtidas com sucesso para tenant_id={tenant_id}, domain={domain}")
                    return config_data.get("json_data", {})
                else:
                    _logger.error("Erro ao obter regras de negócio do serviço de configuração")
                    # Tentar usar o endpoint direto do config-service
                    return self._get_business_rules_direct(tenant_id, domain)
            except Exception as e:
                _logger.error(f"Erro ao usar cliente do módulo ai_credentials_manager: {str(e)}")
                # Tentar usar o endpoint direto do config-service
                return self._get_business_rules_direct(tenant_id, domain)
        except Exception as e:
            _logger.error(f"Erro ao obter regras de negócio: {str(e)}")
            return None

    def _get_business_rules_direct(self, tenant_id, domain):
        """
        Obtém as regras de negócio diretamente do serviço de configuração.

        Args:
            tenant_id: ID do tenant
            domain: Domínio do tenant

        Returns:
            Dicionário com as regras de negócio ou None se não encontradas
        """
        try:
            import requests

            # Construir a URL para o endpoint do config-service
            config_type = "config"  # Tipo de configuração para regras de negócio
            url = f"{self.url}/configs/{tenant_id}/{domain}/{config_type}"

            # Preparar os headers com a chave de API
            headers = {
                "X-API-Key": self.api_key
            }

            _logger.info(f"Obtendo regras de negócio do config-service: URL={url}")

            # Fazer a requisição GET
            response = requests.get(
                url,
                headers=headers,
                timeout=10
            )

            # Verificar o status da resposta
            if response.status_code == 200:
                _logger.info(f"Regras de negócio obtidas com sucesso: {tenant_id}/{domain}/{config_type}")
                config_data = response.json()
                return config_data.get("json_data", {})
            else:
                _logger.error(f"Erro ao obter regras de negócio: {response.status_code} - {response.text}")
                # Fallback para o método legado
                return self._get_business_rules_legacy(tenant_id, domain)
        except Exception as e:
            _logger.error(f"Erro ao obter regras de negócio diretamente: {str(e)}")
            # Fallback para o método legado
            return self._get_business_rules_legacy(tenant_id, domain)

    def _get_business_rules_legacy(self, tenant_id, domain):
        """
        Método legado para obter as regras de negócio.

        Args:
            tenant_id: ID do tenant
            domain: Domínio do tenant

        Returns:
            Dicionário com as regras de negócio ou None se não encontradas
        """
        try:
            # Determinar o caminho do arquivo YAML
            config_file = os.path.join("config", "domains", domain, tenant_id, "config.yaml")

            # Verificar se o arquivo existe
            if not os.path.exists(config_file):
                _logger.warning(f"Arquivo de configuração não encontrado: {config_file}")
                return None

            # Carregar configuração
            with open(config_file, 'r') as f:
                config_data = yaml.safe_load(f) or {}

            return config_data
        except Exception as e:
            _logger.error(f"Erro ao obter regras de negócio: {str(e)}")
            return None
