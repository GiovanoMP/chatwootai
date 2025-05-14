# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # URL do webhook para o microsserviço de vetorização
    business_rules_webhook_url = fields.Char(
        string='URL do Webhook',
        config_parameter='business_rules.webhook_url',
        default='http://localhost:8004',
        help="URL do webhook para o microsserviço de vetorização"
    )

    # ID da conta para identificação no Qdrant
    business_rules_account_id = fields.Char(
        string='ID da Conta',
        config_parameter='business_rules.account_id',
        default='account_1',
        help="""ID da conta para identificação no sistema de IA (ex: account_1, account_2).
Este é o identificador chave que será usado como identificador único no Qdrant.
Cada cliente deve ter um ID de conta único para garantir a separação dos dados."""
    )

    # Token de API para autenticação
    business_rules_api_token = fields.Char(
        string='Token de API',
        config_parameter='business_rules.api_token',
        default='development-api-key',
        help="Token de autenticação para o microsserviço de vetorização"
    )

    # Nome da empresa
    business_rules_company_name = fields.Char(
        string='Nome da Empresa',
        config_parameter='business_rules.company_name',
        help="Nome da empresa para identificação no microsserviço de vetorização"
    )
