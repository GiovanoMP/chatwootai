"""
Módulo de healthcheck padronizado para MCP-Chatwoot
"""

from fastapi import FastAPI
from common.chatwoot import ChatwootClient
import os

def register_health_endpoint(app: FastAPI):
    """
    Registra o endpoint /health na aplicação FastAPI
    
    Args:
        app: Aplicação FastAPI onde o endpoint será registrado
    """
    chatwoot_client = ChatwootClient()
    
    @app.get("/health")
    async def health_check():
        """
        Endpoint de healthcheck padronizado
        Retorna: {"status": "ok"} se o serviço estiver saudável
        """
        try:
            # Verificar conexão com o Chatwoot
            chatwoot_status = await chatwoot_client.check_connection()
            
            return {
                "status": "ok" if chatwoot_status else "error",
                "service": os.environ.get("MCP_SERVICE_NAME", "mcp-chatwoot"),
                "chatwoot": "connected" if chatwoot_status else "disconnected"
            }
        except Exception as e:
            return {
                "status": "error",
                "service": os.environ.get("MCP_SERVICE_NAME", "mcp-chatwoot"),
                "message": str(e)
            }
