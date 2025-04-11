# -*- coding: utf-8 -*-
{
    'name': 'Gerenciamento em Massa de Produtos no Sistema de IA',
    'version': '1.0',
    'category': 'Sales/Sales',
    'summary': 'Interface de gerenciamento em massa para produtos no sistema de IA',
    'description': """
Gerenciamento em Massa de Produtos no Sistema de IA
===================================================
Este módulo adiciona uma interface de lista para gerenciar múltiplos produtos no sistema de IA,
permitindo sincronização em massa, ajustes de preço e visualização rápida de status.

Principais funcionalidades:
- Vista de lista com seleção múltipla
- Sincronização em massa de produtos com o sistema de IA
- Ajustes de preço em massa (descontos, aumentos)
- Indicadores visuais de status de sincronização
    """,
    'author': 'ChatwootAI',
    'website': 'https://github.com/seu-repositorio/product_ai_mass_management',
    'depends': ['product', 'sale', 'stock', 'purchase', 'semantic_product_description'],
    'data': [
        'security/ir.model.access.csv',
        'wizards/adjust_ai_prices_wizard_views.xml',
        'views/product_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
