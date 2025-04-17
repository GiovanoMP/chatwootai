"""
Rotas para o servidor webhook.

Este módulo contém as rotas FastAPI para o servidor webhook,
incluindo o endpoint principal para receber webhooks do Chatwoot.
"""

import logging
import json
from datetime import datetime
from fastapi import APIRouter, Request, HTTPException, Depends
from typing import Dict, Any

from src.webhook.webhook_handler import ChatwootWebhookHandler
from src.webhook.init import get_webhook_handler

# Configurar logging
logger = logging.getLogger(__name__)

# Criar router
router = APIRouter(tags=["webhook"])

@router.get("/")
async def root():
    """Endpoint raiz para verificar se o servidor está funcionando"""
    return {
        "status": "online",
        "message": "Servidor webhook do Chatwoot está funcionando!",
        "timestamp": str(datetime.now())
    }

@router.get("/health")
async def health_check():
    """Endpoint para verificar a saúde do servidor"""
    return {
        "status": "healthy",
        "timestamp": str(datetime.now())
    }

@router.post("/webhook")
@router.post("/")
async def webhook(request: Request, handler: ChatwootWebhookHandler = Depends(get_webhook_handler)):
    """Endpoint para receber webhooks do Chatwoot"""
    try:
        # Registra chegada do webhook com timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        logger.info(f"📩 [{timestamp}] Webhook recebido do Chatwoot")

        # Registra headers da requisição para debug
        headers = dict(request.headers)
        logger.debug(f"Headers da requisição: {json.dumps(headers, indent=2)}")

        # Obtém dados do webhook
        data = await request.json()

        # Log completo dos dados para arquivo
        with open('logs/last_webhook_payload.json', 'w') as f:
            json.dump(data, f, indent=2)

        # Log resumido para console
        logger.debug(f"Dados do webhook: {json.dumps(data, indent=2)[:1000]}...")

        # Verifica o tipo de evento
        event_type = data.get("event")
        if not event_type:
            logger.warning("⚠️ Webhook sem tipo de evento")
            raise HTTPException(status_code=400, detail="Tipo de evento não especificado")

        # Extrai informações importantes para log
        message_info = ""
        if event_type == "message_created":
            message = data.get("message", {})
            conversation = data.get("conversation", {})
            contact = data.get("contact", {})
            message_info = f"ID: {message.get('id')}, Conversa: {conversation.get('id')}, Contato: {contact.get('name')}"
            logger.info(f"📨 Mensagem: '{message.get('content', '')[:100]}...'")

        # Processa o webhook
        logger.info(f"⚙️ Processando evento: {event_type} | {message_info}")
        response = await handler.process_webhook(data)

        # Retorna a resposta do processamento com detalhes
        logger.info(f"✅ Webhook processado com sucesso: {json.dumps(response)}")
        return response

    except Exception as e:
        logger.error(f"❌ Erro ao processar webhook: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao processar webhook: {str(e)}")
