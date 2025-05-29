import logging
from typing import List

from fastembed import TextEmbedding

from mcp_server_qdrant.embeddings.base import EmbeddingProvider

logger = logging.getLogger(__name__)


class FastEmbedProvider(EmbeddingProvider):
    """
    Provedor de embeddings usando a biblioteca FastEmbed.
    """

    def __init__(self, model_name: str):
        """
        Inicializa o provedor de embeddings FastEmbed.
        :param model_name: Nome do modelo a ser usado.
        """
        self.model_name = model_name
        logger.info(f"Inicializando FastEmbedProvider com modelo {model_name}")
        self.model = TextEmbedding(model_name)
        self.vector_size = self.model.dimensions
        logger.info(f"Modelo inicializado com dimensão {self.vector_size}")

    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Gera embeddings para uma lista de documentos.
        :param texts: Lista de textos para gerar embeddings.
        :return: Lista de embeddings (vetores).
        """
        embeddings = list(self.model.embed(texts))
        return [embedding.tolist() for embedding in embeddings]

    async def embed_query(self, text: str) -> List[float]:
        """
        Gera embedding para uma consulta.
        :param text: Texto da consulta.
        :return: Embedding (vetor) da consulta.
        """
        embeddings = await self.embed_documents([text])
        return embeddings[0]

    def get_vector_size(self) -> int:
        """
        Retorna o tamanho do vetor de embedding.
        :return: Tamanho do vetor.
        """
        return self.vector_size

    def get_vector_name(self) -> str:
        """
        Retorna o nome do vetor de embedding.
        :return: Nome do vetor.
        """
        return "vector"
