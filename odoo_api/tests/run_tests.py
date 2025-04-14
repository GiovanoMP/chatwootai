#!/usr/bin/env python3
"""
Script para executar todos os testes da API.

Este script executa todos os testes da API, incluindo testes unitários e de integração.
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

def run_tests():
    """Executar todos os testes."""
    logger.info("Iniciando execução dos testes...")
    
    # Descobrir e executar todos os testes
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover(os.path.dirname(os.path.abspath(__file__)), pattern="test_*.py")
    
    # Executar os testes
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)
    
    # Verificar resultado
    if result.wasSuccessful():
        logger.info("Todos os testes foram executados com sucesso!")
        return 0
    else:
        logger.error("Alguns testes falharam!")
        return 1

if __name__ == "__main__":
    sys.exit(run_tests())
