#!/usr/bin/env python3
"""
Script para executar os testes de integração.

Este script executa os testes de integração entre os componentes.
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

def run_integration_tests():
    """Executar os testes de integração."""
    logger.info("Iniciando execução dos testes de integração...")
    
    # Lista de módulos de teste de integração
    integration_test_modules = [
        "test_business_rules_api",
        "test_odoo_integration"
    ]
    
    # Criar suite de testes
    test_suite = unittest.TestSuite()
    
    # Adicionar testes à suite
    for module_name in integration_test_modules:
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
        logger.info("Todos os testes de integração foram executados com sucesso!")
        return 0
    else:
        logger.error("Alguns testes de integração falharam!")
        return 1

if __name__ == "__main__":
    sys.exit(run_integration_tests())
