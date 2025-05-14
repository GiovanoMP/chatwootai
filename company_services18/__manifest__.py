# -*- coding: utf-8 -*-
{
    'name': 'Empresa e Serviços',
    'version': '18.0.1.0.0',
    'summary': 'Gerenciamento de empresas e serviços',
    'description': """
        Módulo para gerenciar empresas e seus serviços.
        Permite configurar webhooks, chaves de API e outras configurações por empresa.
    """,
    'category': 'Services',
    'author': 'Sprintia',
    'website': 'https://www.sprintia.com.br',
    'license': 'LGPL-3',
    'depends': ['base', 'mail'],
    'data': [
        'security/company_services_security.xml',
        'security/ir.model.access.csv',
        'views/company_service_views.xml',
        'views/special_phone_views.xml',
        'views/res_config_settings_views.xml',
        'views/menu_views.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'assets': {},
}
