# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import requests
import logging

_logger = logging.getLogger(__name__)

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    config_viewer_url = fields.Char(
        string='URL do Visualizador de Configurações',
        help='URL para o visualizador de configurações externo',
        config_parameter='config_viewer.url',
        default='http://localhost:8080'
    )

    config_service_enabled = fields.Boolean(
        string='Ativar Microserviço de Configuração',
        config_parameter='config_service_enabled',
        default=True
    )
    config_service_url = fields.Char(
        string='URL do Microserviço',
        config_parameter='config_service_url',
        default='http://localhost:8002'
    )
    config_service_api_key = fields.Char(
        string='Chave de API',
        config_parameter='config_service_api_key',
        default='development-api-key'
    )



    def action_test_config_service_connection(self):
        """Testa a conexão com o microserviço de configuração."""
        self.ensure_one()

        if not self.config_service_enabled:
            raise UserError(_("O microserviço de configuração não está ativado."))

        if not self.config_service_url:
            raise UserError(_("A URL do microserviço de configuração não está configurada."))

        if not self.config_service_api_key:
            raise UserError(_("A chave de API do microserviço de configuração não está configurada."))

        try:
            url = f"{self.config_service_url}/health"
            headers = {"X-API-Key": self.config_service_api_key}

            response = requests.get(url, headers=headers, timeout=5)

            if response.status_code == 200:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Sucesso'),
                        'message': _('Conexão com o microserviço de configuração estabelecida com sucesso.'),
                        'sticky': False,
                        'type': 'success',
                    }
                }
            else:
                raise UserError(_(
                    "Erro ao conectar ao microserviço de configuração. "
                    "Código de status: %s. Resposta: %s"
                ) % (response.status_code, response.text))
        except requests.RequestException as e:
            raise UserError(_(
                "Erro ao conectar ao microserviço de configuração: %s"
            ) % str(e))
