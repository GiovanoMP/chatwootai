from fastapi import APIRouter, Depends, HTTPException, Header, status, Body
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from app.core.database import get_db
from app.core.security import get_api_key
from app.models.config import Configuration
from app.schemas.config import ConfigResponse
import yaml
import json
import logging
from datetime import datetime

router = APIRouter(
    prefix="/company-services",
    tags=["company-services"],
    dependencies=[Depends(get_api_key)]
)

logger = logging.getLogger(__name__)

def verify_security_token(security_token: str = Header(..., alias="X-Security-Token"), db: Session = Depends(get_db)):
    """
    Verifica se o token de segurança é válido.
    
    Args:
        security_token: Token de segurança fornecido no header
        db: Sessão do banco de dados
        
    Returns:
        O token se for válido
        
    Raises:
        HTTPException: Se o token for inválido
    """
    # Verificar se o token existe no banco de dados
    # Isso poderia ser implementado de várias formas, dependendo da estrutura do banco
    # Por exemplo, poderia haver uma tabela de tokens ou o token poderia estar armazenado
    # nas configurações do tenant
    
    # Por enquanto, vamos apenas verificar se o token não está vazio
    if not security_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de segurança não fornecido",
            headers={"WWW-Authenticate": "SecurityToken"},
        )
    
    return security_token

@router.post("/{tenant_id}/metadata", response_model=ConfigResponse)
def create_company_metadata(
    tenant_id: str,
    yaml_content: Dict[str, Any] = Body(..., embed=True),
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key),
    security_token: str = Depends(verify_security_token)
):
    """
    Cria ou atualiza os metadados da empresa.
    
    Args:
        tenant_id: ID do tenant
        yaml_content: Conteúdo YAML com os metadados da empresa
        db: Sessão do banco de dados
        api_key: Chave de API para autenticação
        security_token: Token de segurança para verificação adicional
        
    Returns:
        Resposta com os metadados criados/atualizados
    """
    try:
        # Converter YAML para dicionário
        config_data = yaml.safe_load(yaml_content)
        
        # Verificar se o tenant_id no YAML corresponde ao tenant_id na URL
        if config_data.get('account_id') != tenant_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"O tenant_id na URL ({tenant_id}) não corresponde ao account_id no YAML ({config_data.get('account_id')})"
            )
        
        # Verificar se o token de segurança no YAML corresponde ao token no header
        if config_data.get('security_token') != security_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token de segurança no YAML não corresponde ao token no header",
                headers={"WWW-Authenticate": "SecurityToken"},
            )
        
        # Obter a versão mais recente
        latest_config = db.query(Configuration).filter(
            Configuration.tenant_id == tenant_id,
            Configuration.config_type == "company_metadata"
        ).order_by(Configuration.version.desc()).first()
        
        new_version = 1
        if latest_config:
            new_version = latest_config.version + 1
        
        # Criar nova configuração
        config = Configuration(
            tenant_id=tenant_id,
            config_type="company_metadata",
            config_data=json.dumps(config_data),
            version=new_version,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        db.add(config)
        db.commit()
        db.refresh(config)
        
        # Enviar notificação de volta para o Odoo (opcional)
        # Isso poderia ser implementado como uma tarefa assíncrona
        # Por exemplo, usando Celery ou um sistema de filas
        
        return {
            "id": config.id,
            "tenant_id": config.tenant_id,
            "config_type": config.config_type,
            "version": config.version,
            "created_at": config.created_at,
            "updated_at": config.updated_at,
            "json_data": json.loads(config.config_data)
        }
    except Exception as e:
        logger.error(f"Erro ao processar metadados da empresa: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao processar metadados da empresa: {str(e)}"
        )

@router.get("/{tenant_id}/metadata", response_model=ConfigResponse)
def get_company_metadata(
    tenant_id: str,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key),
    security_token: Optional[str] = Header(None, alias="X-Security-Token")
):
    """
    Obtém os metadados da empresa.
    
    Args:
        tenant_id: ID do tenant
        db: Sessão do banco de dados
        api_key: Chave de API para autenticação
        security_token: Token de segurança para verificação adicional (opcional)
        
    Returns:
        Resposta com os metadados da empresa
    """
    # Obter a versão mais recente
    config = db.query(Configuration).filter(
        Configuration.tenant_id == tenant_id,
        Configuration.config_type == "company_metadata"
    ).order_by(Configuration.version.desc()).first()
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Metadados da empresa não encontrados para tenant_id={tenant_id}"
        )
    
    # Se o token de segurança foi fornecido, verificar se corresponde
    if security_token:
        config_data = json.loads(config.config_data)
        if config_data.get('security_token') != security_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token de segurança inválido",
                headers={"WWW-Authenticate": "SecurityToken"},
            )
    
    return {
        "id": config.id,
        "tenant_id": config.tenant_id,
        "config_type": config.config_type,
        "version": config.version,
        "created_at": config.created_at,
        "updated_at": config.updated_at,
        "json_data": json.loads(config.config_data)
    }
