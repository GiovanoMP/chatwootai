"""
Interface para serviços de vetorização.

Este módulo define a interface para serviços de vetorização, como armazenamento
e busca de vetores em bancos de dados vetoriais.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union

class VectorService(ABC):
    """Interface para serviços de vetorização."""
    
    @abstractmethod
    async def ensure_collection_exists(self, collection_name: str) -> bool:
        """
        Garante que uma coleção existe no banco de dados vetorial.
        
        Args:
            collection_name: Nome da coleção
            
        Returns:
            True se a coleção foi criada, False se já existia
        """
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass
