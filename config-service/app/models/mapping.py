from sqlalchemy import Column, Integer, String, JSON, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from app.core.database import Base

class ChatwootMapping(Base):
    """
    Modelo para armazenar o mapeamento Chatwoot.
    
    Attributes:
        id: ID único do mapeamento
        version: Versão do mapeamento (incrementado a cada atualização)
        mapping_data: Dados do mapeamento em formato JSON
        created_at: Data e hora de criação do mapeamento
        updated_at: Data e hora da última atualização do mapeamento
    """
    __tablename__ = "chatwoot_mapping"
    
    id = Column(Integer, primary_key=True, index=True)
    version = Column(Integer, default=1)
    mapping_data = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
