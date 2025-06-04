# -*- coding: utf-8 -*-
{
    'name': 'Gestão de Tenants e MCP CREW',
    'version': '16.0.1.0.0',
    'summary': 'Módulo para gerenciar tenants e a integração com o MCP CREW.',
    'description': """
Este módulo centraliza o gerenciamento de tenants (contas), suas configurações de API 
para comunicação bidirecional com o MCP CREW, e o monitoramento de módulos Odoo 
para integração com a plataforma MCP.
    """,
    'category': 'Extra Tools',
    'author': 'Sprintia',
    'website': 'https://www.sprintia.com.br',
    'license': 'OPL-1',
    'depends': ['base', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'data/tenant_mcp_type_data.xml',
        'views/tenant_mcp_tenant_views.xml',
        'views/tenant_mcp_type_views.xml',
        'views/tenant_mcp_ia_service_catalog_views.xml',
        'views/tenant_mcp_tenant_service_access_views.xml',
        'views/tenant_mcp_menus.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
