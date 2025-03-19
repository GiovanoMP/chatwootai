"""
Rotas para gerenciamento de clientes na API de simulação do Odoo.
"""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.customer import Customer, CustomerCreate, CustomerUpdate

router = APIRouter(
    prefix="/customers",
    tags=["customers"],
    responses={404: {"description": "Cliente não encontrado"}},
)

@router.get("/", response_model=List[Customer])
def read_customers(
    skip: int = 0, 
    limit: int = 100, 
    search: Optional[str] = None,
    city: Optional[str] = None,
    state: Optional[str] = None,
    skin_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Retorna a lista de clientes com filtros opcionais.
    """
    query = "SELECT * FROM customers WHERE 1=1"
    params = {}
    
    if search is not None:
        query += " AND (first_name ILIKE :search OR last_name ILIKE :search OR email ILIKE :search OR phone ILIKE :search)"
        params["search"] = f"%{search}%"
    
    if city is not None:
        query += " AND city ILIKE :city"
        params["city"] = f"%{city}%"
    
    if state is not None:
        query += " AND state ILIKE :state"
        params["state"] = f"%{state}%"
    
    if skin_type is not None:
        query += " AND skin_type ILIKE :skin_type"
        params["skin_type"] = f"%{skin_type}%"
    
    query += " ORDER BY id LIMIT :limit OFFSET :skip"
    params["limit"] = limit
    params["skip"] = skip
    
    result = db.execute(text(query), params)
    customers = [dict(row) for row in result]
    
    return customers

@router.get("/{customer_id}", response_model=Customer)
def read_customer(customer_id: int, db: Session = Depends(get_db)):
    """
    Retorna os detalhes de um cliente específico.
    """
    query = "SELECT * FROM customers WHERE id = :customer_id"
    result = db.execute(text(query), {"customer_id": customer_id}).fetchone()
    
    if result is None:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    
    return dict(result)

@router.post("/", response_model=Customer, status_code=status.HTTP_201_CREATED)
def create_customer(customer: CustomerCreate, db: Session = Depends(get_db)):
    """
    Cria um novo cliente.
    """
    query = """
    INSERT INTO customers (
        first_name, last_name, email, phone, birth_date, address, city, 
        state, postal_code, country, skin_type, allergies, preferences, notes
    ) VALUES (
        :first_name, :last_name, :email, :phone, :birth_date, :address, :city, 
        :state, :postal_code, :country, :skin_type, :allergies, :preferences, :notes
    ) RETURNING *
    """
    
    try:
        result = db.execute(
            text(query), 
            {
                "first_name": customer.first_name,
                "last_name": customer.last_name,
                "email": customer.email,
                "phone": customer.phone,
                "birth_date": customer.birth_date,
                "address": customer.address,
                "city": customer.city,
                "state": customer.state,
                "postal_code": customer.postal_code,
                "country": customer.country,
                "skin_type": customer.skin_type,
                "allergies": customer.allergies,
                "preferences": customer.preferences,
                "notes": customer.notes
            }
        ).fetchone()
        
        db.commit()
        return dict(result)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao criar cliente: {str(e)}")

@router.put("/{customer_id}", response_model=Customer)
def update_customer(customer_id: int, customer: CustomerUpdate, db: Session = Depends(get_db)):
    """
    Atualiza os dados de um cliente existente.
    """
    # Verificar se o cliente existe
    check_query = "SELECT id FROM customers WHERE id = :customer_id"
    exists = db.execute(text(check_query), {"customer_id": customer_id}).fetchone()
    
    if not exists:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    
    # Construir a query de atualização dinamicamente com base nos campos fornecidos
    update_fields = []
    params = {"customer_id": customer_id}
    
    # Dicionário com os campos e valores do modelo
    customer_data = customer.dict(exclude_unset=True)
    
    for field, value in customer_data.items():
        if value is not None:  # Apenas incluir campos que não são None
            update_fields.append(f"{field} = :{field}")
            params[field] = value
    
    if not update_fields:
        # Se não houver campos para atualizar, retornar o cliente atual
        return read_customer(customer_id, db)
    
    # Adicionar updated_at ao update
    update_fields.append("updated_at = CURRENT_TIMESTAMP")
    
    # Construir e executar a query
    query = f"""
    UPDATE customers 
    SET {", ".join(update_fields)}
    WHERE id = :customer_id
    RETURNING *
    """
    
    try:
        result = db.execute(text(query), params).fetchone()
        db.commit()
        return dict(result)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar cliente: {str(e)}")

@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_customer(customer_id: int, db: Session = Depends(get_db)):
    """
    Remove um cliente do sistema.
    """
    # Verificar se o cliente existe
    check_query = "SELECT id FROM customers WHERE id = :customer_id"
    exists = db.execute(text(check_query), {"customer_id": customer_id}).fetchone()
    
    if not exists:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    
    # Verificar se o cliente tem pedidos ou agendamentos
    check_orders = "SELECT id FROM orders WHERE customer_id = :customer_id LIMIT 1"
    has_orders = db.execute(text(check_orders), {"customer_id": customer_id}).fetchone()
    
    check_appointments = "SELECT id FROM appointments WHERE customer_id = :customer_id LIMIT 1"
    has_appointments = db.execute(text(check_appointments), {"customer_id": customer_id}).fetchone()
    
    if has_orders or has_appointments:
        raise HTTPException(
            status_code=400, 
            detail="Não é possível excluir o cliente pois existem pedidos ou agendamentos associados"
        )
    
    # Excluir o cliente
    query = "DELETE FROM customers WHERE id = :customer_id"
    
    try:
        db.execute(text(query), {"customer_id": customer_id})
        db.commit()
        return None
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao excluir cliente: {str(e)}")

@router.get("/{customer_id}/orders", response_model=List[dict])
def read_customer_orders(customer_id: int, db: Session = Depends(get_db)):
    """
    Retorna todos os pedidos de um cliente específico.
    """
    # Verificar se o cliente existe
    check_query = "SELECT id FROM customers WHERE id = :customer_id"
    exists = db.execute(text(check_query), {"customer_id": customer_id}).fetchone()
    
    if not exists:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    
    query = """
    SELECT o.*, 
           c.first_name || ' ' || c.last_name as customer_name,
           COUNT(oi.id) as item_count,
           SUM(oi.quantity) as total_items
    FROM orders o
    JOIN customers c ON o.customer_id = c.id
    LEFT JOIN order_items oi ON o.id = oi.order_id
    WHERE o.customer_id = :customer_id
    GROUP BY o.id, c.first_name, c.last_name
    ORDER BY o.order_date DESC
    """
    
    result = db.execute(text(query), {"customer_id": customer_id})
    orders = [dict(row) for row in result]
    
    return orders

@router.get("/{customer_id}/appointments", response_model=List[dict])
def read_customer_appointments(customer_id: int, db: Session = Depends(get_db)):
    """
    Retorna todos os agendamentos de um cliente específico.
    """
    # Verificar se o cliente existe
    check_query = "SELECT id FROM customers WHERE id = :customer_id"
    exists = db.execute(text(check_query), {"customer_id": customer_id}).fetchone()
    
    if not exists:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    
    query = """
    SELECT a.*, 
           c.first_name || ' ' || c.last_name as customer_name,
           s.name as service_name,
           p.first_name || ' ' || p.last_name as professional_name
    FROM appointments a
    JOIN customers c ON a.customer_id = c.id
    JOIN services s ON a.service_id = s.id
    JOIN professionals p ON a.professional_id = p.id
    WHERE a.customer_id = :customer_id
    ORDER BY a.start_time DESC
    """
    
    result = db.execute(text(query), {"customer_id": customer_id})
    appointments = [dict(row) for row in result]
    
    return appointments

@router.get("/{customer_id}/interactions", response_model=List[dict])
def read_customer_interactions(customer_id: int, db: Session = Depends(get_db)):
    """
    Retorna todas as interações de um cliente específico.
    """
    # Verificar se o cliente existe
    check_query = "SELECT id FROM customers WHERE id = :customer_id"
    exists = db.execute(text(check_query), {"customer_id": customer_id}).fetchone()
    
    if not exists:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    
    query = """
    SELECT ci.*,
           c.first_name || ' ' || c.last_name as customer_name
    FROM customer_interactions ci
    JOIN customers c ON ci.customer_id = c.id
    WHERE ci.customer_id = :customer_id
    ORDER BY ci.created_at DESC
    """
    
    result = db.execute(text(query), {"customer_id": customer_id})
    interactions = [dict(row) for row in result]
    
    return interactions
