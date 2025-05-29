# -*- coding: utf-8 -*-
{
    'name': 'Odoo Integration with MCP',
    'version': '1.0',
    'category': 'Tools',
    'summary': 'Agente Universal de IA para Odoo com Integração MCP',
    'description': """
        Este módulo fornece um agente universal de IA que pode:
        - Conectar-se a MCPs externos (Model Context Protocols)
        - Executar operações via comandos em linguagem natural
        - Fornecer dashboards para dados de plataformas externas
        - Sincronizar dados bidirecionalmente
        
        Integração inicial com Mercado Livre, preparado para expansão para outras plataformas.
    """,
    'author': 'Manus',
    'website': 'https://www.manus.ai',
    'depends': [
        'base',
        'web',
        'mail',
        'product',
        'sale',
        'stock',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/mcp_connector_views.xml',
        'views/agent_views.xml',
        'views/dashboard_views.xml',
        'views/menu_views.xml',
        'data/mcp_data.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'odoo_integration/static/src/js/**/*',
            'odoo_integration/static/src/scss/**/*',
            'odoo_integration/static/src/xml/**/*',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
