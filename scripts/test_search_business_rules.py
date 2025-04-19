#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para testar a busca de regras de negócio com a nova arquitetura multi-tenant.

Este script:
1. Inicializa a coleção business_rules
2. Insere regras de negócio de teste para múltiplos account_ids
3. Testa a busca de regras com filtragem por account_id
4. Verifica o isolamento de dados entre account_ids
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
logger = logging.getLogger("search-rules-test")

# Configurações
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")
EMBEDDING_DIMENSION = 1536  # Dimensão dos embeddings OpenAI

# Coleção a ser testada
COLLECTION_NAME = "business_rules"

# Dados de teste para múltiplos account_ids
TEST_ACCOUNTS = [
    "account_1",
    "account_2",
    "account_3"
]

# Regras de negócio de teste para cada account_id
TEST_RULES = [
    # Regras para account_1
    [
        {
            "rule_id": 1,
            "name": "Desconto para Primeira Compra",
            "description": "Desconto de 10% para clientes na primeira compra",
            "type": "discount",
            "priority": "high",
            "is_temporary": False,
            "rule_data": {
                "discount_percentage": 10,
                "min_purchase_value": 50.0,
                "coupon_code": "WELCOME10"
            }
        },
        {
            "rule_id": 2,
            "name": "Frete Grátis",
            "description": "Frete grátis para compras acima de R$ 200",
            "type": "shipping",
            "priority": "medium",
            "is_temporary": False,
            "rule_data": {
                "min_purchase_value": 200.0,
                "excluded_regions": ["Norte", "Nordeste"]
            }
        },
        {
            "rule_id": 3,
            "name": "Promoção de Verão",
            "description": "Desconto de 20% em produtos de verão",
            "type": "promotion",
            "priority": "high",
            "is_temporary": True,
            "start_date": "2023-12-01",
            "end_date": "2024-02-28",
            "rule_data": {
                "discount_percentage": 20,
                "product_categories": ["Protetor Solar", "Bronzeador", "Pós-Sol"]
            }
        }
    ],
    # Regras para account_2
    [
        {
            "rule_id": 1,
            "name": "Desconto para Idosos",
            "description": "Desconto de 15% para clientes acima de 60 anos",
            "type": "discount",
            "priority": "high",
            "is_temporary": False,
            "rule_data": {
                "discount_percentage": 15,
                "min_age": 60,
                "requires_id": True
            }
        },
        {
            "rule_id": 2,
            "name": "Programa de Fidelidade",
            "description": "Pontos para cada compra que podem ser trocados por descontos",
            "type": "loyalty",
            "priority": "medium",
            "is_temporary": False,
            "rule_data": {
                "points_per_real": 1,
                "min_points_for_discount": 100,
                "discount_per_100_points": 10.0
            }
        },
        {
            "rule_id": 3,
            "name": "Black Friday",
            "description": "Descontos especiais na Black Friday",
            "type": "promotion",
            "priority": "high",
            "is_temporary": True,
            "start_date": "2023-11-20",
            "end_date": "2023-11-30",
            "rule_data": {
                "discount_percentage": 30,
                "product_categories": ["Eletrônicos", "Eletrodomésticos", "Informática"]
            }
        }
    ],
    # Regras para account_3
    [
        {
            "rule_id": 1,
            "name": "Horário de Funcionamento",
            "description": "Horário de funcionamento da loja",
            "type": "business_hours",
            "priority": "medium",
            "is_temporary": False,
            "rule_data": {
                "days": [0, 1, 2, 3, 4, 5],
                "start_time": "09:00",
                "end_time": "18:00",
                "saturday_start_time": "09:00",
                "saturday_end_time": "13:00",
                "timezone": "America/Sao_Paulo"
            }
        },
        {
            "rule_id": 2,
            "name": "Política de Devolução",
            "description": "Política de devolução de produtos",
            "type": "return_policy",
            "priority": "medium",
            "is_temporary": False,
            "rule_data": {
                "return_period_days": 7,
                "requires_receipt": True,
                "requires_original_packaging": True,
                "restocking_fee_percentage": 0
            }
        },
        {
            "rule_id": 3,
            "name": "Promoção de Aniversário",
            "description": "Desconto especial no mês de aniversário do cliente",
            "type": "promotion",
            "priority": "medium",
            "is_temporary": False,
            "rule_data": {
                "discount_percentage": 15,
                "requires_id": True,
                "valid_days_before": 7,
                "valid_days_after": 7
            }
        }
    ]
]

# Consultas de teste para busca de regras
TEST_QUERIES = [
    "desconto",
    "frete grátis",
    "promoção",
    "horário de funcionamento",
    "política de devolução",
    "fidelidade"
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
    Garante que a coleção business_rules existe no Qdrant.

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

        client.create_payload_index(
            collection_name=COLLECTION_NAME,
            field_name="type",
            field_schema=models.PayloadSchemaType.KEYWORD,
        )

        client.create_payload_index(
            collection_name=COLLECTION_NAME,
            field_name="is_temporary",
            field_schema=models.PayloadSchemaType.BOOL,
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

async def prepare_rule_text_for_vectorization(rule: Dict[str, Any]) -> str:
    """
    Prepara o texto da regra para vetorização.

    Args:
        rule: Regra de negócio

    Returns:
        Texto preparado para vetorização
    """
    # Iniciar com informações básicas
    text_parts = [
        f"Nome da regra: {rule['name']}",
        f"Descrição: {rule['description']}",
        f"Tipo: {rule['type']}",
        f"Prioridade: {rule['priority']}"
    ]

    # Adicionar informações de temporalidade
    if rule.get('is_temporary', False):
        text_parts.append(f"Regra temporária válida de {rule.get('start_date', 'N/A')} até {rule.get('end_date', 'N/A')}")
    else:
        text_parts.append("Regra permanente")

    # Adicionar dados específicos da regra
    if isinstance(rule.get('rule_data'), dict):
        rule_data = rule['rule_data']

        # Processar diferentes tipos de regras
        if rule['type'] == "business_hours":
            days = rule_data.get("days", [])
            days_map = {
                0: "Segunda-feira",
                1: "Terça-feira",
                2: "Quarta-feira",
                3: "Quinta-feira",
                4: "Sexta-feira",
                5: "Sábado",
                6: "Domingo"
            }
            days_text = ", ".join([days_map.get(day, str(day)) for day in days])
            text_parts.append(f"Dias de funcionamento: {days_text}")
            text_parts.append(f"Horário: {rule_data.get('start_time', '')} até {rule_data.get('end_time', '')}")
            text_parts.append(f"Fuso horário: {rule_data.get('timezone', '')}")

        elif rule['type'] == "discount":
            if rule_data.get('discount_percentage'):
                text_parts.append(f"Desconto de {rule_data.get('discount_percentage')}%")
            if rule_data.get('min_purchase_value'):
                text_parts.append(f"Valor mínimo de compra: R$ {rule_data.get('min_purchase_value')}")
            if rule_data.get('coupon_code'):
                text_parts.append(f"Código do cupom: {rule_data.get('coupon_code')}")

        elif rule['type'] == "shipping":
            if rule_data.get('min_purchase_value'):
                text_parts.append(f"Frete grátis para compras acima de R$ {rule_data.get('min_purchase_value')}")
            if rule_data.get('excluded_regions'):
                text_parts.append(f"Regiões excluídas: {', '.join(rule_data.get('excluded_regions', []))}")

        elif rule['type'] == "promotion":
            if rule_data.get('discount_percentage'):
                text_parts.append(f"Desconto de {rule_data.get('discount_percentage')}%")
            if rule_data.get('product_categories'):
                text_parts.append(f"Categorias de produtos: {', '.join(rule_data.get('product_categories', []))}")

        # Adicionar todos os outros campos como texto
        for key, value in rule_data.items():
            if isinstance(value, (list, tuple)):
                text_parts.append(f"{key}: {', '.join(map(str, value))}")
            elif isinstance(value, dict):
                text_parts.append(f"{key}: {json.dumps(value, ensure_ascii=False)}")
            else:
                text_parts.append(f"{key}: {value}")

    # Combinar todas as partes em um único texto
    return "\n".join(text_parts)

async def insert_test_rules(client: QdrantClient) -> Dict[str, int]:
    """
    Insere regras de negócio de teste para múltiplos account_ids.

    Args:
        client: Cliente Qdrant

    Returns:
        Estatísticas de inserção
    """
    stats = {account_id: 0 for account_id in TEST_ACCOUNTS}

    # Para cada account_id
    for i, account_id in enumerate(TEST_ACCOUNTS):
        # Obter regras de teste para este account_id
        rules = TEST_RULES[i]

        # Para cada regra
        for rule in rules:
            # Preparar texto para vetorização
            rule_text = await prepare_rule_text_for_vectorization(rule)

            # Gerar embedding
            embedding = await generate_dummy_embedding(rule_text)

            # Gerar ID do documento
            # Usar UUID para garantir que o ID seja válido para o Qdrant
            document_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{account_id}_{rule['rule_id']}"))

            # Inserir no Qdrant
            client.upsert(
                collection_name=COLLECTION_NAME,
                points=[
                    models.PointStruct(
                        id=document_id,
                        vector=embedding,
                        payload={
                            "account_id": account_id,
                            "rule_id": rule['rule_id'],
                            "name": rule['name'],
                            "description": rule['description'],
                            "type": rule['type'],
                            "priority": rule['priority'],
                            "is_temporary": rule.get('is_temporary', False),
                            "start_date": rule.get('start_date'),
                            "end_date": rule.get('end_date'),
                            "rule_data": rule.get('rule_data', {}),
                            "processed_text": rule_text,
                            "last_updated": datetime.now().isoformat()
                        }
                    )
                ],
            )

            stats[account_id] += 1
            logger.info(f"Inserida regra {rule['name']} para account_id {account_id}")

    return stats

async def search_business_rules(client: QdrantClient, account_id: str, query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Busca regras de negócio por similaridade semântica.

    Args:
        client: Cliente Qdrant
        account_id: ID da conta
        query: Consulta de busca
        limit: Limite de resultados

    Returns:
        Resultados da busca
    """
    try:
        # Gerar embedding para a consulta
        query_embedding = await generate_dummy_embedding(query)

        # Preparar filtro para buscar apenas regras deste account_id
        account_filter = models.Filter(
            must=[
                models.FieldCondition(
                    key="account_id",
                    match=models.MatchValue(
                        value=account_id
                    )
                )
            ]
        )

        # Buscar regras semanticamente similares
        search_results = client.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_embedding,
            query_filter=account_filter,  # Usar query_filter em vez de filter
            limit=limit,
            score_threshold=0.5
        )

        # Extrair resultados
        results = []
        for result in search_results:
            results.append({
                "id": result.id,
                "score": result.score,
                "rule_id": result.payload.get("rule_id"),
                "name": result.payload.get("name"),
                "description": result.payload.get("description"),
                "type": result.payload.get("type"),
                "account_id": result.payload.get("account_id")
            })

        return results

    except Exception as e:
        logger.error(f"Falha ao buscar regras de negócio para account_id {account_id}: {e}")
        return []

async def test_cross_account_search(client: QdrantClient) -> Dict[str, bool]:
    """
    Testa se é possível acessar regras de um account_id a partir de outro.

    Args:
        client: Cliente Qdrant

    Returns:
        Resultados dos testes
    """
    results = {}

    # Para cada account_id
    for i, account_id in enumerate(TEST_ACCOUNTS):
        # Obter regras de teste para este account_id
        rules = TEST_RULES[i]

        # Para cada regra
        for rule in rules:
            # Preparar texto para busca
            search_text = rule['name']

            # Para cada outro account_id
            for other_account_id in TEST_ACCOUNTS:
                if other_account_id == account_id:
                    continue

                # Buscar regra em outro account_id
                search_results = await search_business_rules(client, other_account_id, search_text)

                # Verificar se a regra foi encontrada em outro account_id
                found_in_other_account = False
                for result in search_results:
                    if result['name'] == rule['name']:
                        found_in_other_account = True
                        logger.error(f"❌ Regra '{rule['name']}' do account_id {account_id} encontrada no account_id {other_account_id}")

                test_key = f"{account_id}_{other_account_id}_{rule['rule_id']}"
                results[test_key] = not found_in_other_account

                if not found_in_other_account:
                    logger.info(f"✅ Regra '{rule['name']}' do account_id {account_id} não encontrada no account_id {other_account_id}")

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

        # Inserir regras de teste
        logger.info("Inserindo regras de negócio de teste...")
        stats = await insert_test_rules(client)
        logger.info(f"Regras inseridas: {stats}")

        # Testar busca de regras
        logger.info("Testando busca de regras...")
        search_results = {}
        for account_id in TEST_ACCOUNTS:
            search_results[account_id] = {}
            for query in TEST_QUERIES:
                results = await search_business_rules(client, account_id, query)
                search_results[account_id][query] = results

                if results:
                    logger.info(f"✅ Busca para account_id {account_id} com query '{query}': {len(results)} resultados")
                    for result in results:
                        logger.info(f"   - {result['name']} (score: {result['score']:.2f})")
                else:
                    logger.info(f"ℹ️ Busca para account_id {account_id} com query '{query}': nenhum resultado")

        # Testar isolamento de dados
        logger.info("Testando isolamento de dados entre account_ids...")
        cross_account_results = await test_cross_account_search(client)

        # Verificar resultados do teste de isolamento
        all_isolation_passed = all(cross_account_results.values())
        if all_isolation_passed:
            logger.info("✅ Isolamento de dados entre account_ids verificado com sucesso")
        else:
            logger.error("❌ Falha no isolamento de dados entre account_ids")

        # Exibir resultados finais
        if all_isolation_passed:
            logger.info("✅ Todos os testes passaram! A busca de regras de negócio com multi-tenancy está funcionando corretamente.")
        else:
            logger.error("❌ Alguns testes falharam. Verifique os logs para mais detalhes.")

        # Limpar dados de teste
        await cleanup_test_data(client)

    except Exception as e:
        logger.error(f"Erro durante os testes: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
