# -*- coding: utf-8 -*-
{
    'name': 'Regras de Negócio para Sistema de IA',
    'version': '1.0',
    'category': 'Sales/CRM',
    'summary': 'Configure regras de negócio para personalizar o comportamento dos agentes de IA',
    'description': """
Regras de Negócio para Sistema de IA
====================================

Este módulo permite configurar regras de negócio específicas para personalizar o comportamento dos agentes de IA.

Características:
- Configuração de informações básicas da empresa
- Definição de regras de atendimento (saudação, estilo de comunicação)
- Seleção de modelo de negócio com regras pré-configuradas
- Criação de regras personalizadas e temporárias
- Sincronização com o sistema de IA
- Dashboard de regras ativas
    """,
    'author': 'ChatwootAI',
    'website': 'https://github.com/GiovanoMP/chatwootai',
    'depends': ['base', 'web', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/business_rules_views.xml',
        'views/rule_item_views.xml',
        'views/temporary_rule_views.xml',
        'views/dashboard_view.xml',
        'views/res_config_settings_views.xml',
        'views/menu_views.xml',
        'data/business_template_data.xml',
        'data/config_parameter.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
    'maintainer': 'ChatwootAI Team',
    'support': 'support@chatwootai.com',
}
