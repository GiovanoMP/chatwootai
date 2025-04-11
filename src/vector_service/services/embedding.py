"""
Serviço de Embeddings

Este módulo contém o serviço para geração de embeddings e armazenamento em Qdrant.
"""

import openai
from typing import Dict, Any, List, Optional
import logging
import time
from datetime import datetime

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmbeddingService:
    """
    Serviço para geração de embeddings e sincronização com Qdrant.
    """
    
    def __init__(self, openai_api_key: str, qdrant_client, redis_client=None):
        """
        Inicializa o serviço de embeddings.
        
        Args:
            openai_api_key: Chave de API do OpenAI
            qdrant_client: Cliente do Qdrant
            redis_client: Cliente do Redis (opcional)
        """
        self.openai_api_key = openai_api_key
        openai.api_key = openai_api_key
        self.qdrant_client = qdrant_client
        self.redis_client = redis_client
        self.embedding_model = "text-embedding-3-small"
        self.embedding_dimensions = 1536  # Dimensões do modelo text-embedding-3-small
    
    def generate_and_store_embedding(
        self, 
        account_id: str, 
        product_id: str, 
        text: str, 
        metadata: Dict[str, Any]
    ) -> str:
        """
        Gera embedding para o texto e armazena no Qdrant.
        
        Args:
            account_id: ID da conta
            product_id: ID do produto
            text: Texto para gerar embedding
            metadata: Metadados adicionais para armazenar
            
        Returns:
            str: ID do vetor no Qdrant
        """
        start_time = time.time()
        logger.info(f"Processing product {product_id} for account {account_id}")
        
        # Verificar cache se disponível
        vector_id = None
        if self.redis_client:
            cache_key = f"embedding:{account_id}:{product_id}"
            cached = self.redis_client.get(cache_key)
            if cached:
                vector_id = cached.decode('utf-8')
                logger.info(f"Found cached vector ID: {vector_id}")
        
        # Gerar embedding
        embedding = self._generate_embedding(text)
        logger.info(f"Generated embedding with {len(embedding)} dimensions")
        
        # Criar ID único para o vetor se não existir
        if not vector_id:
            vector_id = f"prod_{account_id}_{product_id}"
        
        # Adicionar timestamp aos metadados
        enriched_metadata = metadata.copy()
        enriched_metadata.update({
            "product_id": product_id,
            "account_id": account_id,
            "embedding_model": self.embedding_model,
            "last_updated": datetime.now().isoformat(),
            "text_length": len(text)
        })
        
        # Armazenar no Qdrant
        self._store_in_qdrant(account_id, vector_id, embedding, enriched_metadata)
        
        # Atualizar cache se disponível
        if self.redis_client:
            cache_key = f"embedding:{account_id}:{product_id}"
            self.redis_client.set(cache_key, vector_id)
            # Definir expiração de 30 dias
            self.redis_client.expire(cache_key, 60 * 60 * 24 * 30)
        
        elapsed_time = time.time() - start_time
        logger.info(f"Completed processing in {elapsed_time:.2f} seconds")
        
        return vector_id
    
    def _generate_embedding(self, text: str) -> List[float]:
        """
        Gera embedding para o texto usando OpenAI.
        
        Args:
            text: Texto para gerar embedding
            
        Returns:
            List[float]: Vetor de embedding
        """
        try:
            response = openai.Embedding.create(
                model=self.embedding_model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            raise
    
    def _store_in_qdrant(
        self, 
        account_id: str, 
        vector_id: str, 
        embedding: List[float], 
        metadata: Dict[str, Any]
    ) -> None:
        """
        Armazena o embedding no Qdrant.
        
        Args:
            account_id: ID da conta
            vector_id: ID do vetor
            embedding: Vetor de embedding
            metadata: Metadados para armazenar
        """
        # Garantir que a coleção existe
        collection_name = f"products_{account_id}"
        self._ensure_collection_exists(collection_name)
        
        try:
            # Upsert no Qdrant
            self.qdrant_client.upsert(
                collection_name=collection_name,
                points=[
                    {
                        "id": vector_id,
                        "vector": embedding,
                        "payload": metadata
                    }
                ]
            )
            logger.info(f"Successfully stored vector {vector_id} in collection {collection_name}")
        except Exception as e:
            logger.error(f"Error storing vector in Qdrant: {str(e)}")
            raise
    
    def _ensure_collection_exists(self, collection_name: str) -> None:
        """
        Garante que a coleção existe no Qdrant.
        
        Args:
            collection_name: Nome da coleção
        """
        try:
            # Verificar se a coleção existe
            collections = self.qdrant_client.get_collections()
            collection_names = [c.name for c in collections.collections]
            
            if collection_name not in collection_names:
                logger.info(f"Creating new collection: {collection_name}")
                # Criar coleção
                self.qdrant_client.create_collection(
                    collection_name=collection_name,
                    vectors_config={
                        "size": self.embedding_dimensions,
                        "distance": "Cosine"
                    }
                )
                logger.info(f"Collection {collection_name} created successfully")
        except Exception as e:
            logger.error(f"Error ensuring collection exists: {str(e)}")
            raise
    
    def delete_vector(self, account_id: str, product_id: str) -> bool:
        """
        Remove um vetor do Qdrant.
        
        Args:
            account_id: ID da conta
            product_id: ID do produto
            
        Returns:
            bool: True se removido com sucesso
        """
        try:
            # Determinar ID do vetor e nome da coleção
            vector_id = f"prod_{account_id}_{product_id}"
            collection_name = f"products_{account_id}"
            
            # Verificar se a coleção existe
            collections = self.qdrant_client.get_collections()
            collection_names = [c.name for c in collections.collections]
            
            if collection_name not in collection_names:
                logger.warning(f"Collection {collection_name} does not exist")
                return False
            
            # Remover vetor
            self.qdrant_client.delete(
                collection_name=collection_name,
                points_selector=[vector_id]
            )
            
            # Remover do cache se disponível
            if self.redis_client:
                cache_key = f"embedding:{account_id}:{product_id}"
                self.redis_client.delete(cache_key)
            
            logger.info(f"Successfully deleted vector {vector_id} from collection {collection_name}")
            return True
        except Exception as e:
            logger.error(f"Error deleting vector: {str(e)}")
            return False
