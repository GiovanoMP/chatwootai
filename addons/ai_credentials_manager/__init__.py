# -*- coding: utf-8 -*-

from . import models

def _register_default_config(env):
    """Registra as configurações padrão para o microserviço de configuração."""
    config_param = env['ir.config_parameter'].sudo()

    # Configurações do microserviço
    if not config_param.get_param('config_service_url'):
        config_param.set_param('config_service_url', 'http://localhost:8002')

    if not config_param.get_param('config_service_api_key'):
        config_param.set_param('config_service_api_key', 'development-api-key')

    if not config_param.get_param('config_service_enabled'):
        config_param.set_param('config_service_enabled', 'True')

def post_init_hook(cr, registry):
    """Hook executado após a instalação do módulo."""
    from odoo import api, SUPERUSER_ID
    env = api.Environment(cr, SUPERUSER_ID, {})
    _register_default_config(env)
