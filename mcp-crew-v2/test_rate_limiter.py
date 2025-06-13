#!/usr/bin/env python3
"""
Script para testar o sistema de rate limiting.
"""

import logging
import time
from typing import Dict

# Configurar logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("RateLimiterTest")

# Importar o limitador de requisições
from src.redis_manager.rate_limiter import RateLimiter

def test_rate_limiting():
    """Testa o limite de requisições."""
    logger.info("=== Teste de Limite de Requisições ===")
    
    # Criar limitador
    limiter = RateLimiter(tenant_id="test_account")
    
    # Definir limite: 5 requisições por 10 segundos
    operation = "test_api"
    limit = 5
    window = 10
    
    # Fazer várias requisições
    results = []
    for i in range(7):
        allowed, info = limiter.check_limit(operation, limit, window)
        
        logger.info(f"Requisição {i+1}: {'Permitida' if allowed else 'Bloqueada'}")
        logger.info(f"  Atual: {info['current']}/{limit}")
        logger.info(f"  Restante: {info['remaining']}")
        
        results.append(allowed)
        
        # Pequena pausa para evitar problemas de timestamp
        time.sleep(0.1)
    
    # Verificar se as primeiras 5 requisições foram permitidas e as demais bloqueadas
    expected = [True, True, True, True, True, False, False]
    success = results == expected
    
    logger.info(f"Resultado esperado: {expected}")
    logger.info(f"Resultado obtido: {results}")
    logger.info(f"Teste bem-sucedido: {success}")
    
    return success

def test_counter():
    """Testa operações de contador."""
    logger.info("\n=== Teste de Contador ===")
    
    # Criar limitador
    limiter = RateLimiter(tenant_id="test_account")
    
    # Resetar contador para garantir estado inicial
    limiter.reset_counter("test_counter")
    
    # Incrementar contador
    value1 = limiter.increment_counter("test_counter")
    logger.info(f"Valor após primeiro incremento: {value1}")
    
    # Incrementar novamente
    value2 = limiter.increment_counter("test_counter", 5)
    logger.info(f"Valor após incremento de 5: {value2}")
    
    # Obter valor atual
    current = limiter.get_counter("test_counter")
    logger.info(f"Valor atual: {current}")
    
    # Resetar contador
    reset = limiter.reset_counter("test_counter")
    logger.info(f"Contador resetado: {reset}")
    
    # Verificar se foi resetado
    after_reset = limiter.get_counter("test_counter")
    logger.info(f"Valor após reset: {after_reset}")
    
    # Verificar resultados
    success = (value1 == 1 and value2 == 6 and current == 6 and reset and after_reset == 0)
    logger.info(f"Teste bem-sucedido: {success}")
    
    return success

def test_multiple_operations():
    """Testa múltiplas operações com diferentes limites."""
    logger.info("\n=== Teste de Múltiplas Operações ===")
    
    # Criar limitador
    limiter = RateLimiter(tenant_id="test_account")
    
    # Definir operações
    operations = {
        "api_read": {"limit": 10, "window": 60},
        "api_write": {"limit": 5, "window": 60}
    }
    
    # Testar cada operação
    results = {}
    
    for op_name, config in operations.items():
        logger.info(f"Testando operação: {op_name}")
        
        # Fazer requisições até o limite
        allowed_count = 0
        for i in range(config["limit"] + 2):
            allowed, info = limiter.check_limit(op_name, config["limit"], config["window"])
            
            if allowed:
                allowed_count += 1
            
            logger.info(f"  Requisição {i+1}: {'Permitida' if allowed else 'Bloqueada'}")
            logger.info(f"    Atual: {info['current']}/{config['limit']}")
            logger.info(f"    Restante: {info['remaining']}")
            
            # Pequena pausa
            time.sleep(0.1)
        
        # Verificar se o número correto de requisições foi permitido
        results[op_name] = allowed_count == config["limit"]
        logger.info(f"  Resultado para {op_name}: {'Sucesso' if results[op_name] else 'Falha'}")
    
    # Verificar resultados
    success = all(results.values())
    logger.info(f"Teste bem-sucedido: {success}")
    
    return success

def run_all_tests():
    """Executa todos os testes e retorna o resultado"""
    results = {}
    
    # Teste de limite de requisições
    results["rate_limiting"] = test_rate_limiting()
    
    # Teste de contador
    results["counter"] = test_counter()
    
    # Teste de múltiplas operações
    results["multiple_operations"] = test_multiple_operations()
    
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
