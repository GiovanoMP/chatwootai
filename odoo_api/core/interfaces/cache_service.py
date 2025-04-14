"""
Interface para serviços de cache.

Este módulo define a interface para serviços de cache, como armazenamento
e recuperação de dados em cache.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union

class CacheService(ABC):
    """Interface para serviços de cache."""
    
    @abstractmethod
    async def get(self, key: str) -> Any:
        """
        Obtém um valor do cache.
        
        Args:
            key: Chave do valor
            
        Returns:
            Valor armazenado ou None se não existir
        """
        pass
    
    @abstractmethod
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Armazena um valor no cache.
        
        Args:
            key: Chave do valor
            value: Valor a ser armazenado
            ttl: Tempo de vida em segundos (opcional)
            
        Returns:
            True se o valor foi armazenado com sucesso
        """
        pass
    
    @abstractmethod
    async def delete(self, *keys: str) -> int:
        """
        Remove valores do cache.
        
        Args:
            keys: Chaves dos valores a serem removidos
            
        Returns:
            Número de valores removidos
        """
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """
        Verifica se uma chave existe no cache.
        
        Args:
            key: Chave a ser verificada
            
        Returns:
            True se a chave existir
        """
        pass
    
    @abstractmethod
    async def keys(self, pattern: str) -> List[str]:
        """
        Obtém chaves que correspondem a um padrão.
        
        Args:
            pattern: Padrão de chave
            
        Returns:
            Lista de chaves correspondentes
        """
        pass
