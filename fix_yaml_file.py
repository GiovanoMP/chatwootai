#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para corrigir o arquivo chatwoot_mapping.yaml.
Este script lê o conteúdo do arquivo YAML e o reescreve em um formato que possa ser visualizado no editor.
"""

import yaml
import json
import os
import sys

def fix_yaml_file(file_path):
    """
    Corrige o arquivo YAML.
    
    Args:
        file_path: Caminho do arquivo YAML
    
    Returns:
        True se a correção foi bem-sucedida, False caso contrário
    """
    try:
        # Verificar se o arquivo existe
        if not os.path.exists(file_path):
            print(f"Arquivo não encontrado: {file_path}")
            return False
        
        # Ler o conteúdo do arquivo usando o comando cat
        print(f"Lendo arquivo: {file_path}")
        os.system(f"cat {file_path}")
        
        # Ler o conteúdo do arquivo
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"\nConteúdo do arquivo ({len(content)} bytes):")
        print("-" * 50)
        print(content)
        print("-" * 50)
        
        # Carregar o YAML
        data = yaml.safe_load(content)
        
        if not data:
            print("Arquivo YAML vazio ou inválido")
            return False
        
        print("\nDados carregados:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        
        # Criar um backup do arquivo original
        backup_path = f"{file_path}.bak"
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"\nBackup criado: {backup_path}")
        
        # Reescrever o arquivo YAML
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
        
        print(f"\nArquivo reescrito: {file_path}")
        
        # Verificar se o arquivo foi reescrito corretamente
        with open(file_path, 'r', encoding='utf-8') as f:
            new_content = f.read()
        
        print(f"\nNovo conteúdo do arquivo ({len(new_content)} bytes):")
        print("-" * 50)
        print(new_content)
        print("-" * 50)
        
        # Criar uma versão JSON do arquivo para referência
        json_path = f"{os.path.splitext(file_path)[0]}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"\nVersão JSON criada: {json_path}")
        
        return True
    
    except Exception as e:
        print(f"Erro: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """
    Função principal.
    """
    # Definir o caminho do arquivo
    file_path = "config/chatwoot_mapping.yaml"
    
    # Se um caminho foi fornecido como argumento, usá-lo
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    
    print(f"Corrigindo arquivo YAML: {file_path}")
    
    # Corrigir o arquivo
    if fix_yaml_file(file_path):
        print("\n✅ Arquivo YAML corrigido com sucesso!")
    else:
        print("\n❌ Falha ao corrigir arquivo YAML")

if __name__ == "__main__":
    main()
