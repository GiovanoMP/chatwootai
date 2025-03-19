"""
Rotas para gerenciamento de produtos na API de simulação do Odoo.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.product import Product, ProductCreate, ProductUpdate, ProductCategory, ProductInventory, ProductEnrichment

router = APIRouter(
    prefix="/products",
    tags=["products"],
    responses={404: {"description": "Produto não encontrado"}},
)

@router.get("/", response_model=List[Product])
def read_products(
    skip: int = 0, 
    limit: int = 100, 
    active: Optional[bool] = True,
    category_id: Optional[int] = None,
    search: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    db: Session = Depends(get_db)
):
    """
    Retorna a lista de produtos com filtros opcionais.
    
    - **skip**: Número de registros para pular (paginação)
    - **limit**: Número máximo de registros a retornar
    - **active**: Filtrar apenas produtos ativos
    - **category_id**: Filtrar por categoria
    - **search**: Buscar por nome, descrição ou SKU
    - **min_price**: Preço mínimo
    - **max_price**: Preço máximo
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
    
    if min_price is not None:
        query += " AND price >= :min_price"
        params["min_price"] = min_price
    
    if max_price is not None:
        query += " AND price <= :max_price"
        params["max_price"] = max_price
    
    query += " ORDER BY id LIMIT :limit OFFSET :skip"
    params["limit"] = limit
    params["skip"] = skip
    
    result = db.execute(text(query), params)
    products = [dict(row) for row in result]
    
    return products

@router.get("/{product_id}", response_model=Product)
def read_product(product_id: int, db: Session = Depends(get_db)):
    """
    Retorna os detalhes de um produto específico.
    
    - **product_id**: ID do produto
    """
    query = "SELECT * FROM products WHERE id = :product_id"
    result = db.execute(text(query), {"product_id": product_id}).fetchone()
    
    if result is None:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    
    return dict(result)

@router.post("/", response_model=Product, status_code=status.HTTP_201_CREATED)
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    """
    Cria um novo produto.
    
    - **product**: Dados do produto a ser criado
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
        raise HTTPException(status_code=500, detail=f"Erro ao criar produto: {str(e)}")

@router.put("/{product_id}", response_model=Product)
def update_product(product_id: int, product: ProductUpdate, db: Session = Depends(get_db)):
    """
    Atualiza os dados de um produto existente.
    
    - **product_id**: ID do produto a ser atualizado
    - **product**: Dados do produto a serem atualizados
    """
    # Verificar se o produto existe
    check_query = "SELECT id FROM products WHERE id = :product_id"
    exists = db.execute(text(check_query), {"product_id": product_id}).fetchone()
    
    if not exists:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    
    # Construir a query de atualização dinamicamente com base nos campos fornecidos
    update_fields = []
    params = {"product_id": product_id}
    
    # Dicionário com os campos e valores do modelo
    product_data = product.dict(exclude_unset=True)
    
    for field, value in product_data.items():
        if value is not None:  # Apenas incluir campos que não são None
            update_fields.append(f"{field} = :{field}")
            params[field] = value
    
    if not update_fields:
        # Se não houver campos para atualizar, retornar o produto atual
        return read_product(product_id, db)
    
    # Adicionar updated_at ao update
    update_fields.append("updated_at = CURRENT_TIMESTAMP")
    
    # Construir e executar a query
    query = f"""
    UPDATE products 
    SET {", ".join(update_fields)}
    WHERE id = :product_id
    RETURNING *
    """
    
    try:
        result = db.execute(text(query), params).fetchone()
        db.commit()
        return dict(result)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar produto: {str(e)}")

@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: int, db: Session = Depends(get_db)):
    """
    Remove um produto do sistema.
    
    - **product_id**: ID do produto a ser removido
    """
    # Verificar se o produto existe
    check_query = "SELECT id FROM products WHERE id = :product_id"
    exists = db.execute(text(check_query), {"product_id": product_id}).fetchone()
    
    if not exists:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    
    # Verificar se o produto está em algum pedido
    check_orders = "SELECT id FROM order_items WHERE product_id = :product_id LIMIT 1"
    has_orders = db.execute(text(check_orders), {"product_id": product_id}).fetchone()
    
    if has_orders:
        raise HTTPException(
            status_code=400, 
            detail="Não é possível excluir o produto pois existem pedidos associados"
        )
    
    # Excluir o produto
    query = "DELETE FROM products WHERE id = :product_id"
    
    try:
        db.execute(text(query), {"product_id": product_id})
        db.commit()
        return None
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao excluir produto: {str(e)}")

@router.get("/categories/", response_model=List[ProductCategory])
def read_product_categories(
    skip: int = 0, 
    limit: int = 100,
    parent_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Retorna a lista de categorias de produtos.
    
    - **skip**: Número de registros para pular (paginação)
    - **limit**: Número máximo de registros a retornar
    - **parent_id**: Filtrar por categoria pai
    """
    query = "SELECT * FROM product_categories WHERE 1=1"
    params = {}
    
    if parent_id is not None:
        query += " AND parent_id = :parent_id"
        params["parent_id"] = parent_id
    
    query += " ORDER BY id LIMIT :limit OFFSET :skip"
    params["limit"] = limit
    params["skip"] = skip
    
    result = db.execute(text(query), params)
    categories = [dict(row) for row in result]
    
    return categories

@router.get("/inventory/{product_id}", response_model=ProductInventory)
def read_product_inventory(product_id: int, db: Session = Depends(get_db)):
    """
    Retorna as informações de estoque de um produto específico.
    
    - **product_id**: ID do produto
    """
    query = "SELECT * FROM inventory WHERE product_id = :product_id"
    result = db.execute(text(query), {"product_id": product_id}).fetchone()
    
    if result is None:
        raise HTTPException(status_code=404, detail="Informações de estoque não encontradas")
    
    return dict(result)

@router.get("/{product_id}/enrichment", response_model=List[ProductEnrichment])
def read_product_enrichment(product_id: int, db: Session = Depends(get_db)):
    """
    Retorna as informações enriquecidas de um produto específico.
    
    - **product_id**: ID do produto
    """
    query = "SELECT * FROM product_enrichment WHERE product_id = :product_id ORDER BY relevance_score DESC"
    result = db.execute(text(query), {"product_id": product_id})
    enrichments = [dict(row) for row in result]
    
    return enrichments
