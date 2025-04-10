#!/usr/bin/env python3
"""
Script para testar a integração entre o DataProxyAgent e o MCP-Odoo
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
    from src.core.data_proxy_agent import DataProxyAgent
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

    # Inicializar o DataProxyAgent
    logger.info("Inicializando o DataProxyAgent...")
    data_proxy_agent = DataProxyAgent(domain_manager=domain_manager)
    logger.info("DataProxyAgent inicializado com sucesso!")

    # Testar a obtenção da configuração do MCP
    logger.info("Testando a obtenção da configuração do MCP...")
    mcp_config = data_proxy_agent.get_mcp_config("furniture", "account_2")
    logger.info(f"Configuração do MCP obtida com sucesso: {mcp_config}")

    # Testar a criação do cliente MCP
    logger.info("Testando a criação do cliente MCP...")
    mcp_client = data_proxy_agent.create_mcp_client("furniture", "account_2")
    logger.info(f"Cliente MCP criado com sucesso: {mcp_client}")

    # Testar a consulta de produtos
    logger.info("Testando a consulta de produtos...")
    products = data_proxy_agent.query_products("", domain_name="furniture", account_id="account_2")
    logger.info(f"Consulta de produtos realizada com sucesso: {products}")

    # Exibir os produtos encontrados
    if products["success"]:
        logger.info(f"Número de produtos encontrados: {products['count']}")
        for product in products["results"]:
            logger.info(f"Produto: {product['id']} - {product.get('name', 'Sem nome')}")
    else:
        logger.error(f"Erro na consulta de produtos: {products.get('error', 'Erro desconhecido')}")

    logger.info("Teste concluído com sucesso!")
except ImportError as e:
    logger.error(f"Erro ao importar os módulos necessários: {e}")
    logger.error("Verifique se todas as dependências estão instaladas.")
    sys.exit(1)
except Exception as e:
    logger.error(f"Erro ao testar a integração: {e}")
    sys.exit(1)
