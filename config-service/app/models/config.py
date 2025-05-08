from sqlalchemy import Column, Integer, String, DateTime, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from app.core.database import Base

class CrewConfiguration(Base):
    """
    Modelo para armazenar configurações de crews e outras configurações YAML.

    Attributes:
        id: ID único da configuração
        tenant_id: ID do tenant (account_id)
        domain: Domínio do tenant (retail, healthcare, etc.)
        config_type: Tipo de configuração (config, credentials, crew_whatsapp, etc.)
        version: Versão da configuração (incrementado a cada atualização)
        yaml_content: Conteúdo YAML original
        json_data: Dados convertidos para JSON
        created_at: Data e hora de criação da configuração
        updated_at: Data e hora da última atualização da configuração
    """
    __tablename__ = "crew_configurations"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String, nullable=False, index=True)
    domain = Column(String, nullable=False, index=True)
    config_type = Column(String, nullable=False, index=True)
    version = Column(Integer, default=1)
    yaml_content = Column(Text, nullable=False)
    json_data = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint('tenant_id', 'domain', 'config_type', 'version', name='uix_crew_config'),
    )
