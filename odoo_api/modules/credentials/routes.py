# -*- coding: utf-8 -*-

"""
Rotas para o módulo de gerenciamento de credenciais.
"""

import logging
import os
import yaml
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Header, Request
from pydantic import BaseModel

from odoo_api.config.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/credentials", tags=["credentials"])

class CredentialRequest(BaseModel):
    """Modelo para solicitação de credencial."""
    
    credential_ref: str
    account_id: str

class CredentialResponse(BaseModel):
    """Modelo para resposta de credencial."""
    
    credential: str

@router.post("/get", response_model=CredentialResponse)
async def get_credential(
    request: CredentialRequest,
    authorization: Optional[str] = Header(None),
    req: Request = None,
):
    """
    Recupera uma credencial usando sua referência.
    
    Args:
        request: Solicitação de credencial
        authorization: Token de autorização
        req: Objeto de requisição
    
    Returns:
        Credencial
    
    Raises:
        HTTPException: Se a credencial não for encontrada ou o token for inválido
    """
    # Verificar autorização
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token de autorização não fornecido")
    
    token = authorization.replace("Bearer ", "")
    
    # Verificar se o token é válido
    if not await _validate_token(token, request.account_id):
        raise HTTPException(status_code=401, detail="Token de autorização inválido")
    
    # Recuperar credencial
    credential = await _get_credential_by_ref(request.credential_ref, request.account_id)
    
    if not credential:
        raise HTTPException(status_code=404, detail="Credencial não encontrada")
    
    # Registrar acesso à credencial
    logger.info(f"Credential accessed: {request.credential_ref} for account_id {request.account_id}")
    
    return CredentialResponse(credential=credential)

async def _validate_token(token: str, account_id: str) -> bool:
    """
    Valida o token de autorização.
    
    Args:
        token: Token de autorização
        account_id: ID da conta
    
    Returns:
        True se o token for válido, False caso contrário
    """
    # Em um ambiente de produção, isso deve consultar um serviço seguro de validação de tokens
    # Por enquanto, vamos usar uma abordagem simplificada para desenvolvimento
    
    # Verificar se existe um arquivo de credenciais
    credentials_file = os.path.join(settings.CONFIG_DIR, "credentials.yaml")
    
    if os.path.exists(credentials_file):
        try:
            with open(credentials_file, "r") as f:
                credentials = yaml.safe_load(f)
            
            # Verificar se o token existe no arquivo de credenciais
            if credentials and account_id in credentials:
                for ref, value in credentials[account_id].items():
                    if token == ref:
                        return True
        except Exception as e:
            logger.error(f"Failed to validate token: {e}")
    
    # Para desenvolvimento, aceitar qualquer token
    if settings.ENVIRONMENT == "development":
        logger.warning("Accepting any token in development environment")
        return True
    
    return False

async def _get_credential_by_ref(credential_ref: str, account_id: str) -> Optional[str]:
    """
    Recupera a credencial real usando a referência.
    
    Args:
        credential_ref: Referência da credencial
        account_id: ID da conta
    
    Returns:
        Credencial real ou None se não encontrada
    """
    # Em um ambiente de produção, isso deve consultar um serviço seguro de gerenciamento de credenciais
    # Por enquanto, vamos usar uma abordagem simplificada para desenvolvimento
    
    # Verificar se existe um arquivo de credenciais
    credentials_file = os.path.join(settings.CONFIG_DIR, "credentials.yaml")
    
    if os.path.exists(credentials_file):
        try:
            with open(credentials_file, "r") as f:
                credentials = yaml.safe_load(f)
            
            if credentials and account_id in credentials and credential_ref in credentials[account_id]:
                return credentials[account_id][credential_ref]
        except Exception as e:
            logger.error(f"Failed to load credentials: {e}")
    
    # Se não encontrar no arquivo, usar a própria referência como senha (para desenvolvimento)
    if settings.ENVIRONMENT == "development":
        logger.warning(f"Using credential_ref as credential for development: {credential_ref}")
        return credential_ref
    
    return None
