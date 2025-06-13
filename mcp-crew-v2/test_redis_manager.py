#!/usr/bin/env python3
"""
Script para testar o RedisManager unificado.
Verifica conexão, operações básicas, fallback e isolamento multi-tenant.
"""

import os
import time
import json
import logging
from typing import Dict, Any

# Configurar logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("RedisManagerTest")

# Importar o RedisManager
from src.redis_manager.redis_manager import redis_manager, DataType, RedisError

def test_connection():
    """Testa a conexão com o Redis"""
    logger.info("=== Teste de Conexão ===")
    
    # Verificar se o Redis está disponível
    logger.info(f"Redis disponível: {redis_manager.is_available}")
    
    # Obter estatísticas
    stats = redis_manager.get_stats()
    logger.info(f"Estatísticas do Redis: {json.dumps(stats, indent=2)}")
    
    return redis_manager.is_available

def test_basic_operations():
    """Testa operações básicas (set/get/delete)"""
    logger.info("\n=== Teste de Operações Básicas ===")
    
    # Definir dados de teste
    tenant_id = "account_test"
    data_type = DataType.KNOWLEDGE
    identifier = "test:basic"
    test_data = {"name": "Test Data", "value": 42, "timestamp": time.time()}
    
    # Set
    success = redis_manager.set(
        tenant_id=tenant_id,
        data_type=data_type,
        identifier=identifier,
        value=test_data,
        ttl=60  # 1 minuto
    )
    logger.info(f"Set: {success}")
    
    # Get
    retrieved_data = redis_manager.get(
        tenant_id=tenant_id,
        data_type=data_type,
        identifier=identifier
    )
    logger.info(f"Get: {retrieved_data}")
    
    # Verificar se os dados são iguais
    is_equal = retrieved_data == test_data
    logger.info(f"Dados iguais: {is_equal}")
    
    # Verificar se a chave existe
    exists = redis_manager.exists(
        tenant_id=tenant_id,
        data_type=data_type,
        identifier=identifier
    )
    logger.info(f"Exists: {exists}")
    
    # Delete
    deleted = redis_manager.delete(
        tenant_id=tenant_id,
        data_type=data_type,
        identifier=identifier
    )
    logger.info(f"Delete: {deleted}")
    
    # Verificar se foi deletado
    exists_after_delete = redis_manager.exists(
        tenant_id=tenant_id,
        data_type=data_type,
        identifier=identifier
    )
    logger.info(f"Exists após delete: {exists_after_delete}")
    
    return is_equal and exists and deleted and not exists_after_delete

def test_tenant_isolation():
    """Testa o isolamento entre diferentes tenants"""
    logger.info("\n=== Teste de Isolamento Multi-Tenant ===")
    
    # Definir dados de teste para dois tenants
    tenant1 = "account_1"
    tenant2 = "account_2"
    data_type = DataType.CONVERSATION_CONTEXT
    identifier = "test:isolation"
    
    data1 = {"tenant": "Empresa 1", "secret": "segredo1"}
    data2 = {"tenant": "Empresa 2", "secret": "segredo2"}
    
    # Armazenar dados para ambos os tenants
    redis_manager.set(tenant_id=tenant1, data_type=data_type, identifier=identifier, value=data1)
    redis_manager.set(tenant_id=tenant2, data_type=data_type, identifier=identifier, value=data2)
    
    # Recuperar dados
    retrieved1 = redis_manager.get(tenant_id=tenant1, data_type=data_type, identifier=identifier)
    retrieved2 = redis_manager.get(tenant_id=tenant2, data_type=data_type, identifier=identifier)
    
    # Verificar isolamento
    isolation_ok = (
        retrieved1 == data1 and 
        retrieved2 == data2 and
        retrieved1 != retrieved2
    )
    
    logger.info(f"Dados tenant1: {retrieved1}")
    logger.info(f"Dados tenant2: {retrieved2}")
    logger.info(f"Isolamento OK: {isolation_ok}")
    
    # Limpar
    redis_manager.delete(tenant_id=tenant1, data_type=data_type, identifier=identifier)
    redis_manager.delete(tenant_id=tenant2, data_type=data_type, identifier=identifier)
    
    return isolation_ok

def test_fallback_cache():
    """Testa o fallback para cache local quando o Redis não está disponível"""
    logger.info("\n=== Teste de Fallback Cache ===")
    
    # Simular falha no Redis (forçando o circuit breaker a abrir)
    original_client = redis_manager.client
    original_is_available = redis_manager.is_available
    
    try:
        # Forçar indisponibilidade
        redis_manager.is_available = False
        redis_manager.client = None
        
        logger.info("Redis forçado a ficar indisponível para teste")
        
        # Tentar operações
        tenant_id = "account_test"
        data_type = DataType.KNOWLEDGE
        identifier = "test:fallback"
        test_data = {"fallback": True, "timestamp": time.time()}
        
        # Set com fallback
        redis_manager.set(
            tenant_id=tenant_id,
            data_type=data_type,
            identifier=identifier,
            value=test_data
        )
        
        # Get com fallback
        retrieved = redis_manager.get(
            tenant_id=tenant_id,
            data_type=data_type,
            identifier=identifier
        )
        
        fallback_working = retrieved == test_data
        logger.info(f"Dados do fallback: {retrieved}")
        logger.info(f"Fallback funcionando: {fallback_working}")
        
        return fallback_working
        
    finally:
        # Restaurar estado original
        redis_manager.client = original_client
        redis_manager.is_available = original_is_available
        logger.info("Estado original do Redis restaurado")

def run_all_tests():
    """Executa todos os testes e retorna o resultado"""
    results = {}
    
    # Teste de conexão
    results["connection"] = test_connection()
    
    # Se o Redis estiver disponível, executar todos os testes
    if results["connection"]:
        results["basic_operations"] = test_basic_operations()
        results["tenant_isolation"] = test_tenant_isolation()
    
    # Teste de fallback (funciona mesmo sem Redis disponível)
    results["fallback_cache"] = test_fallback_cache()
    
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
