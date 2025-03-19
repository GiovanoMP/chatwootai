#!/usr/bin/env python3

"""
Script para atualizar importações nos arquivos após a reorganização do projeto.
Este script procura ocorrências de importações antigas e as substitui pelas novas.
"""

import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Diretório raiz do projeto
PROJECT_ROOT = "/home/giovano/Projetos/Chatwoot V4"

# Mapeamentos de importações a serem atualizados
IMPORT_MAPPINGS = [
    # DataProxyAgent
    (r'from src\.agents\.data_proxy_agent import DataProxyAgent', 
     'from src.agents.core.data_proxy_agent import DataProxyAgent'),
    
    # Chatwoot Client
    (r'from src\.api\.chatwoot_client import ChatwootClient', 
     'from src.api.chatwoot.client import ChatwootClient'),
    (r'from src\.api\.chatwoot_client import ChatwootWebhookHandler', 
     'from src.api.chatwoot.client import ChatwootWebhookHandler'),
    
    # Chatwoot Legacy
    (r'from src\.api\.chatwoot import ChatwootClient', 
     'from src.api.chatwoot.legacy_client import ChatwootClient'),
    
    # Odoo Simulation
    (r'from src\.api\.odoo_simulation import', 
     'from src.api.erp.simulation.odoo import'),
    
    # Webhook Server
    (r'from src\.api\.webhook_server import', 
     'from src.webhook.server import'),
    
    # Webhook Handler
    (r'from src\.webhook\.webhook_handler import ChatwootWebhookHandler', 
     'from src.webhook.handler import ChatwootWebhookHandler'),
]

def update_file_imports(file_path: str) -> Tuple[int, List[str]]:
    """
    Atualiza as importações em um arquivo.
    
    Args:
        file_path: Caminho do arquivo a ser atualizado
        
    Returns:
        Tuple contendo o número de substituições e a lista de substituições realizadas
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        original_content = content
        changes = []
        
        for old_import, new_import in IMPORT_MAPPINGS:
            if re.search(old_import, content):
                content = re.sub(old_import, new_import, content)
                changes.append(f"{old_import} -> {new_import}")
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(content)
            
            return len(changes), changes
        
        return 0, []
    
    except Exception as e:
        print(f"Erro ao processar {file_path}: {e}")
        return 0, []

def scan_directory(directory: str) -> Dict[str, List[str]]:
    """
    Escaneia um diretório e atualiza importações em todos os arquivos Python.
    
    Args:
        directory: Diretório a ser escaneado
        
    Returns:
        Dicionário com arquivos atualizados e suas alterações
    """
    updated_files = {}
    
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                count, changes = update_file_imports(file_path)
                
                if count > 0:
                    updated_files[file_path] = changes
    
    return updated_files

def main():
    print(f"Atualizando importações em: {PROJECT_ROOT}")
    
    # Escaneia o diretório src para atualizações
    src_dir = os.path.join(PROJECT_ROOT, 'src')
    updated_files = scan_directory(src_dir)
    
    # Escaneia também outros arquivos Python na raiz
    for file in os.listdir(PROJECT_ROOT):
        if file.endswith('.py'):
            file_path = os.path.join(PROJECT_ROOT, file)
            count, changes = update_file_imports(file_path)
            
            if count > 0:
                updated_files[file_path] = changes
    
    # Reporta resultados
    print(f"\nAtualização concluída. {len(updated_files)} arquivos atualizados.")
    
    if updated_files:
        print("\nArquivos atualizados:")
        for file_path, changes in updated_files.items():
            rel_path = os.path.relpath(file_path, PROJECT_ROOT)
            print(f"\n{rel_path}:")
            for change in changes:
                print(f"  - {change}")
    
    print("\nObservação: Algumas importações podem precisar de ajustes manuais.")
    print("Verifique se o código está funcionando corretamente após as atualizações.")

if __name__ == "__main__":
    main()
