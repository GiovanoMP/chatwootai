# -*- coding: utf-8 -*-

"""
Schemas para o módulo Product Management.
"""

from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime


class ProductBatchSyncOptions(BaseModel):
    """Opções para sincronização em massa de produtos."""
    
    generate_descriptions: bool = Field(default=True, description="Gerar descrições para produtos sem descrição")
    skip_odoo_update: bool = Field(default=False, description="Pular atualização do status no Odoo")
    force_update: bool = Field(default=False, description="Forçar atualização mesmo para produtos já sincronizados")


class ProductBatchSyncRequest(BaseModel):
    """Requisição para sincronização em massa de produtos."""
    
    product_ids: List[int] = Field(description="Lista de IDs de produtos para sincronizar")
    options: Optional[ProductBatchSyncOptions] = Field(default_factory=ProductBatchSyncOptions, description="Opções para sincronização")


class ProductSyncResult(BaseModel):
    """Resultado da sincronização de um produto."""
    
    product_id: int = Field(description="ID do produto")
    status: str = Field(description="Status da sincronização (completed, failed)")
    vector_id: Optional[str] = Field(default=None, description="ID do vetor no banco de dados vetorial")
    error: Optional[str] = Field(default=None, description="Mensagem de erro, se houver")


class ProductBatchSyncResponse(BaseModel):
    """Resposta para sincronização em massa de produtos."""
    
    total: int = Field(description="Total de produtos processados")
    successful: int = Field(description="Número de produtos sincronizados com sucesso")
    failed: int = Field(description="Número de produtos que falharam na sincronização")
    results: List[ProductSyncResult] = Field(description="Resultados individuais")
    job_id: Optional[str] = Field(default=None, description="ID do job para consulta posterior")


class PriceAdjustment(BaseModel):
    """Ajuste de preço para produtos."""
    
    type: str = Field(description="Tipo de ajuste (percentage, fixed)")
    value: float = Field(description="Valor do ajuste")
    field: str = Field(default="ai_price", description="Campo de preço a ser ajustado")


class PriceUpdateRequest(BaseModel):
    """Requisição para atualização de preços em massa."""
    
    product_ids: List[int] = Field(description="Lista de IDs de produtos para atualizar")
    adjustment: PriceAdjustment = Field(description="Ajuste de preço a ser aplicado")


class PriceUpdateResult(BaseModel):
    """Resultado da atualização de preço de um produto."""
    
    product_id: int = Field(description="ID do produto")
    old_price: float = Field(description="Preço antigo")
    new_price: float = Field(description="Novo preço")
    error: Optional[str] = Field(default=None, description="Mensagem de erro, se houver")


class PriceUpdateResponse(BaseModel):
    """Resposta para atualização de preços em massa."""
    
    total: int = Field(description="Total de produtos processados")
    successful: int = Field(description="Número de produtos atualizados com sucesso")
    failed: int = Field(description="Número de produtos que falharam na atualização")
    results: List[PriceUpdateResult] = Field(description="Resultados individuais")


class SyncStatus(BaseModel):
    """Status de sincronização de um produto."""
    
    product_id: int = Field(description="ID do produto")
    sync_status: str = Field(description="Status de sincronização (synced, not_synced, pending)")
    last_sync: Optional[datetime] = Field(default=None, description="Data da última sincronização")
    vector_id: Optional[str] = Field(default=None, description="ID do vetor no banco de dados vetorial")


class SyncStatusResponse(BaseModel):
    """Resposta para verificação de status de sincronização."""
    
    total: int = Field(description="Total de produtos verificados")
    synced: int = Field(description="Número de produtos sincronizados")
    not_synced: int = Field(description="Número de produtos não sincronizados")
    products: List[SyncStatus] = Field(description="Status individual de cada produto")


class ProductFilter(BaseModel):
    """Filtro para busca de produtos."""
    
    category_ids: Optional[List[int]] = Field(default=None, description="IDs de categorias")
    price_range: Optional[List[float]] = Field(default=None, description="Faixa de preço [min, max]")
    sync_status: Optional[str] = Field(default=None, description="Status de sincronização (synced, not_synced, pending)")
    search_term: Optional[str] = Field(default=None, description="Termo de busca para nome ou código")


class ProductListRequest(BaseModel):
    """Requisição para listagem de produtos."""
    
    filter: Optional[ProductFilter] = Field(default=None, description="Filtro para produtos")
    limit: int = Field(default=50, description="Limite de resultados")
    offset: int = Field(default=0, description="Offset para paginação")
    order_by: Optional[str] = Field(default="name", description="Campo para ordenação")
    order_dir: Optional[str] = Field(default="asc", description="Direção da ordenação (asc, desc)")


class ProductInfo(BaseModel):
    """Informações básicas de um produto."""
    
    product_id: int = Field(description="ID do produto")
    name: str = Field(description="Nome do produto")
    default_code: Optional[str] = Field(default=None, description="Código do produto")
    list_price: float = Field(description="Preço de lista")
    ai_price: Optional[float] = Field(default=None, description="Preço AI")
    category_id: Optional[int] = Field(default=None, description="ID da categoria")
    category_name: Optional[str] = Field(default=None, description="Nome da categoria")
    sync_status: str = Field(description="Status de sincronização")
    last_sync: Optional[datetime] = Field(default=None, description="Data da última sincronização")


class ProductListResponse(BaseModel):
    """Resposta para listagem de produtos."""
    
    total: int = Field(description="Total de produtos encontrados")
    limit: int = Field(description="Limite de resultados")
    offset: int = Field(description="Offset para paginação")
    products: List[ProductInfo] = Field(description="Lista de produtos")


class APIResponse(BaseModel):
    """Resposta padrão da API."""
    
    success: bool = Field(description="Indica se a operação foi bem-sucedida")
    data: Optional[Any] = Field(default=None, description="Dados da resposta")
    meta: Dict[str, Any] = Field(default_factory=dict, description="Metadados da resposta")
    error: Optional[Dict[str, Any]] = Field(default=None, description="Detalhes do erro, se houver")
