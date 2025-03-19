"""
Rotas para gerenciamento de regras de negócio na API de simulação do Odoo.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.business_rule import BusinessRule, BusinessRuleCreate, BusinessRuleUpdate, CustomerInteraction

router = APIRouter(
    prefix="/business-rules",
    tags=["business_rules"],
    responses={404: {"description": "Regra de negócio não encontrada"}},
)

@router.get("/", response_model=List[BusinessRule])
def read_business_rules(
    skip: int = 0, 
    limit: int = 100, 
    active: Optional[bool] = True,
    category: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Retorna a lista de regras de negócio com filtros opcionais.
    
    - **skip**: Número de registros para pular (paginação)
    - **limit**: Número máximo de registros a retornar
    - **active**: Filtrar apenas regras ativas
    - **category**: Filtrar por categoria
    - **search**: Buscar por nome, descrição ou texto da regra
    """
    query = "SELECT * FROM business_rules WHERE 1=1"
    params = {}
    
    if active is not None:
        query += " AND active = :active"
        params["active"] = active
    
    if category is not None:
        query += " AND category ILIKE :category"
        params["category"] = f"%{category}%"
    
    if search is not None:
        query += " AND (name ILIKE :search OR description ILIKE :search OR rule_text ILIKE :search)"
        params["search"] = f"%{search}%"
    
    query += " ORDER BY id LIMIT :limit OFFSET :skip"
    params["limit"] = limit
    params["skip"] = skip
    
    result = db.execute(text(query), params)
    rules = [dict(row) for row in result]
    
    return rules

@router.get("/{rule_id}", response_model=BusinessRule)
def read_business_rule(rule_id: int, db: Session = Depends(get_db)):
    """
    Retorna os detalhes de uma regra de negócio específica.
    
    - **rule_id**: ID da regra de negócio
    """
    query = "SELECT * FROM business_rules WHERE id = :rule_id"
    result = db.execute(text(query), {"rule_id": rule_id}).fetchone()
    
    if result is None:
        raise HTTPException(status_code=404, detail="Regra de negócio não encontrada")
    
    return dict(result)

@router.post("/", response_model=BusinessRule, status_code=status.HTTP_201_CREATED)
def create_business_rule(rule: BusinessRuleCreate, db: Session = Depends(get_db)):
    """
    Cria uma nova regra de negócio.
    
    - **rule**: Dados da regra de negócio a ser criada
    """
    query = """
    INSERT INTO business_rules (
        name, description, category, rule_text, active
    ) VALUES (
        :name, :description, :category, :rule_text, :active
    ) RETURNING *
    """
    
    try:
        result = db.execute(
            text(query), 
            {
                "name": rule.name,
                "description": rule.description,
                "category": rule.category,
                "rule_text": rule.rule_text,
                "active": rule.active
            }
        ).fetchone()
        
        db.commit()
        return dict(result)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao criar regra de negócio: {str(e)}")

@router.put("/{rule_id}", response_model=BusinessRule)
def update_business_rule(rule_id: int, rule: BusinessRuleUpdate, db: Session = Depends(get_db)):
    """
    Atualiza os dados de uma regra de negócio existente.
    
    - **rule_id**: ID da regra de negócio a ser atualizada
    - **rule**: Dados da regra de negócio a serem atualizados
    """
    # Verificar se a regra existe
    check_query = "SELECT id FROM business_rules WHERE id = :rule_id"
    exists = db.execute(text(check_query), {"rule_id": rule_id}).fetchone()
    
    if not exists:
        raise HTTPException(status_code=404, detail="Regra de negócio não encontrada")
    
    # Construir a query de atualização dinamicamente com base nos campos fornecidos
    update_fields = []
    params = {"rule_id": rule_id}
    
    # Dicionário com os campos e valores do modelo
    rule_data = rule.dict(exclude_unset=True)
    
    for field, value in rule_data.items():
        if value is not None:  # Apenas incluir campos que não são None
            update_fields.append(f"{field} = :{field}")
            params[field] = value
    
    if not update_fields:
        # Se não houver campos para atualizar, retornar a regra atual
        return read_business_rule(rule_id, db)
    
    # Adicionar updated_at ao update
    update_fields.append("updated_at = CURRENT_TIMESTAMP")
    
    # Construir e executar a query
    query = f"""
    UPDATE business_rules 
    SET {", ".join(update_fields)}
    WHERE id = :rule_id
    RETURNING *
    """
    
    try:
        result = db.execute(text(query), params).fetchone()
        db.commit()
        return dict(result)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar regra de negócio: {str(e)}")

@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_business_rule(rule_id: int, db: Session = Depends(get_db)):
    """
    Remove uma regra de negócio do sistema.
    
    - **rule_id**: ID da regra de negócio a ser removida
    """
    # Verificar se a regra existe
    check_query = "SELECT id FROM business_rules WHERE id = :rule_id"
    exists = db.execute(text(check_query), {"rule_id": rule_id}).fetchone()
    
    if not exists:
        raise HTTPException(status_code=404, detail="Regra de negócio não encontrada")
    
    # Excluir a regra
    query = "DELETE FROM business_rules WHERE id = :rule_id"
    
    try:
        db.execute(text(query), {"rule_id": rule_id})
        db.commit()
        return None
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao excluir regra de negócio: {str(e)}")

@router.get("/categories/", response_model=List[str])
def read_business_rule_categories(db: Session = Depends(get_db)):
    """
    Retorna a lista de categorias de regras de negócio.
    """
    query = "SELECT DISTINCT category FROM business_rules ORDER BY category"
    result = db.execute(text(query))
    categories = [row[0] for row in result]
    
    return categories

@router.get("/search/semantic", response_model=List[BusinessRule])
def semantic_search_business_rules(
    query: str,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    Realiza uma busca semântica nas regras de negócio.
    
    Esta é uma simulação de busca semântica, pois a busca real seria feita no Qdrant.
    Na implementação real, este endpoint consultaria o Qdrant para encontrar as regras
    mais similares ao query fornecido.
    
    - **query**: Texto para busca semântica
    - **limit**: Número máximo de resultados a retornar
    """
    # Simulação de busca semântica usando LIKE
    search_query = """
    SELECT * FROM business_rules 
    WHERE active = true 
    AND (
        rule_text ILIKE :query 
        OR name ILIKE :query 
        OR description ILIKE :query
    )
    ORDER BY id
    LIMIT :limit
    """
    
    result = db.execute(text(search_query), {"query": f"%{query}%", "limit": limit})
    rules = [dict(row) for row in result]
    
    return rules

@router.get("/customer-interactions/", response_model=List[CustomerInteraction])
def read_customer_interactions(
    skip: int = 0, 
    limit: int = 100, 
    customer_id: Optional[int] = None,
    channel: Optional[str] = None,
    interaction_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Retorna a lista de interações com clientes.
    
    - **skip**: Número de registros para pular (paginação)
    - **limit**: Número máximo de registros a retornar
    - **customer_id**: Filtrar por cliente
    - **channel**: Filtrar por canal (whatsapp, email, instagram, etc.)
    - **interaction_type**: Filtrar por tipo de interação (message, call, etc.)
    """
    query = "SELECT * FROM customer_interactions WHERE 1=1"
    params = {}
    
    if customer_id is not None:
        query += " AND customer_id = :customer_id"
        params["customer_id"] = customer_id
    
    if channel is not None:
        query += " AND channel = :channel"
        params["channel"] = channel
    
    if interaction_type is not None:
        query += " AND interaction_type = :interaction_type"
        params["interaction_type"] = interaction_type
    
    query += " ORDER BY timestamp DESC LIMIT :limit OFFSET :skip"
    params["limit"] = limit
    params["skip"] = skip
    
    result = db.execute(text(query), params)
    interactions = [dict(row) for row in result]
    
    return interactions
