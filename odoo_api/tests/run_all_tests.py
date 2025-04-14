#!/usr/bin/env python3
"""
Script para executar todos os testes.

Este script executa todos os testes, incluindo testes unitários e de integração.
"""

import os
import sys
import subprocess
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_all_tests():
    """Executar todos os testes."""
    logger.info("Iniciando execução de todos os testes...")
    
    # Verificar ambiente
    logger.info("Verificando ambiente...")
    env_result = subprocess.run(
        [sys.executable, "check_environment.py"],
        cwd=os.path.dirname(os.path.abspath(__file__))
    )
    
    if env_result.returncode != 0:
        logger.error("Verificação de ambiente falhou!")
        return 1
    
    # Executar testes unitários
    logger.info("Executando testes unitários...")
    unit_result = subprocess.run(
        [sys.executable, "run_unit_tests.py"],
        cwd=os.path.dirname(os.path.abspath(__file__))
    )
    
    # Executar testes de integração
    logger.info("Executando testes de integração...")
    integration_result = subprocess.run(
        [sys.executable, "run_integration_tests.py"],
        cwd=os.path.dirname(os.path.abspath(__file__))
    )
    
    # Verificar resultados
    if unit_result.returncode == 0 and integration_result.returncode == 0:
        logger.info("Todos os testes foram executados com sucesso!")
        return 0
    else:
        logger.error("Alguns testes falharam!")
        if unit_result.returncode != 0:
            logger.error("Testes unitários falharam!")
        if integration_result.returncode != 0:
            logger.error("Testes de integração falharam!")
        return 1

if __name__ == "__main__":
    sys.exit(run_all_tests())
