# -*- coding: utf-8 -*-
{
    'name': 'Descrições Inteligentes de Produtos',
    'version': '1.0',
    'category': 'Sales/Sales',
    'summary': 'Adiciona descrições inteligentes e busca de imagens para produtos',
    'description': """
Descrições Inteligentes de Produtos
===================================
Este módulo adiciona campos para descrições inteligentes de produtos diretamente 
na aba de Informações Gerais, além de botões para buscar imagens e descrições 
automaticamente.

Principais funcionalidades:
- Descrição inteligente do produto integrada na aba Informações Gerais
- Botão para buscar imagens do produto online
- Botão para gerar descrições usando IA
- Sistema visual de tags para variações
- Verificação humana para garantir qualidade
    """,
    'author': 'ChatwootAI',
    'website': 'https://github.com/seu-repositorio/semantic_product_inline',
    'depends': ['product', 'sale', 'stock'],
    'data': [
        'views/product_template_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
