#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Executor de testes de integração para o ChatwootAI.

Este script executa todos os testes de integração do sistema ChatwootAI,
incluindo testes de conexão, testes de integração do Hub e testes de integração de Crews.
"""

import os
import sys
import logging
import time
import unittest
from dotenv import load_dotenv

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Criar logger específico para este executor
logger = logging.getLogger('IntegrationTestsRunner')

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def load_environment():
    """Carrega as variáveis de ambiente do arquivo .env."""
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
        logger.info(f"Variáveis de ambiente carregadas de: {env_path}")
    else:
        logger.warning(f"Arquivo .env não encontrado em {env_path}")


def run_connection_tests():
    """Executa os testes de conexão com os serviços."""
    logger.info("\n" + "="*50)
    logger.info("EXECUTANDO TESTES DE CONEXÃO COM SERVIÇOS")
    logger.info("="*50)
    
    start_time = time.time()
    
    try:
        # Importar diretamente do arquivo, sem usar formato de pacote
        import test_forced_connections
        tester = test_forced_connections.ServiceConnectionTester()
        success = tester.run_all_tests()
        
        duration = time.time() - start_time
        logger.info(f"Testes de conexão concluídos em {duration:.2f} segundos")
        
        return success
    except Exception as e:
        logger.error(f"Erro ao executar testes de conexão: {str(e)}")
        return False


def run_hub_integration_tests():
    """Executa os testes de integração do Hub."""
    logger.info("\n" + "="*50)
    logger.info("EXECUTANDO TESTES DE INTEGRAÇÃO DO HUB")
    logger.info("="*50)
    
    start_time = time.time()
    
    try:
        # Importar diretamente do arquivo, sem usar formato de pacote
        import test_hub_integration
        
        # Criar um runner de teste do unittest
        runner = unittest.TextTestRunner(verbosity=2)
        suite = unittest.TestLoader().loadTestsFromTestCase(test_hub_integration.HubIntegrationTester)
        result = runner.run(suite)
        success = result.wasSuccessful()
        
        duration = time.time() - start_time
        logger.info(f"Testes de integração do Hub concluídos em {duration:.2f} segundos")
        
        return success
    except Exception as e:
        logger.error(f"Erro ao executar testes de integração do Hub: {str(e)}")
        return False


def run_crew_integration_tests():
    """Executa os testes de integração das Crews."""
    logger.info("\n" + "="*50)
    logger.info("EXECUTANDO TESTES DE INTEGRAÇÃO DAS CREWS")
    logger.info("="*50)
    
    start_time = time.time()
    
    try:
        # Importar diretamente do arquivo, sem usar formato de pacote
        import test_crew_integration
        
        # Criar um runner de teste do unittest
        runner = unittest.TextTestRunner(verbosity=2)
        suite = unittest.TestLoader().loadTestsFromTestCase(test_crew_integration.CrewIntegrationTester)
        result = runner.run(suite)
        success = result.wasSuccessful()
        
        duration = time.time() - start_time
        logger.info(f"Testes de integração das Crews concluídos em {duration:.2f} segundos")
        
        return success
    except Exception as e:
        logger.error(f"Erro ao executar testes de integração das Crews: {str(e)}")
        return False


def run_specific_tests():
    """Executa testes específicos."""
    logger.info("\n" + "="*50)
    logger.info("EXECUTANDO TESTES ESPECÍFICOS")
    logger.info("="*50)
    
    # Verifica argumentos da linha de comando para determinar quais testes executar
    if len(sys.argv) > 1:
        if "connection" in sys.argv:
            return run_connection_tests()
        elif "hub" in sys.argv:
            return run_hub_integration_tests()
        elif "crew" in sys.argv:
            return run_crew_integration_tests()
        else:
            logger.error("Argumento não reconhecido. Use 'connection', 'hub' ou 'crew'.")
            return False
    else:
        logger.error("Nenhum argumento fornecido. Use 'connection', 'hub' ou 'crew'.")
        return False


def run_all_tests():
    """Executa todos os testes de integração em sequência."""
    logger.info("\n" + "="*50)
    logger.info("INICIANDO TODOS OS TESTES DE INTEGRAÇÃO")
    logger.info("="*50)
    
    # Carregar variáveis de ambiente
    load_environment()
    
    # Armazenar resultados dos testes
    results = {}
    
    # Executar testes de conexão
    logger.info("\n")
    connection_success = run_connection_tests()
    results["Testes de Conexão"] = connection_success
    
    # Se os testes de conexão falharem, podemos continuar com os outros testes,
    # mas eles provavelmente falharão também
    if not connection_success:
        logger.warning("Testes de conexão falharam. Os próximos testes podem falhar também.")
    
    # Executar testes de integração do Hub
    logger.info("\n")
    hub_success = run_hub_integration_tests()
    results["Testes de Integração do Hub"] = hub_success
    
    # Executar testes de integração das Crews
    logger.info("\n")
    crew_success = run_crew_integration_tests()
    results["Testes de Integração das Crews"] = crew_success
    
    # Exibir resumo dos resultados
    logger.info("\n" + "="*50)
    logger.info("RESUMO DE TODOS OS TESTES DE INTEGRAÇÃO")
    logger.info("="*50)
    
    for test, success in results.items():
        status = "✅ PASSOU" if success else "❌ FALHOU"
        logger.info(f"{test}: {status}")
    
    logger.info("="*50)
    
    # Retornar True apenas se todos os testes passaram
    return all(results.values())


if __name__ == "__main__":
    # Verificar se há argumentos específicos
    if len(sys.argv) > 1 and sys.argv[1] != "all":
        success = run_specific_tests()
    else:
        # Executar todos os testes
        success = run_all_tests()
    
    # Sair com código de erro se algum teste falhou
    sys.exit(0 if success else 1)
