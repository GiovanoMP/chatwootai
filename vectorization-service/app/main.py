"""
Aplicação principal do serviço de vetorização.
"""

import logging
import os
from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time
import uuid
from typing import Callable

from app.core.config import settings
from app.core.exceptions import VectorizationServiceError
from app.core.logging_config import setup_logging
from app.services.redis_service import RedisService
from app.services.embedding_service import EmbeddingService
from app.services.vector_service import VectorService
from app.services.enrichment_service import EnrichmentService
from app.services.cache_service import CacheService
from app.api import business_rules, scheduling_rules, support_documents

# Configurar logging
logger = setup_logging()

# Loggers específicos
sync_logger = logging.getLogger("vectorization.sync")
embedding_logger = logging.getLogger("vectorization.embedding")
critical_logger = logging.getLogger("vectorization.critical")

# Criar aplicação FastAPI
app = FastAPI(
    title="Vectorization Service",
    description="Serviço para vetorização de regras de negócio e documentos de suporte",
    version="1.0.0",
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especificar origens permitidas
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware para logging de requisições
@app.middleware("http")
async def log_requests(request: Request, call_next: Callable):
    """Middleware para logging de requisições."""
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id

    start_time = time.time()

    logger.info(f"Request {request_id} started: {request.method} {request.url.path}")

    try:
        response = await call_next(request)

        process_time = time.time() - start_time
        logger.info(f"Request {request_id} completed: {response.status_code} ({process_time:.4f}s)")

        return response
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"Request {request_id} failed: {str(e)} ({process_time:.4f}s)")
        raise

# Tratamento de exceções
@app.exception_handler(VectorizationServiceError)
async def vectorization_service_exception_handler(request: Request, exc: VectorizationServiceError):
    """Handler para exceções do serviço de vetorização."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "code": exc.code,
                "message": exc.message
            }
        }
    )

# Importar dependências do módulo dependencies
from app.core.dependencies import (
    get_redis_service,
    get_embedding_service,
    get_vector_service,
    get_enrichment_service,
    get_cache_service
)

# Registrar dependências na aplicação
app.dependency_overrides[RedisService] = get_redis_service
app.dependency_overrides[EmbeddingService] = get_embedding_service
app.dependency_overrides[VectorService] = get_vector_service
app.dependency_overrides[EnrichmentService] = get_enrichment_service
app.dependency_overrides[CacheService] = get_cache_service

# Incluir routers
app.include_router(business_rules.router)
app.include_router(scheduling_rules.router)
app.include_router(support_documents.router)

# Rota de verificação de saúde
@app.get("/health", tags=["health"])
async def health_check():
    """Verifica a saúde do serviço."""
    return {"status": "ok", "version": "1.0.0"}

# Rota raiz
@app.get("/", tags=["root"])
async def root():
    """Rota raiz do serviço."""
    return {
        "name": "Vectorization Service",
        "version": "1.0.0",
        "description": "Serviço para vetorização de regras de negócio e documentos de suporte"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
