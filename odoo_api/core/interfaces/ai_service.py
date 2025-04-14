"""
Interface para serviços de IA.

Este módulo define a interface para serviços de IA, como geração de texto e embeddings.
"""

from abc import ABC, abstractmethod
from typing import List, Optional

class AIService(ABC):
    """Interface para serviços de IA."""
    
    @abstractmethod
    async def generate_text(
        self,
        system_prompt: str,
        user_prompt: str,
        model: Optional[str] = None,
        max_tokens: int = 500,
        temperature: float = 0.7,
    ) -> str:
        """
        Gera texto usando um modelo de linguagem.
        
        Args:
            system_prompt: Prompt do sistema
            user_prompt: Prompt do usuário
            model: Modelo a ser usado (opcional)
            max_tokens: Número máximo de tokens na resposta
            temperature: Temperatura (0.0 a 1.0)
            
        Returns:
            Texto gerado
        """
        pass
    
    @abstractmethod
    async def generate_embedding(
        self,
        text: str,
        model: Optional[str] = None
    ) -> List[float]:
        """
        Gera embedding para um texto.
        
        Args:
            text: Texto para gerar embedding
            model: Modelo de embedding a ser usado (opcional)
            
        Returns:
            Vetor de embedding
        """
        pass
