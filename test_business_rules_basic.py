#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script simples para testar o módulo business_rules.
Este script testa apenas as funcionalidades básicas do módulo.
"""

import os
import sys
import json
import logging
import dotenv
from datetime import datetime

# Limpar variáveis de ambiente existentes
for key in list(os.environ.keys()):
    if key.startswith(('CHATWOOT_', 'WEBHOOK_', 'POSTGRES_', 'DATABASE_', 'DEV_MODE', 'SQLITE_', 'NGROK_', 'VPS_', 'PROXY_')):
        del os.environ[key]

# Carregar variáveis de ambiente do arquivo .env.test
dotenv.load_dotenv(".env.test")

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configurações
ACCOUNT_ID = "account_1"  # ID da conta Odoo

def test_import_module():
    """Testa a importação do módulo."""
    try:
        logger.info("Testando importação do módulo business_rules...")
        from modules.business_rules.services import get_business_rules_service

        logger.info("Módulo importado com sucesso!")
        return True
    except Exception as e:
        logger.error(f"Erro ao importar módulo: {e}")
        return False

def test_service_initialization():
    """Testa a inicialização do serviço."""
    try:
        logger.info("Testando inicialização do serviço...")
        from modules.business_rules.services import get_business_rules_service

        service = get_business_rules_service()

        logger.info("Serviço inicializado com sucesso!")
        return True
    except Exception as e:
        logger.error(f"Erro ao inicializar serviço: {e}")
        return False

def main():
    """Função principal."""
    logger.info("Iniciando testes básicos do módulo business_rules...")

    # Testar importação do módulo
    import_result = test_import_module()

    # Testar inicialização do serviço
    service_result = test_service_initialization()

    # Exibir resumo
    logger.info("\n" + "="*80)
    logger.info("RESUMO DOS TESTES")
    logger.info("="*80)
    logger.info(f"Importação do módulo: {'SUCESSO' if import_result else 'FALHA'}")
    logger.info(f"Inicialização do serviço: {'SUCESSO' if service_result else 'FALHA'}")

    # Salvar resultados
    results = {
        "timestamp": datetime.now().isoformat(),
        "import_module": import_result,
        "service_initialization": service_result
    }

    with open("basic_test_results.json", "w") as f:
        json.dump(results, f, indent=2)

    logger.info("Testes concluídos.")

if __name__ == "__main__":
    main()
