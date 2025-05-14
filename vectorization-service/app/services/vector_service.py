"""
Serviço para operações com vetores e embeddings.
"""

import logging
from typing import Dict, List, Optional, Any, Union, Set
from datetime import datetime

from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.exceptions import UnexpectedResponse

from app.core.config import settings
from app.core.exceptions import VectorDBError
from app.services.embedding_service import EmbeddingService
from app.services.redis_service import RedisService

logger = logging.getLogger(__name__)

class VectorService:
    """Serviço para operações com vetores e embeddings."""

    def __init__(self, embedding_service: EmbeddingService, redis_service: RedisService):
        """
        Inicializa o serviço de vetores.

        Args:
            embedding_service: Serviço para geração de embeddings
            redis_service: Serviço Redis para cache
        """
        self.qdrant_client = None
        self.embedding_service = embedding_service
        self.redis_service = redis_service

    async def connect(self):
        """Conecta ao serviço de vetores."""
        if self.qdrant_client is not None:
            return

        try:
            # Conectar ao Qdrant
            self.qdrant_client = QdrantClient(
                host=settings.QDRANT_HOST,
                port=settings.QDRANT_PORT,
                api_key=settings.QDRANT_API_KEY,
                timeout=settings.TIMEOUT_DEFAULT
            )

            # Verificar conexão
            self.qdrant_client.get_collections()

            logger.info("Conectado ao Qdrant")

        except Exception as e:
            logger.error(f"Falha ao conectar ao Qdrant: {e}")
            raise VectorDBError(f"Falha ao conectar ao Qdrant: {e}")

    async def ensure_collection_exists(self, collection_name: str, vector_size: int = None):
        """
        Garante que uma coleção existe no Qdrant.

        Args:
            collection_name: Nome da coleção
            vector_size: Tamanho do vetor (opcional, padrão é settings.EMBEDDING_DIMENSION)
        """
        if vector_size is None:
            vector_size = settings.EMBEDDING_DIMENSION

        await self.connect()

        try:
            # Verificar se a coleção já existe
            collections = self.qdrant_client.get_collections()
            if collection_name in [c.name for c in collections.collections]:
                return

            # Criar a coleção
            self.qdrant_client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(
                    size=vector_size,
                    distance=models.Distance.COSINE
                )
            )

            # Criar índice para account_id para facilitar filtragem por tenant
            self.qdrant_client.create_payload_index(
                collection_name=collection_name,
                field_name="account_id",
                field_schema=models.PayloadSchemaType.KEYWORD,
            )

            logger.info(f"Criada coleção {collection_name}")

        except Exception as e:
            logger.error(f"Falha ao garantir que a coleção {collection_name} existe: {e}")
            raise VectorDBError(f"Falha ao garantir que a coleção {collection_name} existe: {e}")

    async def store_vector(
        self,
        collection_name: str,
        vector_id: str,
        vector: List[float],
        payload: Dict[str, Any]
    ):
        """
        Armazena um vetor no Qdrant.

        Args:
            collection_name: Nome da coleção
            vector_id: ID do vetor
            vector: Vetor a ser armazenado
            payload: Dados adicionais a serem armazenados com o vetor
        """
        await self.connect()

        # Garantir que a coleção existe
        await self.ensure_collection_exists(collection_name)

        try:
            # Converter o ID para UUID para garantir compatibilidade com o Qdrant
            # O Qdrant aceita apenas inteiros não assinados ou UUIDs como IDs
            import uuid
            import hashlib

            # Gerar um UUID determinístico baseado no vector_id original
            # Isso garante que o mesmo vector_id sempre gere o mesmo UUID
            uuid_namespace = uuid.UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')  # Namespace para URLs
            uuid_id = uuid.uuid5(uuid_namespace, vector_id)

            # Armazenar o ID original no payload para referência
            payload["original_id"] = vector_id

            # Armazenar o vetor
            self.qdrant_client.upsert(
                collection_name=collection_name,
                points=[
                    models.PointStruct(
                        id=str(uuid_id),
                        vector=vector,
                        payload=payload
                    )
                ]
            )

            logger.debug(f"Vetor {vector_id} (UUID: {uuid_id}) armazenado na coleção {collection_name}")

        except Exception as e:
            logger.error(f"Falha ao armazenar vetor {vector_id} na coleção {collection_name}: {e}")
            raise VectorDBError(f"Falha ao armazenar vetor {vector_id} na coleção {collection_name}: {e}")

    async def get_all_rule_ids(self, collection_name: str, account_id: str) -> Set[str]:
        """
        Obtém todos os IDs de regras existentes no Qdrant para uma conta específica.

        Args:
            collection_name: Nome da coleção
            account_id: ID da conta

        Returns:
            Conjunto de IDs de regras originais (não UUIDs)
        """
        await self.connect()

        try:
            # Consultar todos os pontos com o account_id específico
            scroll_result = self.qdrant_client.scroll(
                collection_name=collection_name,
                scroll_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="account_id",
                            match=models.MatchValue(value=account_id)
                        )
                    ]
                ),
                limit=10000,  # Ajustar conforme necessário
                with_payload=True,   # Precisamos do payload para obter o ID original
                with_vectors=False   # Não precisamos dos vetores
            )

            # Extrair IDs originais do payload
            rule_ids = set()
            for point in scroll_result[0]:
                if point.payload and "original_id" in point.payload:
                    rule_ids.add(point.payload["original_id"])
                else:
                    # Fallback para o ID do ponto se não houver original_id
                    rule_ids.add(str(point.id))

            return rule_ids

        except Exception as e:
            logger.error(f"Erro ao obter IDs de regras: {str(e)}")
            raise VectorDBError(f"Erro ao obter IDs de regras: {str(e)}")

    async def delete_vectors(self, collection_name: str, vector_ids: List[str]):
        """
        Remove múltiplos vetores do Qdrant.

        Args:
            collection_name: Nome da coleção
            vector_ids: Lista de IDs de vetores a serem removidos
        """
        if not vector_ids:
            return

        await self.connect()

        try:
            # Converter os IDs para UUIDs
            import uuid
            uuid_namespace = uuid.UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')
            uuid_ids = [str(uuid.uuid5(uuid_namespace, vector_id)) for vector_id in vector_ids]

            # Remover vetores em lotes para evitar problemas com requisições muito grandes
            batch_size = 100
            for i in range(0, len(uuid_ids), batch_size):
                batch = uuid_ids[i:i+batch_size]
                self.qdrant_client.delete(
                    collection_name=collection_name,
                    points_selector=models.PointIdsList(
                        points=batch
                    )
                )

            logger.info(f"Removidos {len(vector_ids)} vetores da coleção {collection_name}")

        except Exception as e:
            logger.error(f"Erro ao remover vetores: {str(e)}")
            raise VectorDBError(f"Erro ao remover vetores: {str(e)}")

    async def search_vectors(
        self,
        collection_name: str,
        query_vector: List[float],
        filter_conditions: Optional[Dict[str, Any]] = None,
        limit: int = 10,
        score_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Busca vetores similares no Qdrant.

        Args:
            collection_name: Nome da coleção
            query_vector: Vetor de consulta
            filter_conditions: Condições de filtro (opcional)
            limit: Limite de resultados
            score_threshold: Limiar de similaridade

        Returns:
            Lista de resultados ordenados por similaridade
        """
        await self.connect()

        try:
            # Construir filtro
            search_filter = None
            if filter_conditions:
                must_conditions = []

                for key, value in filter_conditions.items():
                    if isinstance(value, list):
                        # Filtro para valores em uma lista
                        must_conditions.append(
                            models.FieldCondition(
                                key=key,
                                match=models.MatchAny(any=value)
                            )
                        )
                    else:
                        # Filtro para valor único
                        must_conditions.append(
                            models.FieldCondition(
                                key=key,
                                match=models.MatchValue(value=value)
                            )
                        )

                if must_conditions:
                    search_filter = models.Filter(
                        must=must_conditions
                    )

            # Buscar vetores similares
            search_result = self.qdrant_client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                query_filter=search_filter,
                limit=limit,
                score_threshold=score_threshold
            )

            # Converter para formato mais amigável
            results = []
            for hit in search_result:
                result = hit.payload
                result["score"] = hit.score
                results.append(result)

            return results

        except Exception as e:
            logger.error(f"Falha ao buscar vetores: {e}")
            raise VectorDBError(f"Falha ao buscar vetores: {e}")

    async def delete_collection(self, collection_name: str):
        """
        Remove uma coleção do Qdrant.

        Args:
            collection_name: Nome da coleção
        """
        await self.connect()

        try:
            # Remover a coleção
            self.qdrant_client.delete_collection(
                collection_name=collection_name
            )

            logger.info(f"Coleção {collection_name} removida")

        except Exception as e:
            logger.error(f"Falha ao remover coleção {collection_name}: {e}")
            raise VectorDBError(f"Falha ao remover coleção {collection_name}: {e}")

    async def clear_collection(self, collection_name: str, account_id: str):
        """
        Remove todos os vetores de uma conta específica em uma coleção.

        Args:
            collection_name: Nome da coleção
            account_id: ID da conta
        """
        await self.connect()

        try:
            # Remover todos os vetores da conta
            self.qdrant_client.delete(
                collection_name=collection_name,
                points_selector=models.FilterSelector(
                    filter=models.Filter(
                        must=[
                            models.FieldCondition(
                                key="account_id",
                                match=models.MatchValue(value=account_id)
                            )
                        ]
                    )
                )
            )

            logger.info(f"Todos os vetores da conta {account_id} removidos da coleção {collection_name}")

        except Exception as e:
            logger.error(f"Falha ao limpar coleção {collection_name} para a conta {account_id}: {e}")
            raise VectorDBError(f"Falha ao limpar coleção {collection_name} para a conta {account_id}: {e}")
