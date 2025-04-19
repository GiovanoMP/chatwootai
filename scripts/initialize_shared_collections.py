#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para inicializar as coleções compartilhadas no Qdrant.

Este script:
1. Conecta ao Qdrant
2. Cria as coleções compartilhadas se não existirem
3. Cria os índices necessários para filtragem por account_id
"""

import os
import sys
import logging
import asyncio

from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.exceptions import UnexpectedResponse

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("qdrant-init")

# Configurações
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")
EMBEDDING_DIMENSION = 1536  # Dimensão dos embeddings OpenAI

# Coleções a serem criadas
COLLECTIONS = [
    "company_metadata",
    "business_rules",
    "support_documents"
]

async def connect_to_qdrant() -> QdrantClient:
    """Conecta ao Qdrant."""
    try:
        client = QdrantClient(
            host=QDRANT_HOST,
            port=QDRANT_PORT,
            api_key=QDRANT_API_KEY,
            timeout=30.0,
            https=False  # Usar HTTP em vez de HTTPS
        )

        # Verificar conexão
        client.get_collections()
        logger.info(f"Conectado ao Qdrant em {QDRANT_HOST}:{QDRANT_PORT}")
        return client

    except Exception as e:
        logger.error(f"Falha ao conectar ao Qdrant: {e}")
        raise

async def ensure_collection_exists(client: QdrantClient, collection_name: str) -> bool:
    """
    Garante que uma coleção existe no Qdrant.

    Args:
        client: Cliente Qdrant
        collection_name: Nome da coleção

    Returns:
        True se a coleção foi criada, False se já existia
    """
    try:
        # Verificar se a coleção já existe
        collections = client.get_collections()
        collection_names = [collection.name for collection in collections.collections]

        if collection_name in collection_names:
            logger.info(f"Coleção {collection_name} já existe")
            return False

        # Criar coleção
        client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(
                size=EMBEDDING_DIMENSION,
                distance=models.Distance.COSINE,
            ),
        )

        # Criar índices para metadados
        client.create_payload_index(
            collection_name=collection_name,
            field_name="account_id",
            field_schema=models.PayloadSchemaType.KEYWORD,
        )

        # Índices adicionais específicos por tipo de coleção
        if collection_name == "business_rules":
            # Índice para tipo de regra
            client.create_payload_index(
                collection_name=collection_name,
                field_name="type",
                field_schema=models.PayloadSchemaType.KEYWORD,
            )

            # Índice para regras temporárias
            client.create_payload_index(
                collection_name=collection_name,
                field_name="is_temporary",
                field_schema=models.PayloadSchemaType.BOOL,
            )

        elif collection_name == "support_documents":
            # Índice para tipo de documento
            client.create_payload_index(
                collection_name=collection_name,
                field_name="document_type",
                field_schema=models.PayloadSchemaType.KEYWORD,
            )

        logger.info(f"Coleção {collection_name} criada com sucesso")
        return True

    except Exception as e:
        logger.error(f"Falha ao garantir que a coleção {collection_name} existe: {e}")
        raise

async def main():
    """Função principal."""
    try:
        # Conectar ao Qdrant
        client = await connect_to_qdrant()

        # Criar coleções se não existirem
        for collection_name in COLLECTIONS:
            await ensure_collection_exists(client, collection_name)

        logger.info("Inicialização das coleções compartilhadas concluída com sucesso!")

    except Exception as e:
        logger.error(f"Erro durante a inicialização: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
