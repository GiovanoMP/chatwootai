#!/usr/bin/env python3
"""
API de simulação do Odoo (ERP) para o sistema ChatwootAI.

Esta API fornece endpoints para acessar os dados do banco de dados PostgreSQL,
simulando as funcionalidades de um ERP real para a empresa de cosméticos.
"""

import os
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from fastapi import FastAPI, Depends, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel, Field

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("odoo_simulation_api")

# Configurações do banco de dados
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "chatwootai")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")

DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

# Configuração do SQLAlchemy
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Inicialização da aplicação FastAPI
app = FastAPI(
    title="Odoo Simulation API",
    description="API de simulação do Odoo (ERP) para o sistema ChatwootAI",
    version="1.0.0",
)

# Configuração de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependência para obter a sessão do banco de dados
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Modelos Pydantic para a API
class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    category_id: int
    price: float
    cost: Optional[float] = None
    sku: Optional[str] = None
    barcode: Optional[str] = None
    weight: Optional[float] = None
    volume: Optional[float] = None
    ingredients: Optional[str] = None
    benefits: Optional[str] = None
    usage_instructions: Optional[str] = None
    image_url: Optional[str] = None
    active: bool = True

class ProductCreate(ProductBase):
    pass

class Product(ProductBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class ServiceBase(BaseModel):
    name: str
    description: Optional[str] = None
    category_id: int
    price: float
    duration: int
    preparation: Optional[str] = None
    aftercare: Optional[str] = None
    contraindications: Optional[str] = None
    image_url: Optional[str] = None
    active: bool = True

class ServiceCreate(ServiceBase):
    pass

class Service(ServiceBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class CustomerBase(BaseModel):
    first_name: str
    last_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    birth_date: Optional[datetime] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = "Brasil"
    skin_type: Optional[str] = None
    allergies: Optional[str] = None
    preferences: Optional[str] = None
    notes: Optional[str] = None

class CustomerCreate(CustomerBase):
    pass

class Customer(CustomerBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class OrderBase(BaseModel):
    customer_id: int
    status: str = "pending"
    total_amount: float
    shipping_address: Optional[str] = None
    shipping_city: Optional[str] = None
    shipping_state: Optional[str] = None
    shipping_postal_code: Optional[str] = None
    shipping_country: Optional[str] = "Brasil"
    shipping_method: Optional[str] = None
    tracking_number: Optional[str] = None
    payment_method: Optional[str] = None
    payment_status: str = "pending"
    notes: Optional[str] = None

class OrderCreate(OrderBase):
    pass

class Order(OrderBase):
    id: int
    order_date: datetime
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class OrderItemBase(BaseModel):
    order_id: int
    product_id: int
    quantity: int
    unit_price: float
    discount: float = 0
    total_price: float

class OrderItemCreate(OrderItemBase):
    pass

class OrderItem(OrderItemBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class AppointmentBase(BaseModel):
    customer_id: int
    service_id: int
    professional_id: int
    start_time: datetime
    end_time: datetime
    status: str = "scheduled"
    notes: Optional[str] = None

class AppointmentCreate(AppointmentBase):
    pass

class Appointment(AppointmentBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
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

class BusinessRule(BusinessRuleBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

# Rotas da API
@app.get("/")
def read_root():
    return {"message": "Bem-vindo à API de simulação do Odoo para o sistema ChatwootAI"}

# Endpoints para Produtos
@app.get("/products/", response_model=List[Product])
def read_products(
    skip: int = 0, 
    limit: int = 100, 
    active: Optional[bool] = True,
    category_id: Optional[int] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Retorna a lista de produtos com filtros opcionais.
    """
    query = "SELECT * FROM products WHERE 1=1"
    params = {}
    
    if active is not None:
        query += " AND active = :active"
        params["active"] = active
    
    if category_id is not None:
        query += " AND category_id = :category_id"
        params["category_id"] = category_id
    
    if search is not None:
        query += " AND (name ILIKE :search OR description ILIKE :search OR sku ILIKE :search)"
        params["search"] = f"%{search}%"
    
    query += " ORDER BY id LIMIT :limit OFFSET :skip"
    params["limit"] = limit
    params["skip"] = skip
    
    result = db.execute(text(query), params)
    products = [dict(row) for row in result]
    
    return products

@app.get("/products/{product_id}", response_model=Product)
def read_product(product_id: int, db: Session = Depends(get_db)):
    """
    Retorna os detalhes de um produto específico.
    """
    query = "SELECT * FROM products WHERE id = :product_id"
    result = db.execute(text(query), {"product_id": product_id}).fetchone()
    
    if result is None:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    
    return dict(result)

@app.post("/products/", response_model=Product, status_code=status.HTTP_201_CREATED)
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    """
    Cria um novo produto.
    """
    query = """
    INSERT INTO products (
        name, description, category_id, price, cost, sku, barcode, 
        weight, volume, ingredients, benefits, usage_instructions, 
        image_url, active
    ) VALUES (
        :name, :description, :category_id, :price, :cost, :sku, :barcode,
        :weight, :volume, :ingredients, :benefits, :usage_instructions,
        :image_url, :active
    ) RETURNING *
    """
    
    try:
        result = db.execute(
            text(query), 
            {
                "name": product.name,
                "description": product.description,
                "category_id": product.category_id,
                "price": product.price,
                "cost": product.cost,
                "sku": product.sku,
                "barcode": product.barcode,
                "weight": product.weight,
                "volume": product.volume,
                "ingredients": product.ingredients,
                "benefits": product.benefits,
                "usage_instructions": product.usage_instructions,
                "image_url": product.image_url,
                "active": product.active
            }
        ).fetchone()
        
        db.commit()
        return dict(result)
    except Exception as e:
        db.rollback()
        logger.error(f"Erro ao criar produto: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao criar produto: {str(e)}")

# Endpoints para Serviços
@app.get("/services/", response_model=List[Service])
def read_services(
    skip: int = 0, 
    limit: int = 100, 
    active: Optional[bool] = True,
    category_id: Optional[int] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Retorna a lista de serviços com filtros opcionais.
    """
    query = "SELECT * FROM services WHERE 1=1"
    params = {}
    
    if active is not None:
        query += " AND active = :active"
        params["active"] = active
    
    if category_id is not None:
        query += " AND category_id = :category_id"
        params["category_id"] = category_id
    
    if search is not None:
        query += " AND (name ILIKE :search OR description ILIKE :search)"
        params["search"] = f"%{search}%"
    
    query += " ORDER BY id LIMIT :limit OFFSET :skip"
    params["limit"] = limit
    params["skip"] = skip
    
    result = db.execute(text(query), params)
    services = [dict(row) for row in result]
    
    return services

@app.get("/services/{service_id}", response_model=Service)
def read_service(service_id: int, db: Session = Depends(get_db)):
    """
    Retorna os detalhes de um serviço específico.
    """
    query = "SELECT * FROM services WHERE id = :service_id"
    result = db.execute(text(query), {"service_id": service_id}).fetchone()
    
    if result is None:
        raise HTTPException(status_code=404, detail="Serviço não encontrado")
    
    return dict(result)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
