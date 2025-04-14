"""
Serviço para interação com a API da OpenAI.

Este módulo implementa um serviço para interação com a API da OpenAI,
permitindo a geração de texto e embeddings.
"""

import logging
from typing import Dict, List

from openai import AsyncOpenAI
from pydantic import BaseModel

from odoo_api.config.settings import settings

logger = logging.getLogger(__name__)

class OpenAIResponse(BaseModel):
    """Resposta da API da OpenAI."""

    text: str
    usage: Dict[str, int]
    model: str


class OpenAIService:
    """
    Serviço para interação com a API da OpenAI.

    Este serviço permite a geração de texto e embeddings usando a API da OpenAI.
    """

    def __init__(self):
        """Inicializa o serviço com a chave da API da OpenAI."""
        self.api_key = settings.OPENAI_API_KEY
        self.default_model = settings.OPENAI_MODEL
        self.embedding_model = settings.EMBEDDING_MODEL
        self.client = AsyncOpenAI(api_key=self.api_key)

    async def generate_text(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str = None,
        max_tokens: int = 500,
        temperature: float = 0.7,
    ) -> str:
        """
        Gera texto usando a API da OpenAI.

        Args:
            system_prompt: Prompt do sistema
            user_prompt: Prompt do usuário
            model: Modelo a ser usado
            max_tokens: Número máximo de tokens na resposta
            temperature: Temperatura (0.0 a 1.0)

        Returns:
            Texto gerado
        """
        try:
            # Usar modelo padrão se nenhum for especificado
            if model is None:
                model = self.default_model

            response = await self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature,
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Erro ao gerar texto com OpenAI: {e}")
            raise

    async def generate_embedding(
        self,
        text: str,
        model: str = None
    ) -> List[float]:
        """
        Gera embedding para um texto usando a API da OpenAI.

        Args:
            text: Texto para gerar embedding
            model: Modelo de embedding a ser usado

        Returns:
            Vetor de embedding
        """
        try:
            # Usar modelo padrão se nenhum for especificado
            if model is None:
                model = self.embedding_model

            response = await self.client.embeddings.create(
                model=model,
                input=text
            )

            return response.data[0].embedding

        except Exception as e:
            logger.error(f"Erro ao gerar embedding com OpenAI: {e}")
            raise


# Singleton para o serviço
_openai_service_instance = None

async def get_openai_service() -> OpenAIService:
    """
    Obtém uma instância do serviço OpenAI.

    Returns:
        Instância do serviço OpenAI
    """
    global _openai_service_instance

    if _openai_service_instance is None:
        _openai_service_instance = OpenAIService()

    return _openai_service_instance
