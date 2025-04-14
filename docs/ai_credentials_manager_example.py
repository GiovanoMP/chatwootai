# -*- coding: utf-8 -*-

"""
Exemplo de como o módulo ai_credentials_manager deve enviar credenciais para o webhook.
"""

import json
import requests
import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)

class AICredentialsManager(models.Model):
    """
    Modelo para gerenciamento de credenciais de IA.
    """
    _name = 'ai.credentials.manager'
    _description = 'Gerenciador de Credenciais para IA'

    name = fields.Char(string='Nome', required=True)
    domain = fields.Char(string='Domínio', required=True, default='cosmetics')
    odoo_url = fields.Char(string='URL do Odoo', required=True)
    odoo_db = fields.Char(string='Banco de Dados Odoo', required=True)
    odoo_username = fields.Char(string='Usuário Odoo', required=True)
    token = fields.Char(string='Token de Referência', required=True)

    # Campos opcionais
    qdrant_collection = fields.Char(string='Coleção Qdrant')
    redis_prefix = fields.Char(string='Prefixo Redis')

    # Credenciais de redes sociais
    facebook_app_id = fields.Char(string='ID do Aplicativo Facebook')
    facebook_app_secret = fields.Char(string='Segredo do Aplicativo Facebook')
    facebook_access_token = fields.Char(string='Token de Acesso do Facebook')

    instagram_client_id = fields.Char(string='ID do Cliente Instagram')
    instagram_client_secret = fields.Char(string='Segredo do Cliente Instagram')
    instagram_access_token = fields.Char(string='Token de Acesso do Instagram')

    mercado_livre_app_id = fields.Char(string='ID do Aplicativo Mercado Livre')
    mercado_livre_client_secret = fields.Char(string='Segredo do Cliente Mercado Livre')
    mercado_livre_access_token = fields.Char(string='Token de Acesso do Mercado Livre')

    # Campos de status
    sync_status = fields.Selection([
        ('not_synced', 'Não Sincronizado'),
        ('syncing', 'Sincronizando'),
        ('synced', 'Sincronizado'),
        ('error', 'Erro')
    ], string='Status de Sincronização', default='not_synced')

    last_sync = fields.Datetime(string='Última Sincronização')
    error_message = fields.Text(string='Mensagem de Erro')

    @api.model
    def get_account_id(self):
        """
        Obtém o ID da conta a partir do nome do banco de dados.
        """
        db_name = self.env.cr.dbname
        return db_name

    def sync_credentials(self):
        """
        Sincroniza as credenciais com o sistema de IA.
        """
        self.ensure_one()

        try:
            # Atualizar status
            self.write({
                'sync_status': 'syncing',
                'error_message': False
            })

            # Obter ID da conta
            account_id = self.get_account_id()

            # Preparar payload
            payload = {
                'source': 'credentials',
                'event': 'credentials_sync',
                'account_id': account_id,
                'token': self.token,  # Token de autenticação
                'credentials': {
                    'domain': self.domain,
                    'name': self.name,
                    'odoo_url': self.odoo_url,
                    'odoo_db': self.odoo_db,
                    'odoo_username': self.odoo_username,
                    'token': self.token,  # Token de referência
                }
            }

            # Adicionar campos opcionais se preenchidos
            if self.qdrant_collection:
                payload['credentials']['qdrant_collection'] = self.qdrant_collection

            if self.redis_prefix:
                payload['credentials']['redis_prefix'] = self.redis_prefix

            # Adicionar credenciais de redes sociais se preenchidas
            if self.facebook_app_id:
                payload['credentials']['facebook_app_id'] = self.facebook_app_id

            if self.facebook_app_secret:
                payload['credentials']['facebook_app_secret'] = self.facebook_app_secret

            if self.facebook_access_token:
                payload['credentials']['facebook_access_token'] = self.facebook_access_token

            if self.instagram_client_id:
                payload['credentials']['instagram_client_id'] = self.instagram_client_id

            if self.instagram_client_secret:
                payload['credentials']['instagram_client_secret'] = self.instagram_client_secret

            if self.instagram_access_token:
                payload['credentials']['instagram_access_token'] = self.instagram_access_token

            if self.mercado_livre_app_id:
                payload['credentials']['mercado_livre_app_id'] = self.mercado_livre_app_id

            if self.mercado_livre_client_secret:
                payload['credentials']['mercado_livre_client_secret'] = self.mercado_livre_client_secret

            if self.mercado_livre_access_token:
                payload['credentials']['mercado_livre_access_token'] = self.mercado_livre_access_token

            # Obter URL do webhook a partir das configurações
            webhook_url = self.env['ir.config_parameter'].sudo().get_param('ai_credentials_manager.webhook_url', 'http://localhost:8001/webhook')

            # Enviar requisição para o webhook
            headers = {'Content-Type': 'application/json'}
            response = requests.post(webhook_url, data=json.dumps(payload), headers=headers, timeout=10)

            # Verificar resposta
            if response.status_code == 200:
                result = response.json()

                if result.get('success'):
                    # Atualizar status
                    self.write({
                        'sync_status': 'synced',
                        'last_sync': fields.Datetime.now()
                    })

                    _logger.info(f"Credenciais sincronizadas com sucesso: {result.get('message')}")
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': 'Sucesso',
                            'message': 'Credenciais sincronizadas com sucesso',
                            'sticky': False,
                            'type': 'success'
                        }
                    }
                else:
                    # Atualizar status
                    self.write({
                        'sync_status': 'error',
                        'error_message': result.get('error', 'Erro desconhecido')
                    })

                    _logger.error(f"Erro ao sincronizar credenciais: {result.get('error')}")
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': 'Erro',
                            'message': f"Erro ao sincronizar credenciais: {result.get('error')}",
                            'sticky': True,
                            'type': 'danger'
                        }
                    }
            else:
                # Atualizar status
                self.write({
                    'sync_status': 'error',
                    'error_message': f"Erro HTTP {response.status_code}: {response.text}"
                })

                _logger.error(f"Erro HTTP {response.status_code} ao sincronizar credenciais: {response.text}")
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Erro',
                        'message': f"Erro HTTP {response.status_code} ao sincronizar credenciais",
                        'sticky': True,
                        'type': 'danger'
                    }
                }

        except Exception as e:
            # Atualizar status
            self.write({
                'sync_status': 'error',
                'error_message': str(e)
            })

            _logger.exception(f"Exceção ao sincronizar credenciais: {str(e)}")
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Erro',
                    'message': f"Exceção ao sincronizar credenciais: {str(e)}",
                    'sticky': True,
                    'type': 'danger'
                }
            }

    def get_credentials(self):
        """
        Obtém as credenciais para uso por outros módulos.
        """
        self.ensure_one()

        # Verificar se as credenciais estão sincronizadas
        if self.sync_status != 'synced':
            _logger.warning(f"Tentativa de obter credenciais não sincronizadas: {self.name}")

        # Retornar credenciais
        return {
            'domain': self.domain,
            'name': self.name,
            'odoo_url': self.odoo_url,
            'odoo_db': self.odoo_db,
            'odoo_username': self.odoo_username,
            'token': self.token,
            'qdrant_collection': self.qdrant_collection,
            'redis_prefix': self.redis_prefix,
            'facebook_app_id': self.facebook_app_id,
            'facebook_app_secret': self.facebook_app_secret,
            'facebook_access_token': self.facebook_access_token,
            'instagram_client_id': self.instagram_client_id,
            'instagram_client_secret': self.instagram_client_secret,
            'instagram_access_token': self.instagram_access_token,
            'mercado_livre_app_id': self.mercado_livre_app_id,
            'mercado_livre_client_secret': self.mercado_livre_client_secret,
            'mercado_livre_access_token': self.mercado_livre_access_token,
        }
