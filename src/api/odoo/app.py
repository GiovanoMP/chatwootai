"""
Aplicação FastAPI para integração com o Odoo.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging

# Configurar logging
logger = logging.getLogger(__name__)

# Criar aplicação
app = FastAPI(
    title="Odoo Integration API",
    description="API para integração com o Odoo",
    version="1.0.0"
)

# Adicionar middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rota raiz
@app.get("/")
async def root():
    """Endpoint raiz para verificar se a API está funcionando."""
    logger.info("Acessando endpoint raiz da API Odoo")
    return {
        "message": "Odoo Integration API",
        "version": "1.0.0",
        "status": "operational"
    }

# Rota de saúde
@app.get("/health")
async def health():
    """Endpoint de verificação de saúde."""
    logger.info("Verificação de saúde da API Odoo")
    return {"status": "healthy"}

# Rota de webhook para receber notificações do Odoo
@app.post("/webhook")
async def webhook(payload: dict):
    """
    Endpoint para receber webhooks do Odoo.
    
    Este endpoint pode ser usado pelo módulo ai_credentials_manager
    para enviar notificações ao sistema de IA.
    """
    logger.info(f"Webhook recebido do Odoo: {payload}")
    
    # Aqui você pode adicionar lógica para processar o webhook
    # Por exemplo, encaminhar para o sistema de IA
    
    return {"status": "received", "message": "Webhook processado com sucesso"}

# Log de inicialização
logger.info("API Odoo inicializada com sucesso")
