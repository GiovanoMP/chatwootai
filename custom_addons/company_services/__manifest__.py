# -*- coding: utf-8 -*-
{
    'name': 'Empresa e Serviços',
    'version': '1.0',
    'category': 'Services',
    'summary': 'Gerenciamento de informações da empresa e serviços para IA',
    'description': """
Empresa e Serviços
========================
Este módulo permite configurar informações da empresa e serviços oferecidos
para integração com o sistema de Inteligência Artificial.

Funcionalidades:
---------------
* Configuração de informações básicas da empresa
* Definição de serviços de IA contratados
* Configuração de horários de atendimento
* Personalização do estilo de comunicação do agente de IA
* Configuração de redes sociais e site para menção ao finalizar conversas
* Integração com o serviço de configuração
* Sincronização automática de dados com o sistema de IA
    """,
    'author': 'Sprintia',
    'website': 'https://www.sprintia.com.br',
    'depends': ['base', 'mail'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/init_data.xml',
        'views/company_service_views.xml',
        'views/res_config_settings_views.xml',
        'views/menu_views.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
