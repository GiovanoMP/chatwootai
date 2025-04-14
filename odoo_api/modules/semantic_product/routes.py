# -*- coding: utf-8 -*-

"""
Rotas para o módulo Semantic Product.
"""

import logging
import time
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Path, Request

from odoo_api.config.settings import settings
from odoo_api.core.exceptions import OdooAPIError, NotFoundError, ValidationError
from odoo_api.modules.semantic_product.schemas import (
    ProductDescriptionRequest,
    ProductDescriptionResponse,
    ProductSyncRequest,
    ProductSyncResponse,
    ProductSearchRequest,
    ProductSearchResponse,
    APIResponse,
)
from odoo_api.modules.semantic_product.services import get_semantic_product_service

logger = logging.getLogger(__name__)

# Criar router
router = APIRouter(
    prefix="/products",
    tags=["semantic-product"],
)

# Função para construir resposta padrão
def build_response(
    success: bool,
    data: Any = None,
    error: Dict[str, Any] = None,
    meta: Dict[str, Any] = None,
) -> APIResponse:
    """
    Constrói uma resposta padrão da API.
    
    Args:
        success: Indica se a operação foi bem-sucedida
        data: Dados da resposta
        error: Detalhes do erro, se houver
        meta: Metadados da resposta
    
    Returns:
        Resposta padrão da API
    """
    if meta is None:
        meta = {}
    
    meta["timestamp"] = time.time()
    
    return APIResponse(
        success=success,
        data=data,
        error=error,
        meta=meta,
    )

# Rota para gerar descrição de produto
@router.post(
    "/{product_id}/description",
    response_model=APIResponse,
    summary="Gera uma descrição semântica para um produto",
    description="Gera uma descrição semântica para um produto específico, incluindo características e casos de uso.",
)
async def generate_product_description(
    request: Request,
    product_id: int = Path(..., description="ID do produto"),
    body: ProductDescriptionRequest = None,
    account_id: str = Query(..., description="ID da conta"),
):
    """
    Gera uma descrição semântica para um produto.
    """
    try:
        service = get_semantic_product_service()
        
        # Usar opções do corpo da requisição ou padrão
        options = body.options if body else None
        
        # Gerar descrição
        result = await service.generate_product_description(
            account_id=account_id,
            product_id=product_id,
            options=options,
        )
        
        # Construir resposta
        return build_response(
            success=True,
            data=result,
            meta={"request_id": getattr(request.state, "request_id", "unknown")},
        )
    
    except NotFoundError as e:
        logger.warning(f"Product not found: {e}")
        raise HTTPException(
            status_code=404,
            detail={"code": e.code, "message": e.message, "details": e.details},
        )
    
    except ValidationError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(
            status_code=422,
            detail={"code": e.code, "message": e.message, "details": e.details},
        )
    
    except OdooAPIError as e:
        logger.error(f"Odoo API error: {e}")
        raise HTTPException(
            status_code=500,
            detail={"code": e.code, "message": e.message, "details": e.details},
        )
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=500,
            detail={"code": "INTERNAL_SERVER_ERROR", "message": str(e)},
        )

# Rota para sincronizar produto com banco de dados vetorial
@router.post(
    "/{product_id}/sync",
    response_model=APIResponse,
    summary="Sincroniza um produto com o banco de dados vetorial",
    description="Sincroniza um produto com o banco de dados vetorial, gerando embeddings para busca semântica.",
)
async def sync_product(
    request: Request,
    product_id: int = Path(..., description="ID do produto"),
    body: ProductSyncRequest = None,
    account_id: str = Query(..., description="ID da conta"),
):
    """
    Sincroniza um produto com o banco de dados vetorial.
    """
    try:
        service = get_semantic_product_service()
        
        # Obter parâmetros do corpo da requisição
        description = None
        skip_odoo_update = False
        
        if body:
            description = body.description
            skip_odoo_update = body.skip_odoo_update
        
        # Sincronizar produto
        result = await service.sync_product_to_vector_db(
            account_id=account_id,
            product_id=product_id,
            description=description,
            skip_odoo_update=skip_odoo_update,
        )
        
        # Construir resposta
        return build_response(
            success=True,
            data=result,
            meta={"request_id": getattr(request.state, "request_id", "unknown")},
        )
    
    except NotFoundError as e:
        logger.warning(f"Product not found: {e}")
        raise HTTPException(
            status_code=404,
            detail={"code": e.code, "message": e.message, "details": e.details},
        )
    
    except ValidationError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(
            status_code=422,
            detail={"code": e.code, "message": e.message, "details": e.details},
        )
    
    except OdooAPIError as e:
        logger.error(f"Odoo API error: {e}")
        raise HTTPException(
            status_code=500,
            detail={"code": e.code, "message": e.message, "details": e.details},
        )
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=500,
            detail={"code": "INTERNAL_SERVER_ERROR", "message": str(e)},
        )

# Rota para busca semântica de produtos
@router.post(
    "/search",
    response_model=APIResponse,
    summary="Realiza uma busca semântica de produtos",
    description="Realiza uma busca semântica de produtos com base em uma consulta em linguagem natural.",
)
async def search_products(
    request: Request,
    body: ProductSearchRequest,
    account_id: str = Query(..., description="ID da conta"),
):
    """
    Realiza uma busca semântica de produtos.
    """
    try:
        service = get_semantic_product_service()
        
        # Realizar busca
        result = await service.search_products(
            account_id=account_id,
            query=body.query,
            limit=body.limit,
            filters=body.filters.dict() if body.filters else None,
        )
        
        # Construir resposta
        return build_response(
            success=True,
            data=result,
            meta={"request_id": getattr(request.state, "request_id", "unknown")},
        )
    
    except ValidationError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(
            status_code=422,
            detail={"code": e.code, "message": e.message, "details": e.details},
        )
    
    except OdooAPIError as e:
        logger.error(f"Odoo API error: {e}")
        raise HTTPException(
            status_code=500,
            detail={"code": e.code, "message": e.message, "details": e.details},
        )
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=500,
            detail={"code": "INTERNAL_SERVER_ERROR", "message": str(e)},
        )
