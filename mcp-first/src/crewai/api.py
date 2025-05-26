"""
API para o serviço CrewAI que gerencia as crews especializadas por canal.

Esta API serve como ponto de entrada para o processamento de mensagens
recebidas via webhook do Chatwoot, distribuindo-as para as crews apropriadas
com base no canal de origem.
"""

import os
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Depends, Header, Request
import uvicorn
from pydantic import BaseModel
import json
from dotenv import load_dotenv

# Importar as crews especializadas
from whatsapp_crew.main import WhatsAppCrew

# Carregar variáveis de ambiente
load_dotenv()

app = FastAPI(
    title="CrewAI API",
    description="API para gerenciamento de crews especializadas por canal",
    version="0.1.0",
)

# Modelo para mensagens recebidas via webhook
class WebhookMessage(BaseModel):
    account_id: str
    conversation_id: str
    message_type: str
    content: str
    source_id: str
    channel: str
    
    class Config:
        schema_extra = {
            "example": {
                "account_id": "tenant1",
                "conversation_id": "12345",
                "message_type": "incoming",
                "content": "Olá, gostaria de saber mais sobre o produto XYZ",
                "source_id": "whatsapp:+5511999999999",
                "channel": "whatsapp"
            }
        }

# Cache para instâncias de crews
crew_instances = {}

def get_crew_for_tenant(account_id: str, channel: str) -> Any:
    """
    Obtém ou cria uma instância da crew apropriada para o tenant e canal.
    
    Args:
        account_id: Identificador do tenant
        channel: Canal de comunicação (whatsapp, facebook, etc.)
    
    Returns:
        Instância da crew apropriada
    """
    cache_key = f"{account_id}_{channel}"
    
    if cache_key not in crew_instances:
        if channel == "whatsapp":
            crew_instances[cache_key] = WhatsAppCrew(account_id=account_id)
        elif channel == "facebook":
            # Implementar FacebookCrew no futuro
            raise HTTPException(status_code=501, detail="Facebook crew não implementada ainda")
        elif channel == "email":
            # Implementar EmailCrew no futuro
            raise HTTPException(status_code=501, detail="Email crew não implementada ainda")
        else:
            raise HTTPException(status_code=400, detail=f"Canal não suportado: {channel}")
    
    return crew_instances[cache_key]

@app.get("/")
async def root():
    """Endpoint raiz para verificar se o serviço está online."""
    return {"status": "online", "service": "CrewAI API"}

@app.post("/webhook")
async def webhook(message: WebhookMessage, request: Request):
    """
    Endpoint para receber mensagens do webhook do Chatwoot.
    
    Args:
        message: Dados da mensagem recebida
    
    Returns:
        Status do processamento
    """
    try:
        # Verificar se é uma mensagem de entrada
        if message.message_type != "incoming":
            return {"status": "ignored", "reason": "not an incoming message"}
        
        # Obter a crew apropriada para o tenant e canal
        crew = get_crew_for_tenant(message.account_id, message.channel)
        
        # Processar a mensagem
        response = crew.process_message(
            message=message.content,
            conversation_id=message.conversation_id
        )
        
        # Enviar a resposta
        sent = crew.send_response(response, message.conversation_id)
        
        return {
            "status": "processed" if sent else "error",
            "account_id": message.account_id,
            "conversation_id": message.conversation_id,
            "channel": message.channel
        }
    
    except Exception as e:
        # Registrar o erro
        print(f"Erro ao processar mensagem: {str(e)}")
        
        # Retornar erro
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Endpoint para verificação de saúde do serviço."""
    # Verificar conexão com os serviços MCP
    health_status = {
        "status": "healthy",
        "mcp_services": {
            "mcp_odoo": "unknown",
            "mcp_mongodb": "unknown",
            "mcp_qdrant": "unknown"
        }
    }
    
    # Implementar verificação de saúde dos serviços MCP
    # (será implementado no futuro)
    
    return health_status

@app.get("/config/{account_id}")
async def get_tenant_config(account_id: str):
    """
    Endpoint para obter a configuração de um tenant específico.
    
    Args:
        account_id: Identificador do tenant
    
    Returns:
        Configuração do tenant
    """
    try:
        # Criar uma instância temporária da WhatsAppCrew para acessar a configuração
        crew = WhatsAppCrew(account_id=account_id)
        
        # Retornar a configuração
        return {
            "status": "success",
            "account_id": account_id,
            "config": crew.config
        }
    
    except Exception as e:
        # Registrar o erro
        print(f"Erro ao obter configuração: {str(e)}")
        
        # Retornar erro
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # Iniciar o servidor
    uvicorn.run("api:app", host="0.0.0.0", port=8003, reload=True)
