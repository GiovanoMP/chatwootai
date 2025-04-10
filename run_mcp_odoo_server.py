#!/usr/bin/env python3
"""
Script para iniciar o servidor MCP-Odoo
"""

import sys
import os
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Adicionar o diretório atual ao path para importar os módulos locais
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    # Importar o servidor MCP-Odoo
    logger.info("Importando o servidor MCP-Odoo...")
    from src.mcp_odoo import mcp
    logger.info("Servidor MCP-Odoo importado com sucesso!")

    # Iniciar o servidor
    logger.info("Iniciando o servidor MCP-Odoo...")
    # O método run() aceita apenas o argumento 'transport', que pode ser 'stdio' ou 'sse'
    mcp.run(transport='sse')
except ImportError as e:
    logger.error(f"Erro ao importar o servidor MCP-Odoo: {e}")
    logger.error("Verifique se todas as dependências estão instaladas.")
    sys.exit(1)
except Exception as e:
    logger.error(f"Erro ao iniciar o servidor MCP-Odoo: {e}")
    sys.exit(1)
