"""
Cache de Embeddings usando Redis para o MCP-Crew v2.

Implementa métodos para armazenar e recuperar vetores de embedding.
"""

import hashlib
import json
import logging
from typing import Dict, List, Optional, Union

import numpy as np

from src.redis_manager.redis_manager import redis_manager, DataType

logger = logging.getLogger(__name__)

class EmbeddingCache:
    """Gerencia cache de embeddings no Redis."""
    
    def __init__(self, tenant_id: str):
        """
        Inicializa o cache de embeddings.
        
        Args:
            tenant_id: ID do tenant (account_id)
        """
        self.tenant_id = tenant_id
    
    def _generate_hash(self, text: str) -> str:
        """Gera um hash para o texto."""
        return hashlib.md5(text.encode('utf-8')).hexdigest()
    
    def store_embedding(self, text: str, embedding: List[float], ttl: Optional[int] = None) -> bool:
        """
        Armazena um embedding no cache.
        
        Args:
            text: Texto original
            embedding: Vetor de embedding
            ttl: Tempo de vida em segundos (opcional)
        
        Returns:
            bool: True se armazenado com sucesso
        """
        try:
            # Gerar hash do texto
            text_hash = self._generate_hash(text)
            
            # Armazenar embedding
            data = {
                "text": text,
                "embedding": embedding,
                "dimensions": len(embedding)
            }
            
            return redis_manager.set(
                tenant_id=self.tenant_id,
                data_type=DataType.EMBEDDING,
                identifier=text_hash,
                value=data,
                ttl=ttl
            )
        except Exception as e:
            logger.error(f"Erro ao armazenar embedding: {e}")
            return False
    
    def get_embedding(self, text: str) -> Optional[List[float]]:
        """
        Recupera um embedding do cache.
        
        Args:
            text: Texto original
        
        Returns:
            List[float]: Vetor de embedding ou None se não encontrado
        """
        try:
            # Gerar hash do texto
            text_hash = self._generate_hash(text)
            
            # Recuperar embedding
            data = redis_manager.get(
                tenant_id=self.tenant_id,
                data_type=DataType.EMBEDDING,
                identifier=text_hash
            )
            
            if data and "embedding" in data:
                return data["embedding"]
            return None
        except Exception as e:
            logger.error(f"Erro ao recuperar embedding: {e}")
            return None
    
    def store_batch_embeddings(self, texts: List[str], embeddings: List[List[float]], ttl: Optional[int] = None) -> bool:
        """
        Armazena múltiplos embeddings no cache.
        
        Args:
            texts: Lista de textos
            embeddings: Lista de vetores de embedding
            ttl: Tempo de vida em segundos (opcional)
        
        Returns:
            bool: True se todos foram armazenados com sucesso
        """
        if len(texts) != len(embeddings):
            logger.error("Número de textos e embeddings não correspondem")
            return False
        
        success = True
        for text, embedding in zip(texts, embeddings):
            if not self.store_embedding(text, embedding, ttl):
                success = False
        
        return success
    
    def get_batch_embeddings(self, texts: List[str]) -> Dict[str, List[float]]:
        """
        Recupera múltiplos embeddings do cache.
        
        Args:
            texts: Lista de textos
        
        Returns:
            Dict[str, List[float]]: Dicionário com textos e seus embeddings
        """
        result = {}
        for text in texts:
            embedding = self.get_embedding(text)
            if embedding:
                result[text] = embedding
        
        return result
    
    def clear_embeddings(self, pattern: str = "*") -> int:
        """
        Remove embeddings do cache.
        
        Args:
            pattern: Padrão para filtrar embeddings a serem removidos
        
        Returns:
            int: Número de embeddings removidos
        """
        try:
            keys = redis_manager.get_keys_by_pattern(
                tenant_id=self.tenant_id,
                data_type=DataType.EMBEDDING,
                pattern=pattern
            )
            
            count = 0
            for key in keys:
                # Extrair identificador da chave
                identifier = key.split(":")[-1]
                if redis_manager.delete(
                    tenant_id=self.tenant_id,
                    data_type=DataType.EMBEDDING,
                    identifier=identifier
                ):
                    count += 1
            
            return count
        except Exception as e:
            logger.error(f"Erro ao limpar embeddings: {e}")
            return 0
