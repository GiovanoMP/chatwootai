# -*- coding: utf-8 -*-
{
    'name': 'Regras de Negócio',
    'version': '1.0',
    'category': 'Services/Business Rules',
    'summary': 'Gerenciamento de regras de negócio para o sistema de IA',
    'description': """
Módulo de Regras de Negócio
===============================

Este módulo permite gerenciar regras de negócio para o sistema de IA, incluindo:

Características:
- Definição de regras de negócio permanentes
- Criação de regras temporárias e promoções
- Configuração de regras de agendamento
- Gerenciamento de documentos de suporte
- Sincronização com o sistema de IA
    """,
    'author': 'Sprintia',
    'website': 'https://www.sprintia.com.br',
    'depends': ['base', 'web', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/business_rules_views.xml',
        'views/rule_item_views.xml',
        'views/temporary_rule_views.xml',
        'views/scheduling_rule_views.xml',
        'views/business_support_document_views.xml',
        'views/res_config_settings_views.xml',
        'views/menu_views.xml',
        'wizards/document_upload_wizard.xml',
        'data/config_parameter.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
