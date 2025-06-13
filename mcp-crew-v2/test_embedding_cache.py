#!/usr/bin/env python3
"""
Script para testar o cache de embeddings.
"""

import logging
import time
import random
from typing import List

# Configurar logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("EmbeddingCacheTest")

# Importar o cache de embeddings
from src.redis_manager.embedding_cache import EmbeddingCache

def generate_random_embedding(dimensions: int = 384) -> List[float]:
    """Gera um embedding aleatório para testes."""
    return [random.uniform(-1, 1) for _ in range(dimensions)]

def test_store_and_retrieve():
    """Testa o armazenamento e recuperação de embeddings."""
    logger.info("=== Teste de Armazenamento e Recuperação de Embeddings ===")
    
    # Criar cache de embeddings
    cache = EmbeddingCache(tenant_id="test_account")
    
    # Dados de teste
    text = "Este é um texto de exemplo para teste de embeddings"
    embedding = generate_random_embedding()
    
    # Armazenar embedding
    success = cache.store_embedding(text, embedding, ttl=300)  # 5 minutos
    logger.info(f"Embedding armazenado: {success}")
    
    # Recuperar embedding
    retrieved = cache.get_embedding(text)
    
    # Verificar se o embedding foi recuperado corretamente
    if retrieved:
        is_same = len(retrieved) == len(embedding) and all(abs(a - b) < 1e-6 for a, b in zip(retrieved, embedding))
        logger.info(f"Embedding recuperado com sucesso: {is_same}")
    else:
        logger.error("Falha ao recuperar embedding")
        is_same = False
    
    return is_same

def test_batch_operations():
    """Testa operações em lote."""
    logger.info("\n=== Teste de Operações em Lote ===")
    
    # Criar cache de embeddings
    cache = EmbeddingCache(tenant_id="test_account")
    
    # Dados de teste
    texts = [
        "Primeiro texto de exemplo",
        "Segundo texto de exemplo",
        "Terceiro texto de exemplo"
    ]
    embeddings = [generate_random_embedding(128) for _ in range(len(texts))]
    
    # Armazenar embeddings em lote
    success = cache.store_batch_embeddings(texts, embeddings, ttl=300)
    logger.info(f"Embeddings em lote armazenados: {success}")
    
    # Recuperar embeddings em lote
    retrieved = cache.get_batch_embeddings(texts)
    
    # Verificar se todos os embeddings foram recuperados
    all_retrieved = len(retrieved) == len(texts)
    logger.info(f"Todos os embeddings recuperados: {all_retrieved}")
    
    # Limpar embeddings
    removed = cache.clear_embeddings()
    logger.info(f"Embeddings removidos: {removed}")
    
    return all_retrieved and removed >= len(texts)

def run_all_tests():
    """Executa todos os testes e retorna o resultado"""
    results = {}
    
    # Teste de armazenamento e recuperação
    results["store_and_retrieve"] = test_store_and_retrieve()
    
    # Teste de operações em lote
    results["batch_operations"] = test_batch_operations()
    
    # Resumo
    logger.info("\n=== Resumo dos Testes ===")
    for test, result in results.items():
        status = "✅ PASSOU" if result else "❌ FALHOU"
        logger.info(f"{test}: {status}")
    
    return all(results.values())

if __name__ == "__main__":
    success = run_all_tests()
    exit_code = 0 if success else 1
    logger.info(f"\nTestes {'concluídos com sucesso' if success else 'falharam'}")
    exit(exit_code)
