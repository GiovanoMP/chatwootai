"""
Serviço de vetorização e integração com Qdrant.

Este módulo implementa um serviço para vetorização e integração com o Qdrant,
permitindo armazenamento e busca de vetores.
"""

import logging
import hashlib
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_exponential

from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.exceptions import UnexpectedResponse

from odoo_api.core.interfaces.vector_service import VectorService as VectorServiceInterface
from odoo_api.infrastructure.config.settings import settings
from odoo_api.core.domain.exceptions import VectorDBError
from odoo_api.core.services.openai_service import get_openai_service
from odoo_api.core.services.cache_service import get_cache_service

logger = logging.getLogger(__name__)

class QdrantVectorService(VectorServiceInterface):
    """Serviço de vetorização e integração com Qdrant."""
    
    def __init__(self):
        """Inicializa o serviço de vetorização."""
        self.qdrant_client = None
        self.embedding_model = settings.EMBEDDING_MODEL
        self.embedding_dimension = settings.EMBEDDING_DIMENSION
    
    async def connect(self):
        """Conecta ao Qdrant."""
        try:
            self.qdrant_client = QdrantClient(
                host=settings.QDRANT_HOST,
                port=settings.QDRANT_PORT,
                api_key=settings.QDRANT_API_KEY,
            )
            
            # Verificar conexão
            self.qdrant_client.get_collections()
            
            logger.info(f"Connected to Qdrant at {settings.QDRANT_HOST}:{settings.QDRANT_PORT}")
        
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {e}")
            raise VectorDBError(f"Failed to connect to Qdrant: {e}")
    
    async def ensure_collection_exists(self, collection_name: str) -> bool:
        """
        Garante que uma coleção existe no Qdrant.
        
        Args:
            collection_name: Nome da coleção
            
        Returns:
            True se a coleção foi criada, False se já existia
        """
        try:
            if not self.qdrant_client:
                await self.connect()
            
            # Verificar se a coleção já existe
            collections = self.qdrant_client.get_collections()
            collection_names = [collection.name for collection in collections.collections]
            
            if collection_name not in collection_names:
                # Criar coleção
                self.qdrant_client.create_collection(
                    collection_name=collection_name,
                    vectors_config=models.VectorParams(
                        size=self.embedding_dimension,
                        distance=models.Distance.COSINE,
                    ),
                )
                
                # Criar índices para metadados
                self.qdrant_client.create_payload_index(
                    collection_name=collection_name,
                    field_name="id",
                    field_schema=models.PayloadSchemaType.KEYWORD,
                )
                
                self.qdrant_client.create_payload_index(
                    collection_name=collection_name,
                    field_name="account_id",
                    field_schema=models.PayloadSchemaType.KEYWORD,
                )
                
                self.qdrant_client.create_payload_index(
                    collection_name=collection_name,
                    field_name="last_updated",
                    field_schema=models.PayloadSchemaType.DATETIME,
                )
                
                logger.info(f"Created collection {collection_name} in Qdrant")
                return True
            
            return False
        
        except Exception as e:
            logger.error(f"Failed to ensure collection {collection_name} exists: {e}")
            raise VectorDBError(f"Failed to ensure collection {collection_name} exists: {e}")
    
    @retry(
        stop=stop_after_attempt(settings.RETRY_MAX_ATTEMPTS),
        wait=wait_exponential(
            multiplier=1,
            min=settings.RETRY_MIN_SECONDS,
            max=settings.RETRY_MAX_SECONDS,
        ),
    )
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Gera um embedding para um texto.
        
        Args:
            text: Texto para gerar embedding
        
        Returns:
            Embedding como lista de floats
        """
        try:
            # Verificar cache
            cache = await get_cache_service()
            cache_key = f"embedding:{hashlib.md5(text.encode()).hexdigest()}"
            cached_embedding = await cache.get(cache_key)
            
            if cached_embedding:
                return cached_embedding
            
            # Gerar embedding via serviço OpenAI
            openai_service = await get_openai_service()
            embedding = await openai_service.generate_embedding(text, model=self.embedding_model)
            
            # Armazenar em cache
            await cache.set(cache_key, embedding, ttl=86400)  # 24 horas
            
            return embedding
        
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise VectorDBError(f"Failed to generate embedding: {e}")
    
    async def store_vector(
        self,
        collection_name: str,
        vector_id: str,
        vector: List[float],
        payload: Dict[str, Any]
    ) -> bool:
        """
        Armazena um vetor no banco de dados vetorial.
        
        Args:
            collection_name: Nome da coleção
            vector_id: ID do vetor
            vector: Vetor a ser armazenado
            payload: Dados associados ao vetor
            
        Returns:
            True se o vetor foi armazenado com sucesso
        """
        try:
            if not self.qdrant_client:
                await self.connect()
            
            # Garantir que a coleção existe
            await self.ensure_collection_exists(collection_name)
            
            # Adicionar timestamp
            payload["last_updated"] = datetime.now().isoformat()
            
            # Armazenar vetor
            self.qdrant_client.upsert(
                collection_name=collection_name,
                points=[
                    models.PointStruct(
                        id=vector_id,
                        vector=vector,
                        payload=payload
                    )
                ],
            )
            
            logger.info(f"Stored vector {vector_id} in collection {collection_name}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to store vector: {e}")
            raise VectorDBError(f"Failed to store vector: {e}")
    
    async def search_vectors(
        self,
        collection_name: str,
        query_vector: List[float],
        limit: int = 10,
        score_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Busca vetores similares no banco de dados vetorial.
        
        Args:
            collection_name: Nome da coleção
            query_vector: Vetor de consulta
            limit: Número máximo de resultados
            score_threshold: Limiar de similaridade
            
        Returns:
            Lista de resultados ordenados por similaridade
        """
        try:
            if not self.qdrant_client:
                await self.connect()
            
            # Buscar vetores similares
            search_result = self.qdrant_client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=limit,
                score_threshold=score_threshold,
            )
            
            # Converter para formato mais amigável
            results = []
            for point in search_result:
                result = point.payload
                result["id"] = point.id
                result["similarity_score"] = point.score
                results.append(result)
            
            return results
        
        except Exception as e:
            logger.error(f"Failed to search vectors: {e}")
            raise VectorDBError(f"Failed to search vectors: {e}")
    
    async def delete_vector(
        self,
        collection_name: str,
        vector_id: str
    ) -> bool:
        """
        Remove um vetor do banco de dados vetorial.
        
        Args:
            collection_name: Nome da coleção
            vector_id: ID do vetor
            
        Returns:
            True se o vetor foi removido com sucesso
        """
        try:
            if not self.qdrant_client:
                await self.connect()
            
            # Remover vetor
            self.qdrant_client.delete(
                collection_name=collection_name,
                points_selector=models.PointIdsList(
                    points=[vector_id]
                ),
            )
            
            logger.info(f"Deleted vector {vector_id} from collection {collection_name}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to delete vector: {e}")
            raise VectorDBError(f"Failed to delete vector: {e}")
    
    async def delete_collection(
        self,
        collection_name: str
    ) -> bool:
        """
        Remove uma coleção do banco de dados vetorial.
        
        Args:
            collection_name: Nome da coleção
            
        Returns:
            True se a coleção foi removida com sucesso
        """
        try:
            if not self.qdrant_client:
                await self.connect()
            
            # Remover coleção
            self.qdrant_client.delete_collection(
                collection_name=collection_name
            )
            
            logger.info(f"Deleted collection {collection_name}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to delete collection: {e}")
            raise VectorDBError(f"Failed to delete collection: {e}")


# Singleton para o serviço
_vector_service_instance = None

async def get_vector_service() -> QdrantVectorService:
    """
    Obtém uma instância do serviço de vetorização.
    
    Returns:
        Instância do serviço de vetorização
    """
    global _vector_service_instance
    
    if _vector_service_instance is None:
        _vector_service_instance = QdrantVectorService()
        await _vector_service_instance.connect()
    
    return _vector_service_instance
