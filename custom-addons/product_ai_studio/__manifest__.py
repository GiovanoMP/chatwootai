# -*- coding: utf-8 -*-
{
    'name': 'Estúdio de Produtos com IA (Simplificado)',
    'version': '0.5',
    'category': 'Sales/Sales',
    'summary': 'Enriquecimento de produtos com IA - Versão simplificada',
    'description': """
Estúdio de Produtos com IA (Simplificado)
========================================

Versão simplificada para enriquecimento de produtos com inteligência artificial:

* Criação de descrições otimizadas para produtos
* Integração básica com marketplaces
* Ferramentas essenciais para melhorar listagens de produtos

Ideal para:
----------
* E-commerces que buscam melhorar descrições de produtos
* Lojistas que precisam de conteúdo otimizado
* Empresas com desafios na criação de conteúdo
    """,
    'author': 'ChatwootAI',
    'website': 'https://www.chatwoot.ai',
    'depends': [
        'base',
        'product',
        'mail',
        'web',
    ],
    'data': [
        'security/security_rules.xml',
        'security/ir.model.access.csv',
        'views/enrichment_profile_views.xml',
        'views/product_enrichment_views.xml',
        'views/marketplace_connector_views.xml',
        'views/menu_views.xml',
        'data/enrichment_profile_data.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'product_ai_studio/static/src/scss/studio.scss',
        ],
    },
    'demo': [],
    'images': ['static/description/banner.png'],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
