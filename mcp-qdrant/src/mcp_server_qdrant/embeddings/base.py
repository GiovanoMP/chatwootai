from abc import ABC, abstractmethod
from typing import List


class EmbeddingProvider(ABC):
    """
    Classe base abstrata para provedores de embeddings.
    """

    @abstractmethod
    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Gera embeddings para uma lista de documentos.
        :param texts: Lista de textos para gerar embeddings.
        :return: Lista de embeddings (vetores).
        """
        pass

    @abstractmethod
    async def embed_query(self, text: str) -> List[float]:
        """
        Gera embedding para uma consulta.
        :param text: Texto da consulta.
        :return: Embedding (vetor) da consulta.
        """
        pass

    @abstractmethod
    def get_vector_size(self) -> int:
        """
        Retorna o tamanho do vetor de embedding.
        :return: Tamanho do vetor.
        """
        pass

    @abstractmethod
    def get_vector_name(self) -> str:
        """
        Retorna o nome do vetor de embedding.
        :return: Nome do vetor.
        """
        pass
