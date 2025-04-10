#!/usr/bin/env python3
"""
Script para testar o servidor MCP-Odoo
"""

import sys
import os

# Adicionar o diretório atual ao path para importar os módulos locais
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from src.mcp_odoo.server import mcp
    print("Servidor MCP-Odoo importado com sucesso!")
    
    # Iniciar o servidor
    print("Iniciando o servidor MCP-Odoo...")
    mcp.run(host="127.0.0.1", port=8080)
except ImportError as e:
    print(f"Erro ao importar o servidor MCP-Odoo: {e}")
    print("Verifique se todas as dependências estão instaladas.")
    sys.exit(1)
except Exception as e:
    print(f"Erro ao iniciar o servidor MCP-Odoo: {e}")
    sys.exit(1)
