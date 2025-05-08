from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from app.models.config import CrewConfiguration
from app.schemas.config import ConfigCreate, ConfigUpdate
from typing import Dict, Any, Optional, List
import yaml
import logging
import json

logger = logging.getLogger(__name__)

class ConfigService:
    """
    Serviço para gerenciar configurações.
    """

    def __init__(self, db: Session):
        """
        Inicializa o serviço.

        Args:
            db: Sessão do banco de dados
        """
        self.db = db

    def get_latest_config(self, tenant_id: str, domain: str, config_type: str) -> Optional[Dict[str, Any]]:
        """
        Obtém a configuração mais recente.

        Args:
            tenant_id: ID do tenant
            domain: Domínio do tenant
            config_type: Tipo de configuração

        Returns:
            Dados da configuração ou None se não existir
        """
        config = self.db.query(CrewConfiguration).filter(
            CrewConfiguration.tenant_id == tenant_id,
            CrewConfiguration.domain == domain,
            CrewConfiguration.config_type == config_type
        ).order_by(CrewConfiguration.version.desc()).first()

        if config:
            return {
                "id": config.id,
                "tenant_id": config.tenant_id,
                "domain": config.domain,
                "config_type": config.config_type,
                "version": config.version,
                "yaml_content": config.yaml_content,
                "json_data": config.json_data,
                "created_at": config.created_at,
                "updated_at": config.updated_at
            }
        return None

    def create_or_update_config(self, tenant_id: str, domain: str, config_type: str, yaml_content: str) -> CrewConfiguration:
        """
        Cria ou atualiza uma configuração.

        Args:
            tenant_id: ID do tenant
            domain: Domínio do tenant
            config_type: Tipo de configuração
            yaml_content: Conteúdo YAML da configuração

        Returns:
            Objeto CrewConfiguration atualizado
        """
        # Obter a versão atual
        latest_config = self.db.query(CrewConfiguration).filter(
            CrewConfiguration.tenant_id == tenant_id,
            CrewConfiguration.domain == domain,
            CrewConfiguration.config_type == config_type
        ).order_by(CrewConfiguration.version.desc()).first()

        new_version = 1 if not latest_config else latest_config.version + 1

        # Converter YAML para JSON
        try:
            json_data = yaml.safe_load(yaml_content)
            if not isinstance(json_data, dict):
                json_data = {"data": json_data}

            # Garantir que enabled_collections seja preservado
            if config_type == "config" and "enabled_collections" in json_data:
                logger.info(f"Preservando enabled_collections: {json_data['enabled_collections']}")
        except Exception as e:
            logger.error(f"Erro ao converter YAML para JSON: {str(e)}")
            raise ValueError(f"YAML inválido: {str(e)}")

        # Criar novo registro
        new_config = CrewConfiguration(
            tenant_id=tenant_id,
            domain=domain,
            config_type=config_type,
            version=new_version,
            yaml_content=yaml_content,
            json_data=json_data
        )

        self.db.add(new_config)
        self.db.commit()
        self.db.refresh(new_config)

        logger.info(f"Configuração atualizada para tenant_id={tenant_id}, domain={domain}, config_type={config_type}, version={new_version}")

        return new_config

    def list_configs(self, tenant_id: str, domain: str = None) -> List[Dict[str, Any]]:
        """
        Lista as configurações disponíveis para um tenant.

        Args:
            tenant_id: ID do tenant
            domain: Domínio do tenant (opcional)

        Returns:
            Lista de configurações
        """
        # Subquery para obter a versão mais recente de cada configuração
        subquery = self.db.query(
            CrewConfiguration.tenant_id,
            CrewConfiguration.domain,
            CrewConfiguration.config_type,
            func.max(CrewConfiguration.version).label("max_version")
        ).filter(
            CrewConfiguration.tenant_id == tenant_id
        )

        if domain:
            subquery = subquery.filter(CrewConfiguration.domain == domain)

        subquery = subquery.group_by(
            CrewConfiguration.tenant_id,
            CrewConfiguration.domain,
            CrewConfiguration.config_type
        ).subquery()

        # Query para obter as configurações mais recentes
        configs = self.db.query(CrewConfiguration).join(
            subquery,
            and_(
                CrewConfiguration.tenant_id == subquery.c.tenant_id,
                CrewConfiguration.domain == subquery.c.domain,
                CrewConfiguration.config_type == subquery.c.config_type,
                CrewConfiguration.version == subquery.c.max_version
            )
        ).all()

        return [
            {
                "id": config.id,
                "tenant_id": config.tenant_id,
                "domain": config.domain,
                "config_type": config.config_type,
                "version": config.version,
                "created_at": config.created_at,
                "updated_at": config.updated_at
            }
            for config in configs
        ]

    def get_config_history(self, tenant_id: str, domain: str, config_type: str) -> List[Dict[str, Any]]:
        """
        Obtém o histórico de versões de uma configuração.

        Args:
            tenant_id: ID do tenant
            domain: Domínio do tenant
            config_type: Tipo de configuração

        Returns:
            Lista de versões da configuração
        """
        configs = self.db.query(CrewConfiguration).filter(
            CrewConfiguration.tenant_id == tenant_id,
            CrewConfiguration.domain == domain,
            CrewConfiguration.config_type == config_type
        ).order_by(CrewConfiguration.version.desc()).all()

        return [
            {
                "id": config.id,
                "tenant_id": config.tenant_id,
                "domain": config.domain,
                "config_type": config.config_type,
                "version": config.version,
                "created_at": config.created_at,
                "updated_at": config.updated_at
            }
            for config in configs
        ]

    def get_config_version(self, tenant_id: str, domain: str, config_type: str, version: int) -> Optional[Dict[str, Any]]:
        """
        Obtém uma versão específica de uma configuração.

        Args:
            tenant_id: ID do tenant
            domain: Domínio do tenant
            config_type: Tipo de configuração
            version: Versão da configuração

        Returns:
            Dados da configuração ou None se não existir
        """
        config = self.db.query(CrewConfiguration).filter(
            CrewConfiguration.tenant_id == tenant_id,
            CrewConfiguration.domain == domain,
            CrewConfiguration.config_type == config_type,
            CrewConfiguration.version == version
        ).first()

        if config:
            return {
                "id": config.id,
                "tenant_id": config.tenant_id,
                "domain": config.domain,
                "config_type": config.config_type,
                "version": config.version,
                "yaml_content": config.yaml_content,
                "json_data": config.json_data,
                "created_at": config.created_at,
                "updated_at": config.updated_at
            }
        return None

def get_latest_config(db: Session, tenant_id: str, domain: str, config_type: str) -> Optional[Dict[str, Any]]:
    """
    Obtém a configuração mais recente.

    Args:
        db: Sessão do banco de dados
        tenant_id: ID do tenant
        domain: Domínio do tenant
        config_type: Tipo de configuração

    Returns:
        Dados da configuração ou None se não existir
    """
    service = ConfigService(db)
    return service.get_latest_config(tenant_id, domain, config_type)

def create_config(db: Session, tenant_id: str, domain: str, config_type: str, yaml_content: str) -> Dict[str, Any]:
    """
    Cria ou atualiza uma configuração.

    Args:
        db: Sessão do banco de dados
        tenant_id: ID do tenant
        domain: Domínio do tenant
        config_type: Tipo de configuração
        yaml_content: Conteúdo YAML da configuração

    Returns:
        Dados da configuração atualizada
    """
    service = ConfigService(db)
    config = service.create_or_update_config(tenant_id, domain, config_type, yaml_content)

    return {
        "id": config.id,
        "tenant_id": config.tenant_id,
        "domain": config.domain,
        "config_type": config.config_type,
        "version": config.version,
        "yaml_content": config.yaml_content,
        "json_data": config.json_data,
        "created_at": config.created_at,
        "updated_at": config.updated_at
    }


def list_configs(db: Session, tenant_id: str, domain: str = None) -> List[Dict[str, Any]]:
    """
    Lista as configurações disponíveis para um tenant.

    Args:
        db: Sessão do banco de dados
        tenant_id: ID do tenant
        domain: Domínio do tenant (opcional)

    Returns:
        Lista de configurações
    """
    service = ConfigService(db)
    return service.list_configs(tenant_id, domain)

def get_config_history(db: Session, tenant_id: str, domain: str, config_type: str) -> List[Dict[str, Any]]:
    """
    Obtém o histórico de versões de uma configuração.

    Args:
        db: Sessão do banco de dados
        tenant_id: ID do tenant
        domain: Domínio do tenant
        config_type: Tipo de configuração

    Returns:
        Lista de versões da configuração
    """
    service = ConfigService(db)
    return service.get_config_history(tenant_id, domain, config_type)

def get_config_version(db: Session, tenant_id: str, domain: str, config_type: str, version: int) -> Optional[Dict[str, Any]]:
    """
    Obtém uma versão específica de uma configuração.

    Args:
        db: Sessão do banco de dados
        tenant_id: ID do tenant
        domain: Domínio do tenant
        config_type: Tipo de configuração
        version: Versão da configuração

    Returns:
        Dados da configuração ou None se não existir
    """
    service = ConfigService(db)
    return service.get_config_version(tenant_id, domain, config_type, version)
