#!/usr/bin/env python3
"""
Teste do MCP-Odoo Simplificado

Este script testa a implementação simplificada do MCP-Odoo.
"""

import sys
import logging
import os
import yaml
from pathlib import Path

# Adicionar o diretório raiz ao PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configurar logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_odoo_mcp():
    """Testa a implementação simplificada do MCP-Odoo"""
    try:
        # Definir o domínio e account_id para teste
        domain_name = "furniture"
        account_id = "account_2"
        logger.info(f"Testando account: {account_id} (domínio: {domain_name})")
        
        # Carregar a configuração do account
        config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config")
        account_config_path = os.path.join(config_dir, "domains", domain_name, account_id, "config.yaml")
        
        if not os.path.exists(account_config_path):
            logger.error(f"Arquivo de configuração não encontrado: {account_config_path}")
            return False
            
        # Carregar a configuração
        with open(account_config_path, 'r') as f:
            account_config = yaml.safe_load(f)
            
        # Extrair configuração do MCP
        mcp_config = account_config.get("integrations", {}).get("mcp", {})
        if not mcp_config:
            logger.error(f"Configuração MCP não encontrada no arquivo {account_config_path}")
            return False
            
        logger.info(f"Configuração MCP encontrada: {mcp_config}")
        
        # Criar o MCP-Odoo simplificado
        from src.mcp_odoo.mcp_simple import create_odoo_mcp
        odoo_mcp = create_odoo_mcp(mcp_config.get("config", {}))
        logger.info(f"MCP-Odoo criado com sucesso: {odoo_mcp}")
        
        # Testar uma consulta simples
        logger.info("Testando consulta de produtos...")
        products = odoo_mcp.search_read(
            model_name="product.product",
            domain=[["active", "=", True]],
            fields=["name", "list_price", "default_code"],
            limit=5
        )
        
        # Verificar os resultados
        logger.info(f"Produtos encontrados: {len(products)}")
        for product in products:
            logger.info(f"  - {product['name']} (R$ {product['list_price']})")
            
        # Testar outras operações do MCP
        if products:
            # Testar leitura de um produto específico
            product_id = products[0]['id']
            logger.info(f"Testando leitura do produto {product_id}...")
            product = odoo_mcp.search_read(
                model_name="product.product",
                domain=[["id", "=", product_id]],
                fields=["name", "list_price", "default_code"]
            )
            logger.info(f"Produto lido: {product}")
            
        logger.info("Teste concluído com sucesso!")
        return True
        
    except Exception as e:
        logger.error(f"Erro durante o teste: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    test_odoo_mcp()
