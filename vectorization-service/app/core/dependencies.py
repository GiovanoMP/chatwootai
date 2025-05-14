"""
Dependências para injeção no FastAPI.
"""

from fastapi import Depends

from app.services.redis_service import RedisService
from app.services.embedding_service import EmbeddingService
from app.services.vector_service import VectorService
from app.services.enrichment_service import EnrichmentService
from app.services.cache_service import CacheService

def get_redis_service():
    """Obtém uma instância do serviço Redis."""
    return RedisService()

def get_embedding_service():
    """Obtém uma instância do serviço de embedding."""
    return EmbeddingService()

def get_vector_service(
    embedding_service: EmbeddingService = Depends(get_embedding_service),
    redis_service: RedisService = Depends(get_redis_service)
):
    """Obtém uma instância do serviço de vetorização."""
    return VectorService(embedding_service, redis_service)

def get_enrichment_service(
    redis_service: RedisService = Depends(get_redis_service)
):
    """Obtém uma instância do serviço de enriquecimento."""
    return EnrichmentService(redis_service)

def get_cache_service(
    redis_service: RedisService = Depends(get_redis_service)
):
    """Obtém uma instância do serviço de cache."""
    return CacheService(redis_service)
