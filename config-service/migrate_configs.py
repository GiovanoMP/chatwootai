#!/usr/bin/env python3
"""
Script para migrar configurações existentes para o microserviço de configuração.

Este script percorre os diretórios de configuração e envia as configurações
para o microserviço de configuração.
"""

import os
import yaml
import argparse
import requests
import logging
from pathlib import Path
from dotenv import load_dotenv

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()

def get_config_service_url():
    """Obtém a URL do serviço de configuração."""
    return os.getenv("CONFIG_SERVICE_URL", "http://localhost:8000")

def get_config_service_api_key():
    """Obtém a chave de API do serviço de configuração."""
    return os.getenv("CONFIG_SERVICE_API_KEY", "development-api-key")

def check_service_health():
    """Verifica a saúde do serviço de configuração."""
    try:
        response = requests.get(
            f"{get_config_service_url()}/health",
            headers={"X-API-Key": get_config_service_api_key()},
            timeout=2
        )
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Erro ao verificar saúde do serviço: {str(e)}")
        return False

def send_config(tenant_id, domain, config_type, yaml_content):
    """
    Envia uma configuração para o serviço de configuração.
    
    Args:
        tenant_id: ID do tenant
        domain: Domínio do tenant
        config_type: Tipo de configuração
        yaml_content: Conteúdo YAML da configuração
        
    Returns:
        True se a configuração foi enviada com sucesso, False caso contrário
    """
    try:
        url = f"{get_config_service_url()}/configs/{tenant_id}/{domain}/{config_type}"
        headers = {
            "Content-Type": "application/json",
            "X-API-Key": get_config_service_api_key()
        }
        
        response = requests.post(
            url,
            json={"yaml_content": yaml_content},
            headers=headers,
            timeout=5
        )
        
        if response.status_code in (200, 201):
            logger.info(f"Configuração enviada com sucesso: {tenant_id}/{domain}/{config_type}")
            return True
        else:
            logger.error(f"Erro ao enviar configuração: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"Erro ao enviar configuração: {str(e)}")
        return False

def migrate_configs(config_dir, dry_run=False):
    """
    Migra as configurações existentes para o microserviço de configuração.
    
    Args:
        config_dir: Diretório base de configurações
        dry_run: Se True, apenas simula a migração sem enviar as configurações
        
    Returns:
        Número de configurações migradas com sucesso
    """
    if not os.path.exists(config_dir):
        logger.error(f"Diretório de configurações não encontrado: {config_dir}")
        return 0
    
    success_count = 0
    error_count = 0
    
    # Percorrer domínios
    for domain in os.listdir(config_dir):
        domain_dir = os.path.join(config_dir, domain)
        if not os.path.isdir(domain_dir):
            continue
        
        # Percorrer tenants
        for tenant_id in os.listdir(domain_dir):
            tenant_dir = os.path.join(domain_dir, tenant_id)
            if not os.path.isdir(tenant_dir):
                continue
            
            # Percorrer arquivos de configuração
            for file_name in os.listdir(tenant_dir):
                if not file_name.endswith(".yaml"):
                    continue
                
                file_path = os.path.join(tenant_dir, file_name)
                config_type = os.path.splitext(file_name)[0]
                
                # Carregar conteúdo YAML
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        yaml_content = f.read()
                except Exception as e:
                    logger.error(f"Erro ao ler arquivo {file_path}: {str(e)}")
                    error_count += 1
                    continue
                
                # Enviar configuração para o serviço
                if dry_run:
                    logger.info(f"[DRY RUN] Enviando configuração: {tenant_id}/{domain}/{config_type}")
                    success_count += 1
                else:
                    if send_config(tenant_id, domain, config_type, yaml_content):
                        success_count += 1
                    else:
                        error_count += 1
    
    logger.info(f"Migração concluída: {success_count} configurações migradas com sucesso, {error_count} erros")
    return success_count

def migrate_chatwoot_mapping(mapping_file, dry_run=False):
    """
    Migra o mapeamento Chatwoot para o microserviço de configuração.
    
    Args:
        mapping_file: Caminho para o arquivo de mapeamento
        dry_run: Se True, apenas simula a migração sem enviar o mapeamento
        
    Returns:
        True se o mapeamento foi migrado com sucesso, False caso contrário
    """
    if not os.path.exists(mapping_file):
        logger.error(f"Arquivo de mapeamento não encontrado: {mapping_file}")
        return False
    
    # Carregar conteúdo YAML
    try:
        with open(mapping_file, 'r', encoding='utf-8') as f:
            yaml_content = f.read()
    except Exception as e:
        logger.error(f"Erro ao ler arquivo {mapping_file}: {str(e)}")
        return False
    
    # Enviar mapeamento para o serviço
    if dry_run:
        logger.info(f"[DRY RUN] Enviando mapeamento Chatwoot: {mapping_file}")
        return True
    else:
        try:
            url = f"{get_config_service_url()}/mapping/"
            headers = {
                "Content-Type": "application/json",
                "X-API-Key": get_config_service_api_key()
            }
            
            # Converter YAML para JSON
            mapping_data = yaml.safe_load(yaml_content)
            
            response = requests.post(
                url,
                json={"mapping_data": mapping_data},
                headers=headers,
                timeout=5
            )
            
            if response.status_code in (200, 201):
                logger.info(f"Mapeamento Chatwoot enviado com sucesso: {mapping_file}")
                return True
            else:
                logger.error(f"Erro ao enviar mapeamento Chatwoot: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Erro ao enviar mapeamento Chatwoot: {str(e)}")
            return False

def main():
    """Função principal."""
    parser = argparse.ArgumentParser(description="Migra configurações existentes para o microserviço de configuração")
    parser.add_argument("--config-dir", default="config/domains", help="Diretório base de configurações")
    parser.add_argument("--mapping-file", default="config/chatwoot_mapping.yaml", help="Arquivo de mapeamento Chatwoot")
    parser.add_argument("--dry-run", action="store_true", help="Apenas simula a migração sem enviar as configurações")
    args = parser.parse_args()
    
    # Verificar saúde do serviço
    if not args.dry_run and not check_service_health():
        logger.error("Serviço de configuração não está saudável. Abortando migração.")
        return
    
    # Migrar configurações
    migrate_configs(args.config_dir, args.dry_run)
    
    # Migrar mapeamento Chatwoot
    migrate_chatwoot_mapping(args.mapping_file, args.dry_run)

if __name__ == "__main__":
    main()
