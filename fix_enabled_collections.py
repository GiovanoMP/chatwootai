#!/usr/bin/env python3
"""
Script para verificar e corrigir o problema com a seção enabled_collections.

Este script:
1. Verifica o payload enviado pelo módulo business_rules
2. Verifica a conversão YAML para JSON no config-service
3. Corrige o problema se necessário
"""

import os
import sys
import yaml
import json
import requests
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()

# Configurações do banco de dados
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5433")
DB_NAME = os.getenv("DB_NAME", "config_service")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

# Configurações do serviço
CONFIG_SERVICE_URL = os.getenv("CONFIG_SERVICE_URL", "http://localhost:8000")
CONFIG_SERVICE_API_KEY = os.getenv("CONFIG_SERVICE_API_KEY", "development-api-key")

def connect_to_db():
    """Conecta ao banco de dados PostgreSQL."""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            cursor_factory=RealDictCursor
        )
        logger.info("Conexão com o banco de dados estabelecida com sucesso!")
        return conn
    except Exception as e:
        logger.error(f"Erro ao conectar ao banco de dados: {str(e)}")
        return None

def check_config_in_db(conn, tenant_id, domain, config_type):
    """Verifica a configuração no banco de dados."""
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, tenant_id, domain, config_type, version, yaml_content, json_data
            FROM crew_configurations
            WHERE tenant_id = %s AND domain = %s AND config_type = %s
            ORDER BY version DESC
            LIMIT 1
        """, (tenant_id, domain, config_type))

        config = cursor.fetchone()
        cursor.close()

        if config:
            logger.info(f"Configuração encontrada: tenant_id={tenant_id}, domain={domain}, config_type={config_type}, version={config['version']}")
            return config
        else:
            logger.warning(f"Configuração não encontrada: tenant_id={tenant_id}, domain={domain}, config_type={config_type}")
            return None
    except Exception as e:
        logger.error(f"Erro ao verificar configuração no banco de dados: {str(e)}")
        return None

def check_enabled_collections_in_config(config):
    """Verifica se a seção enabled_collections está presente na configuração."""
    if not config:
        return False

    # Verificar no JSON
    json_data = config['json_data']
    if 'enabled_collections' in json_data:
        logger.info(f"Seção enabled_collections encontrada no JSON: {json_data['enabled_collections']}")
        return True

    # Verificar no YAML
    try:
        yaml_data = yaml.safe_load(config['yaml_content'])
        if yaml_data and 'enabled_collections' in yaml_data:
            logger.info(f"Seção enabled_collections encontrada no YAML: {yaml_data['enabled_collections']}")
            return True
    except Exception as e:
        logger.error(f"Erro ao carregar YAML: {str(e)}")

    logger.warning("Seção enabled_collections não encontrada na configuração")
    return False

def fix_enabled_collections(conn, config, tenant_id, domain):
    """Corrige a seção enabled_collections na configuração."""
    if not config:
        logger.error("Configuração não fornecida para correção")
        return False

    try:
        # Carregar o YAML
        yaml_data = yaml.safe_load(config['yaml_content'])

        # Verificar se já existe a seção enabled_collections
        if 'enabled_collections' in yaml_data:
            logger.info("Seção enabled_collections já existe no YAML, não é necessário corrigir")
            return True

        # Não é necessário que exista a seção company_metadata para adicionar enabled_collections
        # Vamos apenas verificar se yaml_data é um dicionário válido
        if not isinstance(yaml_data, dict):
            logger.warning("YAML não é um dicionário válido, não é possível corrigir")
            return False

        # Obter as coleções habilitadas do arquivo local
        local_config_path = f"config/domains/{domain}/{tenant_id}/config.yaml"
        if os.path.exists(local_config_path):
            with open(local_config_path, 'r') as f:
                local_yaml = yaml.safe_load(f)
                if local_yaml and 'enabled_collections' in local_yaml:
                    enabled_collections = local_yaml['enabled_collections']
                    logger.info(f"Coleções habilitadas obtidas do arquivo local: {enabled_collections}")

                    # Adicionar a seção enabled_collections ao YAML
                    yaml_data['enabled_collections'] = enabled_collections

                    # Converter de volta para YAML
                    new_yaml_content = yaml.dump(yaml_data, default_flow_style=False)

                    # Atualizar no banco de dados
                    cursor = conn.cursor()
                    cursor.execute("""
                        UPDATE crew_configurations
                        SET yaml_content = %s, json_data = %s
                        WHERE id = %s
                    """, (new_yaml_content, json.dumps(yaml_data), config['id']))
                    conn.commit()
                    cursor.close()

                    logger.info(f"Configuração atualizada com sucesso: id={config['id']}")
                    return True
                else:
                    logger.warning("Seção enabled_collections não encontrada no arquivo local")
        else:
            logger.warning(f"Arquivo local não encontrado: {local_config_path}")

        # Se não conseguir obter do arquivo local, usar valores padrão
        enabled_collections = ['business_rules', 'products_informations']
        logger.info(f"Usando coleções habilitadas padrão: {enabled_collections}")

        # Adicionar a seção enabled_collections ao YAML
        yaml_data['enabled_collections'] = enabled_collections

        # Converter de volta para YAML
        new_yaml_content = yaml.dump(yaml_data, default_flow_style=False)

        # Atualizar no banco de dados
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE crew_configurations
            SET yaml_content = %s, json_data = %s
            WHERE id = %s
        """, (new_yaml_content, json.dumps(yaml_data), config['id']))
        conn.commit()
        cursor.close()

        logger.info(f"Configuração atualizada com sucesso: id={config['id']}")
        return True
    except Exception as e:
        logger.error(f"Erro ao corrigir seção enabled_collections: {str(e)}")
        return False

def main():
    """Função principal."""
    # Conectar ao banco de dados
    conn = connect_to_db()
    if not conn:
        logger.error("Não foi possível conectar ao banco de dados")
        return

    try:
        # Obter todos os tenants
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT tenant_id, domain
            FROM crew_configurations
            WHERE config_type = 'config'
        """)

        tenants = cursor.fetchall()
        cursor.close()

        if not tenants:
            logger.warning("Nenhum tenant encontrado")
            return

        logger.info(f"Encontrados {len(tenants)} tenants")

        # Verificar e corrigir cada tenant
        for tenant in tenants:
            tenant_id = tenant['tenant_id']
            domain = tenant['domain']

            logger.info(f"Verificando tenant: {tenant_id}, domain: {domain}")

            # Verificar configuração
            config = check_config_in_db(conn, tenant_id, domain, 'config')

            # Verificar se a seção enabled_collections está presente
            if not check_enabled_collections_in_config(config):
                logger.info(f"Corrigindo seção enabled_collections para tenant: {tenant_id}, domain: {domain}")
                if fix_enabled_collections(conn, config, tenant_id, domain):
                    logger.info(f"Seção enabled_collections corrigida com sucesso para tenant: {tenant_id}, domain: {domain}")
                else:
                    logger.error(f"Falha ao corrigir seção enabled_collections para tenant: {tenant_id}, domain: {domain}")
            else:
                logger.info(f"Seção enabled_collections já existe para tenant: {tenant_id}, domain: {domain}")
    finally:
        conn.close()
        logger.info("Conexão com o banco de dados fechada")

if __name__ == "__main__":
    main()
