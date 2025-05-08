#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para resolver definitivamente o problema do arquivo chatwoot_mapping.yaml.

Este script:
1. Cria um novo arquivo chatwoot_mapping.yaml com o formato correto
2. Modifica o código que lê e escreve o arquivo para garantir compatibilidade
"""

import yaml
import os
import json
import shutil
import sys

def create_new_mapping_file():
    """
    Cria um novo arquivo chatwoot_mapping.yaml com o formato correto.
    """
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
    file_path = 'config/chatwoot_mapping.yaml'

    # Fazer backup do arquivo existente se necessário
    if os.path.exists(file_path):
        backup_path = f"{file_path}.backup"
        shutil.copy2(file_path, backup_path)
        print(f"Backup do arquivo original criado em: {backup_path}")

    # Salvar o arquivo
    with open(file_path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True)

    print(f"Novo arquivo criado: {file_path}")

    # Verificar o conteúdo do arquivo
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    print(f"Conteúdo do arquivo ({len(content)} bytes):")
    print("-" * 50)
    print(content)
    print("-" * 50)

    return True

def update_channel_mapping_handler():
    """
    Modifica o código que gera o arquivo chatwoot_mapping.yaml.
    """
    file_path = "src/webhook/channel_mapping_handler.py"

    # Verificar se o arquivo existe
    if not os.path.exists(file_path):
        print(f"Arquivo não encontrado: {file_path}")
        return False

    # Criar um backup do arquivo original
    backup_path = f"{file_path}.backup"
    shutil.copy2(file_path, backup_path)
    print(f"Backup do código criado em: {backup_path}")

    # Ler o conteúdo do arquivo
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Substituir o código que salva o arquivo
    old_code = """        # Salvar mapeamento atualizado
        try:
            # Primeiro, converter para string
            yaml_content = yaml.dump(mapping_data, default_flow_style=False, allow_unicode=True)
            
            # Salvar usando 'w' e especificando a codificação
            with open(mapping_path, 'w', encoding='utf-8') as f:
                f.write(yaml_content)
                
            logger.info(f"Arquivo salvo com sucesso usando método alternativo: {len(yaml_content)} bytes")
            
            # Criar uma cópia do arquivo para garantir que ele seja legível
            backup_path = f"{mapping_path}.bak"
            with open(backup_path, 'w', encoding='utf-8') as f:
                yaml.dump(mapping_data, f, default_flow_style=False, allow_unicode=True)
            logger.info(f"Backup do arquivo criado em: {backup_path}")
        except Exception as e:
            logger.error(f"Erro ao salvar arquivo YAML: {str(e)}")
            # Tentar método alternativo
            with open(mapping_path, 'w', encoding='utf-8') as f:
                yaml.dump(mapping_data, f, default_flow_style=False, allow_unicode=True)
            logger.info("Arquivo salvo usando método padrão após falha no método alternativo")"""

    new_code = """        # Salvar mapeamento atualizado de forma simplificada e robusta
        try:
            # Salvar o arquivo principal
            with open(mapping_path, 'w', encoding='utf-8') as f:
                yaml.dump(mapping_data, f, default_flow_style=False, allow_unicode=True)
            
            logger.info(f"Arquivo salvo com sucesso: {mapping_path}")
            
            # Criar uma cópia do arquivo para referência
            copy_path = f"{mapping_path}.copy"
            with open(copy_path, 'w', encoding='utf-8') as f:
                yaml.dump(mapping_data, f, default_flow_style=False, allow_unicode=True)
            
            # Criar um arquivo JSON equivalente para maior compatibilidade
            json_path = f"{os.path.splitext(mapping_path)[0]}.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(mapping_data, f, indent=2, ensure_ascii=False)
                
            logger.info(f"Cópias de backup criadas: {copy_path} e {json_path}")
        except Exception as e:
            logger.error(f"Erro ao salvar arquivo YAML: {str(e)}")
            # Tentar método alternativo com JSON
            try:
                json_path = f"{os.path.splitext(mapping_path)[0]}.json"
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(mapping_data, f, indent=2, ensure_ascii=False)
                logger.info(f"Arquivo JSON salvo como alternativa: {json_path}")
            except Exception as json_error:
                logger.error(f"Erro ao salvar arquivo JSON: {str(json_error)}")"""

    # Verificar se o código antigo existe no arquivo
    if old_code not in content:
        print("Código antigo não encontrado no arquivo. Tentando uma abordagem mais genérica...")
        
        # Tentar encontrar o bloco de código que salva o arquivo
        start_marker = "        # Salvar mapeamento atualizado"
        end_marker = "        logger.info(f\"Mapeamento YAML atualizado em {mapping_path}\")"
        
        start_index = content.find(start_marker)
        end_index = content.find(end_marker)
        
        if start_index != -1 and end_index != -1:
            # Extrair o bloco de código atual
            current_code = content[start_index:end_index].strip()
            print(f"Encontrado bloco de código para substituição ({len(current_code)} caracteres)")
            
            # Substituir o bloco de código
            new_content = content.replace(current_code, new_code)
            
            # Salvar o arquivo modificado
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
                
            print(f"Código modificado: {file_path}")
            return True
        else:
            print("Não foi possível encontrar o bloco de código para substituição")
            return False
    
    # Substituir o código
    new_content = content.replace(old_code, new_code)
    
    # Salvar o arquivo modificado
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
        
    print(f"Código modificado: {file_path}")
    return True

def update_init_file():
    """
    Modifica o código que lê o arquivo chatwoot_mapping.yaml durante a inicialização.
    """
    file_path = "src/webhook/init.py"
    
    # Verificar se o arquivo existe
    if not os.path.exists(file_path):
        print(f"Arquivo não encontrado: {file_path}")
        return False
        
    # Criar um backup do arquivo original
    backup_path = f"{file_path}.backup"
    shutil.copy2(file_path, backup_path)
    print(f"Backup do código criado em: {backup_path}")
    
    # Ler o conteúdo do arquivo
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Substituir o código que lê o arquivo
    old_code = """    mapping_path = os.getenv("CHATWOOT_MAPPING_PATH", "config/chatwoot_mapping.yaml")

    if os.path.exists(mapping_path):
        try:
            with open(mapping_path, 'r') as f:
                mapping_data = yaml.safe_load(f) or {}"""
                
    new_code = """    mapping_path = os.getenv("CHATWOOT_MAPPING_PATH", "config/chatwoot_mapping.yaml")
    json_mapping_path = os.path.splitext(mapping_path)[0] + ".json"

    # Tentar carregar o arquivo YAML ou JSON
    mapping_data = {}
    if os.path.exists(mapping_path):
        try:
            with open(mapping_path, 'r', encoding='utf-8') as f:
                mapping_data = yaml.safe_load(f) or {}
                logger.info(f"Arquivo YAML carregado: {mapping_path}")
        except Exception as yaml_error:
            logger.warning(f"Erro ao carregar arquivo YAML: {str(yaml_error)}")
            
            # Tentar carregar o arquivo JSON como alternativa
            if os.path.exists(json_mapping_path):
                try:
                    with open(json_mapping_path, 'r', encoding='utf-8') as f:
                        mapping_data = json.load(f) or {}
                    logger.info(f"Arquivo JSON carregado como alternativa: {json_mapping_path}")
                except Exception as json_error:
                    logger.warning(f"Erro ao carregar arquivo JSON: {str(json_error)}")
    elif os.path.exists(json_mapping_path):
        # Se o YAML não existe mas o JSON existe, usar o JSON
        try:
            with open(json_mapping_path, 'r', encoding='utf-8') as f:
                mapping_data = json.load(f) or {}
            logger.info(f"Arquivo JSON carregado: {json_mapping_path}")
        except Exception as e:
            logger.warning(f"Erro ao carregar arquivo JSON: {str(e)}")"""
            
    # Verificar se o código antigo existe no arquivo
    if old_code not in content:
        print("Código antigo não encontrado no arquivo init.py. Não foi possível modificar.")
        return False
        
    # Substituir o código
    new_content = content.replace(old_code, new_code)
    
    # Salvar o arquivo modificado
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
        
    print(f"Código init.py modificado: {file_path}")
    return True

if __name__ == "__main__":
    print("Iniciando correção do problema do arquivo chatwoot_mapping.yaml...")
    
    # Criar novo arquivo de mapeamento
    print("\n1. Criando novo arquivo de mapeamento...")
    if create_new_mapping_file():
        print("✅ Arquivo de mapeamento criado com sucesso!")
    else:
        print("❌ Falha ao criar arquivo de mapeamento.")
        
    # Modificar o código que gera o arquivo
    print("\n2. Modificando código que gera o arquivo...")
    if update_channel_mapping_handler():
        print("✅ Código de geração modificado com sucesso!")
    else:
        print("❌ Falha ao modificar código de geração.")
        
    # Modificar o código que lê o arquivo
    print("\n3. Modificando código que lê o arquivo...")
    if update_init_file():
        print("✅ Código de leitura modificado com sucesso!")
    else:
        print("❌ Falha ao modificar código de leitura.")
        
    print("\n✅ Processo concluído! Para aplicar as alterações, reinicie o servidor.")
    print("Comando para reiniciar: pkill -f \"python main.py\" && sleep 2 && screen -dmS server_session bash -c \"echo '🚀 Iniciando servidor unificado...'; python main.py 2>&1 | tee -a logs/server.log; echo 'Servidor encerrado. Pressione qualquer tecla para sair.'; read -n 1;\"")
