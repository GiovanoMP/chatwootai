from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime

class MappingBase(BaseModel):
    """Esquema base para mapeamento"""
    mapping_data: Dict[str, Any] = Field(
        ...,
        description="Dados do mapeamento em formato JSON",
        example={
            "accounts": {
                "1": {
                    "account_id": "account_1",
                    "domain": "retail"
                }
            },
            "inboxes": {
                "1": {
                    "account_id": "account_1",
                    "domain": "retail"
                }
            },
            "fallbacks": [],
            "special_numbers": []
        }
    )

class MappingCreate(MappingBase):
    """Esquema para criação de mapeamento"""
    pass

class MappingUpdate(MappingBase):
    """Esquema para atualização de mapeamento"""
    pass

class MappingInDB(MappingBase):
    """Esquema para mapeamento armazenado no banco de dados"""
    id: int
    version: int
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }
