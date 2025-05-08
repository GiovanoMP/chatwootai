from fastapi import APIRouter, Depends, HTTPException, status, Response, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.config_service import (
    get_latest_config, create_config, list_configs,
    get_config_history, get_config_version
)
from app.schemas.config import ConfigCreate, ConfigUpdate, ConfigInDB, ConfigInfo
from app.core.security import get_api_key
from typing import Dict, Any, Optional, List
import yaml
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/configs", tags=["configs"])

@router.get("/{tenant_id}/{domain}/{config_type}", response_model=Dict[str, Any])
def read_config(
    tenant_id: str,
    domain: str,
    config_type: str,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """
    Obtém a configuração mais recente de um tenant.
    
    Args:
        tenant_id: ID do tenant
        domain: Domínio do tenant
        config_type: Tipo de configuração
        db: Sessão do banco de dados
        api_key: Chave de API para autenticação
        
    Returns:
        Dados da configuração
        
    Raises:
        HTTPException: Se a configuração não for encontrada
    """
    config = get_latest_config(db, tenant_id, domain, config_type)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Configuração não encontrada para tenant_id={tenant_id}, domain={domain}, config_type={config_type}"
        )
    return config

@router.post("/{tenant_id}/{domain}/{config_type}", response_model=Dict[str, Any])
def create_or_update_config(
    tenant_id: str,
    domain: str,
    config_type: str,
    config: ConfigUpdate,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """
    Cria ou atualiza a configuração de um tenant.
    
    Args:
        tenant_id: ID do tenant
        domain: Domínio do tenant
        config_type: Tipo de configuração
        config: Dados da configuração
        db: Sessão do banco de dados
        api_key: Chave de API para autenticação
        
    Returns:
        Dados da configuração atualizada
        
    Raises:
        HTTPException: Se o YAML for inválido
    """
    try:
        return create_config(db, tenant_id, domain, config_type, config.yaml_content)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/{tenant_id}/{domain}/{config_type}/yaml", response_class=Response)
def export_config_yaml(
    tenant_id: str,
    domain: str,
    config_type: str,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """
    Exporta a configuração como YAML.
    
    Args:
        tenant_id: ID do tenant
        domain: Domínio do tenant
        config_type: Tipo de configuração
        db: Sessão do banco de dados
        api_key: Chave de API para autenticação
        
    Returns:
        Conteúdo YAML da configuração
        
    Raises:
        HTTPException: Se a configuração não for encontrada
    """
    config = get_latest_config(db, tenant_id, domain, config_type)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Configuração não encontrada para tenant_id={tenant_id}, domain={domain}, config_type={config_type}"
        )
    
    return Response(content=config["yaml_content"], media_type="application/x-yaml")

@router.get("/{tenant_id}", response_model=List[ConfigInfo])
def list_tenant_configs(
    tenant_id: str,
    domain: str = Query(None, description="Filtrar por domínio"),
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """
    Lista as configurações disponíveis para um tenant.
    
    Args:
        tenant_id: ID do tenant
        domain: Domínio do tenant (opcional)
        db: Sessão do banco de dados
        api_key: Chave de API para autenticação
        
    Returns:
        Lista de configurações
    """
    return list_configs(db, tenant_id, domain)

@router.get("/{tenant_id}/{domain}/{config_type}/history", response_model=List[ConfigInfo])
def get_config_version_history(
    tenant_id: str,
    domain: str,
    config_type: str,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """
    Obtém o histórico de versões de uma configuração.
    
    Args:
        tenant_id: ID do tenant
        domain: Domínio do tenant
        config_type: Tipo de configuração
        db: Sessão do banco de dados
        api_key: Chave de API para autenticação
        
    Returns:
        Lista de versões da configuração
    """
    return get_config_history(db, tenant_id, domain, config_type)

@router.get("/{tenant_id}/{domain}/{config_type}/version/{version}", response_model=Dict[str, Any])
def get_specific_config_version(
    tenant_id: str,
    domain: str,
    config_type: str,
    version: int,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """
    Obtém uma versão específica de uma configuração.
    
    Args:
        tenant_id: ID do tenant
        domain: Domínio do tenant
        config_type: Tipo de configuração
        version: Versão da configuração
        db: Sessão do banco de dados
        api_key: Chave de API para autenticação
        
    Returns:
        Dados da configuração
        
    Raises:
        HTTPException: Se a configuração não for encontrada
    """
    config = get_config_version(db, tenant_id, domain, config_type, version)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Configuração não encontrada para tenant_id={tenant_id}, domain={domain}, config_type={config_type}, version={version}"
        )
    return config
