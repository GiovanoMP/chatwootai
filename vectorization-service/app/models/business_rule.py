"""
Modelos para regras de negócio.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

class PermanentRule(BaseModel):
    """Modelo para regra de negócio permanente."""
    
    id: int
    name: str
    description: str
    type: str
    last_updated: str

class TemporaryRule(BaseModel):
    """Modelo para regra de negócio temporária."""
    
    id: int
    name: str
    description: str
    type: str
    start_date: str
    end_date: str
    last_updated: str

class BusinessRules(BaseModel):
    """Modelo para conjunto de regras de negócio."""
    
    permanent_rules: List[PermanentRule] = Field(default_factory=list)
    temporary_rules: List[TemporaryRule] = Field(default_factory=list)

class BusinessRuleSync(BaseModel):
    """Modelo para sincronização de regras de negócio."""
    
    account_id: str
    business_rule_id: int
    rules: BusinessRules

class BusinessRuleResponse(BaseModel):
    """Modelo para resposta de sincronização de regras de negócio."""
    
    success: bool
    data: Dict[str, Any]
    message: str

class BusinessRuleSearch(BaseModel):
    """Modelo para busca de regras de negócio."""
    
    account_id: str
    query: str
    limit: int = 5
    score_threshold: float = 0.7
