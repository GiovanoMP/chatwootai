"""
Modelos Pydantic para pedidos na API de simulação do Odoo.
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field

class OrderItemBase(BaseModel):
    """Modelo base para itens de pedido."""
    order_id: int = Field(..., description="ID do pedido")
    product_id: int = Field(..., description="ID do produto")
    quantity: int = Field(..., description="Quantidade do produto")
    unit_price: float = Field(..., description="Preço unitário do produto")
    discount: float = Field(0, description="Valor do desconto")
    total_price: float = Field(..., description="Preço total do item (quantidade * unit_price - discount)")

class OrderItemCreate(BaseModel):
    """Modelo para criação de novos itens de pedido."""
    product_id: int = Field(..., description="ID do produto")
    quantity: int = Field(..., description="Quantidade do produto")
    unit_price: Optional[float] = Field(None, description="Preço unitário do produto (opcional, será obtido do produto se não informado)")
    discount: float = Field(0, description="Valor do desconto")

class OrderItemUpdate(BaseModel):
    """
    Modelo para atualização de itens de pedido.
    Todos os campos são opcionais para permitir atualizações parciais.
    """
    quantity: Optional[int] = None
    unit_price: Optional[float] = None
    discount: Optional[float] = None

class OrderItem(OrderItemBase):
    """
    Modelo completo de item de pedido, incluindo campos gerados pelo sistema.
    Usado para respostas da API.
    """
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class OrderBase(BaseModel):
    """Modelo base para pedidos."""
    customer_id: int = Field(..., description="ID do cliente")
    status: str = Field("pending", description="Status do pedido (pending, confirmed, shipped, delivered, cancelled)")
    total_amount: float = Field(..., description="Valor total do pedido")
    shipping_address: Optional[str] = Field(None, description="Endereço de entrega")
    shipping_city: Optional[str] = Field(None, description="Cidade de entrega")
    shipping_state: Optional[str] = Field(None, description="Estado de entrega")
    shipping_postal_code: Optional[str] = Field(None, description="CEP de entrega")
    shipping_country: Optional[str] = Field("Brasil", description="País de entrega")
    shipping_method: Optional[str] = Field(None, description="Método de envio")
    tracking_number: Optional[str] = Field(None, description="Número de rastreamento")
    payment_method: Optional[str] = Field(None, description="Método de pagamento")
    payment_status: str = Field("pending", description="Status do pagamento (pending, paid, failed, refunded)")
    notes: Optional[str] = Field(None, description="Observações adicionais")

class OrderCreate(BaseModel):
    """Modelo para criação de novos pedidos."""
    customer_id: int = Field(..., description="ID do cliente")
    items: List[OrderItemCreate] = Field(..., description="Itens do pedido")
    shipping_address: Optional[str] = Field(None, description="Endereço de entrega")
    shipping_city: Optional[str] = Field(None, description="Cidade de entrega")
    shipping_state: Optional[str] = Field(None, description="Estado de entrega")
    shipping_postal_code: Optional[str] = Field(None, description="CEP de entrega")
    shipping_country: Optional[str] = Field("Brasil", description="País de entrega")
    shipping_method: Optional[str] = Field(None, description="Método de envio")
    payment_method: Optional[str] = Field(None, description="Método de pagamento")
    notes: Optional[str] = Field(None, description="Observações adicionais")

class OrderUpdate(BaseModel):
    """
    Modelo para atualização de pedidos.
    Todos os campos são opcionais para permitir atualizações parciais.
    """
    status: Optional[str] = None
    shipping_address: Optional[str] = None
    shipping_city: Optional[str] = None
    shipping_state: Optional[str] = None
    shipping_postal_code: Optional[str] = None
    shipping_country: Optional[str] = None
    shipping_method: Optional[str] = None
    tracking_number: Optional[str] = None
    payment_method: Optional[str] = None
    payment_status: Optional[str] = None
    notes: Optional[str] = None

class Order(OrderBase):
    """
    Modelo completo de pedido, incluindo campos gerados pelo sistema.
    Usado para respostas da API.
    """
    id: int
    order_date: datetime
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class OrderWithItems(Order):
    """
    Modelo estendido de pedido com itens.
    Usado para respostas detalhadas da API.
    """
    items: List[OrderItem]
    customer_name: Optional[str] = None
    
    class Config:
        orm_mode = True
