"""
Modelos Pydantic para produtos na API de simulação do Odoo.
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field

class ProductBase(BaseModel):
    """Modelo base para produtos com campos comuns."""
    name: str = Field(..., description="Nome do produto")
    description: Optional[str] = Field(None, description="Descrição detalhada do produto")
    category_id: int = Field(..., description="ID da categoria do produto")
    price: float = Field(..., description="Preço de venda do produto")
    cost: Optional[float] = Field(None, description="Custo do produto")
    sku: Optional[str] = Field(None, description="Código de referência do produto (Stock Keeping Unit)")
    barcode: Optional[str] = Field(None, description="Código de barras do produto")
    weight: Optional[float] = Field(None, description="Peso do produto em gramas")
    volume: Optional[float] = Field(None, description="Volume do produto em mililitros")
    ingredients: Optional[str] = Field(None, description="Lista de ingredientes do produto")
    benefits: Optional[str] = Field(None, description="Benefícios do produto")
    usage_instructions: Optional[str] = Field(None, description="Instruções de uso do produto")
    image_url: Optional[str] = Field(None, description="URL da imagem do produto")
    active: bool = Field(True, description="Indica se o produto está ativo")

class ProductCreate(ProductBase):
    """Modelo para criação de novos produtos."""
    pass

class ProductUpdate(BaseModel):
    """
    Modelo para atualização de produtos.
    Todos os campos são opcionais para permitir atualizações parciais.
    """
    name: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[int] = None
    price: Optional[float] = None
    cost: Optional[float] = None
    sku: Optional[str] = None
    barcode: Optional[str] = None
    weight: Optional[float] = None
    volume: Optional[float] = None
    ingredients: Optional[str] = None
    benefits: Optional[str] = None
    usage_instructions: Optional[str] = None
    image_url: Optional[str] = None
    active: Optional[bool] = None

class Product(ProductBase):
    """
    Modelo completo de produto, incluindo campos gerados pelo sistema.
    Usado para respostas da API.
    """
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class ProductCategory(BaseModel):
    """Modelo para categorias de produtos."""
    id: int
    name: str
    description: Optional[str] = None
    parent_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class ProductInventory(BaseModel):
    """Modelo para informações de estoque de produtos."""
    id: int
    product_id: int
    quantity: int
    location: Optional[str] = None
    min_quantity: Optional[int] = None
    max_quantity: Optional[int] = None
    last_restock_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class ProductEnrichment(BaseModel):
    """Modelo para informações enriquecidas de produtos."""
    id: int
    product_id: int
    source: str
    content_type: str
    content: str
    relevance_score: Optional[float] = None
    last_updated: datetime
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True
