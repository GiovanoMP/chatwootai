"""
Ferramenta simples para busca no Qdrant usando o decorador @tool do CrewAI.
"""

import os
import time
import logging
from typing import Dict, List, Any
from crewai.tools import tool
from qdrant_client import QdrantClient
from qdrant_client.http import models
from openai import OpenAI

from ..config import QDRANT_URL, QDRANT_API_KEY, OPENAI_API_KEY, EMBEDDING_MODEL

logger = logging.getLogger(__name__)

# Inicializar clientes
qdrant_client = None
openai_client = None
embedding_cache = {}

def initialize_clients():
    """Inicializa os clientes Qdrant e OpenAI."""
    global qdrant_client, openai_client
    
    if qdrant_client is None:
        logger.info(f"Inicializando cliente Qdrant com URL={QDRANT_URL}")
        try:
            if QDRANT_API_KEY:
                qdrant_client = QdrantClient(
                    url=QDRANT_URL,
                    api_key=QDRANT_API_KEY,
                    timeout=2.0
                )
            else:
                qdrant_client = QdrantClient(
                    url=QDRANT_URL,
                    timeout=2.0
                )
            logger.info("Cliente Qdrant inicializado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao inicializar cliente Qdrant: {e}", exc_info=True)
            raise
    
    if openai_client is None:
        logger.info("Inicializando cliente OpenAI")
        try:
            openai_client = OpenAI(api_key=OPENAI_API_KEY)
            logger.info("Cliente OpenAI inicializado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao inicializar cliente OpenAI: {e}", exc_info=True)
            raise

def get_embedding(text: str) -> List[float]:
    """
    Gera embeddings com cache para reduzir latência.
    
    Args:
        text: Texto para gerar embedding
        
    Returns:
        Lista de floats representando o embedding
    """
    global embedding_cache, openai_client
    
    # Inicializar clientes se necessário
    if openai_client is None:
        initialize_clients()
    
    try:
        # Verificar se o embedding já está em cache
        if text in embedding_cache:
            logger.info("Embedding encontrado em cache")
            return embedding_cache[text]
        
        logger.info(f"Gerando embedding para texto: '{text[:30]}...'")
        # Gerar embedding
        start_time = time.time()
        response = openai_client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=text
        )
        embedding = response.data[0].embedding
        end_time = time.time()
        logger.info(f"Embedding gerado em {end_time - start_time:.2f}s")
        
        # Armazenar em cache
        embedding_cache[text] = embedding
        
        # Limitar tamanho do cache (manter apenas os últimos 100 embeddings)
        if len(embedding_cache) > 100:
            # Remover o primeiro item (mais antigo)
            embedding_cache.pop(next(iter(embedding_cache)))
        
        return embedding
    except Exception as e:
        logger.error(f"Erro ao gerar embedding: {e}", exc_info=True)
        raise

@tool("busca_qdrant")
def busca_qdrant(query: str, account_id: str, collection_name: str, limit: int = 3, score_threshold: float = 0.35) -> str:
    """
    Busca rápida no Qdrant. Use para encontrar informações com baixa latência.
    
    Args:
        query: A consulta do usuário
        account_id: ID da conta do cliente
        collection_name: Nome da coleção (business_rules, company_metadata, support_documents)
        limit: Número máximo de resultados (padrão: 3)
        score_threshold: Limiar mínimo de similaridade (padrão: 0.35)
        
    Returns:
        Resultados da busca em formato JSON
    """
    global qdrant_client
    
    # Inicializar clientes se necessário
    if qdrant_client is None:
        initialize_clients()
    
    try:
        logger.info(f"Executando busca: query='{query}', collection='{collection_name}', account_id='{account_id}'")
        
        # Verificar se a coleção existe
        if not qdrant_client.collection_exists(collection_name):
            logger.warning(f"Coleção '{collection_name}' não existe")
            return "[]"
        
        # Gerar embedding para a consulta (com cache)
        query_embedding = get_embedding(query)
        
        # Buscar documentos relevantes com timeout
        logger.info("Iniciando busca no Qdrant")
        start_time = time.time()
        search_results = qdrant_client.search(
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
            with_vectors=False
        )
        end_time = time.time()
        logger.info(f"Busca concluída em {end_time - start_time:.2f}s, encontrados {len(search_results)} resultados")
        
        # Extrair informações relevantes
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
        
        import json
        return json.dumps(results, ensure_ascii=False)
        
    except Exception as e:
        logger.error(f"Erro na busca: {e}", exc_info=True)
        # Em caso de erro, retornar lista vazia
        return "[]"
