#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para verificar os campos disponíveis em um modelo Odoo.
"""

import sys
import xmlrpc.client
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configurações do Odoo
ODOO_URL = os.getenv("ODOO_URL", "http://localhost:8069")
ODOO_DB = os.getenv("ODOO_DB", "account_1")
ODOO_USERNAME = os.getenv("ODOO_USERNAME", "giovano@sprintia.com.br")
ODOO_PASSWORD = os.getenv("ODOO_PASSWORD", "0701Gio***")

def check_model_fields(model_name):
    """Verifica os campos disponíveis em um modelo Odoo."""
    try:
        # Conectar ao Odoo
        common = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/common")
        uid = common.authenticate(ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD, {})
        
        if not uid:
            print(f"Falha na autenticação com o Odoo. Verifique as credenciais.")
            return
        
        # Criar proxy para o modelo
        models = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/object")
        
        # Verificar se o modelo existe
        model_exists = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'ir.model', 'search_count',
            [[['model', '=', model_name]]]
        )
        
        if not model_exists:
            print(f"Modelo '{model_name}' não encontrado no Odoo.")
            return
        
        # Obter campos do modelo
        fields_data = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            model_name, 'fields_get',
            [], {'attributes': ['string', 'help', 'type']}
        )
        
        # Imprimir informações dos campos
        print(f"\nCampos disponíveis no modelo '{model_name}':")
        print("-" * 80)
        print(f"{'Nome do Campo':<30} {'Tipo':<15} {'Descrição':<35}")
        print("-" * 80)
        
        for field_name, field_info in sorted(fields_data.items()):
            field_type = field_info.get('type', '')
            field_string = field_info.get('string', '')
            print(f"{field_name:<30} {field_type:<15} {field_string:<35}")
        
        print("-" * 80)
        print(f"Total de campos: {len(fields_data)}")
        
    except Exception as e:
        print(f"Erro ao verificar campos do modelo: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python check_odoo_model_fields.py <nome_do_modelo>")
        sys.exit(1)
    
    model_name = sys.argv[1]
    check_model_fields(model_name)
