"""
Ferramenta otimizada para busca no Qdrant com foco em baixa latência.

Esta ferramenta segue a documentação oficial do CrewAI para implementação
de ferramentas personalizadas, com otimizações para garantir respostas
em menos de 3 segundos.
"""

import os
import time
import json
import logging
from typing import Dict, List, Any, Type, Optional
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
from qdrant_client import QdrantClient
from qdrant_client.http import models
from openai import OpenAI

from ..config import QDRANT_URL, QDRANT_API_KEY, OPENAI_API_KEY, EMBEDDING_MODEL

logger = logging.getLogger(__name__)

# Cache global para embeddings
EMBEDDING_CACHE = {}


class QdrantSearchInput(BaseModel):
    """Esquema de entrada para a ferramenta de busca no Qdrant."""

    query: str = Field(description="A consulta do usuário")
    account_id: str = Field(description="ID da conta do cliente")
    collection_name: str = Field(description="Nome da coleção no Qdrant")
    limit: int = Field(default=3, description="Número máximo de resultados")
    score_threshold: float = Field(default=0.35, description="Limiar mínimo de similaridade")


class OptimizedQdrantTool(BaseTool):
    """
    Ferramenta otimizada para busca no Qdrant com foco em baixa latência.

    Esta ferramenta implementa várias otimizações para garantir respostas rápidas:
    1. Cache de embeddings para consultas repetidas
    2. Timeout reduzido para chamadas ao Qdrant
    3. Limite de resultados otimizado
    4. Processamento mínimo de resultados
    """

    name: str = "optimized_qdrant_search"
    description: str = """
    Busca otimizada no Qdrant para encontrar informações relevantes com baixa latência.

    Use esta ferramenta para buscar informações em coleções do Qdrant com base em uma consulta.
    A ferramenta retorna os resultados mais relevantes, priorizando regras temporárias.

    Parâmetros:
    - query: A consulta do usuário
    - account_id: ID da conta do cliente
    - collection_name: Nome da coleção (business_rules, company_metadata, support_documents)
    - limit: Número máximo de resultados (padrão: 3)
    - score_threshold: Limiar mínimo de similaridade (padrão: 0.35)
    """
    args_schema: Type[BaseModel] = QdrantSearchInput

    # Atributos adicionais
    qdrant_client: Optional[Any] = None
    openai_client: Optional[Any] = None

    def __init__(self):
        """Inicializa a ferramenta de busca no Qdrant."""
        super().__init__()

        # Inicializar clientes
        self.qdrant_client = None
        self.openai_client = None

        # Inicializar clientes na criação da ferramenta
        self._initialize_clients()

    def _initialize_clients(self):
        """Inicializa os clientes Qdrant e OpenAI."""
        logger.info(f"Inicializando clientes com QDRANT_URL={QDRANT_URL}")

        try:
            # Inicializar cliente Qdrant
            if QDRANT_API_KEY:
                self.qdrant_client = QdrantClient(
                    url=QDRANT_URL,
                    api_key=QDRANT_API_KEY,
                    timeout=1.0  # Timeout reduzido para garantir resposta rápida
                )
            else:
                self.qdrant_client = QdrantClient(
                    url=QDRANT_URL,
                    timeout=1.0  # Timeout reduzido para garantir resposta rápida
                )
            logger.info("Cliente Qdrant inicializado com sucesso")

            # Inicializar cliente OpenAI
            self.openai_client = OpenAI(api_key=OPENAI_API_KEY)
            logger.info("Cliente OpenAI inicializado com sucesso")

        except Exception as e:
            logger.error(f"Erro ao inicializar clientes: {e}", exc_info=True)
            raise

    def _get_embedding(self, text: str) -> List[float]:
        """
        Gera embeddings com cache para reduzir latência.

        Args:
            text: Texto para gerar embedding

        Returns:
            Lista de floats representando o embedding
        """
        global EMBEDDING_CACHE

        # Verificar se o embedding já está em cache
        if text in EMBEDDING_CACHE:
            logger.info("Embedding encontrado em cache")
            return EMBEDDING_CACHE[text]

        try:
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
            EMBEDDING_CACHE[text] = embedding

            # Limitar tamanho do cache (manter apenas os últimos 100 embeddings)
            if len(EMBEDDING_CACHE) > 100:
                # Remover o primeiro item (mais antigo)
                EMBEDDING_CACHE.pop(next(iter(EMBEDDING_CACHE)))

            return embedding

        except Exception as e:
            logger.error(f"Erro ao gerar embedding: {e}", exc_info=True)
            raise

    def _run(
        self,
        query: str,
        account_id: str,
        collection_name: str,
        limit: int = 3,
        score_threshold: float = 0.35
    ) -> str:
        """
        Executa a busca no Qdrant com otimizações para baixa latência.

        Args:
            query: A consulta do usuário
            account_id: ID da conta do cliente
            collection_name: Nome da coleção no Qdrant
            limit: Número máximo de resultados
            score_threshold: Limiar mínimo de similaridade

        Returns:
            Resultados da busca em formato JSON
        """
        # Verificar se os clientes estão inicializados
        if self.qdrant_client is None or self.openai_client is None:
            self._initialize_clients()

        try:
            logger.info(f"Executando busca: query='{query}', collection='{collection_name}', account_id='{account_id}'")

            # Verificar se a coleção existe
            if not self.qdrant_client.collection_exists(collection_name):
                logger.warning(f"Coleção '{collection_name}' não existe")
                return json.dumps([])

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
                with_payload=["text", "title", "is_temporary", "priority", "company_name", "greeting_message"],
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

            # Ordenar por prioridade (menor número = maior prioridade) e depois por score (maior = melhor)
            results.sort(key=lambda x: (x.get("priority", 3), -x.get("score", 0)))

            return json.dumps(results, ensure_ascii=False)

        except Exception as e:
            logger.error(f"Erro na busca: {e}", exc_info=True)
            # Em caso de erro, retornar lista vazia
            return json.dumps([])
