"""
Serviço para operações com vetores e embeddings.

Este módulo implementa um serviço para operações com vetores e embeddings,
incluindo geração de embeddings, armazenamento e busca de vetores.
"""

import logging
import json
import os
import time
from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime

import numpy as np
from tenacity import retry, stop_after_attempt, wait_exponential
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.exceptions import UnexpectedResponse

from odoo_api.config.settings import settings
from odoo_api.core.exceptions import VectorDBError

logger = logging.getLogger(__name__)

class VectorService:
    """Serviço para operações com vetores e embeddings."""

    def __init__(self):
        """Inicializa o serviço de vetores."""
        self.qdrant_client = None
        self.openai_client = None

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

            # Conectar ao OpenAI
            from openai import AsyncOpenAI
            self.openai_client = AsyncOpenAI(
                api_key=settings.OPENAI_API_KEY,
                timeout=settings.TIMEOUT_DEFAULT
            )

            logger.info("Connected to vector services")

        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {e}")
            raise VectorDBError(f"Failed to connect to Qdrant: {e}")

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

            logger.info(f"Created collection {collection_name}")

        except Exception as e:
            logger.error(f"Failed to ensure collection {collection_name} exists: {e}")
            raise VectorDBError(f"Failed to ensure collection {collection_name} exists: {e}")

    @retry(
        stop=stop_after_attempt(settings.RETRY_MAX_ATTEMPTS),
        wait=wait_exponential(
            multiplier=1,
            min=settings.RETRY_MIN_SECONDS,
            max=settings.RETRY_MAX_SECONDS,
        ),
    )
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Gera um embedding para um texto.

        Args:
            text: Texto para gerar o embedding

        Returns:
            Embedding do texto
        """
        if not text:
            # Retornar um vetor de zeros se o texto estiver vazio
            return [0.0] * settings.EMBEDDING_DIMENSION

        await self.connect()

        try:
            # Gerar embedding usando o OpenAI
            response = await self.openai_client.embeddings.create(
                model=settings.EMBEDDING_MODEL,
                input=text
            )

            # Extrair o embedding
            embedding = response.data[0].embedding

            return embedding

        except Exception as e:
            if hasattr(e, "status_code") and e.status_code:
                logger.error(f"HTTP error while generating embedding: {e}")
                raise VectorDBError(f"HTTP error while generating embedding: {e}")
            else:
                logger.error(f"Failed to generate embedding: {e}")
                raise VectorDBError(f"Failed to generate embedding: {e}")

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

        # Armazenar o vetor
        self.qdrant_client.upsert(
            collection_name=collection_name,
            points=[
                models.PointStruct(
                    id=vector_id,
                    vector=vector,
                    payload=payload
                )
            ]
        )

    async def sync_product_to_vector_db(
        self,
        account_id: str,
        product_id: int,
        product_data: Dict[str, Any]
    ) -> bool:
        """
        Sincroniza um produto com o banco de dados de vetores.

        Args:
            account_id: ID da conta
            product_id: ID do produto
            product_data: Dados do produto

        Returns:
            True se a sincronização foi bem-sucedida
        """
        try:
            # Preparar dados para embedding
            product_text = self._prepare_product_for_embedding(product_data)

            # Gerar embedding
            embedding = await self.generate_embedding(product_text)

            # Armazenar no Qdrant
            collection_name = f"products_{account_id}"
            await self.ensure_collection_exists(collection_name)

            # Preparar payload
            payload = {
                "product_id": product_id,
                "name": product_data.get("name", ""),
                "description": product_data.get("description", ""),
                "default_code": product_data.get("default_code", ""),
                "barcode": product_data.get("barcode", ""),
                "categ_id": product_data.get("categ_id", [0, ""]),
                "list_price": product_data.get("list_price", 0.0),
                "standard_price": product_data.get("standard_price", 0.0),
                "qty_available": product_data.get("qty_available", 0.0),
                "attributes": product_data.get("attributes", {}),
                "last_updated": datetime.now().isoformat()
            }

            # Armazenar no Qdrant
            await self.store_vector(
                collection_name=collection_name,
                vector_id=f"product_{product_id}",
                vector=embedding,
                payload=payload
            )

            return True

        except Exception as e:
            logger.error(f"Failed to sync product {product_id} to vector DB: {e}")
            raise VectorDBError(f"Failed to sync product {product_id} to vector DB: {e}")

    def _prepare_product_for_embedding(self, product_data: Dict[str, Any]) -> str:
        """
        Prepara os dados do produto para geração de embedding.

        Args:
            product_data: Dados do produto

        Returns:
            Texto formatado para geração de embedding
        """
        # Extrair dados básicos
        name = product_data.get("name", "")
        description = product_data.get("description", "")
        default_code = product_data.get("default_code", "")
        barcode = product_data.get("barcode", "")
        
        # Extrair categoria
        categ_id = product_data.get("categ_id", [0, ""])
        category = categ_id[1] if isinstance(categ_id, list) and len(categ_id) > 1 else ""
        
        # Extrair preços
        list_price = product_data.get("list_price", 0.0)
        standard_price = product_data.get("standard_price", 0.0)
        
        # Extrair atributos
        attributes = product_data.get("attributes", {})
        attributes_text = ""
        if attributes:
            for attr_name, attr_value in attributes.items():
                attributes_text += f"{attr_name}: {attr_value}\n"
        
        # Combinar tudo em um texto
        product_text = f"""
        Nome: {name}
        Código: {default_code}
        Código de Barras: {barcode}
        Categoria: {category}
        Preço de Venda: {list_price}
        Preço de Custo: {standard_price}
        
        Descrição:
        {description}
        
        Atributos:
        {attributes_text}
        """
        
        return product_text

    async def search_vectors(
        self,
        collection_name: str,
        query_vector: List[float],
        limit: int = 10,
        score_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Busca vetores similares no Qdrant.

        Args:
            collection_name: Nome da coleção
            query_vector: Vetor de consulta
            limit: Limite de resultados
            score_threshold: Limiar de similaridade

        Returns:
            Lista de resultados ordenados por similaridade
        """
        await self.connect()

        try:
            # Buscar vetores similares
            search_result = self.qdrant_client.search(
                collection_name=collection_name,
                query_vector=query_vector,
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
            logger.error(f"Failed to search products: {e}")
            raise VectorDBError(f"Failed to search products: {e}")

    async def delete_vector(self, collection_name: str, vector_id: str):
        """
        Remove um vetor do Qdrant.

        Args:
            collection_name: Nome da coleção
            vector_id: ID do vetor
        """
        await self.connect()

        # Remover o vetor
        self.qdrant_client.delete(
            collection_name=collection_name,
            points_selector=models.PointIdsList(
                points=[vector_id]
            )
        )

    async def delete_product_from_vector_db(self, account_id: str, product_id: int) -> bool:
        """
        Remove um produto do banco de dados de vetores.

        Args:
            account_id: ID da conta
            product_id: ID do produto

        Returns:
            True se a remoção foi bem-sucedida
        """
        try:
            # Remover do Qdrant
            collection_name = f"products_{account_id}"
            await self.delete_vector(
                collection_name=collection_name,
                vector_id=f"product_{product_id}"
            )

            return True

        except Exception as e:
            logger.error(f"Failed to delete product {product_id} from vector DB: {e}")
            raise VectorDBError(f"Failed to delete product {product_id} from vector DB: {e}")

    async def delete_collection(self, collection_name: str):
        """
        Remove uma coleção do Qdrant.

        Args:
            collection_name: Nome da coleção
        """
        await self.connect()

        # Remover a coleção
        self.qdrant_client.delete_collection(
            collection_name=collection_name
        )


# Singleton para o serviço
_vector_service_instance = None

async def get_vector_service() -> VectorService:
    """
    Obtém uma instância do serviço de vetores.

    Returns:
        Instância do serviço de vetores
    """
    global _vector_service_instance

    if _vector_service_instance is None:
        _vector_service_instance = VectorService()
        await _vector_service_instance.connect()

    return _vector_service_instance
