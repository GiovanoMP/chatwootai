#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para limpar arquivos de mapeamento desnecessários.
Este script remove os arquivos YAML e backups desnecessários,
mantendo apenas o arquivo JSON principal.
"""

import os
import json
import glob
import sys

def cleanup_mapping_files():
    """
    Remove arquivos de mapeamento desnecessários.
    """
    # Diretório de configuração
    config_dir = os.path.join(os.getcwd(), "config")
    
    # Verificar se o diretório existe
    if not os.path.exists(config_dir):
        print(f"Diretório de configuração não encontrado: {config_dir}")
        return False
    
    # Caminho para o arquivo JSON principal
    json_path = os.path.join(config_dir, "chatwoot_mapping.json")
    
    # Verificar se o arquivo JSON existe
    if not os.path.exists(json_path):
        print(f"Arquivo JSON principal não encontrado: {json_path}")
        return False
    
    # Ler o conteúdo do arquivo JSON
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            mapping_data = json.load(f)
        
        print(f"Arquivo JSON principal carregado: {json_path}")
        print(f"Conteúdo: {json.dumps(mapping_data, indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"Erro ao ler arquivo JSON: {str(e)}")
        return False
    
    # Listar todos os arquivos de mapeamento
    mapping_files = glob.glob(os.path.join(config_dir, "chatwoot_mapping*"))
    
    # Remover arquivos desnecessários
    for file_path in mapping_files:
        # Manter apenas o arquivo JSON principal
        if file_path != json_path:
            try:
                print(f"Removendo arquivo: {file_path}")
                os.remove(file_path)
            except Exception as e:
                print(f"Erro ao remover arquivo {file_path}: {str(e)}")
    
    # Verificar se a limpeza foi bem-sucedida
    remaining_files = glob.glob(os.path.join(config_dir, "chatwoot_mapping*"))
    
    print(f"\nArquivos restantes ({len(remaining_files)}):")
    for file_path in remaining_files:
        print(f"- {file_path}")
    
    return True

def main():
    """
    Função principal.
    """
    print("Iniciando limpeza de arquivos de mapeamento desnecessários...")
    
    if cleanup_mapping_files():
        print("\n✅ Limpeza concluída com sucesso!")
    else:
        print("\n❌ Falha na limpeza de arquivos")

if __name__ == "__main__":
    main()
