# -*- coding: utf-8 -*-
{
    'name': 'Gestão de Produtos e Estoque',
    'version': '1.0',
    'category': 'Inventory/Sales',
    'summary': 'Gerencie produtos no sistema de IA de forma eficiente e visual',
    'description': """
Gestão de Produtos e Estoque
===================================================
Este módulo adiciona uma interface de lista para gerenciar múltiplos produtos no sistema de IA,
permitindo sincronização em massa, ajustes de preço e visualização rápida de status.

Principais funcionalidades:
- Vista de lista com seleção múltipla
- Badges coloridos para status visual rápido
- Sincronização em massa de produtos com o sistema de IA
- Geração e verificação de descrições
- Ajustes de preço em massa (descontos, aumentos)
- Monitoramento de popularidade de produtos
- Indicadores visuais de status de sincronização
    """,
    'author': 'ChatwootAI',
    'website': 'https://github.com/GiovanoMP/chatwootai',
    'depends': ['product', 'sale', 'stock', 'purchase', 'semantic_product_description'],
    'data': [
        'security/ir.model.access.csv',
        'wizards/adjust_ai_prices_wizard_views.xml',
        'views/product_views.xml',
        'views/menu_views.xml',
    ],
    'images': ['static/description/banner.png'],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
    'maintainer': 'ChatwootAI Team',
    'support': 'support@chatwootai.com',
}
