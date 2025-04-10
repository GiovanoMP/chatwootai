"""
Odoo MCP Server - MCP Server for Odoo Integration

Este módulo implementa um servidor MCP (Message Control Program) para integração com o Odoo,
permitindo que o ChatwootAI se conecte diretamente ao banco de dados Odoo.
"""

# Importação condicional do servidor MCP original (pode falhar se fastmcp não estiver instalado)
try:
    from .server import mcp
    has_fastmcp = True
except ImportError:
    has_fastmcp = False

# Importação do cliente Odoo
from .odoo_client import OdooClient, get_odoo_client, get_odoo_client_for_account

# A implementação simplificada do MCP foi removida
# Agora usamos apenas a implementação baseada em FastMCP

# Exportação de símbolos
if has_fastmcp:
    __all__ = ["mcp", "OdooClient", "get_odoo_client", "get_odoo_client_for_account"]
else:
    __all__ = ["OdooClient", "get_odoo_client", "get_odoo_client_for_account"]
