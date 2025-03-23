"""
Odoo Simulation API.

This module implements a FastAPI-based simulation of the Odoo API,
providing endpoints for products, customers, orders, and business rules.
"""

import logging
import os
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from fastapi import FastAPI, Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuração do banco de dados
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "chatwootai")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")

DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

# Configuração de segurança
API_KEY_NAME = "X-API-Key"
API_KEY = os.getenv("API_KEY", "test_api_key")
api_key_header = APIKeyHeader(name=API_KEY_NAME)

# Configuração do SQLAlchemy
engine = sa.create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Modelos SQLAlchemy
class Product(Base):
    __tablename__ = "products"
    
    id = sa.Column(sa.Integer, primary_key=True, index=True)
    name = sa.Column(sa.String, index=True)
    description = sa.Column(sa.Text)
    price = sa.Column(sa.Float)
    category = sa.Column(sa.String, index=True)
    stock = sa.Column(sa.Integer)
    created_at = sa.Column(sa.DateTime, default=datetime.utcnow)
    updated_at = sa.Column(sa.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Customer(Base):
    __tablename__ = "customers"
    
    id = sa.Column(sa.Integer, primary_key=True, index=True)
    name = sa.Column(sa.String, index=True)
    email = sa.Column(sa.String, unique=True, index=True)
    phone = sa.Column(sa.String)
    address = sa.Column(sa.String)
    loyalty_level = sa.Column(sa.String, default="standard")
    created_at = sa.Column(sa.DateTime, default=datetime.utcnow)
    updated_at = sa.Column(sa.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Order(Base):
    __tablename__ = "orders"
    
    id = sa.Column(sa.Integer, primary_key=True, index=True)
    customer_id = sa.Column(sa.Integer, sa.ForeignKey("customers.id"))
    total_amount = sa.Column(sa.Float)
    status = sa.Column(sa.String, default="pending")
    created_at = sa.Column(sa.DateTime, default=datetime.utcnow)
    updated_at = sa.Column(sa.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class OrderItem(Base):
    __tablename__ = "order_items"
    
    id = sa.Column(sa.Integer, primary_key=True, index=True)
    order_id = sa.Column(sa.Integer, sa.ForeignKey("orders.id"))
    product_id = sa.Column(sa.Integer, sa.ForeignKey("products.id"))
    quantity = sa.Column(sa.Integer)
    price = sa.Column(sa.Float)
    created_at = sa.Column(sa.DateTime, default=datetime.utcnow)


class BusinessRule(Base):
    __tablename__ = "business_rules"
    
    id = sa.Column(sa.Integer, primary_key=True, index=True)
    name = sa.Column(sa.String, index=True)
    description = sa.Column(sa.Text)
    category = sa.Column(sa.String, index=True)
    rule_text = sa.Column(sa.Text)
    active = sa.Column(sa.Boolean, default=True)
    created_at = sa.Column(sa.DateTime, default=datetime.utcnow)
    updated_at = sa.Column(sa.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# Modelos Pydantic
class ProductBase(BaseModel):
    name: str
    description: str
    price: float
    category: str
    stock: int


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    category: Optional[str] = None
    stock: Optional[int] = None


class ProductResponse(ProductBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True


class CustomerBase(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    address: Optional[str] = None
    loyalty_level: str = "standard"


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    loyalty_level: Optional[str] = None


class CustomerResponse(CustomerBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True


class OrderItemBase(BaseModel):
    product_id: int
    quantity: int
    price: float


class OrderItemCreate(OrderItemBase):
    pass


class OrderItemResponse(OrderItemBase):
    id: int
    order_id: int
    created_at: datetime
    
    class Config:
        orm_mode = True


class OrderBase(BaseModel):
    customer_id: int
    total_amount: float
    status: str = "pending"
    items: List[OrderItemCreate]


class OrderCreate(OrderBase):
    pass


class OrderUpdate(BaseModel):
    status: Optional[str] = None
    total_amount: Optional[float] = None


class OrderResponse(BaseModel):
    id: int
    customer_id: int
    total_amount: float
    status: str
    created_at: datetime
    updated_at: datetime
    items: List[OrderItemResponse]
    
    class Config:
        orm_mode = True


class BusinessRuleBase(BaseModel):
    name: str
    description: str
    category: str
    rule_text: str
    active: bool = True


class BusinessRuleCreate(BusinessRuleBase):
    pass


class BusinessRuleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    rule_text: Optional[str] = None
    active: Optional[bool] = None


class BusinessRuleResponse(BusinessRuleBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True


# Dependências
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key",
        )
    return api_key


# Aplicação FastAPI
app = FastAPI(
    title="Odoo Simulation API",
    description="API para simulação do Odoo para o projeto ChatwootAI",
    version="1.0.0",
)

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Endpoints para produtos
@app.post("/products/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(
    product: ProductCreate,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    db_product = Product(**product.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


@app.get("/products/", response_model=List[ProductResponse])
def read_products(
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = None,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    query = db.query(Product)
    if category:
        query = query.filter(Product.category == category)
    return query.offset(skip).limit(limit).all()


@app.get("/products/{product_id}", response_model=ProductResponse)
def read_product(
    product_id: int,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return db_product


@app.put("/products/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    product: ProductUpdate,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    
    update_data = product.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_product, key, value)
    
    db_product.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_product)
    return db_product


@app.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    
    db.delete(db_product)
    db.commit()
    return None


# Endpoints para clientes
@app.post("/customers/", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
def create_customer(
    customer: CustomerCreate,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    db_customer = Customer(**customer.dict())
    db.add(db_customer)
    db.commit()
    db.refresh(db_customer)
    return db_customer


@app.get("/customers/", response_model=List[CustomerResponse])
def read_customers(
    skip: int = 0,
    limit: int = 100,
    loyalty_level: Optional[str] = None,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    query = db.query(Customer)
    if loyalty_level:
        query = query.filter(Customer.loyalty_level == loyalty_level)
    return query.offset(skip).limit(limit).all()


@app.get("/customers/{customer_id}", response_model=CustomerResponse)
def read_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    db_customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if db_customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    return db_customer


@app.put("/customers/{customer_id}", response_model=CustomerResponse)
def update_customer(
    customer_id: int,
    customer: CustomerUpdate,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    db_customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if db_customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    update_data = customer.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_customer, key, value)
    
    db_customer.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_customer)
    return db_customer


@app.delete("/customers/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    db_customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if db_customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    db.delete(db_customer)
    db.commit()
    return None


# Endpoints para pedidos
@app.post("/orders/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(
    order: OrderCreate,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    # Verificar se o cliente existe
    db_customer = db.query(Customer).filter(Customer.id == order.customer_id).first()
    if db_customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Criar o pedido
    db_order = Order(
        customer_id=order.customer_id,
        total_amount=order.total_amount,
        status=order.status
    )
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    
    # Criar os itens do pedido
    order_items = []
    for item in order.items:
        db_product = db.query(Product).filter(Product.id == item.product_id).first()
        if db_product is None:
            db.delete(db_order)
            db.commit()
            raise HTTPException(status_code=404, detail=f"Product {item.product_id} not found")
        
        # Verificar estoque
        if db_product.stock < item.quantity:
            db.delete(db_order)
            db.commit()
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock for product {db_product.name}"
            )
        
        # Atualizar estoque
        db_product.stock -= item.quantity
        
        # Criar item do pedido
        db_order_item = OrderItem(
            order_id=db_order.id,
            product_id=item.product_id,
            quantity=item.quantity,
            price=item.price
        )
        db.add(db_order_item)
        order_items.append(db_order_item)
    
    db.commit()
    
    # Atualizar os itens do pedido na resposta
    for item in order_items:
        db.refresh(item)
    
    # Obter o pedido completo com itens
    result = db.query(Order).filter(Order.id == db_order.id).first()
    result.items = order_items
    
    return result


@app.get("/orders/", response_model=List[OrderResponse])
def read_orders(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    customer_id: Optional[int] = None,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    query = db.query(Order)
    if status:
        query = query.filter(Order.status == status)
    if customer_id:
        query = query.filter(Order.customer_id == customer_id)
    
    orders = query.offset(skip).limit(limit).all()
    
    # Adicionar itens aos pedidos
    for order in orders:
        order.items = db.query(OrderItem).filter(OrderItem.order_id == order.id).all()
    
    return orders


@app.get("/orders/{order_id}", response_model=OrderResponse)
def read_order(
    order_id: int,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    db_order = db.query(Order).filter(Order.id == order_id).first()
    if db_order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Adicionar itens ao pedido
    db_order.items = db.query(OrderItem).filter(OrderItem.order_id == order_id).all()
    
    return db_order


@app.put("/orders/{order_id}", response_model=OrderResponse)
def update_order(
    order_id: int,
    order: OrderUpdate,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    db_order = db.query(Order).filter(Order.id == order_id).first()
    if db_order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    
    update_data = order.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_order, key, value)
    
    db_order.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_order)
    
    # Adicionar itens ao pedido
    db_order.items = db.query(OrderItem).filter(OrderItem.order_id == order_id).all()
    
    return db_order


@app.delete("/orders/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_order(
    order_id: int,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    db_order = db.query(Order).filter(Order.id == order_id).first()
    if db_order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Excluir itens do pedido
    db.query(OrderItem).filter(OrderItem.order_id == order_id).delete()
    
    # Excluir o pedido
    db.delete(db_order)
    db.commit()
    return None


# Endpoints para regras de negócio
@app.post("/business-rules/", response_model=BusinessRuleResponse, status_code=status.HTTP_201_CREATED)
def create_business_rule(
    rule: BusinessRuleCreate,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    db_rule = BusinessRule(**rule.dict())
    db.add(db_rule)
    db.commit()
    db.refresh(db_rule)
    return db_rule


@app.get("/business-rules/", response_model=List[BusinessRuleResponse])
def read_business_rules(
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = None,
    active: Optional[bool] = None,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    query = db.query(BusinessRule)
    if category:
        query = query.filter(BusinessRule.category == category)
    if active is not None:
        query = query.filter(BusinessRule.active == active)
    return query.offset(skip).limit(limit).all()


@app.get("/business-rules/{rule_id}", response_model=BusinessRuleResponse)
def read_business_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    db_rule = db.query(BusinessRule).filter(BusinessRule.id == rule_id).first()
    if db_rule is None:
        raise HTTPException(status_code=404, detail="Business rule not found")
    return db_rule


@app.put("/business-rules/{rule_id}", response_model=BusinessRuleResponse)
def update_business_rule(
    rule_id: int,
    rule: BusinessRuleUpdate,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    db_rule = db.query(BusinessRule).filter(BusinessRule.id == rule_id).first()
    if db_rule is None:
        raise HTTPException(status_code=404, detail="Business rule not found")
    
    update_data = rule.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_rule, key, value)
    
    db_rule.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_rule)
    return db_rule


@app.delete("/business-rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_business_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    db_rule = db.query(BusinessRule).filter(BusinessRule.id == rule_id).first()
    if db_rule is None:
        raise HTTPException(status_code=404, detail="Business rule not found")
    
    db.delete(db_rule)
    db.commit()
    return None


# Endpoint para pesquisa semântica de regras de negócio
@app.get("/search/business-rules/", response_model=List[BusinessRuleResponse])
def search_business_rules(
    query: str,
    limit: int = 10,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    # Simulação de pesquisa semântica
    # Em uma implementação real, usaríamos embeddings e busca vetorial
    rules = db.query(BusinessRule).filter(
        sa.or_(
            BusinessRule.name.ilike(f"%{query}%"),
            BusinessRule.description.ilike(f"%{query}%"),
            BusinessRule.rule_text.ilike(f"%{query}%")
        )
    ).limit(limit).all()
    
    return rules


# Endpoint para pesquisa semântica de produtos
@app.get("/search/products/", response_model=List[ProductResponse])
def search_products(
    query: str,
    limit: int = 10,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    # Simulação de pesquisa semântica
    products = db.query(Product).filter(
        sa.or_(
            Product.name.ilike(f"%{query}%"),
            Product.description.ilike(f"%{query}%"),
            Product.category.ilike(f"%{query}%")
        )
    ).limit(limit).all()
    
    return products


# Endpoint para inicialização do banco de dados
@app.post("/init-db/", status_code=status.HTTP_200_OK)
def init_db(
    api_key: str = Depends(verify_api_key)
):
    try:
        # Criar tabelas
        Base.metadata.create_all(bind=engine)
        
        # Inicializar dados de exemplo
        db = SessionLocal()
        
        # Verificar se já existem dados
        if db.query(Product).count() > 0:
            db.close()
            return {"message": "Database already initialized"}
        
        # Produtos
        products = [
            Product(
                name="Shampoo Revitalizante",
                description="Shampoo para cabelos danificados com fórmula revitalizante",
                price=29.90,
                category="Cabelos",
                stock=100
            ),
            Product(
                name="Condicionador Hidratante",
                description="Condicionador para cabelos secos com fórmula hidratante",
                price=27.90,
                category="Cabelos",
                stock=80
            ),
            Product(
                name="Creme Facial Noturno",
                description="Creme facial para uso noturno com ação anti-idade",
                price=89.90,
                category="Rosto",
                stock=50
            ),
            Product(
                name="Protetor Solar FPS 50",
                description="Protetor solar com alta proteção contra raios UVA e UVB",
                price=59.90,
                category="Proteção Solar",
                stock=70
            ),
            Product(
                name="Máscara Capilar Intensiva",
                description="Máscara de tratamento intensivo para cabelos muito danificados",
                price=45.90,
                category="Cabelos",
                stock=60
            ),
        ]
        
        for product in products:
            db.add(product)
        
        # Clientes
        customers = [
            Customer(
                name="Maria Silva",
                email="maria.silva@example.com",
                phone="11987654321",
                address="Rua das Flores, 123",
                loyalty_level="premium"
            ),
            Customer(
                name="João Santos",
                email="joao.santos@example.com",
                phone="11912345678",
                address="Avenida Central, 456",
                loyalty_level="standard"
            ),
            Customer(
                name="Ana Oliveira",
                email="ana.oliveira@example.com",
                phone="11976543210",
                address="Rua dos Pinheiros, 789",
                loyalty_level="gold"
            ),
        ]
        
        for customer in customers:
            db.add(customer)
        
        # Regras de negócio
        business_rules = [
            BusinessRule(
                name="Desconto para Clientes Premium",
                description="Clientes com nível de fidelidade Premium recebem 10% de desconto em todos os produtos",
                category="Descontos",
                rule_text="Se o cliente tem nível de fidelidade 'premium', aplicar desconto de 10% no valor total do pedido."
            ),
            BusinessRule(
                name="Frete Grátis para Compras Acima de R$150",
                description="Pedidos com valor total acima de R$150 têm frete grátis",
                category="Frete",
                rule_text="Se o valor total do pedido for maior ou igual a R$150, o frete é gratuito."
            ),
            BusinessRule(
                name="Desconto para Compras em Quantidade",
                description="Compras de 5 ou mais unidades do mesmo produto têm 5% de desconto",
                category="Descontos",
                rule_text="Se a quantidade de um mesmo produto no pedido for maior ou igual a 5, aplicar desconto de 5% no valor desse produto."
            ),
            BusinessRule(
                name="Política de Devolução",
                description="Produtos podem ser devolvidos em até 7 dias após a compra",
                category="Devoluções",
                rule_text="O cliente pode solicitar devolução de qualquer produto em até 7 dias após a data da compra, desde que o produto esteja em perfeito estado e na embalagem original."
            ),
            BusinessRule(
                name="Programa de Fidelidade",
                description="Regras para acúmulo de pontos no programa de fidelidade",
                category="Fidelidade",
                rule_text="Para cada R$1 gasto, o cliente acumula 1 ponto. Ao atingir 500 pontos, o cliente sobe para o nível 'gold'. Ao atingir 1000 pontos, o cliente sobe para o nível 'premium'."
            ),
        ]
        
        for rule in business_rules:
            db.add(rule)
        
        db.commit()
        db.close()
        
        return {"message": "Database initialized successfully"}
    
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error initializing database: {str(e)}"
        )


# Endpoint de status
@app.get("/status/", status_code=status.HTTP_200_OK)
def get_status():
    return {
        "status": "online",
        "timestamp": datetime.utcnow(),
        "version": "1.0.0"
    }


# Inicialização do banco de dados na inicialização do aplicativo
@app.on_event("startup")
async def startup_event():
    try:
        # Criar tabelas
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
