# -*- coding: utf-8 -*-
{
    'name': 'Descrições Inteligentes de Produtos',
    'version': '1.0',
    'category': 'Sales/Sales',
    'summary': 'Adiciona campos estruturados para descrições inteligentes de produtos',
    'description': """
Descrições Inteligentes de Produtos
=================================
Este módulo adiciona campos estruturados para descrições de produtos otimizadas para IA,
facilitando buscas inteligentes e melhorando a experiência do cliente.

Principais funcionalidades:
- Descrição do produto otimizada para IA
- Principais características em formato de lista
- Cenários de uso comuns para cada produto
- Variações e características adicionais
- Geração automática de descrições com IA
- Verificação humana para garantir qualidade
    """,
    'author': 'ChatwootAI',
    'website': 'https://github.com/seu-repositorio/semantic_product_description',
    'depends': ['product', 'sale', 'stock'],
    'data': [
        'views/product_template_views.xml',
    ],
    'images': ['static/description/banner.png'],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
