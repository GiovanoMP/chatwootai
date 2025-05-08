from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.mapping_service import get_latest_mapping, create_or_update_mapping, merge_mapping
from app.schemas.mapping import MappingCreate, MappingUpdate, MappingInDB
from app.core.security import get_api_key
from typing import Dict, Any, Optional
import yaml
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/mapping", tags=["mapping"])

@router.get("/", response_model=Dict[str, Any])
def read_mapping(db: Session = Depends(get_db), api_key: str = Depends(get_api_key)):
    """
    Obtém o mapeamento atual do Chatwoot.
    
    Args:
        db: Sessão do banco de dados
        api_key: Chave de API para autenticação
        
    Returns:
        Dados do mapeamento
        
    Raises:
        HTTPException: Se o mapeamento não for encontrado
    """
    mapping = get_latest_mapping(db)
    if not mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Mapeamento não encontrado"
        )
    return mapping

@router.post("/", response_model=Dict[str, Any])
def create_mapping(
    mapping: MappingCreate, 
    db: Session = Depends(get_db), 
    api_key: str = Depends(get_api_key)
):
    """
    Cria um novo mapeamento, substituindo o existente.
    
    Args:
        mapping: Dados do mapeamento
        db: Sessão do banco de dados
        api_key: Chave de API para autenticação
        
    Returns:
        Dados do mapeamento atualizado
    """
    logger.info("Criando novo mapeamento")
    return create_or_update_mapping(db, mapping.mapping_data)

@router.patch("/", response_model=Dict[str, Any])
def update_mapping(
    mapping: MappingUpdate, 
    db: Session = Depends(get_db), 
    api_key: str = Depends(get_api_key)
):
    """
    Atualiza parcialmente o mapeamento existente.
    
    Args:
        mapping: Dados parciais do mapeamento
        db: Sessão do banco de dados
        api_key: Chave de API para autenticação
        
    Returns:
        Dados do mapeamento atualizado
    """
    logger.info("Atualizando mapeamento existente")
    return merge_mapping(db, mapping.mapping_data)

@router.get("/export", response_class=Response)
def export_mapping_yaml(db: Session = Depends(get_db), api_key: str = Depends(get_api_key)):
    """
    Exporta o mapeamento como YAML.
    
    Args:
        db: Sessão do banco de dados
        api_key: Chave de API para autenticação
        
    Returns:
        Conteúdo YAML do mapeamento
        
    Raises:
        HTTPException: Se o mapeamento não for encontrado
    """
    mapping = get_latest_mapping(db)
    if not mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Mapeamento não encontrado"
        )
    
    # Converter para YAML e retornar
    yaml_content = yaml.dump(mapping, default_flow_style=False)
    return Response(content=yaml_content, media_type="application/x-yaml")
