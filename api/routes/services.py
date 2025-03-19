"""
Rotas para gerenciamento de serviços na API de simulação do Odoo.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.service import Service, ServiceCreate, ServiceUpdate, ServiceCategory, Professional, ServiceWithDetails

router = APIRouter(
    prefix="/services",
    tags=["services"],
    responses={404: {"description": "Serviço não encontrado"}},
)

@router.get("/", response_model=List[Service])
def read_services(
    skip: int = 0, 
    limit: int = 100, 
    active: Optional[bool] = True,
    category_id: Optional[int] = None,
    search: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    max_duration: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Retorna a lista de serviços com filtros opcionais.
    
    - **skip**: Número de registros para pular (paginação)
    - **limit**: Número máximo de registros a retornar
    - **active**: Filtrar apenas serviços ativos
    - **category_id**: Filtrar por categoria
    - **search**: Buscar por nome ou descrição
    - **min_price**: Preço mínimo
    - **max_price**: Preço máximo
    - **max_duration**: Duração máxima em minutos
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
    
    if min_price is not None:
        query += " AND price >= :min_price"
        params["min_price"] = min_price
    
    if max_price is not None:
        query += " AND price <= :max_price"
        params["max_price"] = max_price
    
    if max_duration is not None:
        query += " AND duration <= :max_duration"
        params["max_duration"] = max_duration
    
    query += " ORDER BY id LIMIT :limit OFFSET :skip"
    params["limit"] = limit
    params["skip"] = skip
    
    result = db.execute(text(query), params)
    services = [dict(row) for row in result]
    
    return services

@router.get("/{service_id}", response_model=ServiceWithDetails)
def read_service(service_id: int, db: Session = Depends(get_db)):
    """
    Retorna os detalhes de um serviço específico, incluindo profissionais associados.
    
    - **service_id**: ID do serviço
    """
    # Buscar informações básicas do serviço
    service_query = "SELECT * FROM services WHERE id = :service_id"
    service_result = db.execute(text(service_query), {"service_id": service_id}).fetchone()
    
    if service_result is None:
        raise HTTPException(status_code=404, detail="Serviço não encontrado")
    
    service_data = dict(service_result)
    
    # Buscar categoria
    category_query = "SELECT name FROM service_categories WHERE id = :category_id"
    category_result = db.execute(text(category_query), {"category_id": service_data["category_id"]}).fetchone()
    
    if category_result:
        service_data["category_name"] = category_result[0]
    
    # Buscar profissionais associados
    professionals_query = """
    SELECT p.* 
    FROM professionals p
    JOIN professional_services ps ON p.id = ps.professional_id
    WHERE ps.service_id = :service_id AND p.active = true
    """
    professionals_result = db.execute(text(professionals_query), {"service_id": service_id})
    service_data["professionals"] = [dict(row) for row in professionals_result]
    
    # Buscar informações enriquecidas
    enrichment_query = """
    SELECT * FROM service_enrichment 
    WHERE service_id = :service_id 
    ORDER BY relevance_score DESC
    """
    enrichment_result = db.execute(text(enrichment_query), {"service_id": service_id})
    service_data["enrichments"] = [dict(row) for row in enrichment_result]
    
    return service_data

@router.post("/", response_model=Service, status_code=status.HTTP_201_CREATED)
def create_service(service: ServiceCreate, db: Session = Depends(get_db)):
    """
    Cria um novo serviço.
    
    - **service**: Dados do serviço a ser criado
    """
    query = """
    INSERT INTO services (
        name, description, category_id, price, duration, 
        preparation, aftercare, contraindications, image_url, active
    ) VALUES (
        :name, :description, :category_id, :price, :duration, 
        :preparation, :aftercare, :contraindications, :image_url, :active
    ) RETURNING *
    """
    
    try:
        result = db.execute(
            text(query), 
            {
                "name": service.name,
                "description": service.description,
                "category_id": service.category_id,
                "price": service.price,
                "duration": service.duration,
                "preparation": service.preparation,
                "aftercare": service.aftercare,
                "contraindications": service.contraindications,
                "image_url": service.image_url,
                "active": service.active
            }
        ).fetchone()
        
        db.commit()
        return dict(result)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao criar serviço: {str(e)}")

@router.put("/{service_id}", response_model=Service)
def update_service(service_id: int, service: ServiceUpdate, db: Session = Depends(get_db)):
    """
    Atualiza os dados de um serviço existente.
    
    - **service_id**: ID do serviço a ser atualizado
    - **service**: Dados do serviço a serem atualizados
    """
    # Verificar se o serviço existe
    check_query = "SELECT id FROM services WHERE id = :service_id"
    exists = db.execute(text(check_query), {"service_id": service_id}).fetchone()
    
    if not exists:
        raise HTTPException(status_code=404, detail="Serviço não encontrado")
    
    # Construir a query de atualização dinamicamente com base nos campos fornecidos
    update_fields = []
    params = {"service_id": service_id}
    
    # Dicionário com os campos e valores do modelo
    service_data = service.dict(exclude_unset=True)
    
    for field, value in service_data.items():
        if value is not None:  # Apenas incluir campos que não são None
            update_fields.append(f"{field} = :{field}")
            params[field] = value
    
    if not update_fields:
        # Se não houver campos para atualizar, retornar o serviço atual
        return read_service(service_id, db)
    
    # Adicionar updated_at ao update
    update_fields.append("updated_at = CURRENT_TIMESTAMP")
    
    # Construir e executar a query
    query = f"""
    UPDATE services 
    SET {", ".join(update_fields)}
    WHERE id = :service_id
    RETURNING *
    """
    
    try:
        result = db.execute(text(query), params).fetchone()
        db.commit()
        return dict(result)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar serviço: {str(e)}")

@router.delete("/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_service(service_id: int, db: Session = Depends(get_db)):
    """
    Remove um serviço do sistema.
    
    - **service_id**: ID do serviço a ser removido
    """
    # Verificar se o serviço existe
    check_query = "SELECT id FROM services WHERE id = :service_id"
    exists = db.execute(text(check_query), {"service_id": service_id}).fetchone()
    
    if not exists:
        raise HTTPException(status_code=404, detail="Serviço não encontrado")
    
    # Verificar se o serviço está em algum agendamento
    check_appointments = "SELECT id FROM appointments WHERE service_id = :service_id LIMIT 1"
    has_appointments = db.execute(text(check_appointments), {"service_id": service_id}).fetchone()
    
    if has_appointments:
        raise HTTPException(
            status_code=400, 
            detail="Não é possível excluir o serviço pois existem agendamentos associados"
        )
    
    # Excluir associações com profissionais
    delete_assoc = "DELETE FROM professional_services WHERE service_id = :service_id"
    
    try:
        db.execute(text(delete_assoc), {"service_id": service_id})
        
        # Excluir o serviço
        query = "DELETE FROM services WHERE id = :service_id"
        db.execute(text(query), {"service_id": service_id})
        
        db.commit()
        return None
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao excluir serviço: {str(e)}")

@router.get("/categories/", response_model=List[ServiceCategory])
def read_service_categories(
    skip: int = 0, 
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Retorna a lista de categorias de serviços.
    
    - **skip**: Número de registros para pular (paginação)
    - **limit**: Número máximo de registros a retornar
    """
    query = "SELECT * FROM service_categories ORDER BY id LIMIT :limit OFFSET :skip"
    result = db.execute(text(query), {"limit": limit, "skip": skip})
    categories = [dict(row) for row in result]
    
    return categories

@router.get("/professionals/", response_model=List[Professional])
def read_professionals(
    skip: int = 0, 
    limit: int = 100,
    active: Optional[bool] = True,
    service_id: Optional[int] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Retorna a lista de profissionais.
    
    - **skip**: Número de registros para pular (paginação)
    - **limit**: Número máximo de registros a retornar
    - **active**: Filtrar apenas profissionais ativos
    - **service_id**: Filtrar por serviço
    - **search**: Buscar por nome, especialização ou biografia
    """
    if service_id is not None:
        # Se service_id for fornecido, buscar apenas profissionais associados ao serviço
        query = """
        SELECT p.* 
        FROM professionals p
        JOIN professional_services ps ON p.id = ps.professional_id
        WHERE ps.service_id = :service_id
        """
        params = {"service_id": service_id}
        
        if active is not None:
            query += " AND p.active = :active"
            params["active"] = active
        
        if search is not None:
            query += " AND (p.first_name ILIKE :search OR p.last_name ILIKE :search OR p.specialization ILIKE :search OR p.bio ILIKE :search)"
            params["search"] = f"%{search}%"
        
        query += " ORDER BY p.id LIMIT :limit OFFSET :skip"
        params["limit"] = limit
        params["skip"] = skip
    else:
        # Caso contrário, buscar todos os profissionais
        query = "SELECT * FROM professionals WHERE 1=1"
        params = {}
        
        if active is not None:
            query += " AND active = :active"
            params["active"] = active
        
        if search is not None:
            query += " AND (first_name ILIKE :search OR last_name ILIKE :search OR specialization ILIKE :search OR bio ILIKE :search)"
            params["search"] = f"%{search}%"
        
        query += " ORDER BY id LIMIT :limit OFFSET :skip"
        params["limit"] = limit
        params["skip"] = skip
    
    result = db.execute(text(query), params)
    professionals = [dict(row) for row in result]
    
    return professionals

@router.get("/{service_id}/enrichment", response_model=List[dict])
def read_service_enrichment(service_id: int, db: Session = Depends(get_db)):
    """
    Retorna as informações enriquecidas de um serviço específico.
    
    - **service_id**: ID do serviço
    """
    # Verificar se o serviço existe
    check_query = "SELECT id FROM services WHERE id = :service_id"
    exists = db.execute(text(check_query), {"service_id": service_id}).fetchone()
    
    if not exists:
        raise HTTPException(status_code=404, detail="Serviço não encontrado")
    
    query = """
    SELECT * FROM service_enrichment 
    WHERE service_id = :service_id 
    ORDER BY relevance_score DESC
    """
    
    result = db.execute(text(query), {"service_id": service_id})
    enrichments = [dict(row) for row in result]
    
    return enrichments
