# -*- coding: utf-8 -*-

from odoo import models, api
import logging

_logger = logging.getLogger(__name__)

class InitConfig(models.AbstractModel):
    _name = 'company.init.config'
    _description = 'Inicialização de Configurações'

    @api.model
    def init_mcp_config(self):
        """
        Inicializa as configurações de MCP e banco de dados.
        Este método é chamado durante a instalação do módulo.
        """
        IrConfigParam = self.env['ir.config_parameter'].sudo()

        # Verificar se as configurações já existem
        mcp_type = IrConfigParam.get_param('company_services.mcp_type', False)

        # Se não existirem, criar com valores padrão
        if not mcp_type:
            _logger.info("Inicializando configurações de MCP e banco de dados")

            # Configurações de MCP
            IrConfigParam.set_param('company_services.mcp_type', 'odoo')
            IrConfigParam.set_param('company_services.mcp_version', '14.0')

            # Configurações de banco de dados
            IrConfigParam.set_param('company_services.db_url', 'http://localhost:8069')
            IrConfigParam.set_param('company_services.db_name', 'odoo')
            IrConfigParam.set_param('company_services.db_user', 'admin')
            IrConfigParam.set_param('company_services.db_password', 'admin')
            IrConfigParam.set_param('company_services.db_access_level', 'read')

            # Configurações adicionais
            IrConfigParam.set_param('company_services.mention_website', 'True')
            IrConfigParam.set_param('company_services.mention_social_media', 'True')

            # Configurações de serviços disponíveis (todos desabilitados por padrão)
            IrConfigParam.set_param('company_services.enable_sales', 'False')
            IrConfigParam.set_param('company_services.enable_scheduling', 'False')
            IrConfigParam.set_param('company_services.enable_delivery', 'False')
            IrConfigParam.set_param('company_services.enable_support', 'False')

            # As descrições dos serviços foram removidas, pois agora são textos estáticos na view

            _logger.info("Configurações de MCP, banco de dados e serviços inicializadas com sucesso")

        return True
