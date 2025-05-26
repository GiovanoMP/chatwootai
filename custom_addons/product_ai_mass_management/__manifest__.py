# -*- coding: utf-8 -*-
{
    'name': 'Gestão de Produtos e Estoque',
    'version': '1.0',
    'category': 'Inventory/Sales',
    'summary': 'Gerencie produtos e serviços de forma integrada com canais de venda e estoque',
    'description': """
Gestão de Produtos e Estoque
===================================================
Este módulo oferece uma interface completa para gerenciar produtos e serviços,
com integração ao estoque e múltiplos canais de venda, incluindo sistema de IA.

Principais funcionalidades:
- Gerenciamento de produtos e serviços em múltiplos canais
- Importação/exportação em massa via CSV e Excel
- Integração bidirecional com estoque
- Sincronização com sistema de IA e outros canais
- Ajustes de preço por canal (descontos, aumentos)
- Monitoramento de popularidade de produtos
- Interface moderna com vistas Kanban e gráficos
    """,
    'author': 'ChatwootAI',
    'website': 'https://github.com/GiovanoMP/chatwootai',
    'depends': [
        'base',
        'product',
        'sale',
        'stock',
        'purchase',
        'semantic_product_description',
        'base_import',
    ],
    # Todas as dependências necessárias já estão incluídas no Odoo
    'data': [
        'security/ir.model.access.csv',
        'wizards/adjust_ai_prices_wizard_views.xml',
        'wizards/import_export_products_wizard_views.xml',
        'wizards/product_channel_add_wizard_views.xml',
        'wizards/stock_import_wizard_views.xml',
        'views/product_views.xml',
        'views/product_channel_views.xml',
        'views/product_kanban_view.xml',
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
