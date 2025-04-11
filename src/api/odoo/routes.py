"""
Rotas da API REST para integração com o módulo Odoo semantic_product_description.

Este módulo define as rotas da API REST para receber webhooks do módulo Odoo,
permitindo a sincronização de produtos e a geração de descrições semânticas.

Autor: Augment Agent
Data: 26/03/2025
"""

from fastapi import APIRouter, Depends, HTTPException, Header, status
from typing import Dict, Any, Optional, List

from .schemas import (
    WebhookRequest,
    WebhookResponse,
    TaskStatusResponse,
    TaskType,
    TaskStatus,
    ProductMetadata
)
from .api import verify_token, enqueue_task, get_account_id_from_token

# Criar router
router = APIRouter(prefix="/api/v1/webhook", tags=["webhook"])

@router.post("/product/sync", response_model=WebhookResponse)
async def sync_product(
    request: WebhookRequest,
    authorized: bool = Depends(verify_token)
):
    """
    Endpoint para sincronização de produtos.
    
    Recebe metadados de um produto do Odoo e enfileira uma tarefa para
    sincronização com o Qdrant.
    
    Args:
        request: Dados do webhook
        authorized: Resultado da verificação do token
        
    Returns:
        WebhookResponse: Resposta do webhook
    """
    try:
        # Extrair metadados
        metadata = request.metadata
        params = request.params
        
        # Verificar se os parâmetros necessários estão presentes
        if "product_id" not in params:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Parâmetro obrigatório 'product_id' não fornecido"
            )
        
        # Extrair account_id do token
        account_id = metadata.get("account_id") or get_account_id_from_token(
            Header(...).get("Authorization", "")
        )
        
        # Enfileirar tarefa para processamento assíncrono
        task_data = {
            "account_id": account_id,
            "product_id": params["product_id"],
            "metadata": metadata,
            "params": params
        }
        request_id = enqueue_task(TaskType.SYNC_PRODUCT, task_data)
        
        # Retornar resposta
        return WebhookResponse(
            success=True,
            message="Produto enfileirado para sincronização",
            request_id=request_id
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno: {str(e)}"
        )

@router.post("/product/description", response_model=WebhookResponse)
async def generate_description(
    request: WebhookRequest,
    authorized: bool = Depends(verify_token)
):
    """
    Endpoint para geração de descrição de produto.
    
    Recebe metadados de um produto do Odoo e enfileira uma tarefa para
    geração de descrição semântica.
    
    Args:
        request: Dados do webhook
        authorized: Resultado da verificação do token
        
    Returns:
        WebhookResponse: Resposta do webhook
    """
    try:
        # Extrair metadados
        metadata = request.metadata
        params = request.params
        
        # Verificar se os parâmetros necessários estão presentes
        if "product_id" not in params:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Parâmetro obrigatório 'product_id' não fornecido"
            )
        
        # Extrair account_id do token
        account_id = metadata.get("account_id") or get_account_id_from_token(
            Header(...).get("Authorization", "")
        )
        
        # Enfileirar tarefa para processamento assíncrono
        task_data = {
            "account_id": account_id,
            "product_id": params["product_id"],
            "metadata": metadata,
            "params": params
        }
        request_id = enqueue_task(TaskType.GENERATE_DESCRIPTION, task_data)
        
        # Retornar resposta
        return WebhookResponse(
            success=True,
            message="Produto enfileirado para geração de descrição",
            request_id=request_id
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno: {str(e)}"
        )

@router.get("/status/{request_id}", response_model=TaskStatusResponse)
async def check_status(
    request_id: str,
    authorized: bool = Depends(verify_token)
):
    """
    Endpoint para verificar o status de uma tarefa.
    
    Args:
        request_id: ID da tarefa
        authorized: Resultado da verificação do token
        
    Returns:
        TaskStatusResponse: Status da tarefa
    """
    # TODO: Implementar verificação real do status da tarefa
    # Por enquanto, retornar um status fixo
    return TaskStatusResponse(
        request_id=request_id,
        status=TaskStatus.PENDING,
        message="Tarefa em processamento"
    )

@router.delete("/product/{product_id}", response_model=WebhookResponse)
async def delete_product(
    product_id: int,
    authorized: bool = Depends(verify_token),
    authorization: str = Header(...)
):
    """
    Endpoint para exclusão de produto.
    
    Recebe o ID de um produto do Odoo e enfileira uma tarefa para
    exclusão do produto no Qdrant.
    
    Args:
        product_id: ID do produto
        authorized: Resultado da verificação do token
        authorization: Token de autorização
        
    Returns:
        WebhookResponse: Resposta do webhook
    """
    try:
        # Extrair account_id do token
        account_id = get_account_id_from_token(authorization)
        
        # Enfileirar tarefa para processamento assíncrono
        task_data = {
            "account_id": account_id,
            "product_id": product_id
        }
        request_id = enqueue_task(TaskType.DELETE_PRODUCT, task_data)
        
        # Retornar resposta
        return WebhookResponse(
            success=True,
            message=f"Produto {product_id} enfileirado para exclusão",
            request_id=request_id
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno: {str(e)}"
        )
