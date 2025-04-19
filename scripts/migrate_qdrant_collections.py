#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para migrar dados das coleções específicas por account_id para coleções compartilhadas.

Este script:
1. Identifica todas as coleções existentes no Qdrant
2. Agrupa as coleções por tipo (company_metadata, business_rules, support_documents)
3. Cria novas coleções compartilhadas se não existirem
4. Migra os dados das coleções específicas para as coleções compartilhadas
5. Opcionalmente, remove as coleções antigas após a migração
"""

import os
import sys
import logging
import asyncio
import uuid
from typing import List, Dict, Any
from datetime import datetime

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
logger = logging.getLogger("qdrant-migration")

# Configurações
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")
EMBEDDING_DIMENSION = 1536  # Dimensão dos embeddings OpenAI

# Tipos de coleções
COLLECTION_TYPES = {
    "company_metadata": "company_metadata",
    "business_rules": "business_rules",
    "support_documents": "support_documents"
}

# Prefixos das coleções antigas
OLD_PREFIXES = {
    "company_metadata_": COLLECTION_TYPES["company_metadata"],
    "business_rules_": COLLECTION_TYPES["business_rules"],
    "support_documents_": COLLECTION_TYPES["support_documents"]
}

async def connect_to_qdrant() -> QdrantClient:
    """Conecta ao Qdrant."""
    try:
        client = QdrantClient(
            host=QDRANT_HOST,
            port=QDRANT_PORT,
            api_key=QDRANT_API_KEY,
            timeout=60.0,  # Timeout maior para operações de migração
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

        logger.info(f"Coleção {collection_name} criada com sucesso")
        return True

    except Exception as e:
        logger.error(f"Falha ao garantir que a coleção {collection_name} existe: {e}")
        raise

async def get_all_collections(client: QdrantClient) -> Dict[str, List[str]]:
    """
    Obtém todas as coleções existentes no Qdrant e as agrupa por tipo.

    Returns:
        Dicionário com as coleções agrupadas por tipo
    """
    try:
        collections = client.get_collections()
        collection_names = [collection.name for collection in collections.collections]

        # Agrupar coleções por tipo
        grouped_collections = {
            "company_metadata": [],
            "business_rules": [],
            "support_documents": [],
            "other": []
        }

        for name in collection_names:
            categorized = False
            for prefix, collection_type in OLD_PREFIXES.items():
                if name.startswith(prefix):
                    grouped_collections[collection_type].append(name)
                    categorized = True
                    break

            if not categorized:
                # Verificar se é uma das novas coleções compartilhadas
                if name in COLLECTION_TYPES.values():
                    logger.info(f"Coleção compartilhada {name} já existe")
                else:
                    grouped_collections["other"].append(name)

        return grouped_collections

    except Exception as e:
        logger.error(f"Falha ao obter coleções: {e}")
        raise

async def extract_account_id_from_collection_name(collection_name: str) -> str:
    """
    Extrai o account_id do nome da coleção.

    Args:
        collection_name: Nome da coleção (ex: company_metadata_account_1)

    Returns:
        account_id extraído
    """
    for prefix in OLD_PREFIXES.keys():
        if collection_name.startswith(prefix):
            return collection_name[len(prefix):]

    return None

async def migrate_collection_data(
    client: QdrantClient,
    source_collection: str,
    target_collection: str,
    account_id: str
) -> int:
    """
    Migra dados de uma coleção específica para uma coleção compartilhada.

    Args:
        client: Cliente Qdrant
        source_collection: Nome da coleção de origem
        target_collection: Nome da coleção de destino
        account_id: ID da conta

    Returns:
        Número de pontos migrados
    """
    try:
        # Obter todos os pontos da coleção de origem
        points = client.scroll(
            collection_name=source_collection,
            limit=10000,  # Limite alto para obter todos os pontos
            with_payload=True,
            with_vectors=True,
            # Não usar filtro aqui, pois queremos todos os pontos da coleção de origem
        )[0]  # O método scroll retorna uma tupla (pontos, next_page_offset)

        if not points:
            logger.info(f"Nenhum ponto encontrado na coleção {source_collection}")
            return 0

        logger.info(f"Encontrados {len(points)} pontos na coleção {source_collection}")

        # Preparar pontos para a coleção de destino
        new_points = []
        for point in points:
            # Gerar um novo ID para evitar conflitos
            # Para metadados da empresa, usar um ID baseado no account_id
            if target_collection == COLLECTION_TYPES["company_metadata"]:
                # Gerar UUID determinístico baseado no account_id
                new_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{account_id}_metadata"))
            else:
                # Para outros tipos, gerar UUID baseado no ID original e account_id
                new_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{account_id}_{point.id}"))

            # Adicionar account_id ao payload
            payload = point.payload or {}
            payload["account_id"] = account_id

            # Adicionar timestamp de migração
            payload["migrated_at"] = datetime.now().isoformat()

            # Criar novo ponto
            new_points.append(
                models.PointStruct(
                    id=new_id,
                    vector=point.vector,
                    payload=payload
                )
            )

        # Inserir pontos na coleção de destino
        client.upsert(
            collection_name=target_collection,
            points=new_points,
            wait=True  # Aguardar a conclusão da operação
        )

        logger.info(f"Migrados {len(new_points)} pontos de {source_collection} para {target_collection}")
        return len(new_points)

    except Exception as e:
        logger.error(f"Falha ao migrar dados da coleção {source_collection}: {e}")
        raise

async def delete_collection(client: QdrantClient, collection_name: str) -> bool:
    """
    Remove uma coleção do Qdrant.

    Args:
        client: Cliente Qdrant
        collection_name: Nome da coleção

    Returns:
        True se a coleção foi removida com sucesso
    """
    try:
        client.delete_collection(collection_name=collection_name)
        logger.info(f"Coleção {collection_name} removida com sucesso")
        return True

    except Exception as e:
        logger.error(f"Falha ao remover coleção {collection_name}: {e}")
        return False

async def main():
    """Função principal."""
    try:
        # Conectar ao Qdrant
        client = await connect_to_qdrant()

        # Obter todas as coleções
        collections = await get_all_collections(client)

        # Criar coleções compartilhadas se não existirem
        for collection_type in COLLECTION_TYPES.values():
            await ensure_collection_exists(client, collection_type)

        # Migrar dados das coleções específicas para as coleções compartilhadas
        migration_stats = {
            "company_metadata": 0,
            "business_rules": 0,
            "support_documents": 0
        }

        # Migrar metadados da empresa
        for collection_name in collections["company_metadata"]:
            account_id = await extract_account_id_from_collection_name(collection_name)
            if account_id:
                migrated = await migrate_collection_data(
                    client,
                    collection_name,
                    COLLECTION_TYPES["company_metadata"],
                    account_id
                )
                migration_stats["company_metadata"] += migrated

        # Migrar regras de negócio
        for collection_name in collections["business_rules"]:
            account_id = await extract_account_id_from_collection_name(collection_name)
            if account_id:
                migrated = await migrate_collection_data(
                    client,
                    collection_name,
                    COLLECTION_TYPES["business_rules"],
                    account_id
                )
                migration_stats["business_rules"] += migrated

        # Migrar documentos de suporte
        for collection_name in collections["support_documents"]:
            account_id = await extract_account_id_from_collection_name(collection_name)
            if account_id:
                migrated = await migrate_collection_data(
                    client,
                    collection_name,
                    COLLECTION_TYPES["support_documents"],
                    account_id
                )
                migration_stats["support_documents"] += migrated

        # Exibir estatísticas de migração
        logger.info("Migração concluída com sucesso!")
        logger.info(f"Metadados da empresa: {migration_stats['company_metadata']} pontos migrados")
        logger.info(f"Regras de negócio: {migration_stats['business_rules']} pontos migrados")
        logger.info(f"Documentos de suporte: {migration_stats['support_documents']} pontos migrados")

        # Perguntar se deseja remover as coleções antigas
        remove_old = input("Deseja remover as coleções antigas? (s/n): ").lower() == 's'

        if remove_old:
            # Remover coleções antigas
            for collection_type in ["company_metadata", "business_rules", "support_documents"]:
                for collection_name in collections[collection_type]:
                    await delete_collection(client, collection_name)

            logger.info("Coleções antigas removidas com sucesso!")

    except Exception as e:
        logger.error(f"Erro durante a migração: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
