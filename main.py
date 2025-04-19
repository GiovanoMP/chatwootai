#!/usr/bin/env python3
# -*- coding: utf-8 -*-


# Porta do servidor: 8001

"""
Servidor Unificado para o Sistema Integrado Odoo-AI.

Este servidor unifica o sistema de webhook do Chatwoot e a API Odoo
em um único aplicativo FastAPI, mantendo a separação lógica entre
os diferentes tipos de endpoints.
"""

import os
import logging
import time
import uuid
from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from datetime import datetime
from contextlib import asynccontextmanager

# Carregar variáveis de ambiente
load_dotenv()

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Função de inicialização
@asynccontextmanager
async def lifespan(_: FastAPI):
    # Código de inicialização
    logger.info("🚀 Iniciando Sistema Integrado Odoo-AI")
    yield
    # Código de finalização
    logger.info("Desligando Sistema Integrado Odoo-AI")

# Criar aplicação FastAPI
app = FastAPI(
    title="Sistema Integrado Odoo-AI",
    description="API unificada para webhook do Chatwoot e integração com Odoo",
    version="1.0.0",
    lifespan=lifespan,
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especificar origens permitidas
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware para logging e request_id
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()

    # Gerar request_id único
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id

    # Log de início de requisição
    logger.info(f"Request started: {request.method} {request.url.path} - Request ID: {request_id}")

    # Processar requisição
    try:
        response = await call_next(request)
        process_time = time.time() - start_time

        # Adicionar headers de resposta
        response.headers["X-Process-Time"] = str(process_time)
        response.headers["X-Request-ID"] = request_id

        # Log de fim de requisição
        logger.info(f"Request completed: {request.method} {request.url.path} - Status: {response.status_code} - Time: {process_time:.4f}s - Request ID: {request_id}")

        return response
    except Exception as e:
        # Log de erro
        logger.error(f"Request failed: {request.method} {request.url.path} - Error: {str(e)} - Request ID: {request_id}")
        process_time = time.time() - start_time

        # Retornar erro
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": str(e),
                },
                "meta": {
                    "request_id": request_id,
                    "process_time": process_time,
                },
            },
        )

# Importar o middleware de autenticação
from odoo_api.core.auth_middleware import AuthMiddleware

# Adicionar o middleware de autenticação
app.add_middleware(AuthMiddleware)

# Middleware para compatibilidade com código legado que espera account_id na URL
@app.middleware("http")
async def legacy_account_id_middleware(request: Request, call_next):
    # Verificar se é uma rota de API (ignorar rotas de documentação, etc.)
    if request.url.path.startswith("/api/v1/") and not request.url.path.startswith("/api/v1/credentials"):
        # Se o account_id já foi definido pelo middleware de autenticação, usar esse valor
        if hasattr(request.state, "account_id"):
            # Nada a fazer, o middleware de autenticação já definiu o account_id
            pass
        else:
            # Para compatibilidade com código legado, verificar se o account_id está na URL
            account_id = request.query_params.get("account_id")
            if account_id:
                # Armazenar account_id no estado da requisição
                request.state.account_id = account_id
                logger.warning(f"Usando account_id da URL (legado): {account_id}")
            else:
                # Se não tiver account_id na URL e não foi autenticado, retornar erro
                return JSONResponse(
                    status_code=400,
                    content={
                        "success": False,
                        "error": {
                            "code": "MISSING_ACCOUNT_ID",
                            "message": "account_id is required",
                        },
                        "meta": {
                            "request_id": getattr(request.state, "request_id", "unknown"),
                        },
                    },
                )

    return await call_next(request)

# Rota raiz
@app.get("/")
async def root():
    """Endpoint raiz para verificar se o servidor está funcionando"""
    return {
        "status": "online",
        "message": "Sistema Integrado Odoo-AI",
        "version": app.version,
        "timestamp": str(datetime.now())
    }

# Rota de healthcheck
@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "version": app.version,
        "timestamp": time.time(),
    }

# Importar rotas do webhook
try:
    from src.webhook.routes import router as webhook_router
    from src.webhook.webhook_handler import ChatwootWebhookHandler
    from src.webhook.init import get_webhook_handler

    # Incluir rotas do webhook
    app.include_router(webhook_router, prefix="/webhook")

    # Adicionar rota direta para o webhook (para compatibilidade com configurações antigas)
    @app.post("/webhook")
    async def webhook_direct(request: Request, handler: ChatwootWebhookHandler = Depends(get_webhook_handler)):
        """Endpoint direto para receber webhooks do Chatwoot (para compatibilidade)"""
        # Redirecionar para a implementação em src.webhook.routes
        from src.webhook.routes import webhook as webhook_handler
        return await webhook_handler(request, handler)

    logger.info("✅ Rotas do webhook carregadas com sucesso")
except ImportError as e:
    logger.warning(f"⚠️ Não foi possível carregar as rotas do webhook: {str(e)}")

# Importar rotas da API Odoo
try:
    from odoo_api.modules.semantic_product.routes import router as semantic_product_router
    app.include_router(semantic_product_router, prefix="/api/v1")
    logger.info("✅ Rotas do módulo semantic_product carregadas com sucesso")
except ImportError as e:
    logger.warning(f"⚠️ Não foi possível carregar as rotas do módulo semantic_product: {str(e)}")

try:
    from odoo_api.modules.product_management.routes import router as product_management_router
    app.include_router(product_management_router, prefix="/api/v1")
    logger.info("✅ Rotas do módulo product_management carregadas com sucesso")
except ImportError as e:
    logger.warning(f"⚠️ Não foi possível carregar as rotas do módulo product_management: {str(e)}")

try:
    from odoo_api.modules.business_rules.routes import router as business_rules_router
    app.include_router(business_rules_router, prefix="/api/v1")
    logger.info("✅ Rotas do módulo business_rules carregadas com sucesso")
except ImportError as e:
    logger.warning(f"⚠️ Não foi possível carregar as rotas do módulo business_rules: {str(e)}")

try:
    from odoo_api.modules.credentials.routes import router as credentials_router
    app.include_router(credentials_router, prefix="/api/v1")
    logger.info("✅ Rotas do módulo credentials carregadas com sucesso")
except ImportError as e:
    logger.warning(f"⚠️ Não foi possível carregar as rotas do módulo credentials: {str(e)}")

if __name__ == "__main__":
    import uvicorn

    # Usar valores de .env ou padrões
    port = int(os.getenv("SERVER_PORT", "8001"))  # Alterado para 8001 para compatibilidade com Ngrok e VPS
    host = os.getenv("SERVER_HOST", "0.0.0.0")

    print("\n" + "="*70)
    print("🚀 INICIANDO SISTEMA INTEGRADO ODOO-AI")
    print("="*70)
    print(f"📡 Servidor rodando em: http://{host}:{port}")
    print(f"🔗 Use ngrok para expor este servidor para a internet:")
    print(f"   ngrok http {port}")
    print("="*70 + "\n")

    uvicorn.run("main:app", host=host, port=port, reload=False)
