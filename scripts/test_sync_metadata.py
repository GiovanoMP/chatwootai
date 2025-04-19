#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para testar a sincronização de metadados da empresa com a nova arquitetura multi-tenant.

Este script:
1. Inicializa a coleção company_metadata
2. Simula a sincronização de metadados para múltiplos account_ids
3. Verifica se os dados são corretamente armazenados e recuperados
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
logger = logging.getLogger("sync-metadata-test")

# Configurações
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")
EMBEDDING_DIMENSION = 1536  # Dimensão dos embeddings OpenAI

# Coleção a ser testada
COLLECTION_NAME = "company_metadata"

# Dados de teste para múltiplos account_ids
TEST_ACCOUNTS = [
    "account_1",
    "account_2",
    "account_3"
]

# Dados de teste para metadados da empresa
TEST_METADATA = [
    {
        "company_info": {
            "company_name": "Empresa A",
            "description": "Uma empresa de cosméticos",
            "business_area": "cosmetics",
            "company_values": "Qualidade, Inovação, Sustentabilidade"
        },
        "online_channels": {
            "website": {
                "url": "https://empresaa.com.br",
                "mention_at_end": True
            },
            "facebook": {
                "url": "https://facebook.com/empresaa",
                "mention_at_end": False
            },
            "instagram": {
                "url": "https://instagram.com/empresaa",
                "mention_at_end": True
            }
        },
        "business_hours": {
            "days": [0, 1, 2, 3, 4],
            "start_time": "09:00",
            "end_time": "18:00",
            "has_lunch_break": True,
            "lunch_break_start": "12:00",
            "lunch_break_end": "13:00"
        },
        "customer_service": {
            "greeting_message": "Olá! Bem-vindo à Empresa A. Como posso ajudar?",
            "communication_style": "friendly",
            "emoji_usage": "moderate"
        }
    },
    {
        "company_info": {
            "company_name": "Empresa B",
            "description": "Uma empresa de saúde",
            "business_area": "health",
            "company_values": "Cuidado, Atenção, Profissionalismo"
        },
        "online_channels": {
            "website": {
                "url": "https://empresab.com.br",
                "mention_at_end": True
            },
            "facebook": {
                "url": "https://facebook.com/empresab",
                "mention_at_end": True
            }
        },
        "business_hours": {
            "days": [0, 1, 2, 3, 4, 5],
            "start_time": "08:00",
            "end_time": "20:00",
            "has_lunch_break": False
        },
        "customer_service": {
            "greeting_message": "Olá! Bem-vindo à Empresa B. Como posso ajudar?",
            "communication_style": "formal",
            "emoji_usage": "minimal"
        }
    },
    {
        "company_info": {
            "company_name": "Empresa C",
            "description": "Uma empresa de varejo",
            "business_area": "retail",
            "company_values": "Preço baixo, Variedade, Atendimento"
        },
        "online_channels": {
            "website": {
                "url": "https://empresac.com.br",
                "mention_at_end": True
            },
            "instagram": {
                "url": "https://instagram.com/empresac",
                "mention_at_end": True
            }
        },
        "business_hours": {
            "days": [0, 1, 2, 3, 4, 5, 6],
            "start_time": "10:00",
            "end_time": "22:00",
            "has_lunch_break": False
        },
        "customer_service": {
            "greeting_message": "Olá! Bem-vindo à Empresa C. Como posso ajudar?",
            "communication_style": "casual",
            "emoji_usage": "frequent"
        }
    }
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

async def ensure_collection_exists(client: QdrantClient) -> bool:
    """
    Garante que a coleção company_metadata existe no Qdrant.

    Args:
        client: Cliente Qdrant

    Returns:
        True se a coleção foi criada, False se já existia
    """
    try:
        # Verificar se a coleção já existe
        collections = client.get_collections()
        collection_names = [collection.name for collection in collections.collections]

        if COLLECTION_NAME in collection_names:
            logger.info(f"Coleção {COLLECTION_NAME} já existe")
            return False

        # Criar coleção
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=models.VectorParams(
                size=EMBEDDING_DIMENSION,
                distance=models.Distance.COSINE,
            ),
        )

        # Criar índices para metadados
        client.create_payload_index(
            collection_name=COLLECTION_NAME,
            field_name="account_id",
            field_schema=models.PayloadSchemaType.KEYWORD,
        )

        logger.info(f"Coleção {COLLECTION_NAME} criada com sucesso")
        return True

    except Exception as e:
        logger.error(f"Falha ao garantir que a coleção {COLLECTION_NAME} existe: {e}")
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

async def format_company_metadata(metadata: Dict[str, Any]) -> str:
    """
    Formata os metadados da empresa em texto legível.

    Args:
        metadata: Metadados da empresa

    Returns:
        Texto formatado
    """
    formatted_text = """
    Informações Gerais da Empresa
    """

    # Informações básicas da empresa
    company_info = metadata.get('company_info', {})
    formatted_text += f"""
    Nome da empresa: {company_info.get('company_name', 'N/A')}
    Website: {company_info.get('website', 'N/A')}
    Descrição: {company_info.get('description', 'N/A')}
    Valores da empresa: {company_info.get('company_values', 'N/A')}
    Área de negócio: {company_info.get('business_area', 'N/A')}
    """

    # Horários de funcionamento
    business_hours = metadata.get('business_hours', {})
    days_map = {
        0: "Segunda-feira",
        1: "Terça-feira",
        2: "Quarta-feira",
        3: "Quinta-feira",
        4: "Sexta-feira",
        5: "Sábado",
        6: "Domingo"
    }

    days = business_hours.get('days', [])
    days_text = ", ".join([days_map.get(day, str(day)) for day in days])

    formatted_text += f"""
    Horário de Funcionamento:
    Dias de funcionamento: {days_text}
    Horário de funcionamento: {business_hours.get('start_time', 'N/A')} até {business_hours.get('end_time', 'N/A')}
    """

    if 5 in days:  # Se sábado está incluído
        formatted_text += f"Horário de sábado: {business_hours.get('saturday_start_time', 'N/A')} até {business_hours.get('saturday_end_time', 'N/A')}\n"

    if business_hours.get('has_lunch_break'):
        formatted_text += f"Intervalo de almoço: {business_hours.get('lunch_break_start', 'N/A')} até {business_hours.get('lunch_break_end', 'N/A')}\n"

    # Informações de atendimento ao cliente
    customer_service = metadata.get('customer_service', {})
    formatted_text += f"""
    Atendimento ao Cliente:
    Saudação: {customer_service.get('greeting_message', 'N/A')}
    Estilo de comunicação: {customer_service.get('communication_style', 'N/A')}
    Uso de emojis: {customer_service.get('emoji_usage', 'N/A')}
    """

    # Informações dos canais online
    if "online_channels" in metadata:
        online_channels = metadata["online_channels"]
        formatted_text += f"""
        Canais Online da Empresa:
        """

        # Site
        website = online_channels.get('website', {})
        if website.get('url'):
            formatted_text += f"""
        Site: {website.get('url', 'N/A')}
        Mencionar site ao finalizar: {'Sim' if website.get('mention_at_end', False) else 'Não'}
        """

        # Facebook
        facebook = online_channels.get('facebook', {})
        if facebook.get('url'):
            formatted_text += f"""
        Facebook: {facebook.get('url', 'N/A')}
        Mencionar Facebook ao finalizar: {'Sim' if facebook.get('mention_at_end', False) else 'Não'}
        """

        # Instagram
        instagram = online_channels.get('instagram', {})
        if instagram.get('url'):
            formatted_text += f"""
        Instagram: {instagram.get('url', 'N/A')}
        Mencionar Instagram ao finalizar: {'Sim' if instagram.get('mention_at_end', False) else 'Não'}
        """

    return formatted_text

async def sync_company_metadata(client: QdrantClient, account_id: str, metadata: Dict[str, Any]) -> bool:
    """
    Simula a sincronização de metadados da empresa.

    Args:
        client: Cliente Qdrant
        account_id: ID da conta
        metadata: Metadados da empresa

    Returns:
        True se a sincronização foi bem-sucedida
    """
    try:
        # Processar metadados para o agente
        processed_text = await format_company_metadata(metadata)

        # Gerar embedding do texto processado
        embedding = await generate_dummy_embedding(processed_text)

        # Gerar um ID único para o documento baseado no account_id
        # Usar UUID para garantir que o ID seja válido para o Qdrant
        document_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{account_id}_metadata"))

        # Armazenar no Qdrant
        client.upsert(
            collection_name=COLLECTION_NAME,
            points=[
                models.PointStruct(
                    id=document_id,
                    vector=embedding,
                    payload={
                        "account_id": account_id,
                        "metadata": metadata,
                        "processed_text": processed_text,
                        "last_updated": datetime.now().isoformat()
                    }
                )
            ],
        )

        logger.info(f"Metadados da empresa sincronizados para account_id {account_id}")
        return True

    except Exception as e:
        logger.error(f"Falha ao sincronizar metadados da empresa para account_id {account_id}: {e}")
        return False

async def search_company_metadata(client: QdrantClient, account_id: str, query: str) -> List[Dict[str, Any]]:
    """
    Simula a busca de metadados da empresa.

    Args:
        client: Cliente Qdrant
        account_id: ID da conta
        query: Consulta de busca

    Returns:
        Resultados da busca
    """
    try:
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
            collection_name=COLLECTION_NAME,
            query_vector=query_embedding,
            query_filter=filter_condition,  # Usar query_filter em vez de filter
            limit=1,
            with_payload=True,
            with_vectors=False,
        )

        # Extrair resultados
        results = []
        for result in search_results:
            results.append({
                "id": result.id,
                "score": result.score,
                "metadata": result.payload.get("metadata", {}),
                "account_id": result.payload.get("account_id")
            })

        return results

    except Exception as e:
        logger.error(f"Falha ao buscar metadados da empresa para account_id {account_id}: {e}")
        return []

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
            collection_name=COLLECTION_NAME,
            scroll_filter=filter_condition,  # Usar scroll_filter em vez de filter
            limit=100,
            with_payload=False,
            with_vectors=False,
        )[0]

        point_ids = [point.id for point in points]

        if point_ids:
            # Remover pontos
            client.delete(
                collection_name=COLLECTION_NAME,
                points_selector=models.PointIdsList(
                    points=point_ids
                ),
            )

            logger.info(f"Removidos {len(point_ids)} pontos da coleção {COLLECTION_NAME} para o account_id {account_id}")

    logger.info("Dados de teste limpos com sucesso")

async def main():
    """Função principal."""
    try:
        # Conectar ao Qdrant
        client = await connect_to_qdrant()

        # Criar coleção se não existir
        await ensure_collection_exists(client)

        # Sincronizar metadados para cada account_id
        logger.info("Sincronizando metadados da empresa...")
        sync_results = []
        for i, account_id in enumerate(TEST_ACCOUNTS):
            result = await sync_company_metadata(client, account_id, TEST_METADATA[i])
            sync_results.append(result)

        # Verificar resultados da sincronização
        all_sync_passed = all(sync_results)
        if all_sync_passed:
            logger.info("✅ Sincronização de metadados bem-sucedida para todos os account_ids")
        else:
            logger.error("❌ Falha na sincronização de metadados para alguns account_ids")

        # Testar busca de metadados
        logger.info("Testando busca de metadados...")
        search_queries = [
            "empresa de cosméticos",
            "horário de funcionamento",
            "canais online",
            "atendimento ao cliente"
        ]

        search_results = {}
        for account_id in TEST_ACCOUNTS:
            search_results[account_id] = {}
            for query in search_queries:
                results = await search_company_metadata(client, account_id, query)
                search_results[account_id][query] = results

                if results:
                    logger.info(f"✅ Busca para account_id {account_id} com query '{query}': {len(results)} resultados")
                else:
                    logger.error(f"❌ Busca para account_id {account_id} com query '{query}': nenhum resultado")

        # Verificar isolamento de dados
        logger.info("Verificando isolamento de dados...")
        isolation_passed = True
        for account_id in TEST_ACCOUNTS:
            for query in search_queries:
                results = search_results[account_id][query]
                for result in results:
                    if result["account_id"] != account_id:
                        isolation_passed = False
                        logger.error(f"❌ Resultado para account_id {account_id} contém dados do account_id {result['account_id']}")

        if isolation_passed:
            logger.info("✅ Isolamento de dados verificado com sucesso")
        else:
            logger.error("❌ Falha no isolamento de dados")

        # Exibir resultados finais
        if all_sync_passed and isolation_passed:
            logger.info("✅ Todos os testes passaram! A sincronização de metadados com multi-tenancy está funcionando corretamente.")
        else:
            logger.error("❌ Alguns testes falharam. Verifique os logs para mais detalhes.")

        # Limpar dados de teste
        await cleanup_test_data(client)

    except Exception as e:
        logger.error(f"Erro durante os testes: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
