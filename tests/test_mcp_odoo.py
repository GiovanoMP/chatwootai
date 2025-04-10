#!/usr/bin/env python3
"""
Teste de Conexão com Odoo

Este script testa a conexão direta com o Odoo usando as credenciais do account_2.
"""

import sys
import logging
from pathlib import Path

# Adicionar o diretório raiz ao PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

import os
import yaml

# Configurar logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configurar logging para outros módulos
logging.getLogger('src.core.domain.domain_loader').setLevel(logging.DEBUG)
logging.getLogger('src.core.domain.domain_manager').setLevel(logging.DEBUG)
logging.getLogger('src.core.data_proxy_agent').setLevel(logging.DEBUG)

def test_odoo_connection():
    """Testa a conexão direta com o Odoo usando as credenciais do account_2"""
    try:
        # Verificar a estrutura de diretórios
        logger.info(f"Verificando estrutura de diretórios...")
        config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config")

        # Vamos acessar diretamente o arquivo de configuração do account

        # Definir o domínio e account_id para teste
        domain_name = "furniture"
        account_id = "account_2"
        logger.info(f"Testando account: {account_id} (domínio: {domain_name})")

        # Acessar diretamente o arquivo de configuração do account
        account_config_path = os.path.join(config_dir, "domains", domain_name, account_id, "config.yaml")
        logger.info(f"Verificando arquivo de configuração: {account_config_path}")

        if os.path.exists(account_config_path):
            logger.info(f"Arquivo de configuração encontrado para account {account_id}")
            with open(account_config_path, 'r') as f:
                account_config = yaml.safe_load(f)
                logger.info(f"Configuração do account: {account_config}")

                # Extrair configuração do MCP diretamente do arquivo
                mcp_config = account_config.get("integrations", {}).get("mcp", {})
                logger.info(f"Configuração do MCP: {mcp_config}")

                # Criar o cliente Odoo diretamente
                from src.mcp_odoo.odoo_client import OdooClient
                config = mcp_config.get("config", {})
                mcp_client = OdooClient(
                    url=config.get("url"),
                    db=config.get("db"),
                    username=config.get("username"),
                    password=config.get("password"),
                    timeout=config.get("timeout", 30),
                    verify_ssl=config.get("verify_ssl", True)
                )
                logger.info(f"Cliente Odoo criado: {mcp_client}")
        else:
            logger.error(f"Arquivo de configuração não encontrado para account {account_id}")
            return False

        # Testar uma consulta simples
        if mcp_client:
            logger.info("Testando consulta de produtos...")
            products = mcp_client.search_read(
                model_name="product.product",
                domain=[["active", "=", True]],
                fields=["name", "list_price", "default_code"],
                limit=5
            )
            logger.info(f"Produtos encontrados: {len(products)}")
            for product in products:
                logger.info(f"  - {product['name']} (R$ {product['list_price']})")

        logger.info("Teste concluído com sucesso!")
        return True

    except Exception as e:
        logger.error(f"Erro durante o teste: {str(e)}")
        return False

if __name__ == "__main__":
    test_mcp_odoo()
