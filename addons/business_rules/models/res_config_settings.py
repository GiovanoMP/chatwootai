# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    business_rules_api_url = fields.Char(
        string='URL da API',
        config_parameter='business_rules.api_url',
        default='http://localhost:8000'
    )
    
    business_rules_api_token = fields.Char(
        string='Token de API',
        config_parameter='business_rules.api_token',
        default='default_token'
    )
