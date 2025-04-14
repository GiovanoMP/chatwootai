#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script simples para testar o módulo business_rules.
"""

import os
import sys
import json
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configurar variáveis de ambiente
os.environ["OPENAI_API_KEY"] = os.environ.get("OPENAI_API_KEY", "sk-your-api-key")

# Adicionar diretório atual ao path
sys.path.append(os.path.abspath("."))

def test_import_modules():
    """Testa a importação dos módulos necessários."""
    try:
        logger.info("Testando importação de módulos...")
        
        # Importar módulos
        from modules.business_rules.services import BusinessRulesService
        from modules.business_rules.schemas import BusinessRuleRequest, RuleType, RulePriority
        
        logger.info("Módulos importados com sucesso!")
        return True
    except Exception as e:
        logger.error(f"Erro ao importar módulos: {e}")
        return False

def test_service_initialization():
    """Testa a inicialização do serviço."""
    try:
        logger.info("Testando inicialização do serviço...")
        
        # Importar e inicializar serviço
        from modules.business_rules.services import get_business_rules_service
        
        service = get_business_rules_service()
        
        logger.info("Serviço inicializado com sucesso!")
        return True
    except Exception as e:
        logger.error(f"Erro ao inicializar serviço: {e}")
        return False

def main():
    """Função principal."""
    logger.info("Iniciando testes simples do módulo business_rules...")
    
    # Testar importação de módulos
    import_result = test_import_modules()
    
    # Testar inicialização do serviço
    service_result = test_service_initialization()
    
    # Exibir resumo
    logger.info("\n" + "="*80)
    logger.info("RESUMO DOS TESTES")
    logger.info("="*80)
    logger.info(f"Importação de módulos: {'SUCESSO' if import_result else 'FALHA'}")
    logger.info(f"Inicialização do serviço: {'SUCESSO' if service_result else 'FALHA'}")
    
    # Salvar resultados
    results = {
        "timestamp": datetime.now().isoformat(),
        "import_modules": import_result,
        "service_initialization": service_result
    }
    
    with open("simple_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    logger.info("Testes concluídos.")

if __name__ == "__main__":
    main()
