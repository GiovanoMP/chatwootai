"""
Modelos Pydantic para regras de negócio na API de simulação do Odoo.
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field

class BusinessRuleBase(BaseModel):
    """Modelo base para regras de negócio."""
    name: str = Field(..., description="Nome da regra de negócio")
    description: str = Field(..., description="Descrição detalhada da regra")
    category: str = Field(..., description="Categoria da regra (pricing, shipping, return, promotion, etc.)")
    rule_text: str = Field(..., description="Texto completo da regra de negócio")
    active: bool = Field(True, description="Indica se a regra está ativa")

class BusinessRuleCreate(BusinessRuleBase):
    """Modelo para criação de novas regras de negócio."""
    pass

class BusinessRuleUpdate(BaseModel):
    """
    Modelo para atualização de regras de negócio.
    Todos os campos são opcionais para permitir atualizações parciais.
    """
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    rule_text: Optional[str] = None
    active: Optional[bool] = None

class BusinessRule(BusinessRuleBase):
    """
    Modelo completo de regra de negócio, incluindo campos gerados pelo sistema.
    Usado para respostas da API.
    """
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class CustomerInteraction(BaseModel):
    """Modelo para interações com clientes."""
    id: int
    customer_id: int
    channel: str
    interaction_type: str
    content: str
    timestamp: datetime
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True
