"""
Modelos Pydantic para agendamentos na API de simulação do Odoo.
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field

class AppointmentBase(BaseModel):
    """Modelo base para agendamentos."""
    customer_id: int = Field(..., description="ID do cliente")
    service_id: int = Field(..., description="ID do serviço")
    professional_id: int = Field(..., description="ID do profissional")
    start_time: datetime = Field(..., description="Data e hora de início")
    end_time: datetime = Field(..., description="Data e hora de término")
    status: str = Field("scheduled", description="Status do agendamento (scheduled, confirmed, in_progress, completed, cancelled, no_show)")
    notes: Optional[str] = Field(None, description="Observações adicionais")

class AppointmentCreate(AppointmentBase):
    """Modelo para criação de novos agendamentos."""
    pass

class AppointmentUpdate(BaseModel):
    """
    Modelo para atualização de agendamentos.
    Todos os campos são opcionais para permitir atualizações parciais.
    """
    service_id: Optional[int] = None
    professional_id: Optional[int] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: Optional[str] = None
    notes: Optional[str] = None

class Appointment(AppointmentBase):
    """
    Modelo completo de agendamento, incluindo campos gerados pelo sistema.
    Usado para respostas da API.
    """
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class AppointmentWithDetails(Appointment):
    """
    Modelo estendido de agendamento com informações adicionais.
    Usado para respostas detalhadas da API.
    """
    customer_name: Optional[str] = None
    service_name: Optional[str] = None
    service_duration: Optional[int] = None
    professional_name: Optional[str] = None
    
    class Config:
        orm_mode = True

class TimeSlot(BaseModel):
    """Modelo para representar um slot de tempo disponível para agendamento."""
    professional_id: int
    professional_name: str
    start_time: datetime
    end_time: datetime
    is_available: bool
