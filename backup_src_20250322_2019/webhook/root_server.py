"""
Servidor webhook completo para o ChatwootAI.

Este script inicia um servidor webhook que recebe webhooks do Chatwoot
e os processa usando o sistema de agentes.
"""

import os
import sys
import logging
import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import json
from datetime import datetime
from typing import Dict, Any, Optional
import asyncio
import traceback
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

# Configura logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f"logs/webhook_server_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    ]
)

logger = logging.getLogger("webhook_server")

# Importa o handler de webhook
try:
    from src.webhook.handler import ChatwootWebhookHandler
    logger.info("Handler de webhook importado com sucesso")
except Exception as e:
    logger.error(f"Erro ao importar handler de webhook: {str(e)}")
    logger.error(traceback.format_exc())
    ChatwootWebhookHandler = None

# Carrega configuração do ambiente
config = {
    "chatwoot_api_key": os.environ.get("CHATWOOT_API_KEY", ""),
    "chatwoot_base_url": os.environ.get("CHATWOOT_BASE_URL", ""),
    "chatwoot_account_id": int(os.environ.get("CHATWOOT_ACCOUNT_ID", "1")),
    "active_domain": os.environ.get("ACTIVE_DOMAIN", "cosmetics"),
    "channel_mapping": {
        "1": "whatsapp",  # Mapeamento de inbox_id para tipos de canais
        "2": "instagram",
        "3": "web"
    }
}

# Cria FastAPI app
app = FastAPI(title="ChatwootAI Webhook Server")

# Adiciona CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializa o handler de webhook
webhook_handler = None

@app.on_event("startup")
async def startup_event():
    """Evento executado na inicialização do servidor."""
    logger.info("Inicializando servidor webhook...")
    
    global webhook_handler
    
    try:
        # Inicializa o handler de webhook
        if ChatwootWebhookHandler:
            webhook_handler = ChatwootWebhookHandler(config=config)
            logger.info("Handler de webhook inicializado com sucesso")
        else:
            logger.error("ChatwootWebhookHandler não disponível")
    except Exception as e:
        logger.error(f"Erro ao inicializar handler de webhook: {str(e)}")
        logger.error(traceback.format_exc())

@app.get("/")
async def root():
    """Endpoint raiz para verificar se o servidor está funcionando."""
    return {
        "status": "online", 
        "message": "ChatwootAI Webhook server is running", 
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "handler_initialized": webhook_handler is not None
    }

@app.get("/health")
async def health_check():
    """Endpoint para verificação de saúde do servidor."""
    if webhook_handler:
        # Inclui estatísticas do handler
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "stats": webhook_handler.stats if hasattr(webhook_handler, "stats") else {}
        }
    else:
        return {
            "status": "degraded",
            "timestamp": datetime.now().isoformat(),
            "reason": "Webhook handler not initialized"
        }

@app.post("/webhook")
async def webhook_endpoint(request: Request):
    """
    Endpoint para receber webhooks do Chatwoot.
    """
    # Verifica se o handler foi inicializado
    if not webhook_handler:
        logger.error("Webhook handler não inicializado")
        raise HTTPException(status_code=503, detail="Webhook handler not initialized")
    
    try:
        # Log detalhado dos headers
        headers = dict(request.headers)
        logger.info(f"Headers recebidos: {json.dumps(headers, indent=2)}")
        
        # Marca o início do processamento para medir performance
        start_time = datetime.now()
        
        # Obtém os dados do webhook (formato JSON)
        data = await request.json()
        
        # Registra o recebimento do webhook no log com detalhes
        event_type = data.get('event')
        timestamp_received = datetime.now().isoformat()
        logger.info(f"Webhook recebido: {event_type} de {request.client.host} em {timestamp_received}")
        
        # Log detalhado do payload para depuração
        try:
            # Formata o JSON para melhor legibilidade
            logger.debug(f"Payload do webhook: {json.dumps(data, indent=2, ensure_ascii=False)}")
        except Exception as log_err:
            logger.warning(f"Erro ao logar payload completo: {log_err}")
        
        # Processa o webhook usando o handler
        result = await webhook_handler.process_webhook(data)
        
        # Calcula e registra o tempo de processamento
        processing_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"Tempo de processamento do webhook {event_type}: {processing_time:.3f}s")
        
        # Adiciona o tempo de processamento ao resultado
        result["processing_time"] = f"{processing_time:.3f}s"
        
        return result
    
    except json.JSONDecodeError as e:
        # Log detalhado para erro de JSON inválido
        logger.error(f"Erro de JSON inválido no webhook: {e}")
        body = await request.body()
        logger.error(f"Corpo da requisição: {body.decode('utf-8', errors='replace')}")
        raise HTTPException(status_code=400, detail=f"JSON inválido: {str(e)}")
    
    except Exception as e:
        # Registra o erro de forma detalhada
        logger.error(f"Erro ao processar webhook: {type(e).__name__}: {str(e)}")
        logger.error(traceback.format_exc())
        # Retorna um erro HTTP 500 com a mensagem de erro
        raise HTTPException(status_code=500, detail=str(e))

def start_webhook_server():
    """Inicia o servidor webhook."""
    # Cria diretório de logs se não existir
    os.makedirs("logs", exist_ok=True)
    
    # Obtém a porta do ambiente ou usa o padrão
    port = int(os.environ.get("WEBHOOK_PORT", 8001))
    # Obtém o domínio do webhook do ambiente ou usa localhost
    host = os.environ.get("WEBHOOK_HOST", "0.0.0.0")
    
    logger.info(f"Iniciando servidor webhook em http://{host}:{port}")
    logger.info(f"URL completa do webhook: http://{host}:{port}/webhook")
    
    # Inicia o servidor uvicorn
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    start_webhook_server()
