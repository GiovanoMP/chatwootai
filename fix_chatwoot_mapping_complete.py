#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para corrigir o arquivo chatwoot_mapping.yaml.
"""

import yaml
import os
import sys
import shutil

def fix_yaml_file(input_path):
    """
    Corrige o arquivo YAML para garantir que ele seja legível pelo editor.
    
    Args:
        input_path: Caminho do arquivo a ser corrigido
    """
    try:
        # Verificar se o arquivo existe
        if not os.path.exists(input_path):
            print(f"Arquivo não encontrado: {input_path}")
            return False
            
        # Criar um backup do arquivo original
        backup_path = f"{input_path}.original"
        shutil.copy2(input_path, backup_path)
        print(f"Backup criado em: {backup_path}")
        
        # Ler o conteúdo do arquivo
        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        print(f"Conteúdo do arquivo original ({len(content)} bytes):")
        print("-" * 50)
        print(content)
        print("-" * 50)
        
        # Carregar o YAML
        data = yaml.safe_load(content)
        
        # Criar um arquivo temporário
        temp_path = f"{input_path}.temp"
        with open(temp_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
            
        # Verificar se o arquivo temporário foi criado corretamente
        if not os.path.exists(temp_path):
            print(f"Falha ao criar arquivo temporário: {temp_path}")
            return False
            
        # Substituir o arquivo original pelo temporário
        os.remove(input_path)
        os.rename(temp_path, input_path)
        
        print(f"Arquivo corrigido: {input_path}")
        
        # Verificar o conteúdo do arquivo corrigido
        with open(input_path, 'r', encoding='utf-8') as f:
            new_content = f.read()
            
        print(f"Conteúdo do arquivo corrigido ({len(new_content)} bytes):")
        print("-" * 50)
        print(new_content)
        print("-" * 50)
        
        return True
        
    except Exception as e:
        print(f"Erro: {str(e)}")
        return False

# Modificar o código que gera o arquivo
def update_channel_mapping_handler():
    """
    Modifica o código que gera o arquivo chatwoot_mapping.yaml.
    """
    try:
        file_path = "src/webhook/channel_mapping_handler.py"
        
        # Verificar se o arquivo existe
        if not os.path.exists(file_path):
            print(f"Arquivo não encontrado: {file_path}")
            return False
            
        # Criar um backup do arquivo original
        backup_path = f"{file_path}.original"
        shutil.copy2(file_path, backup_path)
        print(f"Backup do código criado em: {backup_path}")
        
        # Ler o conteúdo do arquivo
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Substituir o código que salva o arquivo
        old_code = """        # Salvar mapeamento atualizado
        with open(mapping_path, 'w') as f:
            yaml.dump(mapping_data, f, default_flow_style=False)"""
            
        new_code = """        # Salvar mapeamento atualizado
        # Primeiro, converter para string
        yaml_content = yaml.dump(mapping_data, default_flow_style=False, allow_unicode=True)
        
        # Salvar usando 'w' e especificando a codificação
        with open(mapping_path, 'w', encoding='utf-8') as f:
            f.write(yaml_content)"""
            
        # Verificar se o código antigo existe no arquivo
        if old_code not in content:
            print("Código antigo não encontrado no arquivo. O arquivo já pode ter sido modificado.")
            return False
            
        # Substituir o código
        new_content = content.replace(old_code, new_code)
        
        # Salvar o arquivo modificado
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
            
        print(f"Código modificado: {file_path}")
        
        return True
        
    except Exception as e:
        print(f"Erro ao modificar código: {str(e)}")
        return False

if __name__ == "__main__":
    # Corrigir o arquivo YAML
    yaml_path = "config/chatwoot_mapping.yaml"
    
    print(f"Corrigindo arquivo YAML: {yaml_path}")
    if fix_yaml_file(yaml_path):
        print("Arquivo YAML corrigido com sucesso!")
    else:
        print("Falha ao corrigir arquivo YAML.")
        
    # Modificar o código
    print("\nModificando código que gera o arquivo...")
    if update_channel_mapping_handler():
        print("Código modificado com sucesso!")
    else:
        print("Falha ao modificar código.")
        
    print("\nPara aplicar as alterações no código, reinicie o servidor.")
