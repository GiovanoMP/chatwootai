# -*- coding: utf-8 -*-

"""
Schemas para o módulo Business Rules.
"""

from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field, validator
from datetime import datetime, date
from enum import Enum


class RuleType(str, Enum):
    """Tipos de regras de negócio."""

    GREETING = "greeting"
    BUSINESS_HOURS = "business_hours"
    DELIVERY = "delivery"
    PRICING = "pricing"
    PROMOTION = "promotion"
    CUSTOMER_SERVICE = "customer_service"
    PRODUCT = "product"
    CUSTOM = "custom"


class RulePriority(int, Enum):
    """Prioridades de regras de negócio."""

    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class BusinessHoursRule(BaseModel):
    """Regra de horário de funcionamento."""

    days: List[int] = Field(description="Dias da semana (0=Segunda, 6=Domingo)")
    start_time: str = Field(description="Hora de início (formato HH:MM)")
    end_time: str = Field(description="Hora de fim (formato HH:MM)")
    timezone: str = Field(description="Fuso horário (ex: America/Sao_Paulo)")

    @validator('days')
    def validate_days(cls, v):
        """Valida os dias da semana."""
        if not all(0 <= day <= 6 for day in v):
            raise ValueError("Dias devem estar entre 0 (Segunda) e 6 (Domingo)")
        return v

    @validator('start_time', 'end_time')
    def validate_time(cls, v):
        """Valida o formato da hora."""
        try:
            hours, minutes = v.split(':')
            if not (0 <= int(hours) <= 23 and 0 <= int(minutes) <= 59):
                raise ValueError()
        except:
            raise ValueError("Hora deve estar no formato HH:MM")
        return v


class DeliveryRule(BaseModel):
    """Regra de entrega."""

    min_days: int = Field(description="Mínimo de dias para entrega")
    max_days: int = Field(description="Máximo de dias para entrega")
    free_shipping_min_value: Optional[float] = Field(default=None, description="Valor mínimo para frete grátis")
    excluded_regions: Optional[List[str]] = Field(default=None, description="Regiões excluídas")
    shipping_methods: Optional[List[str]] = Field(default=None, description="Métodos de envio disponíveis")


class PricingRule(BaseModel):
    """Regra de precificação."""

    discount_percentage: Optional[float] = Field(default=None, description="Percentual de desconto")
    min_margin_percentage: Optional[float] = Field(default=None, description="Margem mínima percentual")
    round_to_nearest: Optional[float] = Field(default=None, description="Arredondar para o mais próximo")
    product_categories: Optional[List[int]] = Field(default=None, description="IDs das categorias de produtos")
    product_ids: Optional[List[int]] = Field(default=None, description="IDs dos produtos")


class PromotionRule(BaseModel):
    """Regra de promoção."""

    name: str = Field(description="Nome da promoção")
    description: str = Field(description="Descrição da promoção")
    discount_type: str = Field(description="Tipo de desconto (percentage, fixed)")
    discount_value: float = Field(description="Valor do desconto")
    min_purchase: Optional[float] = Field(default=None, description="Valor mínimo de compra")
    product_categories: Optional[List[int]] = Field(default=None, description="IDs das categorias de produtos")
    product_ids: Optional[List[int]] = Field(default=None, description="IDs dos produtos")
    coupon_code: Optional[str] = Field(default=None, description="Código do cupom")


class CustomerServiceRule(BaseModel):
    """Regra de atendimento ao cliente."""

    greeting_message: Optional[str] = Field(default=None, description="Mensagem de saudação")
    farewell_message: Optional[str] = Field(default=None, description="Mensagem de despedida")
    response_templates: Optional[Dict[str, str]] = Field(default=None, description="Templates de resposta")
    escalation_threshold: Optional[int] = Field(default=None, description="Limite para escalonamento")
    auto_response_keywords: Optional[List[str]] = Field(default=None, description="Palavras-chave para resposta automática")


class ProductRule(BaseModel):
    """Regra de produto."""

    min_stock_alert: Optional[int] = Field(default=None, description="Alerta de estoque mínimo")
    max_stock_alert: Optional[int] = Field(default=None, description="Alerta de estoque máximo")
    reorder_point: Optional[int] = Field(default=None, description="Ponto de reposição")
    product_categories: Optional[List[int]] = Field(default=None, description="IDs das categorias de produtos")
    product_ids: Optional[List[int]] = Field(default=None, description="IDs dos produtos")


class CustomRule(BaseModel):
    """Regra personalizada."""

    content: Dict[str, Any] = Field(description="Conteúdo da regra personalizada")


class BusinessRuleRequest(BaseModel):
    """Requisição para criação/atualização de regra de negócio."""

    name: str = Field(description="Nome da regra")
    description: str = Field(description="Descrição da regra")
    type: RuleType = Field(description="Tipo da regra")
    priority: RulePriority = Field(default=RulePriority.MEDIUM, description="Prioridade da regra")
    active: bool = Field(default=True, description="Indica se a regra está ativa")
    rule_data: Union[
        BusinessHoursRule,
        DeliveryRule,
        PricingRule,
        PromotionRule,
        CustomerServiceRule,
        ProductRule,
        CustomRule,
        Dict[str, Any]
    ] = Field(description="Dados específicos da regra")


class TemporaryRuleRequest(BusinessRuleRequest):
    """Requisição para criação/atualização de regra temporária."""

    start_date: date = Field(description="Data de início da regra")
    end_date: date = Field(description="Data de fim da regra")

    @validator('end_date')
    def validate_end_date(cls, v, values):
        """Valida a data de fim."""
        if 'start_date' in values and v < values['start_date']:
            raise ValueError("Data de fim deve ser posterior à data de início")
        return v


class BusinessRuleResponse(BaseModel):
    """Resposta para operações de regra de negócio."""

    id: int = Field(description="ID da regra")
    name: str = Field(description="Nome da regra")
    description: str = Field(description="Descrição da regra")
    type: str = Field(description="Tipo da regra")
    priority: int = Field(description="Prioridade da regra")
    active: bool = Field(description="Indica se a regra está ativa")
    rule_data: Dict[str, Any] = Field(description="Dados específicos da regra")
    is_temporary: bool = Field(description="Indica se é uma regra temporária")
    start_date: Optional[date] = Field(default=None, description="Data de início (se temporária)")
    end_date: Optional[date] = Field(default=None, description="Data de fim (se temporária)")
    created_at: datetime = Field(description="Data de criação")
    updated_at: datetime = Field(description="Data de última atualização")


class BusinessRuleListResponse(BaseModel):
    """Resposta para listagem de regras de negócio."""

    rules: List[BusinessRuleResponse] = Field(description="Lista de regras")
    total: int = Field(description="Total de regras")
    page: int = Field(description="Página atual")
    page_size: int = Field(description="Tamanho da página")
    total_pages: int = Field(description="Total de páginas")


class BusinessRuleSyncResponse(BaseModel):
    """Resposta para sincronização de regras de negócio."""

    permanent_rules: int = Field(description="Número de regras permanentes sincronizadas")
    temporary_rules: int = Field(description="Número de regras temporárias sincronizadas")
    vectorized_rules: int = Field(description="Número de regras vetorizadas no Qdrant")
    sync_status: str = Field(description="Status da sincronização")
    timestamp: datetime = Field(description="Timestamp da sincronização")


class DocumentUploadRequest(BaseModel):
    """Requisição para upload de documento."""

    name: str = Field(description="Nome do documento")
    description: str = Field(description="Descrição do documento")
    document_type: str = Field(description="Tipo do documento (pdf, docx)")
    content_base64: str = Field(description="Conteúdo do documento em base64")


class DocumentResponse(BaseModel):
    """Resposta para operações de documento."""

    id: int = Field(description="ID do documento")
    name: str = Field(description="Nome do documento")
    description: str = Field(description="Descrição do documento")
    document_type: str = Field(description="Tipo do documento")
    created_at: datetime = Field(description="Data de criação")
    updated_at: datetime = Field(description="Data de última atualização")
    status: str = Field(description="Status do processamento")


class DocumentListResponse(BaseModel):
    """Resposta para listagem de documentos."""

    documents: List[DocumentResponse] = Field(description="Lista de documentos")
    total: int = Field(description="Total de documentos")


class GreetingStyleConfig(BaseModel):
    """Configuração de saudação."""

    enabled: bool = Field(description="Se a saudação está habilitada")
    message: str = Field(description="Mensagem de saudação")


class FarewellStyleConfig(BaseModel):
    """Configuração de despedida."""

    enabled: bool = Field(description="Se a despedida está habilitada")
    message: str = Field(description="Mensagem de despedida")


class EmojisStyleConfig(BaseModel):
    """Configuração de emojis."""

    enabled: bool = Field(description="Se o uso de emojis está habilitado")
    frequency: str = Field(description="Frequência de uso de emojis (none, minimal, moderate, frequent)")


class ToneStyleConfig(BaseModel):
    """Configuração de tom."""

    formal: int = Field(description="Nível de formalidade (1-5)")
    friendly: int = Field(description="Nível de amigabilidade (1-5)")
    technical: int = Field(description="Nível técnico (1-5)")


class CustomerServiceStyleConfig(BaseModel):
    """Configuração de estilo para a crew de atendimento ao cliente."""

    greeting: GreetingStyleConfig = Field(description="Configuração de saudação")
    farewell: FarewellStyleConfig = Field(description="Configuração de despedida")
    emojis: EmojisStyleConfig = Field(description="Configuração de emojis")
    tone: ToneStyleConfig = Field(description="Configuração de tom")


class APIResponse(BaseModel):
    """Resposta padrão da API."""

    success: bool = Field(description="Indica se a operação foi bem-sucedida")
    data: Optional[Any] = Field(default=None, description="Dados da resposta")
    meta: Dict[str, Any] = Field(default_factory=dict, description="Metadados da resposta")
    error: Optional[Dict[str, Any]] = Field(default=None, description="Detalhes do erro, se houver")
