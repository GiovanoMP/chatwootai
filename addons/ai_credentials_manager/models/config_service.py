# -*- coding: utf-8 -*-

"""
Integração com o serviço de configuração.

Este módulo fornece a integração com o microserviço de configuração,
permitindo sincronizar o mapeamento Chatwoot e gerenciar configurações YAML.
"""

import requests
import logging
import json
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class ConfigServiceIntegration(models.AbstractModel):
    """
    Modelo abstrato para integração com o serviço de configuração.

    Este modelo fornece métodos para interagir com o microserviço de configuração,
    permitindo sincronizar o mapeamento Chatwoot e gerenciar configurações YAML.
    """
    _name = 'ai.config.service'
    _description = 'Integração com o Serviço de Configuração'

    def _get_config_service_url(self):
        """
        Obtém a URL do serviço de configuração.

        Returns:
            URL do serviço de configuração
        """
        return self.env['ir.config_parameter'].sudo().get_param(
            'ai_credentials_manager.config_service_url',
            'http://localhost:8000'
        )

    def _get_config_service_api_key(self):
        """
        Obtém a chave de API do serviço de configuração.

        Returns:
            Chave de API do serviço de configuração
        """
        return self.env['ir.config_parameter'].sudo().get_param(
            'ai_credentials_manager.config_service_api_key',
            'development-api-key'
        )

    def sync_chatwoot_mapping(self, account_id, domain, chatwoot_account_id, chatwoot_inbox_id):
        """
        Sincroniza o mapeamento Chatwoot com o serviço de configuração.

        Args:
            account_id: ID da conta no sistema
            domain: Domínio da conta
            chatwoot_account_id: ID da conta no Chatwoot
            chatwoot_inbox_id: ID da caixa de entrada no Chatwoot

        Returns:
            True se a sincronização foi bem-sucedida, False caso contrário
        """
        try:
            # Preparar dados de mapeamento
            mapping_data = {
                "accounts": {
                    str(chatwoot_account_id): {
                        "account_id": account_id,
                        "domain": domain
                    }
                },
                "inboxes": {
                    str(chatwoot_inbox_id): {
                        "account_id": account_id,
                        "domain": domain
                    }
                }
            }

            # Enviar para o serviço de configuração
            url = f"{self._get_config_service_url()}/mapping/"
            headers = {
                "Content-Type": "application/json",
                "X-API-Key": self._get_config_service_api_key()
            }

            # Verificar a saúde do serviço
            try:
                health_response = requests.get(
                    f"{self._get_config_service_url()}/health",
                    headers=headers,
                    timeout=2
                )

                if health_response.status_code != 200:
                    _logger.warning(f"Serviço de configuração não está saudável: {health_response.status_code}")
                    # Fallback para o método legado
                    return self._sync_chatwoot_mapping_legacy(account_id, domain, chatwoot_account_id, chatwoot_inbox_id)
            except Exception as e:
                _logger.warning(f"Erro ao verificar saúde do serviço de configuração: {str(e)}")
                # Fallback para o método legado
                return self._sync_chatwoot_mapping_legacy(account_id, domain, chatwoot_account_id, chatwoot_inbox_id)

            # Enviar mapeamento para o serviço
            response = requests.patch(
                url,
                json={"mapping_data": mapping_data},
                headers=headers,
                timeout=5
            )

            if response.status_code not in (200, 201):
                _logger.error(f"Erro ao sincronizar mapeamento: {response.text}")
                # Fallback para o método legado
                return self._sync_chatwoot_mapping_legacy(account_id, domain, chatwoot_account_id, chatwoot_inbox_id)

            _logger.info(f"Mapeamento sincronizado com sucesso para account_id: {account_id}")
            return True

        except Exception as e:
            _logger.error(f"Erro ao sincronizar mapeamento: {str(e)}")
            # Fallback para o método legado
            return self._sync_chatwoot_mapping_legacy(account_id, domain, chatwoot_account_id, chatwoot_inbox_id)

    def sync_config(self, tenant_id, domain, config_type, yaml_content):
        """
        Sincroniza a configuração com o serviço de configuração.

        Args:
            tenant_id: ID do tenant
            domain: Domínio do tenant
            config_type: Tipo de configuração
            yaml_content: Conteúdo YAML da configuração

        Returns:
            True se a sincronização foi bem-sucedida, False caso contrário
        """
        try:
            # Enviar para o serviço de configuração
            url = f"{self._get_config_service_url()}/configs/{tenant_id}/{domain}/{config_type}"
            headers = {
                "Content-Type": "application/json",
                "X-API-Key": self._get_config_service_api_key()
            }

            # Verificar a saúde do serviço
            try:
                health_response = requests.get(
                    f"{self._get_config_service_url()}/health",
                    headers=headers,
                    timeout=2
                )

                if health_response.status_code != 200:
                    _logger.warning(f"Serviço de configuração não está saudável: {health_response.status_code}")
                    # Fallback para o método legado
                    return self._sync_config_legacy(tenant_id, domain, config_type, yaml_content)
            except Exception as e:
                _logger.warning(f"Erro ao verificar saúde do serviço de configuração: {str(e)}")
                # Fallback para o método legado
                return self._sync_config_legacy(tenant_id, domain, config_type, yaml_content)

            # Enviar configuração para o serviço
            response = requests.post(
                url,
                json={"yaml_content": yaml_content},
                headers=headers,
                timeout=5
            )

            if response.status_code not in (200, 201):
                _logger.error(f"Erro ao sincronizar configuração: {response.text}")
                # Fallback para o método legado
                return self._sync_config_legacy(tenant_id, domain, config_type, yaml_content)

            _logger.info(f"Configuração sincronizada com sucesso para tenant_id={tenant_id}, domain={domain}, config_type={config_type}")
            return True

        except Exception as e:
            _logger.error(f"Erro ao sincronizar configuração: {str(e)}")
            # Fallback para o método legado
            return self._sync_config_legacy(tenant_id, domain, config_type, yaml_content)

    def get_config(self, tenant_id, domain, config_type):
        """
        Obtém a configuração do serviço de configuração.

        Args:
            tenant_id: ID do tenant
            domain: Domínio do tenant
            config_type: Tipo de configuração

        Returns:
            Dados da configuração ou None em caso de erro
        """
        try:
            # Obter do serviço de configuração
            url = f"{self._get_config_service_url()}/configs/{tenant_id}/{domain}/{config_type}"
            headers = {
                "Content-Type": "application/json",
                "X-API-Key": self._get_config_service_api_key()
            }

            # Verificar a saúde do serviço
            try:
                health_response = requests.get(
                    f"{self._get_config_service_url()}/health",
                    headers=headers,
                    timeout=2
                )

                if health_response.status_code != 200:
                    _logger.warning(f"Serviço de configuração não está saudável: {health_response.status_code}")
                    # Fallback para o método legado
                    return self._get_config_legacy(tenant_id, domain, config_type)
            except Exception as e:
                _logger.warning(f"Erro ao verificar saúde do serviço de configuração: {str(e)}")
                # Fallback para o método legado
                return self._get_config_legacy(tenant_id, domain, config_type)

            # Obter configuração do serviço
            response = requests.get(
                url,
                headers=headers,
                timeout=5
            )

            if response.status_code != 200:
                _logger.error(f"Erro ao obter configuração: {response.text}")
                # Fallback para o método legado
                return self._get_config_legacy(tenant_id, domain, config_type)

            config_data = response.json()
            _logger.info(f"Configuração obtida com sucesso para tenant_id={tenant_id}, domain={domain}, config_type={config_type}")
            return config_data

        except Exception as e:
            _logger.error(f"Erro ao obter configuração: {str(e)}")
            # Fallback para o método legado
            return self._get_config_legacy(tenant_id, domain, config_type)

    def _sync_chatwoot_mapping_legacy(self, account_id, domain, chatwoot_account_id, chatwoot_inbox_id):
        """
        Método legado para sincronizar o mapeamento Chatwoot.

        Este método é usado como fallback quando o serviço de configuração não está disponível.

        Args:
            account_id: ID da conta no sistema
            domain: Domínio da conta
            chatwoot_account_id: ID da conta no Chatwoot
            chatwoot_inbox_id: ID da caixa de entrada no Chatwoot

        Returns:
            True se a sincronização foi bem-sucedida, False caso contrário
        """
        _logger.info(f"Usando método legado para sincronizar mapeamento para account_id: {account_id}")

        try:
            import yaml
            import os
            from pathlib import Path

            # Carregar o mapeamento existente ou criar um novo
            mapping_file = os.path.join("config", "chatwoot_mapping.yaml")
            mapping_data = {}

            # Criar diretório se não existir
            os.makedirs(os.path.dirname(mapping_file), exist_ok=True)

            # Carregar mapeamento existente se o arquivo existir
            if os.path.exists(mapping_file):
                try:
                    with open(mapping_file, 'r') as f:
                        mapping_data = yaml.safe_load(f) or {}
                except Exception as e:
                    _logger.error(f"Erro ao carregar mapeamento existente: {str(e)}")
                    mapping_data = {}

            # Inicializar seções se não existirem
            if 'accounts' not in mapping_data:
                mapping_data['accounts'] = {}
            if 'inboxes' not in mapping_data:
                mapping_data['inboxes'] = {}
            if 'fallbacks' not in mapping_data:
                mapping_data['fallbacks'] = []
            if 'special_numbers' not in mapping_data:
                mapping_data['special_numbers'] = []

            # Atualizar mapeamento de conta
            mapping_data['accounts'][str(chatwoot_account_id)] = {
                'account_id': account_id,
                'domain': domain
            }

            # Atualizar mapeamento de caixa de entrada se fornecido
            if chatwoot_inbox_id:
                mapping_data['inboxes'][str(chatwoot_inbox_id)] = {
                    'account_id': account_id,
                    'domain': domain
                }

            # Salvar mapeamento atualizado
            with open(mapping_file, 'w') as f:
                yaml.dump(mapping_data, f, default_flow_style=False)

            _logger.info(f"Mapeamento Chatwoot atualizado com sucesso para account_id: {account_id}")
            return True
        except Exception as e:
            _logger.error(f"Erro ao sincronizar mapeamento Chatwoot: {str(e)}")
            return False

    def _sync_config_legacy(self, tenant_id, domain, config_type, yaml_content):
        """
        Método legado para sincronizar a configuração.

        Este método é usado como fallback quando o serviço de configuração não está disponível.

        Args:
            tenant_id: ID do tenant
            domain: Domínio do tenant
            config_type: Tipo de configuração
            yaml_content: Conteúdo YAML da configuração

        Returns:
            True se a sincronização foi bem-sucedida, False caso contrário
        """
        _logger.info(f"Usando método legado para sincronizar configuração para tenant_id={tenant_id}, domain={domain}, config_type={config_type}")

        try:
            import yaml
            import os

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

        Este método é usado como fallback quando o serviço de configuração não está disponível.

        Args:
            tenant_id: ID do tenant
            domain: Domínio do tenant
            config_type: Tipo de configuração

        Returns:
            Dados da configuração ou None em caso de erro
        """
        _logger.info(f"Usando método legado para obter configuração para tenant_id={tenant_id}, domain={domain}, config_type={config_type}")

        try:
            import yaml
            import os

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

            # Retornar configuração no mesmo formato que o serviço de configuração
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

    def get_mapping(self):
        """
        Obtém o mapeamento Chatwoot do serviço de configuração.

        Returns:
            Dicionário com o mapeamento ou None em caso de erro
        """
        try:
            # Obter do serviço de configuração
            url = f"{self._get_config_service_url()}/mapping/"
            headers = {
                "Content-Type": "application/json",
                "X-API-Key": self._get_config_service_api_key()
            }

            # Verificar a saúde do serviço
            try:
                health_response = requests.get(
                    f"{self._get_config_service_url()}/health",
                    headers=headers,
                    timeout=2
                )

                if health_response.status_code != 200:
                    _logger.warning(f"Serviço de configuração não está saudável: {health_response.status_code}")
                    # Fallback para o método legado
                    return self._get_mapping_legacy()
            except Exception as e:
                _logger.warning(f"Erro ao verificar saúde do serviço de configuração: {str(e)}")
                # Fallback para o método legado
                return self._get_mapping_legacy()

            # Obter mapeamento do serviço
            response = requests.get(
                url,
                headers=headers,
                timeout=5
            )

            if response.status_code != 200:
                _logger.error(f"Erro ao obter mapeamento: {response.text}")
                # Fallback para o método legado
                return self._get_mapping_legacy()

            mapping_data = response.json()
            _logger.info("Mapeamento obtido com sucesso do serviço de configuração")
            return mapping_data

        except Exception as e:
            _logger.error(f"Erro ao obter mapeamento: {str(e)}")
            # Fallback para o método legado
            return self._get_mapping_legacy()

    def _get_mapping_legacy(self):
        """
        Método legado para obter o mapeamento Chatwoot.

        Returns:
            Dicionário com o mapeamento ou None em caso de erro
        """
        _logger.info("Usando método legado para obter mapeamento Chatwoot")

        try:
            import yaml
            import os

            # Caminho para o arquivo de mapeamento
            mapping_file = os.path.join("config", "chatwoot_mapping.yaml")

            # Verificar se o arquivo existe
            if not os.path.exists(mapping_file):
                _logger.warning(f"Arquivo de mapeamento não encontrado: {mapping_file}")
                return None

            # Carregar mapeamento
            with open(mapping_file, 'r') as f:
                mapping_data = yaml.safe_load(f) or {}

            return mapping_data
        except Exception as e:
            _logger.error(f"Erro ao obter mapeamento: {str(e)}")
            return None
