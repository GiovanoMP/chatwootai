#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para corrigir o arquivo chatwoot_mapping.yaml.
"""

import yaml
import os
import sys

def fix_yaml_file(input_path, output_path):
    """
    Lê o arquivo YAML e cria uma cópia corrigida.
    
    Args:
        input_path: Caminho do arquivo de entrada
        output_path: Caminho do arquivo de saída
    """
    try:
        # Ler o arquivo como texto
        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        print(f"Conteúdo do arquivo original ({len(content)} bytes):")
        print("-" * 50)
        print(content)
        print("-" * 50)
        
        # Carregar o YAML
        data = yaml.safe_load(content)
        
        print(f"Dados carregados: {data}")
        
        # Salvar em um novo arquivo
        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
            
        print(f"Arquivo corrigido salvo em: {output_path}")
        
        # Verificar o conteúdo do arquivo corrigido
        with open(output_path, 'r', encoding='utf-8') as f:
            fixed_content = f.read()
            
        print(f"Conteúdo do arquivo corrigido ({len(fixed_content)} bytes):")
        print("-" * 50)
        print(fixed_content)
        print("-" * 50)
        
    except Exception as e:
        print(f"Erro: {str(e)}")
        return False
        
    return True

if __name__ == "__main__":
    input_path = "config/chatwoot_mapping.yaml"
    output_path = "config/chatwoot_mapping_fixed.yaml"
    
    if len(sys.argv) > 1:
        input_path = sys.argv[1]
    if len(sys.argv) > 2:
        output_path = sys.argv[2]
        
    success = fix_yaml_file(input_path, output_path)
    
    if success:
        print("Operação concluída com sucesso!")
    else:
        print("Falha na operação!")
