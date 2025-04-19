#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para testar a arquitetura multi-tenant do Qdrant.

Este script:
1. Inicializa as coleções compartilhadas
2. Insere dados de teste para múltiplos account_ids
3. Realiza consultas para verificar o isolamento de dados
4. Valida que os dados são corretamente filtrados por account_id
"""

import os
import sys
import logging
import asyncio
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any

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
logger = logging.getLogger("multi-tenant-test")

# Configurações
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")
EMBEDDING_DIMENSION = 1536  # Dimensão dos embeddings OpenAI

# Coleções a serem testadas
COLLECTIONS = [
    "company_metadata",
    "business_rules",
    "support_documents"
]

# Dados de teste para múltiplos account_ids
TEST_ACCOUNTS = [
    "account_1",
    "account_2",
    "account_3"
]

# Dados de teste para cada tipo de coleção
TEST_DATA = {
    "company_metadata": [
        {
            "company_name": "Empresa A",
            "description": "Uma empresa de cosméticos",
            "business_area": "cosmetics"
        },
        {
            "company_name": "Empresa B",
            "description": "Uma empresa de saúde",
            "business_area": "health"
        },
        {
            "company_name": "Empresa C",
            "description": "Uma empresa de varejo",
            "business_area": "retail"
        }
    ],
    "business_rules": [
        {
            "name": "Regra 1",
            "description": "Regra de desconto",
            "type": "discount",
            "rule_text": "Desconto de 10% para compras acima de R$ 100"
        },
        {
            "name": "Regra 2",
            "description": "Regra de frete",
            "type": "shipping",
            "rule_text": "Frete grátis para compras acima de R$ 200"
        },
        {
            "name": "Regra 3",
            "description": "Regra de promoção",
            "type": "promotion",
            "rule_text": "Compre 2, leve 3"
        }
    ],
    "support_documents": [
        {
            "name": "FAQ",
            "description": "Perguntas frequentes",
            "document_type": "faq",
            "content": "Perguntas e respostas sobre nossos produtos"
        },
        {
            "name": "Política de Devolução",
            "description": "Política de devolução de produtos",
            "document_type": "policy",
            "content": "Informações sobre como devolver produtos"
        },
        {
            "name": "Termos de Uso",
            "description": "Termos de uso do site",
            "document_type": "terms",
            "content": "Termos e condições de uso do site"
        }
    ]
}

# Consultas de teste para cada tipo de coleção
TEST_QUERIES = {
    "company_metadata": [
        "empresa de cosméticos",
        "empresa de saúde",
        "empresa de varejo"
    ],
    "business_rules": [
        "desconto",
        "frete",
        "promoção"
    ],
    "support_documents": [
        "perguntas frequentes",
        "devolução",
        "termos de uso"
    ]
}

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

        logger.info(f"Coleção {collection_name} criada com sucesso")
        return True

    except Exception as e:
        logger.error(f"Falha ao garantir que a coleção {collection_name} existe: {e}")
        raise

async def generate_dummy_embedding(text: str) -> List[float]:
    """
    Gera um embedding fictício para testes.

    Args:
        text: Texto para gerar embedding

    Returns:
        Embedding fictício
    """
    import hashlib
    import numpy as np

    # Gerar um hash do texto
    hash_object = hashlib.md5(text.encode())
    hash_hex = hash_object.hexdigest()

    # Usar o hash como seed para o gerador de números aleatórios
    seed = int(hash_hex, 16) % (2**32)
    np.random.seed(seed)

    # Gerar um embedding aleatório
    embedding = np.random.normal(0, 1, EMBEDDING_DIMENSION)

    # Normalizar o embedding
    embedding = embedding / np.linalg.norm(embedding)

    return embedding.tolist()

async def insert_test_data(client: QdrantClient) -> Dict[str, int]:
    """
    Insere dados de teste para múltiplos account_ids.

    Args:
        client: Cliente Qdrant

    Returns:
        Estatísticas de inserção
    """
    stats = {
        "company_metadata": 0,
        "business_rules": 0,
        "support_documents": 0
    }

    # Para cada account_id
    for i, account_id in enumerate(TEST_ACCOUNTS):
        # Para cada tipo de coleção
        for collection_name in COLLECTIONS:
            # Obter dados de teste para este tipo de coleção
            test_data = TEST_DATA[collection_name]

            # Inserir dados de teste
            for j, data in enumerate(test_data):
                # Gerar um ID único para o documento
                # Usar UUID para garantir que o ID seja válido para o Qdrant
                # Mas manter um padrão determinístico para facilitar a identificação
                if collection_name == "company_metadata":
                    # Gerar UUID determinístico baseado no account_id
                    document_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{account_id}_metadata"))
                else:
                    # Gerar UUID determinístico baseado no account_id e no índice do documento
                    document_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{account_id}_{j+1}"))

                # Gerar um embedding fictício
                text_for_embedding = json.dumps(data)
                embedding = await generate_dummy_embedding(text_for_embedding)

                # Preparar payload
                payload = {
                    "account_id": account_id,
                    **data,
                    "processed_text": text_for_embedding,
                    "last_updated": datetime.now().isoformat()
                }

                # Inserir no Qdrant
                client.upsert(
                    collection_name=collection_name,
                    points=[
                        models.PointStruct(
                            id=document_id,
                            vector=embedding,
                            payload=payload
                        )
                    ],
                )

                stats[collection_name] += 1
                logger.info(f"Inserido documento {document_id} na coleção {collection_name}")

    return stats

async def test_data_isolation(client: QdrantClient) -> Dict[str, bool]:
    """
    Testa o isolamento de dados entre account_ids.

    Args:
        client: Cliente Qdrant

    Returns:
        Resultados dos testes
    """
    results = {}

    # Para cada account_id
    for account_id in TEST_ACCOUNTS:
        # Para cada tipo de coleção
        for collection_name in COLLECTIONS:
            # Criar filtro para este account_id
            filter_condition = models.Filter(
                must=[
                    models.FieldCondition(
                        key="account_id",
                        match=models.MatchValue(
                            value=account_id
                        )
                    )
                ]
            )

            # Obter todos os pontos para este account_id
            points = client.scroll(
                collection_name=collection_name,
                scroll_filter=filter_condition,  # Usar scroll_filter em vez de filter
                limit=100,
                with_payload=True,
                with_vectors=False,
            )[0]

            # Verificar se todos os pontos pertencem a este account_id
            all_match = True
            for point in points:
                if point.payload.get("account_id") != account_id:
                    all_match = False
                    logger.error(f"Ponto {point.id} na coleção {collection_name} pertence ao account_id {point.payload.get('account_id')}, mas deveria pertencer ao account_id {account_id}")

            test_key = f"{account_id}_{collection_name}_isolation"
            results[test_key] = all_match

            if all_match:
                logger.info(f"✅ Teste de isolamento para {account_id} na coleção {collection_name}: PASSOU")
            else:
                logger.error(f"❌ Teste de isolamento para {account_id} na coleção {collection_name}: FALHOU")

    return results

async def test_search_queries(client: QdrantClient) -> Dict[str, bool]:
    """
    Testa consultas de busca com filtragem por account_id.

    Args:
        client: Cliente Qdrant

    Returns:
        Resultados dos testes
    """
    results = {}

    # Para cada account_id
    for account_id in TEST_ACCOUNTS:
        # Para cada tipo de coleção
        for collection_name in COLLECTIONS:
            # Obter consultas de teste para este tipo de coleção
            test_queries = TEST_QUERIES[collection_name]

            # Para cada consulta
            for query in test_queries:
                # Gerar embedding para a consulta
                query_embedding = await generate_dummy_embedding(query)

                # Criar filtro para este account_id
                filter_condition = models.Filter(
                    must=[
                        models.FieldCondition(
                            key="account_id",
                            match=models.MatchValue(
                                value=account_id
                            )
                        )
                    ]
                )

                # Realizar busca
                search_results = client.search(
                    collection_name=collection_name,
                    query_vector=query_embedding,
                    query_filter=filter_condition,  # Usar query_filter em vez de filter
                    limit=10,
                    with_payload=True,
                    with_vectors=False,
                )

                # Verificar se todos os resultados pertencem a este account_id
                all_match = True
                for result in search_results:
                    if result.payload.get("account_id") != account_id:
                        all_match = False
                        logger.error(f"Resultado {result.id} na coleção {collection_name} pertence ao account_id {result.payload.get('account_id')}, mas deveria pertencer ao account_id {account_id}")

                test_key = f"{account_id}_{collection_name}_{query.replace(' ', '_')}_search"
                results[test_key] = all_match

                if all_match:
                    logger.info(f"✅ Teste de busca para {account_id} na coleção {collection_name} com query '{query}': PASSOU")
                else:
                    logger.error(f"❌ Teste de busca para {account_id} na coleção {collection_name} com query '{query}': FALHOU")

    return results

async def cleanup_test_data(client: QdrantClient) -> None:
    """
    Limpa os dados de teste.

    Args:
        client: Cliente Qdrant
    """
    # Perguntar se deseja limpar os dados de teste
    cleanup = input("Deseja limpar os dados de teste? (s/n): ").lower() == 's'

    if not cleanup:
        logger.info("Dados de teste mantidos")
        return

    # Para cada account_id
    for account_id in TEST_ACCOUNTS:
        # Para cada tipo de coleção
        for collection_name in COLLECTIONS:
            # Criar filtro para este account_id
            filter_condition = models.Filter(
                must=[
                    models.FieldCondition(
                        key="account_id",
                        match=models.MatchValue(
                            value=account_id
                        )
                    )
                ]
            )

            # Obter IDs dos pontos para este account_id
            points = client.scroll(
                collection_name=collection_name,
                scroll_filter=filter_condition,  # Usar scroll_filter em vez de filter
                limit=100,
                with_payload=False,
                with_vectors=False,
            )[0]

            point_ids = [point.id for point in points]

            if point_ids:
                # Remover pontos
                client.delete(
                    collection_name=collection_name,
                    points_selector=models.PointIdsList(
                        points=point_ids
                    ),
                )

                logger.info(f"Removidos {len(point_ids)} pontos da coleção {collection_name} para o account_id {account_id}")

    logger.info("Dados de teste limpos com sucesso")

async def main():
    """Função principal."""
    try:
        # Conectar ao Qdrant
        client = await connect_to_qdrant()

        # Criar coleções se não existirem
        for collection_name in COLLECTIONS:
            await ensure_collection_exists(client, collection_name)

        # Inserir dados de teste
        logger.info("Inserindo dados de teste...")
        stats = await insert_test_data(client)
        logger.info(f"Dados de teste inseridos: {stats}")

        # Testar isolamento de dados
        logger.info("Testando isolamento de dados...")
        isolation_results = await test_data_isolation(client)

        # Testar consultas de busca
        logger.info("Testando consultas de busca...")
        search_results = await test_search_queries(client)

        # Exibir resultados
        logger.info("Resultados dos testes:")

        all_passed = True

        logger.info("Testes de isolamento:")
        for test_key, result in isolation_results.items():
            logger.info(f"  {test_key}: {'PASSOU' if result else 'FALHOU'}")
            if not result:
                all_passed = False

        logger.info("Testes de busca:")
        for test_key, result in search_results.items():
            logger.info(f"  {test_key}: {'PASSOU' if result else 'FALHOU'}")
            if not result:
                all_passed = False

        if all_passed:
            logger.info("✅ Todos os testes passaram! A arquitetura multi-tenant está funcionando corretamente.")
        else:
            logger.error("❌ Alguns testes falharam. Verifique os logs para mais detalhes.")

        # Limpar dados de teste
        await cleanup_test_data(client)

    except Exception as e:
        logger.error(f"Erro durante os testes: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
