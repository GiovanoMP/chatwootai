"""
Modelos Pydantic para serviços na API de simulação do Odoo.
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field

class ServiceBase(BaseModel):
    """Modelo base para serviços com campos comuns."""
    name: str = Field(..., description="Nome do serviço")
    description: Optional[str] = Field(None, description="Descrição detalhada do serviço")
    category_id: int = Field(..., description="ID da categoria do serviço")
    price: float = Field(..., description="Preço do serviço")
    duration: int = Field(..., description="Duração do serviço em minutos")
    preparation: Optional[str] = Field(None, description="Instruções de preparação para o serviço")
    aftercare: Optional[str] = Field(None, description="Cuidados pós-procedimento")
    contraindications: Optional[str] = Field(None, description="Contraindicações do serviço")
    image_url: Optional[str] = Field(None, description="URL da imagem do serviço")
    active: bool = Field(True, description="Indica se o serviço está ativo")

class ServiceCreate(ServiceBase):
    """Modelo para criação de novos serviços."""
    pass

class ServiceUpdate(BaseModel):
    """
    Modelo para atualização de serviços.
    Todos os campos são opcionais para permitir atualizações parciais.
    """
    name: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[int] = None
    price: Optional[float] = None
    duration: Optional[int] = None
    preparation: Optional[str] = None
    aftercare: Optional[str] = None
    contraindications: Optional[str] = None
    image_url: Optional[str] = None
    active: Optional[bool] = None

class Service(ServiceBase):
    """
    Modelo completo de serviço, incluindo campos gerados pelo sistema.
    Usado para respostas da API.
    """
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class ServiceCategory(BaseModel):
    """Modelo para categorias de serviços."""
    id: int
    name: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class Professional(BaseModel):
    """Modelo para profissionais que realizam os serviços."""
    id: int
    first_name: str
    last_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    specialization: Optional[str] = None
    bio: Optional[str] = None
    image_url: Optional[str] = None
    active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class ProfessionalService(BaseModel):
    """Modelo para associação entre profissionais e serviços."""
    professional_id: int
    service_id: int
    
    class Config:
        orm_mode = True

class ServiceEnrichment(BaseModel):
    """Modelo para informações enriquecidas de serviços."""
    id: int
    service_id: int
    source: str
    content_type: str
    content: str
    relevance_score: Optional[float] = None
    last_updated: datetime
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class ServiceWithDetails(Service):
    """
    Modelo estendido de serviço com informações adicionais.
    Usado para respostas detalhadas da API.
    """
    category_name: Optional[str] = None
    professionals: Optional[List[Professional]] = None
    enrichments: Optional[List[ServiceEnrichment]] = None
    
    class Config:
        orm_mode = True
