"""
Modelos Pydantic para clientes na API de simulação do Odoo.
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field

class CustomerBase(BaseModel):
    """Modelo base para clientes com campos comuns."""
    first_name: str = Field(..., description="Nome do cliente")
    last_name: str = Field(..., description="Sobrenome do cliente")
    email: Optional[EmailStr] = Field(None, description="Email do cliente")
    phone: Optional[str] = Field(None, description="Telefone do cliente")
    birth_date: Optional[datetime] = Field(None, description="Data de nascimento")
    address: Optional[str] = Field(None, description="Endereço completo")
    city: Optional[str] = Field(None, description="Cidade")
    state: Optional[str] = Field(None, description="Estado")
    postal_code: Optional[str] = Field(None, description="CEP")
    country: Optional[str] = Field("Brasil", description="País")
    skin_type: Optional[str] = Field(None, description="Tipo de pele (seca, oleosa, mista, etc.)")
    allergies: Optional[str] = Field(None, description="Alergias conhecidas")
    preferences: Optional[str] = Field(None, description="Preferências do cliente")
    notes: Optional[str] = Field(None, description="Observações adicionais")

class CustomerCreate(CustomerBase):
    """Modelo para criação de novos clientes."""
    pass

class CustomerUpdate(BaseModel):
    """
    Modelo para atualização de clientes.
    Todos os campos são opcionais para permitir atualizações parciais.
    """
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    birth_date: Optional[datetime] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    skin_type: Optional[str] = None
    allergies: Optional[str] = None
    preferences: Optional[str] = None
    notes: Optional[str] = None

class Customer(CustomerBase):
    """
    Modelo completo de cliente, incluindo campos gerados pelo sistema.
    Usado para respostas da API.
    """
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True
