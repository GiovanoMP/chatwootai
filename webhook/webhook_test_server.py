"""
Servidor webhook simplificado para testes de integração com Chatwoot.

Este servidor recebe notificações do Chatwoot e apenas registra os eventos
para verificar se a integração está funcionando corretamente.
"""

import os
import logging
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import json
from datetime import datetime

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Cria a aplicação FastAPI
app = FastAPI(title="Chatwoot Webhook Test Server", description="Servidor de teste para webhooks do Chatwoot")

# Adiciona middleware CORS para permitir requisições de diferentes origens
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """
    Rota raiz para verificar se o servidor está funcionando.
    """
    return {
        "message": "Chatwoot Webhook Test Server",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """
    Endpoint de verificação de saúde (health check) para monitoramento.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/webhook")
async def webhook(request: Request):
    """
    Endpoint para receber webhooks do Chatwoot.
    
    Este endpoint é simplificado para testes e apenas registra os eventos recebidos.
    """
    try:
        # Registrar cabeçalhos para debug
        headers_dict = dict(request.headers)
        client_ip = request.client.host
        logger.info(f"Requisição recebida de {client_ip}")
        logger.info(f"Cabeçalhos: {headers_dict}")
        
        # Receber o corpo da requisição
        body = await request.json()
        event_type = body.get('event', 'unknown')
        logger.info(f"Evento recebido: {event_type}")
        logger.info(f"Corpo da requisição: {json.dumps(body, indent=2)}")
        
        # Processar diferentes tipos de eventos
        if event_type == 'message_created':
            message = body.get('message', {})
            content = message.get('content', '')
            sender = message.get('sender', {})
            logger.info(f"Nova mensagem: {content} de {sender.get('name', 'Desconhecido')}")
        
        elif event_type == 'conversation_created':
            conversation = body.get('conversation', {})
            logger.info(f"Nova conversa: {conversation.get('id')} - {conversation.get('status')}")
        
        elif event_type == 'conversation_status_changed':
            conversation = body.get('conversation', {})
            logger.info(f"Status da conversa alterado: {conversation.get('id')} - {conversation.get('status')}")
        
        return {
            "status": "success",
            "message": f"Evento {event_type} processado com sucesso",
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Erro ao processar webhook: {str(e)}")
        return {
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }

def main():
    """
    Função principal para iniciar o servidor.
    """
    port = int(os.getenv('WEBHOOK_PORT', 8001))
    logger.info(f"Iniciando servidor webhook na porta {port}")
    
    # URL completa do webhook para configuração no Chatwoot
    webhook_domain = os.getenv('WEBHOOK_DOMAIN', 'localhost')
    webhook_use_https = os.getenv('WEBHOOK_USE_HTTPS', 'false').lower() == 'true'
    protocol = 'https' if webhook_use_https else 'http'
    
    webhook_url = f"{protocol}://{webhook_domain}:{port}/webhook"
    logger.info(f"URL do webhook: {webhook_url}")
    
    # Inicia o servidor
    uvicorn.run(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()
