#!/usr/bin/env python3
"""
Webhook Forwarder para Chatwoot
Autor: Cascade AI
Data: 2025-03-19

Este servidor recebe webhooks do Chatwoot e os encaminha para o ambiente de desenvolvimento local.
"""

import os
import requests
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import json
import logging
from datetime import datetime

# Configurar logging
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("webhook_server")

# Configurações
FORWARD_URL = os.getenv('FORWARD_URL', 'https://example.ngrok-free.app/webhook')
AUTH_TOKEN = os.getenv('WEBHOOK_AUTH_TOKEN', 'efetivia_webhook_secret_token_2025')
PORT = int(os.getenv('WEBHOOK_PORT', 8002))

app = FastAPI(title="Chatwoot Webhook Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Estatísticas do servidor
server_stats = {
    "start_time": datetime.now().isoformat(),
    "requests_received": 0,
    "requests_forwarded": 0,
    "errors": 0,
    "last_request_time": None,
    "last_error_time": None,
    "last_error_message": None
}

@app.get("/")
async def root():
    """Endpoint raiz para verificar se o servidor está funcionando"""
    return {
        "status": "online",
        "message": "Chatwoot Webhook Server is running",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    """Endpoint para verificar a saúde do serviço"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "uptime": (datetime.now() - datetime.fromisoformat(server_stats["start_time"])).total_seconds(),
        "stats": server_stats
    }

@app.get("/stats")
async def get_stats():
    """Endpoint para obter estatísticas do servidor"""
    return server_stats

@app.post("/webhook")
async def webhook_handler(request: Request):
    """
    Endpoint principal que recebe webhooks do Chatwoot e os encaminha
    para o ambiente de desenvolvimento local
    """
    # Atualizar estatísticas
    server_stats["requests_received"] += 1
    server_stats["last_request_time"] = datetime.now().isoformat()
    
    try:
        # Registrar cabeçalhos para debug
        headers_dict = dict(request.headers)
        client_ip = request.client.host
        logger.info(f"Requisição recebida de {client_ip}")
        logger.debug(f"Cabeçalhos: {headers_dict}")
        
        # Receber o corpo da requisição
        body = await request.json()
        event_type = body.get('event', 'unknown')
        logger.info(f"Evento recebido: {event_type}")
        logger.debug(f"Corpo da requisição: {json.dumps(body)[:500]}...")
        
        # Encaminhar o evento para o ambiente local
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {AUTH_TOKEN}'
        }
        
        logger.info(f"Encaminhando para: {FORWARD_URL}")
        response = requests.post(FORWARD_URL, json=body, headers=headers, timeout=10)
        logger.info(f"Resposta: {response.status_code}")
        
        # Atualizar estatísticas
        server_stats["requests_forwarded"] += 1
        
        return {
            "status": "success", 
            "message": "Webhook processado com sucesso",
            "event_type": event_type,
            "forward_status": response.status_code,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        # Atualizar estatísticas de erro
        server_stats["errors"] += 1
        server_stats["last_error_time"] = datetime.now().isoformat()
        server_stats["last_error_message"] = str(e)
        
        logger.error(f"Erro ao processar webhook: {str(e)}")
        return {
            "status": "error", 
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }

if __name__ == "__main__":
    logger.info(f"Iniciando servidor webhook na porta {PORT}")
    logger.info(f"URL de encaminhamento: {FORWARD_URL}")
    logger.info(f"Nível de log: {LOG_LEVEL}")
    uvicorn.run(app, host="0.0.0.0", port=PORT)
