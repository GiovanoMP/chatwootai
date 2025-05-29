# -*- coding: utf-8 -*-

from odoo import api, fields, models
import uuid

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # Campos de configuração para o serviço
    company_services_account_id = fields.Char(
        string='ID da Conta',
        help="ID da conta para identificação no sistema de IA (ex: account_1)",
        config_parameter='company_services.account_id'
    )

    company_services_security_token = fields.Char(
        string='Token de Segurança',
        help="Token único para autenticação no webhook",
        config_parameter='company_services.security_token'
    )

    company_services_config_service_url = fields.Char(
        string='URL do Serviço de Configuração',
        help="URL do serviço de configuração (ex: http://localhost:8002)",
        config_parameter='company_services.config_service_url'
    )

    company_services_config_service_api_key = fields.Char(
        string='Chave de API do Serviço de Configuração',
        help="Chave de API para autenticação no serviço de configuração",
        config_parameter='company_services.config_service_api_key'
    )

    # Campos de configuração para o MCP
    company_services_mcp_type = fields.Selection([
        ('odoo', 'Odoo'),
        ('sap', 'SAP'),
        ('other', 'Outro')
    ], string='Tipo de MCP',
       help="Tipo de MCP (Model Communication Protocol) utilizado",
       config_parameter='company_services.mcp_type',
       default='odoo')

    company_services_mcp_version = fields.Char(
        string='Versão do ERP',
        help="Versão do sistema ERP (ex: 14.0 para Odoo)",
        config_parameter='company_services.mcp_version'
    )

    # Campos para conexão com o banco de dados
    company_services_db_url = fields.Char(
        string='URL do Servidor',
        help="URL do servidor ERP (ex: http://localhost:8069)",
        config_parameter='company_services.db_url'
    )

    company_services_db_name = fields.Char(
        string='Nome do Banco de Dados',
        help="Nome do banco de dados específico do tenant",
        config_parameter='company_services.db_name'
    )

    company_services_db_user = fields.Char(
        string='Usuário do Banco',
        help="Usuário com permissões adequadas para acesso ao banco",
        config_parameter='company_services.db_user'
    )

    company_services_db_password = fields.Char(
        string='Senha do Banco',
        help="Senha do usuário (será armazenada de forma segura)",
        config_parameter='company_services.db_password',
        password=True
    )

    company_services_db_access_level = fields.Selection([
        ('read', 'Somente Leitura'),
        ('write', 'Leitura e Escrita'),
        ('admin', 'Administrador')
    ], string='Nível de Acesso',
       help="Nível de acesso ao banco de dados",
       config_parameter='company_services.db_access_level',
       default='read')

    # Campos para configuração de serviços disponíveis
    company_services_enable_sales = fields.Boolean(
        string='Vendas de Produtos e Serviços',
        help="Habilita o serviço de vendas de produtos e serviços",
        config_parameter='company_services.enable_sales'
    )

    company_services_sales_description = fields.Char(
        string='Descrição do Serviço de Vendas',
        help="Descrição detalhada do serviço de vendas",
        config_parameter='company_services.sales_description',
        default="Permite que o agente de IA forneça informações sobre produtos, preços, promoções e realize vendas."
    )

    company_services_enable_scheduling = fields.Boolean(
        string='Agendamentos',
        help="Habilita o serviço de agendamentos",
        config_parameter='company_services.enable_scheduling'
    )

    company_services_scheduling_description = fields.Char(
        string='Descrição do Serviço de Agendamentos',
        help="Descrição detalhada do serviço de agendamentos",
        config_parameter='company_services.scheduling_description',
        default="Permite que o agente de IA realize agendamentos de serviços, consultas ou reservas."
    )

    company_services_enable_delivery = fields.Boolean(
        string='Delivery',
        help="Habilita o serviço de delivery",
        config_parameter='company_services.enable_delivery'
    )

    company_services_delivery_description = fields.Char(
        string='Descrição do Serviço de Delivery',
        help="Descrição detalhada do serviço de delivery",
        config_parameter='company_services.delivery_description',
        default="Permite que o agente de IA forneça informações sobre entregas, prazos e status de pedidos."
    )

    company_services_enable_support = fields.Boolean(
        string='Suporte ao Cliente',
        help="Habilita o serviço de suporte ao cliente",
        config_parameter='company_services.enable_support'
    )

    company_services_support_description = fields.Char(
        string='Descrição do Serviço de Suporte',
        help="Descrição detalhada do serviço de suporte",
        config_parameter='company_services.support_description',
        default="Permite que o agente de IA forneça suporte técnico, responda dúvidas e resolva problemas."
    )

    def generate_security_token(self):
        """Gera um novo token de segurança."""
        token = str(uuid.uuid4())
        self.company_services_security_token = token
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Token Gerado',
                'message': f'Novo token de segurança gerado: {token}',
                'sticky': False,
                'type': 'success',
            }
        }
