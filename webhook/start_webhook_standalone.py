"""
Script simplificado para iniciar o servidor webhook sem todas as dependências.
Isso é útil para testar apenas a recepção e o logging dos webhooks.
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

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f"logs/webhook_standalone_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    ]
)

logger = logging.getLogger("webhook_standalone")

# Create FastAPI app
app = FastAPI(title="ChatwootAI Webhook Server (Standalone)")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Sem verificação de token para ser compatível com Chatwoot 4.0

@app.get("/")
async def root():
    """Endpoint raiz para verificar se o servidor está funcionando."""
    return {
        "status": "online", 
        "message": "Webhook server is running", 
        "timestamp": datetime.now().isoformat(),
        "version": "standalone-0.1"
    }

@app.get("/health")
async def health_check():
    """Endpoint para verificar a saúde do servidor."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/webhook")
async def webhook_endpoint(request: Request):
    """
    Endpoint para receber webhooks do Chatwoot.
    """
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
            
        # Simula processamento com base no tipo de evento
        response = {"status": "received", "event_type": event_type}
        
        # Calcula e registra o tempo de processamento
        processing_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"Tempo de processamento do webhook {event_type}: {processing_time:.3f}s")
        
        # Adiciona o tempo de processamento à resposta
        response["processing_time"] = f"{processing_time:.3f}s"
        
        return response
    
    except json.JSONDecodeError as e:
        # Log detalhado para erro de JSON inválido
        logger.error(f"Erro de JSON inválido no webhook: {e}")
        body = await request.body()
        logger.error(f"Corpo da requisição: {body.decode('utf-8', errors='replace')}")
        raise HTTPException(status_code=400, detail=f"JSON inválido: {str(e)}")
    
    except Exception as e:
        # Registra o erro de forma detalhada
        logger.error(f"Erro ao processar webhook: {type(e).__name__}: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        # Retorna um erro HTTP 500 com a mensagem de erro
        raise HTTPException(status_code=500, detail=str(e))

def start_webhook_server():
    """Inicia o servidor webhook."""
    # Obtenha a porta do ambiente ou use o padrão
    port = int(os.environ.get("WEBHOOK_PORT", 8001))
    # Obtenha o domínio do webhook do ambiente ou use localhost
    host = os.environ.get("WEBHOOK_HOST", "0.0.0.0")
    
    logger.info(f"Iniciando servidor webhook em http://{host}:{port}")
    logger.info(f"URL completa do webhook: http://{host}:{port}/webhook")
    
    # Cria diretório de logs se não existir
    os.makedirs("logs", exist_ok=True)
    
    # Inicia o servidor uvicorn
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    start_webhook_server()
