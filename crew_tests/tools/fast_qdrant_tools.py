"""
Ferramentas otimizadas para integração com Qdrant com foco em baixa latência.
"""

import os
import time
import logging
from typing import Dict, List, Any, Optional, Callable, Type
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from qdrant_client import QdrantClient
from qdrant_client.http import models
from openai import OpenAI

logger = logging.getLogger(__name__)

from ..config import QDRANT_URL, QDRANT_API_KEY, OPENAI_API_KEY, EMBEDDING_MODEL


class FastQdrantSearchInput(BaseModel):
    """Modelo de entrada otimizado para a ferramenta de busca vetorial."""

    query: str = Field(description="A consulta do usuário")
    account_id: str = Field(description="ID da conta do cliente")
    collection_name: str = Field(description="Nome da coleção no Qdrant")
    limit: int = Field(default=3, description="Número máximo de resultados")
    score_threshold: float = Field(default=0.35, description="Limiar mínimo de similaridade")


class FastQdrantSearchTool(BaseTool):
    """Ferramenta de busca vetorial otimizada para baixa latência."""

    name: str = "fast_qdrant_search"
    description: str = """
    Busca rápida no Qdrant. Use para encontrar informações com baixa latência.

    Parâmetros:
    - query: A consulta do usuário
    - account_id: ID da conta do cliente
    - collection_name: Nome da coleção (business_rules, company_metadata, support_documents)
    - limit: Número máximo de resultados (padrão: 3)
    - score_threshold: Limiar mínimo de similaridade (padrão: 0.35)
    """
    args_schema: Type[BaseModel] = FastQdrantSearchInput

    # Atributos adicionais
    qdrant_client: Any = None
    openai_client: Any = None
    embedding_cache: Dict[str, List[float]] = {}

    def __init__(self):
        """Inicializa a ferramenta de busca vetorial otimizada."""
        super().__init__()

        logger.info(f"Inicializando FastQdrantSearchTool com URL={QDRANT_URL}")

        # Verificar se as configurações estão definidas
        if not QDRANT_URL:
            logger.error("QDRANT_URL não está definido")
            raise ValueError("QDRANT_URL não está definido")

        if not OPENAI_API_KEY:
            logger.error("OPENAI_API_KEY não está definido")
            raise ValueError("OPENAI_API_KEY não está definido")

        try:
            # Inicializar cliente Qdrant
            if QDRANT_API_KEY:
                self.qdrant_client = QdrantClient(
                    url=QDRANT_URL,
                    api_key=QDRANT_API_KEY,
                    timeout=2.0  # Timeout reduzido para garantir resposta rápida
                )
            else:
                self.qdrant_client = QdrantClient(
                    url=QDRANT_URL,
                    timeout=2.0  # Timeout reduzido para garantir resposta rápida
                )
            logger.info("Cliente Qdrant inicializado com sucesso")

            # Inicializar cliente OpenAI para embeddings
            self.openai_client = OpenAI(api_key=OPENAI_API_KEY)
            logger.info("Cliente OpenAI inicializado com sucesso")

            # Inicializar cache de embeddings
            self.embedding_cache = {}
            logger.info("Cache de embeddings inicializado")
        except Exception as e:
            logger.error(f"Erro ao inicializar ferramentas: {e}", exc_info=True)
            raise

    def _get_embedding(self, text: str) -> List[float]:
        """
        Gera embeddings com cache para reduzir latência.

        Args:
            text: Texto para gerar embedding

        Returns:
            Lista de floats representando o embedding
        """
        try:
            # Verificar se o embedding já está em cache
            if text in self.embedding_cache:
                logger.info("Embedding encontrado em cache")
                return self.embedding_cache[text]

            logger.info(f"Gerando embedding para texto: '{text[:30]}...'")
            # Gerar embedding
            start_time = time.time()
            response = self.openai_client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=text
            )
            embedding = response.data[0].embedding
            end_time = time.time()
            logger.info(f"Embedding gerado em {end_time - start_time:.2f}s")

            # Armazenar em cache
            self.embedding_cache[text] = embedding

            # Limitar tamanho do cache (manter apenas os últimos 100 embeddings)
            if len(self.embedding_cache) > 100:
                # Remover o primeiro item (mais antigo)
                self.embedding_cache.pop(next(iter(self.embedding_cache)))

            return embedding
        except Exception as e:
            logger.error(f"Erro ao gerar embedding: {e}", exc_info=True)
            raise

    def _execute(
        self,
        query: str,
        account_id: str,
        collection_name: str,
        limit: int = 3,
        score_threshold: float = 0.35
    ) -> List[Dict[str, Any]]:
        """
        Executa a busca no Qdrant com otimizações para baixa latência.

        Args:
            query: A consulta do usuário
            account_id: ID da conta do cliente
            collection_name: Nome da coleção no Qdrant
            limit: Número máximo de resultados
            score_threshold: Limiar mínimo de similaridade

        Returns:
            Lista de resultados
        """
        try:
            logger.info(f"Executando busca: query='{query}', collection='{collection_name}', account_id='{account_id}'")

            # Verificar se a coleção existe
            if not self.qdrant_client.collection_exists(collection_name):
                logger.warning(f"Coleção '{collection_name}' não existe")
                return []

            # Gerar embedding para a consulta (com cache)
            query_embedding = self._get_embedding(query)

            # Buscar documentos relevantes com timeout
            logger.info("Iniciando busca no Qdrant")
            start_time = time.time()
            search_results = self.qdrant_client.search(
                collection_name=collection_name,
                query_vector=query_embedding,
                query_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="account_id",
                            match=models.MatchValue(
                                value=account_id
                            )
                        )
                    ]
                ),
                limit=limit,
                score_threshold=score_threshold,
                with_payload=["text", "title", "is_temporary", "priority", "company_name", "greeting_message"],  # Limitar campos retornados
                with_vectors=False  # Não retornar vetores para economizar largura de banda
            )
            end_time = time.time()
            logger.info(f"Busca concluída em {end_time - start_time:.2f}s, encontrados {len(search_results)} resultados")

            # Extrair informações relevantes (processamento mínimo)
            results = []
            for hit in search_results:
                results.append({
                    "id": hit.id,
                    "text": hit.payload.get("text", ""),
                    "score": hit.score,
                    "is_temporary": hit.payload.get("is_temporary", False),
                    "priority": hit.payload.get("priority", 3),
                    "company_name": hit.payload.get("company_name", ""),
                    "greeting_message": hit.payload.get("greeting_message", "")
                })

            return results

        except Exception as e:
            logger.error(f"Erro na busca: {e}", exc_info=True)
            # Em caso de erro, retornar lista vazia para não bloquear o fluxo
            return []
