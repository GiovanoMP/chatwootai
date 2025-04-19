# -*- coding: utf-8 -*-

"""
Rotas para o módulo Business Rules.
"""

import logging
import time
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query, Path, Request, File, UploadFile
import base64

from odoo_api.core.exceptions import OdooAPIError, NotFoundError, ValidationError
from odoo_api.modules.business_rules.schemas import (
    BusinessRuleRequest,
    TemporaryRuleRequest,
    APIResponse,
    DocumentUploadRequest,
    CustomerServiceStyleConfig,
    GreetingStyleConfig,
    FarewellStyleConfig,
    EmojisStyleConfig,
    ToneStyleConfig,
)
from odoo_api.modules.business_rules.services import get_business_rules_service
from odoo_api.modules.business_rules.style_manager import get_customer_service_style_manager

logger = logging.getLogger(__name__)

# Criar router
router = APIRouter(
    prefix="/business-rules",
    tags=["business-rules"],
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

# IMPORTANTE: Definir rotas específicas ANTES das rotas com parâmetros de caminho

# Rota para busca semântica de regras
@router.get(
    "/semantic-search",
    response_model=APIResponse,
    summary="Busca semântica de regras",
    description="Busca regras de negócio semanticamente similares a uma consulta.",
)
async def search_business_rules(
    request: Request,
    query: str = Query(..., description="Consulta para busca semântica"),
    limit: int = Query(5, description="Número máximo de resultados"),
    score_threshold: float = Query(0.7, description="Limiar de similaridade (0.0 a 1.0)"),
    account_id: str = Query(None, description="ID da conta (opcional, para compatibilidade)"),
):
    """
    Busca semântica de regras de negócio.
    """
    try:
        service = get_business_rules_service()

        # Obter account_id do estado da requisição (definido pelo middleware de autenticação)
        # Se não estiver definido, usar o account_id da URL (para compatibilidade)
        account_id = getattr(request.state, "account_id", account_id)

        if not account_id:
            raise ValidationError("account_id is required")

        # Buscar regras
        result = await service.search_business_rules(
            account_id=account_id,
            query=query,
            limit=limit,
            score_threshold=score_threshold,
        )

        # Construir resposta
        return build_response(
            success=True,
            data=result,
            meta={
                "request_id": getattr(request.state, "request_id", "unknown"),
                "query": query,
                "limit": limit,
                "score_threshold": score_threshold,
            },
        )

    except ValidationError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(
            status_code=422,
            detail={"code": getattr(e, "code", "VALIDATION_ERROR"), "message": str(e), "details": getattr(e, "details", None)},
        )

    except OdooAPIError as e:
        logger.error(f"Odoo API error: {e}")
        raise HTTPException(
            status_code=500,
            detail={"code": getattr(e, "code", "ODOO_API_ERROR"), "message": str(e), "details": getattr(e, "details", None)},
        )

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=500,
            detail={"code": "INTERNAL_SERVER_ERROR", "message": str(e)},
        )

# Rota para sincronizar regras com o sistema de IA
@router.post(
    "/sync",
    response_model=APIResponse,
    summary="Sincroniza regras com o sistema de IA",
    description="Sincroniza todas as regras ativas com o sistema de IA.",
)
async def sync_business_rules(
    request: Request,
    account_id: str = Query(None, description="ID da conta (opcional, para compatibilidade)"),
):
    """
    Sincroniza regras com o sistema de IA.
    """
    try:
        service = get_business_rules_service()

        # Obter account_id do estado da requisição (definido pelo middleware de autenticação)
        # Se não estiver definido, usar o account_id da URL (para compatibilidade)
        account_id = getattr(request.state, "account_id", account_id)

        if not account_id:
            raise ValidationError("account_id is required")

        # Sincronizar regras
        result = await service.sync_business_rules(
            account_id=account_id,
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
            detail={"code": getattr(e, "code", "VALIDATION_ERROR"), "message": str(e), "details": getattr(e, "details", None)},
        )

    except OdooAPIError as e:
        logger.error(f"Odoo API error: {e}")
        raise HTTPException(
            status_code=500,
            detail={"code": getattr(e, "code", "ODOO_API_ERROR"), "message": str(e), "details": getattr(e, "details", None)},
        )

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=500,
            detail={"code": "INTERNAL_SERVER_ERROR", "message": str(e)},
        )

# Rota para sincronizar metadados da empresa com o sistema de IA
@router.post(
    "/sync-company-metadata",
    response_model=APIResponse,
    summary="Sincroniza metadados da empresa com o sistema de IA",
    description="Sincroniza metadados gerais da empresa com o sistema de IA.",
)
async def sync_company_metadata(
    request: Request,
    account_id: str = Query(None, description="ID da conta (opcional, para compatibilidade)"),
):
    """
    Sincroniza metadados da empresa com o sistema de IA.
    """
    try:
        service = get_business_rules_service()

        # Obter account_id do estado da requisição (definido pelo middleware de autenticação)
        # Se não estiver definido, usar o account_id da URL (para compatibilidade)
        account_id = getattr(request.state, "account_id", account_id)

        if not account_id:
            raise ValidationError("account_id is required")

        # Sincronizar metadados da empresa
        result = await service.sync_company_metadata(
            account_id=account_id,
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
            detail={"code": getattr(e, "code", "VALIDATION_ERROR"), "message": str(e), "details": getattr(e, "details", None)},
        )

    except OdooAPIError as e:
        logger.error(f"Odoo API error: {e}")
        raise HTTPException(
            status_code=500,
            detail={"code": getattr(e, "code", "ODOO_API_ERROR"), "message": str(e), "details": getattr(e, "details", None)},
        )

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=500,
            detail={"code": "INTERNAL_SERVER_ERROR", "message": str(e)},
        )

# Rota para sincronizar documentos de suporte com o sistema de IA
@router.post(
    "/sync-support-documents",
    response_model=APIResponse,
    summary="Sincroniza documentos de suporte com o sistema de IA",
    description="Sincroniza documentos de suporte ao cliente com o sistema de IA.",
)
async def sync_support_documents(
    request: Request,
    account_id: str = Query(None, description="ID da conta (opcional, para compatibilidade)"),
):
    """
    Sincroniza documentos de suporte com o sistema de IA.
    """
    try:
        service = get_business_rules_service()

        # Obter account_id do estado da requisição (definido pelo middleware de autenticação)
        # Se não estiver definido, usar o account_id da URL (para compatibilidade)
        account_id = getattr(request.state, "account_id", account_id)

        if not account_id:
            raise ValidationError("account_id is required")

        # Obter dados do corpo da requisição
        data = await request.json()
        business_rule_id = data.get("business_rule_id")
        documents = data.get("documents", [])

        if not business_rule_id:
            raise ValidationError("business_rule_id is required")

        if not documents:
            raise ValidationError("documents list is required")

        # Sincronizar documentos de suporte
        result = await service.sync_support_documents(
            account_id=account_id,
            business_rule_id=business_rule_id,
            documents=documents,
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
            detail={"code": getattr(e, "code", "VALIDATION_ERROR"), "message": str(e), "details": getattr(e, "details", None)},
        )

    except OdooAPIError as e:
        logger.error(f"Odoo API error: {e}")
        raise HTTPException(
            status_code=500,
            detail={"code": getattr(e, "code", "ODOO_API_ERROR"), "message": str(e), "details": getattr(e, "details", None)},
        )

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=500,
            detail={"code": "INTERNAL_SERVER_ERROR", "message": str(e)},
        )



    except ValidationError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(
            status_code=422,
            detail={"code": getattr(e, "code", "VALIDATION_ERROR"), "message": str(e), "details": getattr(e, "details", None)},
        )

    except OdooAPIError as e:
        logger.error(f"Odoo API error: {e}")
        raise HTTPException(
            status_code=500,
            detail={"code": getattr(e, "code", "ODOO_API_ERROR"), "message": str(e), "details": getattr(e, "details", None)},
        )

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=500,
            detail={"code": "INTERNAL_SERVER_ERROR", "message": str(e)},
        )

# Rota para listar regras ativas
@router.get(
    "/active",
    response_model=APIResponse,
    summary="Lista regras de negócio ativas",
    description="Lista regras de negócio ativas no momento.",
)
async def list_active_rules(
    request: Request,
    account_id: str = Query(None, description="ID da conta (opcional, para compatibilidade)"),
    rule_type: Optional[str] = Query(None, description="Filtrar por tipo de regra"),
):
    """
    Lista regras de negócio ativas.
    """
    try:
        service = get_business_rules_service()

        # Obter account_id do estado da requisição (definido pelo middleware de autenticação)
        # Se não estiver definido, usar o account_id da URL (para compatibilidade)
        account_id = getattr(request.state, "account_id", account_id)

        if not account_id:
            raise ValidationError("account_id is required")

        # Listar regras ativas
        result = await service.list_active_rules(
            account_id=account_id,
            rule_type=rule_type,
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
            detail={"code": getattr(e, "code", "VALIDATION_ERROR"), "message": str(e), "details": getattr(e, "details", None)},
        )

    except OdooAPIError as e:
        logger.error(f"Odoo API error: {e}")
        raise HTTPException(
            status_code=500,
            detail={"code": getattr(e, "code", "ODOO_API_ERROR"), "message": str(e), "details": getattr(e, "details", None)},
        )

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=500,
            detail={"code": "INTERNAL_SERVER_ERROR", "message": str(e)},
        )

# Rota para upload de documento
@router.post(
    "/documents",
    response_model=APIResponse,
    summary="Faz upload de um documento",
    description="Faz upload de um documento para extração de regras de negócio.",
)
async def upload_document(
    request: Request,
    name: str = Query(..., description="Nome do documento"),
    description: str = Query(..., description="Descrição do documento"),
    document_type: str = Query(..., description="Tipo do documento (pdf, docx)"),
    file: UploadFile = File(..., description="Arquivo do documento"),
    account_id: str = Query(..., description="ID da conta"),
):
    """
    Faz upload de um documento.
    """
    try:
        service = get_business_rules_service()

        # Ler conteúdo do arquivo
        content = await file.read()

        # Codificar em base64
        content_base64 = base64.b64encode(content).decode('utf-8')

        # Criar requisição
        document_request = DocumentUploadRequest(
            name=name,
            description=description,
            document_type=document_type,
            content_base64=content_base64,
        )

        # Fazer upload do documento
        result = await service.upload_document(
            account_id=account_id,
            document_data=document_request,
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
            detail={"code": getattr(e, "code", "VALIDATION_ERROR"), "message": str(e), "details": getattr(e, "details", None)},
        )

    except OdooAPIError as e:
        logger.error(f"Odoo API error: {e}")
        raise HTTPException(
            status_code=500,
            detail={"code": getattr(e, "code", "ODOO_API_ERROR"), "message": str(e), "details": getattr(e, "details", None)},
        )

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=500,
            detail={"code": "INTERNAL_SERVER_ERROR", "message": str(e)},
        )

# Rota para listar documentos
@router.get(
    "/documents",
    response_model=APIResponse,
    summary="Lista documentos",
    description="Lista documentos de regras de negócio.",
)
async def list_documents(
    request: Request,
    account_id: str = Query(..., description="ID da conta"),
):
    """
    Lista documentos.
    """
    try:
        service = get_business_rules_service()

        # Listar documentos
        result = await service.list_documents(
            account_id=account_id,
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
            detail={"code": getattr(e, "code", "VALIDATION_ERROR"), "message": str(e), "details": getattr(e, "details", None)},
        )

    except OdooAPIError as e:
        logger.error(f"Odoo API error: {e}")
        raise HTTPException(
            status_code=500,
            detail={"code": getattr(e, "code", "ODOO_API_ERROR"), "message": str(e), "details": getattr(e, "details", None)},
        )

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=500,
            detail={"code": "INTERNAL_SERVER_ERROR", "message": str(e)},
        )


# Rota para obter configurações de estilo da crew de atendimento ao cliente
@router.get(
    "/customer-service/style",
    response_model=APIResponse,
    summary="Obtém configurações de estilo da crew de atendimento ao cliente",
    description="Obtém configurações de estilo da crew de atendimento ao cliente.",
)
async def get_customer_service_style(
    request: Request,
    account_id: str = Query(..., description="ID da conta"),
    domain: str = Query(..., description="Domínio da conta"),
):
    """
    Obtém configurações de estilo da crew de atendimento ao cliente.
    """
    try:
        # Obter gerenciador de estilo
        style_manager = get_customer_service_style_manager(domain, account_id)

        # Obter configurações de estilo
        style = style_manager.get_style()

        # Construir resposta
        return build_response(
            success=True,
            data=style,
            meta={"request_id": getattr(request.state, "request_id", "unknown")},
        )

    except ValidationError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(
            status_code=422,
            detail={"code": getattr(e, "code", "VALIDATION_ERROR"), "message": str(e), "details": getattr(e, "details", None)},
        )

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=500,
            detail={"code": "INTERNAL_SERVER_ERROR", "message": str(e)},
        )


# Rota para atualizar configurações de estilo da crew de atendimento ao cliente
@router.put(
    "/customer-service/style",
    response_model=APIResponse,
    summary="Atualiza configurações de estilo da crew de atendimento ao cliente",
    description="Atualiza configurações de estilo da crew de atendimento ao cliente.",
)
async def update_customer_service_style(
    request: Request,
    body: CustomerServiceStyleConfig,
    account_id: str = Query(..., description="ID da conta"),
    domain: str = Query(..., description="Domínio da conta"),
):
    """
    Atualiza configurações de estilo da crew de atendimento ao cliente.
    """
    try:
        # Obter gerenciador de estilo
        style_manager = get_customer_service_style_manager(domain, account_id)

        # Atualizar configurações de estilo
        success = style_manager.update_style(body.model_dump())

        # Construir resposta
        return build_response(
            success=success,
            data={"message": "Style updated successfully" if success else "Failed to update style"},
            meta={"request_id": getattr(request.state, "request_id", "unknown")},
        )

    except ValidationError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(
            status_code=422,
            detail={"code": getattr(e, "code", "VALIDATION_ERROR"), "message": str(e), "details": getattr(e, "details", None)},
        )

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=500,
            detail={"code": "INTERNAL_SERVER_ERROR", "message": str(e)},
        )


# Rota para atualizar saudação da crew de atendimento ao cliente
@router.put(
    "/customer-service/style/greeting",
    response_model=APIResponse,
    summary="Atualiza saudação da crew de atendimento ao cliente",
    description="Atualiza saudação da crew de atendimento ao cliente.",
)
async def update_customer_service_greeting(
    request: Request,
    body: GreetingStyleConfig,
    account_id: str = Query(..., description="ID da conta"),
    domain: str = Query(..., description="Domínio da conta"),
):
    """
    Atualiza saudação da crew de atendimento ao cliente.
    """
    try:
        # Obter gerenciador de estilo
        style_manager = get_customer_service_style_manager(domain, account_id)

        # Atualizar saudação
        success = style_manager.update_greeting(body.enabled, body.message)

        # Construir resposta
        return build_response(
            success=success,
            data={"message": "Greeting updated successfully" if success else "Failed to update greeting"},
            meta={"request_id": getattr(request.state, "request_id", "unknown")},
        )

    except ValidationError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(
            status_code=422,
            detail={"code": getattr(e, "code", "VALIDATION_ERROR"), "message": str(e), "details": getattr(e, "details", None)},
        )

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=500,
            detail={"code": "INTERNAL_SERVER_ERROR", "message": str(e)},
        )

# Rota para criar regra temporária
@router.post(
    "/temporary",
    response_model=APIResponse,
    summary="Cria uma nova regra de negócio temporária",
    description="Cria uma nova regra de negócio temporária com datas de início e fim.",
)
async def create_temporary_rule(
    request: Request,
    body: TemporaryRuleRequest,
    account_id: str = Query(..., description="ID da conta"),
):
    """
    Cria uma nova regra de negócio temporária.
    """
    try:
        service = get_business_rules_service()

        # Criar regra temporária
        result = await service.create_temporary_rule(
            account_id=account_id,
            rule_data=body,
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
            detail={"code": getattr(e, "code", "VALIDATION_ERROR"), "message": str(e), "details": getattr(e, "details", None)},
        )

    except OdooAPIError as e:
        logger.error(f"Odoo API error: {e}")
        raise HTTPException(
            status_code=500,
            detail={"code": getattr(e, "code", "ODOO_API_ERROR"), "message": str(e), "details": getattr(e, "details", None)},
        )

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=500,
            detail={"code": "INTERNAL_SERVER_ERROR", "message": str(e)},
        )

# Rota para listar regras de negócio
@router.get(
    "",
    response_model=APIResponse,
    summary="Lista regras de negócio",
    description="Lista regras de negócio com paginação e filtros.",
)
async def list_business_rules(
    request: Request,
    account_id: str = Query(..., description="ID da conta"),
    page: int = Query(1, description="Número da página"),
    page_size: int = Query(20, description="Tamanho da página"),
    active_only: bool = Query(False, description="Filtrar apenas regras ativas"),
    rule_type: Optional[str] = Query(None, description="Filtrar por tipo de regra"),
):
    """
    Lista regras de negócio.
    """
    try:
        service = get_business_rules_service()

        # Listar regras
        result = await service.list_business_rules(
            account_id=account_id,
            page=page,
            page_size=page_size,
            active_only=active_only,
            rule_type=rule_type,
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
            detail={"code": getattr(e, "code", "VALIDATION_ERROR"), "message": str(e), "details": getattr(e, "details", None)},
        )

    except OdooAPIError as e:
        logger.error(f"Odoo API error: {e}")
        raise HTTPException(
            status_code=500,
            detail={"code": getattr(e, "code", "ODOO_API_ERROR"), "message": str(e), "details": getattr(e, "details", None)},
        )

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=500,
            detail={"code": "INTERNAL_SERVER_ERROR", "message": str(e)},
        )

# Rota para criar regra de negócio
@router.post(
    "",
    response_model=APIResponse,
    summary="Cria uma nova regra de negócio",
    description="Cria uma nova regra de negócio permanente.",
)
async def create_business_rule(
    request: Request,
    body: BusinessRuleRequest,
    account_id: str = Query(..., description="ID da conta"),
):
    """
    Cria uma nova regra de negócio.
    """
    try:
        service = get_business_rules_service()

        # Criar regra
        result = await service.create_business_rule(
            account_id=account_id,
            rule_data=body,
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
            detail={"code": getattr(e, "code", "VALIDATION_ERROR"), "message": str(e), "details": getattr(e, "details", None)},
        )

    except OdooAPIError as e:
        logger.error(f"Odoo API error: {e}")
        raise HTTPException(
            status_code=500,
            detail={"code": getattr(e, "code", "ODOO_API_ERROR"), "message": str(e), "details": getattr(e, "details", None)},
        )

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=500,
            detail={"code": "INTERNAL_SERVER_ERROR", "message": str(e)},
        )

# IMPORTANTE: Definir rotas com parâmetros de caminho DEPOIS das rotas específicas

# Rota para atualizar regra de negócio
@router.put(
    "/{rule_id}",
    response_model=APIResponse,
    summary="Atualiza uma regra de negócio",
    description="Atualiza uma regra de negócio existente.",
)
async def update_business_rule(
    request: Request,
    rule_id: int = Path(..., description="ID da regra"),
    body: BusinessRuleRequest = None,
    account_id: str = Query(..., description="ID da conta"),
):
    """
    Atualiza uma regra de negócio.
    """
    try:
        service = get_business_rules_service()

        # Atualizar regra
        result = await service.update_business_rule(
            account_id=account_id,
            rule_id=rule_id,
            rule_data=body,
        )

        # Construir resposta
        return build_response(
            success=True,
            data=result,
            meta={"request_id": getattr(request.state, "request_id", "unknown")},
        )

    except NotFoundError as e:
        logger.warning(f"Rule not found: {e}")
        raise HTTPException(
            status_code=404,
            detail={"code": getattr(e, "code", "NOT_FOUND"), "message": str(e), "details": getattr(e, "details", None)},
        )

    except ValidationError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(
            status_code=422,
            detail={"code": getattr(e, "code", "VALIDATION_ERROR"), "message": str(e), "details": getattr(e, "details", None)},
        )

    except OdooAPIError as e:
        logger.error(f"Odoo API error: {e}")
        raise HTTPException(
            status_code=500,
            detail={"code": getattr(e, "code", "ODOO_API_ERROR"), "message": str(e), "details": getattr(e, "details", None)},
        )

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=500,
            detail={"code": "INTERNAL_SERVER_ERROR", "message": str(e)},
        )

# Rota para remover regra de negócio
@router.delete(
    "/{rule_id}",
    response_model=APIResponse,
    summary="Remove uma regra de negócio",
    description="Remove uma regra de negócio existente.",
)
async def delete_business_rule(
    request: Request,
    rule_id: int = Path(..., description="ID da regra"),
    account_id: str = Query(..., description="ID da conta"),
):
    """
    Remove uma regra de negócio.
    """
    try:
        service = get_business_rules_service()

        # Remover regra
        result = await service.delete_business_rule(
            account_id=account_id,
            rule_id=rule_id,
        )

        # Construir resposta
        return build_response(
            success=True,
            data={"deleted": result},
            meta={"request_id": getattr(request.state, "request_id", "unknown")},
        )

    except NotFoundError as e:
        logger.warning(f"Rule not found: {e}")
        raise HTTPException(
            status_code=404,
            detail={"code": getattr(e, "code", "NOT_FOUND"), "message": str(e), "details": getattr(e, "details", None)},
        )

    except OdooAPIError as e:
        logger.error(f"Odoo API error: {e}")
        raise HTTPException(
            status_code=500,
            detail={"code": getattr(e, "code", "ODOO_API_ERROR"), "message": str(e), "details": getattr(e, "details", None)},
        )

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=500,
            detail={"code": "INTERNAL_SERVER_ERROR", "message": str(e)},
        )

# Rota para obter regra de negócio
@router.get(
    "/{rule_id}",
    response_model=APIResponse,
    summary="Obtém uma regra de negócio",
    description="Obtém uma regra de negócio pelo ID.",
)
async def get_business_rule(
    request: Request,
    rule_id: int = Path(..., description="ID da regra"),
    account_id: str = Query(..., description="ID da conta"),
):
    """
    Obtém uma regra de negócio.
    """
    try:
        service = get_business_rules_service()

        # Obter regra
        result = await service.get_business_rule(
            account_id=account_id,
            rule_id=rule_id,
        )

        # Construir resposta
        return build_response(
            success=True,
            data=result,
            meta={"request_id": getattr(request.state, "request_id", "unknown")},
        )

    except NotFoundError as e:
        logger.warning(f"Rule not found: {e}")
        raise HTTPException(
            status_code=404,
            detail={"code": getattr(e, "code", "NOT_FOUND"), "message": str(e), "details": getattr(e, "details", None)},
        )

    except OdooAPIError as e:
        logger.error(f"Odoo API error: {e}")
        raise HTTPException(
            status_code=500,
            detail={"code": getattr(e, "code", "ODOO_API_ERROR"), "message": str(e), "details": getattr(e, "details", None)},
        )

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=500,
            detail={"code": "INTERNAL_SERVER_ERROR", "message": str(e)},
        )

# Rota para obter documentos de suporte processados
@router.get(
    "/view-support-document/{document_id}",
    response_model=APIResponse,
    summary="Obtém um documento de suporte processado",
    description="Obtém um documento de suporte processado pelo sistema de IA.",
)
async def view_support_document(
    request: Request,
    document_id: int = Path(..., description="ID do documento"),
    account_id: str = Query(None, description="ID da conta (opcional, para compatibilidade)"),
):
    """
    Obtém um documento de suporte processado pelo sistema de IA.
    """
    try:
        service = get_business_rules_service()

        # Obter account_id do estado da requisição (definido pelo middleware de autenticação)
        # Se não estiver definido, usar o account_id da URL (para compatibilidade)
        account_id = getattr(request.state, "account_id", account_id)

        if not account_id:
            raise ValidationError("account_id is required")

        # Obter documento processado
        result = await service.get_processed_support_document(
            account_id=account_id,
            document_id=document_id,
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
            detail={"code": getattr(e, "code", "VALIDATION_ERROR"), "message": str(e), "details": getattr(e, "details", None)},
        )

    except OdooAPIError as e:
        logger.error(f"Odoo API error: {e}")
        raise HTTPException(
            status_code=500,
            detail={"code": getattr(e, "code", "ODOO_API_ERROR"), "message": str(e), "details": getattr(e, "details", None)},
        )

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=500,
            detail={"code": "INTERNAL_SERVER_ERROR", "message": str(e)},
        )

# Rota para obter metadados da empresa processados
@router.get(
    "/view-company-metadata",
    response_model=APIResponse,
    summary="Obtém os metadados da empresa processados",
    description="Obtém os metadados da empresa processados pelo sistema de IA.",
)
async def view_company_metadata(
    request: Request,
    account_id: str = Query(None, description="ID da conta (opcional, para compatibilidade)"),
):
    """
    Obtém os metadados da empresa processados pelo sistema de IA.
    """
    try:
        service = get_business_rules_service()

        # Obter account_id do estado da requisição (definido pelo middleware de autenticação)
        # Se não estiver definido, usar o account_id da URL (para compatibilidade)
        account_id = getattr(request.state, "account_id", account_id)

        if not account_id:
            raise ValidationError("account_id is required")

        # Obter metadados processados
        result = await service.get_processed_company_metadata(
            account_id=account_id,
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
            detail={"code": getattr(e, "code", "VALIDATION_ERROR"), "message": str(e), "details": getattr(e, "details", None)},
        )

    except OdooAPIError as e:
        logger.error(f"Odoo API error: {e}")
        raise HTTPException(
            status_code=500,
            detail={"code": getattr(e, "code", "ODOO_API_ERROR"), "message": str(e), "details": getattr(e, "details", None)},
        )

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=500,
            detail={"code": "INTERNAL_SERVER_ERROR", "message": str(e)},
        )