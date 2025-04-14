#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Ponto de entrada principal para a API Odoo.
"""

import logging
from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time
import uuid

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Criar aplicação FastAPI
app = FastAPI(
    title="Odoo API",
    description="API para integração com Odoo",
    version="0.1.0",
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

        # Retornar resposta de erro
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An internal server error occurred",
                },
                "meta": {
                    "request_id": request_id,
                },
            },
        )

# Middleware para verificação de account_id
@app.middleware("http")
async def verify_account_id(request: Request, call_next):
    # Verificar se é uma rota de API (ignorar rotas de documentação, etc.)
    if request.url.path.startswith("/api/"):
        account_id = request.query_params.get("account_id")
        if not account_id:
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

        # Armazenar account_id no estado da requisição
        request.state.account_id = account_id

    return await call_next(request)

# Rota de healthcheck
@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "version": app.version,
        "timestamp": time.time(),
    }

# Importar e incluir rotas dos módulos
from odoo_api.modules.semantic_product.routes import router as semantic_product_router
from odoo_api.modules.product_management.routes import router as product_management_router
from odoo_api.modules.business_rules.routes import router as business_rules_router

# Incluir rotas
app.include_router(semantic_product_router, prefix="/api/v1")
app.include_router(product_management_router, prefix="/api/v1")
app.include_router(business_rules_router, prefix="/api/v1")

# Inicialização da aplicação
@app.on_event("startup")
async def startup_event():
    logger.info("Starting Odoo API")
    # Inicializar conexões, etc.

# Finalização da aplicação
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down Odoo API")
    # Fechar conexões, etc.

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
