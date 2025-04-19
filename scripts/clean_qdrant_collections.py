#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para limpar os dados das coleções no Qdrant, mantendo as coleções intactas.
"""

import os
import sys
import logging
import asyncio
from qdrant_client import QdrantClient
from qdrant_client.http import models

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("clean-qdrant")

# Configurações
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")

# Coleções a serem limpas
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

async def clean_collection(client: QdrantClient, collection_name: str) -> int:
    """
    Limpa todos os dados de uma coleção.
    
    Args:
        client: Cliente Qdrant
        collection_name: Nome da coleção
        
    Returns:
        Número de pontos removidos
    """
    try:
        # Verificar se a coleção existe
        collections = client.get_collections()
        collection_names = [c.name for c in collections.collections]
        
        if collection_name not in collection_names:
            logger.warning(f"Coleção {collection_name} não existe. Pulando.")
            return 0
        
        # Obter todos os pontos da coleção
        points = client.scroll(
            collection_name=collection_name,
            limit=10000,  # Limite alto para obter todos os pontos
            with_payload=False,
            with_vectors=False,
        )[0]
        
        point_ids = [point.id for point in points]
        
        if not point_ids:
            logger.info(f"Coleção {collection_name} já está vazia.")
            return 0
        
        # Remover todos os pontos
        client.delete(
            collection_name=collection_name,
            points_selector=models.PointIdsList(
                points=point_ids
            ),
        )
        
        logger.info(f"Removidos {len(point_ids)} pontos da coleção {collection_name}")
        return len(point_ids)
    
    except Exception as e:
        logger.error(f"Falha ao limpar a coleção {collection_name}: {e}")
        return 0

async def main():
    """Função principal."""
    try:
        # Conectar ao Qdrant
        client = await connect_to_qdrant()
        
        # Limpar cada coleção
        total_removed = 0
        for collection_name in COLLECTIONS:
            removed = await clean_collection(client, collection_name)
            total_removed += removed
        
        logger.info(f"Total de pontos removidos: {total_removed}")
        logger.info("Limpeza concluída com sucesso.")
        
    except Exception as e:
        logger.error(f"Erro durante a limpeza: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
