"""
Esquemas de dados para a API REST de integração com o Odoo.

Este módulo define os modelos Pydantic utilizados para validação de dados
na API REST de integração com o Odoo.

Autor: Augment Agent
Data: 26/03/2025
"""

from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, validator

class ProductAttributeValue(BaseModel):
    """Valor de um atributo de produto."""
    id: int
    name: str
    
class ProductAttribute(BaseModel):
    """Atributo de produto."""
    id: int
    name: str
    values: List[ProductAttributeValue]

class ProductCategory(BaseModel):
    """Categoria de produto."""
    id: int
    name: str
    parent_id: Optional[int] = None
    parent_name: Optional[str] = None
    
class ProductImage(BaseModel):
    """Imagem de produto."""
    id: int
    name: Optional[str] = None
    url: str
    
class ProductVariant(BaseModel):
    """Variante de produto."""
    id: int
    name: str
    default_code: Optional[str] = None
    barcode: Optional[str] = None
    list_price: float
    attributes: Dict[str, str] = Field(default_factory=dict)
    
class ProductMetadata(BaseModel):
    """Metadados completos de um produto."""
    product_id: int
    name: str
    description: Optional[str] = None
    description_sale: Optional[str] = None
    categ_id: Optional[int] = None
    categ_name: Optional[str] = None
    list_price: Optional[float] = None
    default_code: Optional[str] = None
    barcode: Optional[str] = None
    active: bool = True
    sale_ok: bool = True
    purchase_ok: bool = True
    type: str = "product"
    category: Optional[ProductCategory] = None
    attributes: List[ProductAttribute] = Field(default_factory=list)
    variants: List[ProductVariant] = Field(default_factory=list)
    images: List[ProductImage] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    
class TaskType(str, Enum):
    """Tipos de tarefas para processamento assíncrono."""
    SYNC_PRODUCT = "sync_product"
    GENERATE_DESCRIPTION = "generate_description"
    UPDATE_EMBEDDING = "update_embedding"
    DELETE_PRODUCT = "delete_product"
    
class TaskStatus(str, Enum):
    """Status possíveis para uma tarefa."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    
class WebhookRequest(BaseModel):
    """Modelo para requisições de webhook do Odoo."""
    metadata: Dict[str, Any] = Field(..., description="Metadados da requisição")
    params: Dict[str, Any] = Field(..., description="Parâmetros da requisição")
    
    @validator('metadata')
    def validate_metadata(cls, v):
        """Valida os metadados da requisição."""
        required_fields = ["source", "action"]
        for field in required_fields:
            if field not in v:
                raise ValueError(f"Campo obrigatório '{field}' não encontrado em metadata")
        
        if v.get("source") != "odoo":
            raise ValueError(f"Fonte inválida: {v.get('source')}. Esperado: 'odoo'")
        
        return v

class WebhookResponse(BaseModel):
    """Modelo para respostas de webhook."""
    success: bool
    message: str
    request_id: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    
class TaskStatusResponse(BaseModel):
    """Modelo para resposta de status de tarefa."""
    request_id: str
    status: TaskStatus
    message: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    
class DescriptionGenerationRequest(BaseModel):
    """Modelo para requisição de geração de descrição."""
    product_id: int
    account_id: str
    metadata: Dict[str, Any]
    
class DescriptionGenerationResponse(BaseModel):
    """Modelo para resposta de geração de descrição."""
    product_id: int
    description: str
    embedding_id: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
