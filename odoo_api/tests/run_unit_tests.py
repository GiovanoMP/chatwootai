#!/usr/bin/env python3
"""
Script para executar os testes unitários.

Este script executa os testes unitários para os componentes individuais.
"""

import os
import sys
import unittest
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Adicionar o diretório raiz ao PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_unit_tests():
    """Executar os testes unitários."""
    logger.info("Iniciando execução dos testes unitários...")
    
    # Lista de módulos de teste unitário
    unit_test_modules = [
        "test_openai_service",
        "test_embedding_agent"
    ]
    
    # Criar suite de testes
    test_suite = unittest.TestSuite()
    
    # Adicionar testes à suite
    for module_name in unit_test_modules:
        try:
            # Importar módulo de teste
            module = __import__(module_name)
            
            # Adicionar todos os testes do módulo à suite
            test_suite.addTest(unittest.defaultTestLoader.loadTestsFromModule(module))
            
            logger.info(f"Adicionados testes do módulo {module_name}")
        except ImportError as e:
            logger.error(f"Erro ao importar módulo {module_name}: {e}")
    
    # Executar os testes
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)
    
    # Verificar resultado
    if result.wasSuccessful():
        logger.info("Todos os testes unitários foram executados com sucesso!")
        return 0
    else:
        logger.error("Alguns testes unitários falharam!")
        return 1

if __name__ == "__main__":
    sys.exit(run_unit_tests())
