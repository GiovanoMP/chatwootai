#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para testar a performance de consultas nas coleções compartilhadas.

Este script:
1. Realiza consultas em todas as coleções (company_metadata, business_rules, support_documents)
2. Mede o tempo de resposta para cada consulta
3. Simula uma conversa fluida com múltiplas consultas sequenciais
"""

import os
import sys
import time
import logging
import asyncio
import uuid
import statistics
from typing import List, Dict, Any, Tuple
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
logger = logging.getLogger("query-performance-test")

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

# Account ID para teste
TEST_ACCOUNT = "account_3"

# Consultas de teste para cada coleção
TEST_QUERIES = {
    "company_metadata": [
        "Qual é o nome da empresa?",
        "Quais são os horários de funcionamento?",
        "Quais canais online a empresa possui?",
        "Como é o estilo de atendimento ao cliente?",
        "Quais são os valores da empresa?"
    ],
    "business_rules": [
        "Existe alguma política de desconto?",
        "Como funciona o frete?",
        "Quais são as promoções atuais?",
        "Qual é a política de devolução?",
        "Existe programa de fidelidade?"
    ],
    "support_documents": [
        "Como posso trocar um produto?",
        "Quais são as formas de pagamento?",
        "Como rastrear meu pedido?",
        "Qual é a garantia dos produtos?",
        "Como entrar em contato com o suporte?"
    ]
}

# Consultas para simular uma conversa fluida
CONVERSATION_QUERIES = [
    "Olá, gostaria de saber mais sobre a empresa",
    "Quais são os horários de funcionamento?",
    "Vocês têm alguma promoção atual?",
    "Como funciona a política de devolução?",
    "Posso pagar com cartão de crédito?",
    "Quanto tempo leva para entregar?",
    "Vocês têm programa de fidelidade?",
    "Como faço para rastrear meu pedido?",
    "Qual é a garantia dos produtos?",
    "Vocês têm loja física?",
    "Vocês têm Instagram ou Facebook?",
    "Obrigado pela ajuda!"
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

async def search_collection(
    client: QdrantClient, 
    collection_name: str, 
    account_id: str, 
    query: str,
    limit: int = 3
) -> Tuple[List[Dict[str, Any]], float]:
    """
    Busca em uma coleção e mede o tempo de resposta.
    
    Args:
        client: Cliente Qdrant
        collection_name: Nome da coleção
        account_id: ID da conta
        query: Consulta de busca
        limit: Limite de resultados
        
    Returns:
        Tupla com resultados da busca e tempo de resposta em milissegundos
    """
    try:
        # Gerar embedding para a consulta
        start_time = time.time()
        query_embedding = await generate_dummy_embedding(query)
        
        # Preparar filtro para buscar apenas dados deste account_id
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
        
        # Realizar busca
        search_results = client.search(
            collection_name=collection_name,
            query_vector=query_embedding,
            query_filter=account_filter,
            limit=limit,
            with_payload=True,
            with_vectors=False,
        )
        
        # Calcular tempo de resposta
        end_time = time.time()
        response_time_ms = (end_time - start_time) * 1000
        
        # Extrair resultados
        results = []
        for result in search_results:
            results.append({
                "id": result.id,
                "score": result.score,
                "payload": result.payload
            })
        
        return results, response_time_ms
    
    except Exception as e:
        logger.error(f"Falha ao buscar na coleção {collection_name}: {e}")
        return [], 0

async def test_collection_performance(
    client: QdrantClient, 
    collection_name: str, 
    account_id: str,
    queries: List[str]
) -> Dict[str, Any]:
    """
    Testa a performance de consultas em uma coleção.
    
    Args:
        client: Cliente Qdrant
        collection_name: Nome da coleção
        account_id: ID da conta
        queries: Lista de consultas
        
    Returns:
        Estatísticas de performance
    """
    response_times = []
    result_counts = []
    
    for query in queries:
        results, response_time = await search_collection(client, collection_name, account_id, query)
        
        if response_time > 0:
            response_times.append(response_time)
            result_counts.append(len(results))
            
            logger.info(f"Consulta '{query}' na coleção {collection_name}: {len(results)} resultados em {response_time:.2f}ms")
    
    # Calcular estatísticas
    stats = {
        "min_time_ms": min(response_times) if response_times else 0,
        "max_time_ms": max(response_times) if response_times else 0,
        "avg_time_ms": statistics.mean(response_times) if response_times else 0,
        "median_time_ms": statistics.median(response_times) if response_times else 0,
        "total_queries": len(queries),
        "successful_queries": len(response_times),
        "avg_results": statistics.mean(result_counts) if result_counts else 0
    }
    
    return stats

async def simulate_conversation(
    client: QdrantClient, 
    account_id: str,
    queries: List[str]
) -> Dict[str, Any]:
    """
    Simula uma conversa fluida com múltiplas consultas sequenciais.
    
    Args:
        client: Cliente Qdrant
        account_id: ID da conta
        queries: Lista de consultas
        
    Returns:
        Estatísticas de performance
    """
    logger.info(f"Simulando conversa fluida com {len(queries)} consultas...")
    
    response_times = []
    total_results = []
    
    for query in queries:
        # Buscar em todas as coleções
        start_time = time.time()
        all_results = []
        
        for collection_name in COLLECTIONS:
            results, _ = await search_collection(client, collection_name, account_id, query)
            all_results.extend(results)
        
        # Calcular tempo total
        end_time = time.time()
        total_time_ms = (end_time - start_time) * 1000
        
        response_times.append(total_time_ms)
        total_results.append(len(all_results))
        
        logger.info(f"Consulta: '{query}'")
        logger.info(f"  Resultados: {len(all_results)} em {total_time_ms:.2f}ms")
    
    # Calcular estatísticas
    stats = {
        "min_time_ms": min(response_times) if response_times else 0,
        "max_time_ms": max(response_times) if response_times else 0,
        "avg_time_ms": statistics.mean(response_times) if response_times else 0,
        "median_time_ms": statistics.median(response_times) if response_times else 0,
        "total_queries": len(queries),
        "avg_results": statistics.mean(total_results) if total_results else 0
    }
    
    return stats

async def main():
    """Função principal."""
    try:
        # Conectar ao Qdrant
        client = await connect_to_qdrant()
        
        # Testar performance de cada coleção
        logger.info(f"Testando performance de consultas para account_id {TEST_ACCOUNT}...")
        
        collection_stats = {}
        for collection_name in COLLECTIONS:
            logger.info(f"Testando coleção {collection_name}...")
            stats = await test_collection_performance(
                client, 
                collection_name, 
                TEST_ACCOUNT,
                TEST_QUERIES.get(collection_name, [])
            )
            collection_stats[collection_name] = stats
        
        # Exibir estatísticas por coleção
        logger.info("Estatísticas de performance por coleção:")
        for collection_name, stats in collection_stats.items():
            logger.info(f"  {collection_name}:")
            logger.info(f"    Tempo mínimo: {stats['min_time_ms']:.2f}ms")
            logger.info(f"    Tempo máximo: {stats['max_time_ms']:.2f}ms")
            logger.info(f"    Tempo médio: {stats['avg_time_ms']:.2f}ms")
            logger.info(f"    Tempo mediano: {stats['median_time_ms']:.2f}ms")
            logger.info(f"    Consultas bem-sucedidas: {stats['successful_queries']}/{stats['total_queries']}")
            logger.info(f"    Média de resultados: {stats['avg_results']:.2f}")
        
        # Simular conversa fluida
        logger.info("\nSimulando conversa fluida...")
        conversation_stats = await simulate_conversation(client, TEST_ACCOUNT, CONVERSATION_QUERIES)
        
        # Exibir estatísticas da conversa
        logger.info("Estatísticas da conversa fluida:")
        logger.info(f"  Tempo mínimo: {conversation_stats['min_time_ms']:.2f}ms")
        logger.info(f"  Tempo máximo: {conversation_stats['max_time_ms']:.2f}ms")
        logger.info(f"  Tempo médio: {conversation_stats['avg_time_ms']:.2f}ms")
        logger.info(f"  Tempo mediano: {conversation_stats['median_time_ms']:.2f}ms")
        logger.info(f"  Total de consultas: {conversation_stats['total_queries']}")
        logger.info(f"  Média de resultados: {conversation_stats['avg_results']:.2f}")
        
        # Verificar se atende ao requisito de tempo de resposta
        if conversation_stats['max_time_ms'] < 3000:
            logger.info("✅ O sistema atende ao requisito de tempo de resposta (< 3 segundos)")
        else:
            logger.warning("⚠️ O sistema NÃO atende ao requisito de tempo de resposta (< 3 segundos)")
        
    except Exception as e:
        logger.error(f"Erro durante os testes: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
