from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime

class ConfigBase(BaseModel):
    """Esquema base para configurações"""
    yaml_content: str = Field(
        ...,
        description="Conteúdo YAML da configuração",
        example="tenant_id: account_1\ndomain: retail\nname: Example Company"
    )

class ConfigCreate(ConfigBase):
    """Esquema para criação de configuração"""
    pass

class ConfigUpdate(ConfigBase):
    """Esquema para atualização de configuração"""
    pass

class ConfigInDB(ConfigBase):
    """Esquema para configuração armazenada no banco de dados"""
    id: int
    tenant_id: str
    domain: str
    config_type: str
    version: int
    json_data: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }

class ConfigInfo(BaseModel):
    """Esquema para informações resumidas de configuração"""
    tenant_id: str
    domain: str
    config_type: str
    version: int
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }
