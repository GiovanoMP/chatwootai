"""
Modelos para regras de agendamento.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class DaysAvailable(BaseModel):
    """Modelo para dias disponíveis."""
    
    monday: bool = False
    tuesday: bool = False
    wednesday: bool = False
    thursday: bool = False
    friday: bool = False
    saturday: bool = False
    sunday: bool = False

class Hours(BaseModel):
    """Modelo para horários."""
    
    morning_start: str
    morning_end: str
    afternoon_start: str
    afternoon_end: str
    has_lunch_break: bool = True

class SpecialDayHours(BaseModel):
    """Modelo para horários especiais."""
    
    morning_start: str
    morning_end: str
    afternoon_start: Optional[str] = None
    afternoon_end: Optional[str] = None
    has_afternoon: bool = False

class SpecialHours(BaseModel):
    """Modelo para horários especiais por dia."""
    
    saturday: SpecialDayHours
    sunday: SpecialDayHours

class Policies(BaseModel):
    """Modelo para políticas de agendamento."""
    
    cancellation: str = ""
    rescheduling: str = ""
    required_information: str = ""
    confirmation_instructions: str = ""

class SchedulingRule(BaseModel):
    """Modelo para regra de agendamento."""
    
    id: int
    name: str
    description: str = ""
    service_type: str
    service_type_other: str = ""
    duration: int
    min_interval: int
    min_advance_time: int
    max_advance_time: int
    days_available: DaysAvailable
    hours: Hours
    special_hours: SpecialHours
    policies: Policies
    last_updated: str

class SchedulingRuleSync(BaseModel):
    """Modelo para sincronização de regras de agendamento."""
    
    account_id: str
    business_rule_id: int
    scheduling_rules: List[SchedulingRule] = Field(default_factory=list)

class SchedulingRuleResponse(BaseModel):
    """Modelo para resposta de sincronização de regras de agendamento."""
    
    success: bool
    data: Dict[str, Any]
    message: str
