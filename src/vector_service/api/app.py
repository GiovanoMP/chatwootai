"""
API do Serviço de Vetorização

Este módulo contém a API REST para o serviço de vetorização.
"""

import os
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import logging

from ..services.embedding import EmbeddingService
from ..services.search import SearchService
from ..utils.qdrant_client import get_qdrant_client
from ..utils.redis_client import get_redis_client

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Criar aplicação FastAPI
app = FastAPI(
    title="Vector Service API",
    description="API for product vectorization and semantic search",
    version="0.1.0"
)

# Modelos de dados
class ProductData(BaseModel):
    """Dados de um produto para vetorização."""
    account_id: str = Field(..., description="ID da conta")
    product_id: str = Field(..., description="ID do produto")
    text: str = Field(..., description="Texto para gerar embedding")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadados adicionais")

class SearchQuery(BaseModel):
    """Consulta para busca semântica."""
    account_id: str = Field(..., description="ID da conta")
    query: str = Field(..., description="Consulta em linguagem natural")
    limit: int = Field(default=10, description="Número máximo de resultados")
    filter: Optional[Dict[str, Any]] = Field(default=None, description="Filtros adicionais")

class DeleteRequest(BaseModel):
    """Requisição para excluir um vetor."""
    account_id: str = Field(..., description="ID da conta")
    product_id: str = Field(..., description="ID do produto")

# Dependências
def get_embedding_service():
    """
    Obtém uma instância do serviço de embeddings.
    
    Returns:
        EmbeddingService: Serviço de embeddings configurado
    """
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    if not openai_api_key:
        logger.error("OPENAI_API_KEY environment variable not set")
        raise HTTPException(status_code=500, detail="OpenAI API key not configured")
    
    qdrant_client = get_qdrant_client()
    redis_client = get_redis_client()
    
    return EmbeddingService(openai_api_key, qdrant_client, redis_client)

def get_search_service():
    """
    Obtém uma instância do serviço de busca.
    
    Returns:
        SearchService: Serviço de busca configurado
    """
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    if not openai_api_key:
        logger.error("OPENAI_API_KEY environment variable not set")
        raise HTTPException(status_code=500, detail="OpenAI API key not configured")
    
    qdrant_client = get_qdrant_client()
    redis_client = get_redis_client()
    
    return SearchService(openai_api_key, qdrant_client, redis_client)

# Rotas
@app.get("/")
async def root():
    """Rota raiz para verificar se a API está funcionando."""
    return {"message": "Vector Service API is running"}

@app.post("/api/v1/vectors", status_code=201)
async def create_vector(
    product_data: ProductData,
    embedding_service: EmbeddingService = Depends(get_embedding_service)
):
    """
    Cria ou atualiza um vetor para um produto.
    
    Args:
        product_data: Dados do produto
        embedding_service: Serviço de embeddings
        
    Returns:
        Dict: Resultado da operação
    """
    try:
        logger.info(f"Creating vector for product {product_data.product_id} in account {product_data.account_id}")
        
        vector_id = embedding_service.generate_and_store_embedding(
            account_id=product_data.account_id,
            product_id=product_data.product_id,
            text=product_data.text,
            metadata=product_data.metadata
        )
        
        return {
            "success": True,
            "vector_id": vector_id,
            "message": f"Vector created for product {product_data.product_id}"
        }
    except Exception as e:
        logger.error(f"Error creating vector: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/search")
async def search(
    search_query: SearchQuery,
    search_service: SearchService = Depends(get_search_service)
):
    """
    Realiza busca semântica.
    
    Args:
        search_query: Consulta de busca
        search_service: Serviço de busca
        
    Returns:
        Dict: Resultados da busca
    """
    try:
        logger.info(f"Searching for '{search_query.query}' in account {search_query.account_id}")
        
        results = search_service.search(
            account_id=search_query.account_id,
            query=search_query.query,
            limit=search_query.limit,
            filter=search_query.filter
        )
        
        return {
            "success": True,
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        logger.error(f"Error searching: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/v1/vectors")
async def delete_vector(
    delete_request: DeleteRequest,
    embedding_service: EmbeddingService = Depends(get_embedding_service)
):
    """
    Remove um vetor do Qdrant.
    
    Args:
        delete_request: Requisição de exclusão
        embedding_service: Serviço de embeddings
        
    Returns:
        Dict: Resultado da operação
    """
    try:
        logger.info(f"Deleting vector for product {delete_request.product_id} in account {delete_request.account_id}")
        
        success = embedding_service.delete_vector(
            account_id=delete_request.account_id,
            product_id=delete_request.product_id
        )
        
        if success:
            return {
                "success": True,
                "message": f"Vector deleted for product {delete_request.product_id}"
            }
        else:
            return {
                "success": False,
                "message": f"Vector not found for product {delete_request.product_id}"
            }
    except Exception as e:
        logger.error(f"Error deleting vector: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Inicialização da aplicação
if __name__ == "__main__":
    import uvicorn
    
    # Obter configurações do ambiente
    host = os.environ.get("VECTOR_SERVICE_HOST", "0.0.0.0")
    port = int(os.environ.get("VECTOR_SERVICE_PORT", 8001))
    
    # Iniciar servidor
    uvicorn.run(app, host=host, port=port)
