#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para testar a integração entre o módulo Odoo business_rules e o sistema de IA.
"""

import asyncio
import logging
import sys
from pprint import pprint

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_sync_rules():
    """Testar sincronização de regras."""
    try:
        from odoo_api.modules.business_rules.services import get_business_rules_service
        
        logger.info("Obtendo serviço de regras de negócio...")
        service = get_business_rules_service()
        
        logger.info("Sincronizando regras de negócio...")
        result = await service.sync_business_rules("account_1")
        
        logger.info("Sincronização concluída:")
        pprint(result)
        
        return True
    except Exception as e:
        logger.error(f"Erro ao sincronizar regras: {e}")
        return False

async def test_search_rules():
    """Testar busca semântica de regras."""
    try:
        from odoo_api.modules.business_rules.services import get_business_rules_service
        
        logger.info("Obtendo serviço de regras de negócio...")
        service = get_business_rules_service()
        
        # Consultas de teste
        queries = [
            "Qual é o horário de funcionamento?",
            "Como faço para devolver um produto?",
            "Quais são as políticas de entrega?",
            "Vocês oferecem garantia?"
        ]
        
        for query in queries:
            logger.info(f"Buscando regras para: '{query}'...")
            results = await service.search_business_rules("account_1", query)
            
            logger.info(f"Resultados para '{query}':")
            pprint(results)
            print("\n" + "-"*80 + "\n")
        
        return True
    except Exception as e:
        logger.error(f"Erro ao buscar regras: {e}")
        return False

async def test_customer_support():
    """Testar funcionalidade de suporte ao cliente."""
    try:
        from odoo_api.modules.business_rules.services import get_business_rules_service
        
        logger.info("Obtendo serviço de regras de negócio...")
        service = get_business_rules_service()
        
        logger.info("Enviando mensagem de suporte...")
        result = await service.customer_support(
            account_id="account_1",
            message="Estou com problemas para acessar minha conta. Podem me ajudar?",
            file_content=None,
            file_name=None,
            file_type=None
        )
        
        logger.info("Mensagem enviada:")
        pprint(result)
        
        return True
    except Exception as e:
        logger.error(f"Erro ao enviar mensagem de suporte: {e}")
        return False

async def main():
    """Função principal."""
    logger.info("Iniciando testes de integração...")
    
    # Testar sincronização
    logger.info("\n" + "="*80)
    logger.info("TESTE 1: Sincronização de Regras")
    logger.info("="*80)
    sync_result = await test_sync_rules()
    
    # Testar busca
    logger.info("\n" + "="*80)
    logger.info("TESTE 2: Busca Semântica de Regras")
    logger.info("="*80)
    search_result = await test_search_rules()
    
    # Testar suporte
    logger.info("\n" + "="*80)
    logger.info("TESTE 3: Suporte ao Cliente")
    logger.info("="*80)
    support_result = await test_customer_support()
    
    # Resumo
    logger.info("\n" + "="*80)
    logger.info("RESUMO DOS TESTES")
    logger.info("="*80)
    logger.info(f"Sincronização de Regras: {'SUCESSO' if sync_result else 'FALHA'}")
    logger.info(f"Busca Semântica de Regras: {'SUCESSO' if search_result else 'FALHA'}")
    logger.info(f"Suporte ao Cliente: {'SUCESSO' if support_result else 'FALHA'}")

if __name__ == "__main__":
    asyncio.run(main())
