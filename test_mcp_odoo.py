#!/usr/bin/env python3
"""
Script para testar o MCP-Odoo com a configuração correta
"""

import sys
import os
import logging
import yaml
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Adicionar o diretório atual ao path para importar os módulos locais
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    # Importar os módulos necessários
    logger.info("Importando os módulos necessários...")
    from src.mcp_odoo import OdooClient, get_odoo_client_for_account
    from src.core.domain.domain_manager import DomainManager
    from src.core.domain.domain_loader import DomainLoader
    logger.info("Módulos importados com sucesso!")
    
    # Criar um arquivo de configuração de domínio temporário para teste
    logger.info("Criando arquivo de configuração de domínio temporário...")
    config_dir = Path("@config")
    if not config_dir.exists():
        config_dir.mkdir(parents=True)
        
    domain_dir = config_dir / "furniture"
    if not domain_dir.exists():
        domain_dir.mkdir(parents=True)
        
    # Criar arquivo de configuração do domínio
    domain_config = {
        "name": "Móveis",
        "description": "Domínio de móveis para teste",
        "domain": "furniture",
        "integrations": {
            "odoo": {
                "url": "http://localhost:8069",
                "db": "account_2",
                "username": "giovano@sprintia.com.br",
                "password": "0701Gio***",
                "timeout": 30,
                "verify_ssl": False
            },
            "mcp": {
                "type": "odoo-mcp",
                "config": {
                    "url": "http://localhost:8069",
                    "db": "account_2",
                    "username": "giovano@sprintia.com.br",
                    "password": "0701Gio***",
                    "timeout": 30,
                    "verify_ssl": False
                }
            }
        }
    }
    
    with open(domain_dir / "domain.yaml", "w") as f:
        yaml.dump(domain_config, f)
    logger.info("Arquivo de configuração de domínio criado com sucesso!")
    
    # Criar arquivo de configuração da conta
    account_config = {
        "name": "Móveis Elegantes",
        "description": "Loja de móveis elegantes e modernos",
        "domain": "furniture",
        "account_id": "account_2",
        "integrations": {
            "odoo": {
                "url": "http://localhost:8069",
                "db": "account_2",
                "username": "giovano@sprintia.com.br",
                "password": "0701Gio***",
                "timeout": 30,
                "verify_ssl": False
            },
            "mcp": {
                "type": "odoo-mcp",
                "config": {
                    "url": "http://localhost:8069",
                    "db": "account_2",
                    "username": "giovano@sprintia.com.br",
                    "password": "0701Gio***",
                    "timeout": 30,
                    "verify_ssl": False
                }
            }
        }
    }
    
    with open(domain_dir / "account_2.yaml", "w") as f:
        yaml.dump(account_config, f)
    logger.info("Arquivo de configuração de conta criado com sucesso!")
    
    # Inicializar o DomainLoader e DomainManager
    logger.info("Inicializando o DomainLoader e DomainManager...")
    domain_loader = DomainLoader(config_dir=str(config_dir))
    domain_manager = DomainManager(domain_loader=domain_loader)
    logger.info("DomainLoader e DomainManager inicializados com sucesso!")
    
    # Obter cliente Odoo para um domínio e conta específicos
    logger.info("Obtendo cliente Odoo para o domínio 'furniture' e conta 'account_2'...")
    client = get_odoo_client_for_account(
        domain_name="furniture",
        account_id="account_2",
        domain_manager=domain_manager
    )
    
    if client:
        logger.info(f"Cliente Odoo obtido com sucesso: {client}")
        
        # Testar a conexão com o Odoo
        logger.info("Testando a conexão com o Odoo...")
        
        # Buscar parceiros
        logger.info("Buscando parceiros...")
        partner_ids = client.search(
            model_name='res.partner',
            domain=[],
            limit=5
        )
        logger.info(f"IDs de parceiros encontrados: {partner_ids}")
        
        # Ler dados dos parceiros
        if partner_ids:
            partners = client.read_records(
                model_name='res.partner',
                ids=partner_ids,
                fields=['name', 'email', 'phone']
            )
            logger.info(f"Número de parceiros encontrados: {len(partners)}")
            for partner in partners:
                logger.info(f"Parceiro: {partner['id']} - {partner.get('name', 'Sem nome')}")
        else:
            logger.info("Nenhum parceiro encontrado.")
        
        # Buscar produtos
        logger.info("Buscando produtos...")
        product_ids = client.search(
            model_name='product.product',
            domain=[],
            limit=5
        )
        logger.info(f"IDs de produtos encontrados: {product_ids}")
        
        # Ler dados dos produtos
        if product_ids:
            products = client.read_records(
                model_name='product.product',
                ids=product_ids,
                fields=['name', 'list_price', 'default_code']
            )
            logger.info(f"Número de produtos encontrados: {len(products)}")
            for product in products:
                logger.info(f"Produto: {product['id']} - {product.get('name', 'Sem nome')} - Preço: {product.get('list_price', 0.0)}")
        else:
            logger.info("Nenhum produto encontrado.")
    else:
        logger.error("Não foi possível obter o cliente Odoo.")
    
    logger.info("Teste concluído com sucesso!")
except ImportError as e:
    logger.error(f"Erro ao importar os módulos necessários: {e}")
    logger.error("Verifique se todas as dependências estão instaladas.")
    sys.exit(1)
except Exception as e:
    logger.error(f"Erro ao testar o MCP-Odoo: {e}")
    sys.exit(1)
