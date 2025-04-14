"""
Interface para agentes de embedding.

Este módulo define a interface para agentes de embedding, que processam
dados brutos para gerar texto rico para embeddings.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class EmbeddingAgent(ABC):
    """Interface para agentes de embedding."""
    
    @abstractmethod
    async def process_data(
        self,
        data: Dict[str, Any],
        business_area: Optional[str] = None
    ) -> str:
        """
        Processa dados brutos para gerar texto rico para embeddings.
        
        Args:
            data: Dados brutos a serem processados
            business_area: Área de negócio (opcional)
            
        Returns:
            Texto processado pronto para vetorização
        """
        pass
