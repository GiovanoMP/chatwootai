# -*- coding: utf-8 -*-

"""
Schemas para o módulo Semantic Product.
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime


class ProductDescriptionOptions(BaseModel):
    """Opções para geração de descrição de produto."""
    
    include_features: bool = Field(default=True, description="Incluir características do produto")
    include_use_cases: bool = Field(default=True, description="Incluir casos de uso do produto")
    tone: str = Field(default="professional", description="Tom da descrição (professional, casual, enthusiastic)")


class ProductDescriptionRequest(BaseModel):
    """Requisição para geração de descrição de produto."""
    
    options: Optional[ProductDescriptionOptions] = Field(default_factory=ProductDescriptionOptions, description="Opções para geração de descrição")


class ProductDescriptionResponse(BaseModel):
    """Resposta para geração de descrição de produto."""
    
    product_id: int = Field(description="ID do produto")
    description: str = Field(description="Descrição gerada")
    key_features: Optional[List[str]] = Field(default=None, description="Características principais")
    use_cases: Optional[List[str]] = Field(default=None, description="Casos de uso")


class ProductSyncRequest(BaseModel):
    """Requisição para sincronização de produto."""
    
    description: Optional[str] = Field(default=None, description="Descrição do produto")
    skip_odoo_update: bool = Field(default=False, description="Pular atualização do status no Odoo")


class ProductSyncResponse(BaseModel):
    """Resposta para sincronização de produto."""
    
    product_id: int = Field(description="ID do produto")
    vector_id: str = Field(description="ID do vetor no banco de dados vetorial")
    sync_status: str = Field(description="Status da sincronização")
    timestamp: datetime = Field(description="Timestamp da sincronização")


class ProductSearchFilter(BaseModel):
    """Filtro para busca de produtos."""
    
    category_id: Optional[int] = Field(default=None, description="ID da categoria")
    price_range: Optional[List[float]] = Field(default=None, description="Faixa de preço [min, max]")


class ProductSearchRequest(BaseModel):
    """Requisição para busca semântica de produtos."""
    
    query: str = Field(description="Consulta de busca")
    limit: int = Field(default=10, description="Limite de resultados")
    filters: Optional[ProductSearchFilter] = Field(default=None, description="Filtros adicionais")


class ProductSearchResult(BaseModel):
    """Resultado de busca de produto."""
    
    product_id: int = Field(description="ID do produto")
    name: str = Field(description="Nome do produto")
    description: Optional[str] = Field(default=None, description="Descrição do produto")
    score: float = Field(description="Pontuação de relevância")
    price: Optional[float] = Field(default=None, description="Preço do produto")
    category_id: Optional[int] = Field(default=None, description="ID da categoria")


class ProductSearchResponse(BaseModel):
    """Resposta para busca semântica de produtos."""
    
    results: List[ProductSearchResult] = Field(description="Resultados da busca")
    total: int = Field(description="Total de resultados")


class APIResponse(BaseModel):
    """Resposta padrão da API."""
    
    success: bool = Field(description="Indica se a operação foi bem-sucedida")
    data: Optional[Any] = Field(default=None, description="Dados da resposta")
    meta: Dict[str, Any] = Field(default_factory=dict, description="Metadados da resposta")
    error: Optional[Dict[str, Any]] = Field(default=None, description="Detalhes do erro, se houver")
