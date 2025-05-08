#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para criar um novo arquivo chatwoot_mapping.yaml.
"""

import yaml
import os

# Definir o conteúdo do arquivo
data = {
    'accounts': {
        '1': {
            'account_id': 'account_1',
            'domain': 'retail'
        }
    },
    'default_domain': 'default',
    'fallbacks': [],
    'inboxes': {
        '1': {
            'account_id': 'account_1',
            'domain': 'retail'
        }
    },
    'special_numbers': []
}

# Caminho do arquivo
file_path = 'config/chatwoot_mapping_created.yaml'

# Salvar o arquivo
with open(file_path, 'w', encoding='utf-8') as f:
    yaml.dump(data, f, default_flow_style=False, allow_unicode=True)

print(f"Arquivo criado: {file_path}")

# Verificar o conteúdo do arquivo
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

print(f"Conteúdo do arquivo ({len(content)} bytes):")
print("-" * 50)
print(content)
print("-" * 50)
