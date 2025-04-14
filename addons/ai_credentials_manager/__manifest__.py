# -*- coding: utf-8 -*-
{
    'name': 'Gerenciador de Credenciais para IA',
    'version': '1.0',
    'summary': 'Gerenciamento seguro de credenciais para integração com sistemas de IA',
    'description': """
Gerenciador de Credenciais para IA
==================================

Este módulo fornece uma interface segura e centralizada para gerenciar credenciais
utilizadas na integração entre o Odoo e sistemas de Inteligência Artificial.

Características:
---------------
* Armazenamento seguro de credenciais de API
* Acesso restrito apenas para administradores
* Auditoria completa de acessos e modificações
* Integração com arquivos YAML de configuração
* Suporte a múltiplos clientes e ambientes

Segurança:
---------
* Credenciais sensíveis armazenadas de forma segura no banco de dados
* Controle de acesso granular baseado em grupos de segurança
* Registro detalhado de todas as operações para auditoria
    """,
    'author': 'Sua Empresa',
    'website': 'https://www.suaempresa.com',
    'category': 'Technical',
    'depends': ['base', 'mail'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/menu_views.xml',
        'views/credentials_views.xml',
        'views/sync_queue_views.xml',
    ],
    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
    'images': ['static/description/banner.png'],
}
