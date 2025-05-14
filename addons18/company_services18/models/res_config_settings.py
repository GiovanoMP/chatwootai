# -*- coding: utf-8 -*-

from odoo import api, fields, models
import uuid

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # Campos de configuração para o serviço
    company_services_account_id = fields.Char(
        string='ID da Conta',
        help="""ID da conta para identificação no sistema de IA (ex: account_1, account_2).
Este é o identificador chave que será usado como identificador único no MongoDB.
Cada cliente deve ter um ID de conta único para garantir a separação dos dados.
Este ID também será usado como nome do banco de dados nas configurações de MCP.""",
        config_parameter='company_services.account_id'
    )

    company_services_security_token = fields.Char(
        string='Token de Segurança',
        help="""Token único para autenticação no webhook.
Este token é enviado junto com os dados para garantir a segurança da comunicação.
Use o botão 'Gerar Token' para criar um token seguro automaticamente.
Guarde este token em um local seguro, pois ele será necessário para autenticar as requisições.""",
        config_parameter='company_services.security_token'
    )

    company_services_config_service_url = fields.Char(
        string='URL do Serviço de Configuração',
        help="""URL do serviço de configuração (webhook) que receberá os dados.
Para o webhook MongoDB, use: http://localhost:8003
Para o config-service original, use: http://localhost:8002
Esta URL deve apontar para o serviço que está rodando e acessível pela rede.""",
        config_parameter='company_services.config_service_url'
    )

    company_services_config_service_api_key = fields.Char(
        string='Chave de API do Serviço de Configuração',
        help="""Chave de API para autenticação no serviço de configuração.
Esta chave deve corresponder à chave configurada no serviço (API_KEY).
Para o webhook MongoDB, o valor padrão é: development-api-key
Esta chave é enviada no cabeçalho da requisição para autenticar o cliente.""",
        config_parameter='company_services.config_service_api_key'
    )

    # Campos para configuração de MCP
    company_services_mcp_type = fields.Selection([
        ('odoo', 'Odoo'),
        ('custom', 'Personalizado')
    ], string='Tipo de MCP',
       help="""Tipo de Model Communication Protocol:
- Odoo: Utiliza o protocolo padrão do Odoo
- Personalizado: Utiliza um protocolo personalizado""",
       config_parameter='company_services.mcp_type',
       default='odoo')

    company_services_mcp_version = fields.Selection([
        ('14.0', 'Odoo 14'),
        ('15.0', 'Odoo 15'),
        ('16.0', 'Odoo 16'),
        ('18.0', 'Odoo 18'),
        ('custom', 'Personalizado')
    ], string='Versão do MCP',
       help="""Versão do Model Communication Protocol:
- Odoo 14/15/16/18: Versão específica do Odoo
- Personalizado: Versão personalizada""",
       config_parameter='company_services.mcp_version',
       default='18.0')

    # Campos para conexão com o banco de dados
    company_services_db_url = fields.Char(
        string='URL do Servidor',
        help="""URL do servidor ERP (ex: http://localhost:8069).
Esta URL será usada pelos agentes de IA para se conectarem ao ERP.
Certifique-se de que esta URL seja acessível a partir do servidor onde os agentes estão rodando.""",
        config_parameter='company_services.db_url'
    )

    company_services_db_name = fields.Char(
        string='Nome do Banco de Dados',
        help="""Nome do banco de dados específico do tenant.
IMPORTANTE: Para garantir consistência, recomenda-se usar o mesmo valor do ID da Conta.
Este campo será preenchido automaticamente com o valor do ID da Conta quando ele for alterado.""",
        config_parameter='company_services.db_name'
    )

    company_services_db_user = fields.Char(
        string='Usuário do Banco',
        help="""Usuário com permissões adequadas para acesso ao banco.
Este usuário deve ter as permissões necessárias de acordo com o nível de acesso selecionado.""",
        config_parameter='company_services.db_user'
    )

    company_services_db_password = fields.Char(
        string='Senha do Banco',
        help="""Senha do usuário para acesso ao banco de dados.
Esta senha será armazenada de forma segura e criptografada no sistema.
Será referenciada como '{account_id}_db_pwd' nos dados enviados ao sistema de IA.""",
        config_parameter='company_services.db_password',
        password=True
    )

    company_services_db_access_level = fields.Selection([
        ('read', 'Somente Leitura'),
        ('write', 'Leitura e Escrita'),
        ('admin', 'Administrador')
    ], string='Nível de Acesso',
       help="""Nível de acesso ao banco de dados:
- Somente Leitura: Permite apenas consultar dados (recomendado para maior segurança)
- Leitura e Escrita: Permite consultar e modificar dados
- Administrador: Acesso completo (use com cautela)""",
       config_parameter='company_services.db_access_level',
       default='read')

    # Campos para configuração de canais disponíveis
    company_services_channel_whatsapp = fields.Boolean(
        string='Canal WhatsApp',
        help="Habilita o canal de WhatsApp para os serviços de IA",
        config_parameter='company_services.channel_whatsapp',
        default=True
    )

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

    # Configurações de idioma
    company_services_language_pt_BR = fields.Boolean(
        string='Português Brasileiro',
        help="Habilita o idioma Português Brasileiro para o agente de IA",
        config_parameter='company_services.language_pt_BR',
        default=True
    )

    company_services_language_es_ES = fields.Boolean(
        string='Espanhol',
        help="Habilita o idioma Espanhol para o agente de IA",
        config_parameter='company_services.language_es_ES',
        default=False
    )

    company_services_language_en_US = fields.Boolean(
        string='Inglês',
        help="Habilita o idioma Inglês para o agente de IA",
        config_parameter='company_services.language_en_US',
        default=False
    )

    # Números de telefone especiais
    special_phone_ids = fields.Many2many(
        'company.services.special.phone',
        string='Números de Telefone Especiais',
        help="Lista de números de telefone com permissões especiais para acesso a funcionalidades avançadas"
    )

    @api.onchange('company_services_account_id')
    def _onchange_account_id(self):
        """Atualiza o nome do banco de dados quando o ID da conta é alterado."""
        if self.company_services_account_id:
            self.company_services_db_name = self.company_services_account_id

    def action_generate_security_token(self):
        """Gera um token de segurança aleatório."""
        self.company_services_security_token = str(uuid.uuid4())
