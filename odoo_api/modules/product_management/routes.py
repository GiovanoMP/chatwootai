# -*- coding: utf-8 -*-

"""
Rotas para o módulo Product Management.
"""

import logging
import time
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Path, Request

from odoo_api.config.settings import settings
from odoo_api.core.exceptions import OdooAPIError, NotFoundError, ValidationError
from odoo_api.modules.product_management.schemas import (
    ProductBatchSyncRequest,
    ProductBatchSyncResponse,
    PriceUpdateRequest,
    PriceUpdateResponse,
    SyncStatusResponse,
    ProductListRequest,
    ProductListResponse,
    APIResponse,
)
from odoo_api.modules.product_management.services import get_product_management_service

logger = logging.getLogger(__name__)

# Criar router
router = APIRouter(
    prefix="/products",
    tags=["product-management"],
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

# Rota para sincronização em massa de produtos
@router.post(
    "/sync-batch",
    response_model=APIResponse,
    summary="Sincroniza múltiplos produtos com o banco de dados vetorial",
    description="Sincroniza múltiplos produtos com o banco de dados vetorial, gerando embeddings para busca semântica.",
)
async def sync_products_batch(
    request: Request,
    body: ProductBatchSyncRequest,
    account_id: str = Query(..., description="ID da conta"),
):
    """
    Sincroniza múltiplos produtos com o banco de dados vetorial.
    """
    try:
        service = get_product_management_service()
        
        # Sincronizar produtos
        result = await service.sync_products_batch(
            account_id=account_id,
            product_ids=body.product_ids,
            options=body.options,
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

# Rota para atualização de preços em massa
@router.post(
    "/update-prices",
    response_model=APIResponse,
    summary="Atualiza preços de múltiplos produtos",
    description="Atualiza preços de múltiplos produtos com base em um ajuste percentual ou fixo.",
)
async def update_prices_batch(
    request: Request,
    body: PriceUpdateRequest,
    account_id: str = Query(..., description="ID da conta"),
):
    """
    Atualiza preços de múltiplos produtos.
    """
    try:
        service = get_product_management_service()
        
        # Atualizar preços
        result = await service.update_prices_batch(
            account_id=account_id,
            product_ids=body.product_ids,
            adjustment=body.adjustment,
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

# Rota para verificação de status de sincronização
@router.get(
    "/sync-status",
    response_model=APIResponse,
    summary="Verifica o status de sincronização de produtos",
    description="Verifica o status de sincronização de produtos com o banco de dados vetorial.",
)
async def get_sync_status(
    request: Request,
    account_id: str = Query(..., description="ID da conta"),
    product_ids: Optional[str] = Query(None, description="Lista de IDs de produtos separados por vírgula"),
):
    """
    Verifica o status de sincronização de produtos.
    """
    try:
        service = get_product_management_service()
        
        # Converter string de IDs para lista de inteiros
        product_id_list = None
        if product_ids:
            try:
                product_id_list = [int(pid.strip()) for pid in product_ids.split(",") if pid.strip()]
            except ValueError:
                raise ValidationError("IDs de produtos inválidos. Forneça uma lista de inteiros separados por vírgula.")
        
        # Verificar status
        result = await service.get_sync_status(
            account_id=account_id,
            product_ids=product_id_list,
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

# Rota para listagem de produtos
@router.post(
    "/list",
    response_model=APIResponse,
    summary="Lista produtos com filtros",
    description="Lista produtos com filtros, paginação e ordenação.",
)
async def list_products(
    request: Request,
    body: ProductListRequest,
    account_id: str = Query(..., description="ID da conta"),
):
    """
    Lista produtos com filtros.
    """
    try:
        service = get_product_management_service()
        
        # Listar produtos
        result = await service.list_products(
            account_id=account_id,
            filter=body.filter,
            limit=body.limit,
            offset=body.offset,
            order_by=body.order_by,
            order_dir=body.order_dir,
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
