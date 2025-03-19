#!/usr/bin/env python
"""
Script para testar os serviços de sincronização entre PostgreSQL e Qdrant.

Este script demonstra como os serviços de sincronização funcionam, realizando
operações de sincronização manual e verificando os resultados.

Uso:
    python test_sync_services.py
"""
import os
import sys
import logging
import asyncio
import json
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Adicionar diretório raiz ao PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Importar serviços
from src.services.data_sync_service import DataSyncService
from src.services.embedding_service import EmbeddingService
from src.services.product_search_service import ProductSearchService

async def test_data_sync():
    """
    Testa o serviço de sincronização de dados.
    """
    logger = logging.getLogger("test_data_sync")
    logger.info("Iniciando teste do serviço de sincronização de dados...")
    
    try:
        # Inicializar serviços
        embedding_service = EmbeddingService()
        data_sync_service = DataSyncService(embedding_service=embedding_service)
        
        # 1. Testar sincronização de produtos
        logger.info("Testando sincronização de produtos...")
        
        # Obter todos os IDs de produtos
        product_ids = data_sync_service.get_all_product_ids()
        logger.info(f"Encontrados {len(product_ids)} produtos no PostgreSQL")
        
        if product_ids:
            # Sincronizar o primeiro produto
            first_product_id = product_ids[0]
            product = data_sync_service.get_product(first_product_id)
            logger.info(f"Sincronizando produto: {product['name']} (ID: {first_product_id})")
            
            success = data_sync_service.sync_product(first_product_id)
            logger.info(f"Sincronização do produto {first_product_id}: {'Sucesso' if success else 'Falha'}")
            
            # Sincronizar todos os produtos
            logger.info("Sincronizando todos os produtos...")
            success = data_sync_service.full_sync_products(batch_size=5)
            logger.info(f"Sincronização completa de produtos: {'Sucesso' if success else 'Falha'}")
        else:
            logger.warning("Nenhum produto encontrado para sincronizar")
        
        # 2. Testar sincronização de regras de negócio
        logger.info("Testando sincronização de regras de negócio...")
        
        # Obter todos os IDs de regras de negócio
        rule_ids = data_sync_service.get_all_business_rule_ids()
        logger.info(f"Encontradas {len(rule_ids)} regras de negócio no PostgreSQL")
        
        if rule_ids:
            # Sincronizar a primeira regra
            first_rule_id = rule_ids[0]
            rule = data_sync_service.get_business_rule(first_rule_id)
            logger.info(f"Sincronizando regra: {rule['name']} (ID: {first_rule_id})")
            
            success = data_sync_service.sync_business_rule(first_rule_id)
            logger.info(f"Sincronização da regra {first_rule_id}: {'Sucesso' if success else 'Falha'}")
            
            # Sincronizar todas as regras
            logger.info("Sincronizando todas as regras de negócio...")
            success = data_sync_service.full_sync_business_rules(batch_size=5)
            logger.info(f"Sincronização completa de regras de negócio: {'Sucesso' if success else 'Falha'}")
        else:
            logger.warning("Nenhuma regra de negócio encontrada para sincronizar")
            
        logger.info("Teste do serviço de sincronização de dados concluído com sucesso!")
        
    except Exception as e:
        logger.error(f"Erro durante o teste de sincronização: {e}")

async def test_product_search():
    """
    Testa o serviço de busca de produtos.
    """
    logger = logging.getLogger("test_product_search")
    logger.info("Iniciando teste do serviço de busca de produtos...")
    
    try:
        # Inicializar serviço de busca
        search_service = ProductSearchService()
        
        # Realizar algumas buscas de teste
        test_queries = [
            "hidratante para pele seca",
            "protetor solar",
            "shampoo anticaspa",
            "creme para rugas"
        ]
        
        for query in test_queries:
            logger.info(f"Realizando busca para: '{query}'")
            
            # Buscar produtos
            products = search_service.search_products(query, limit=3)
            
            if products:
                logger.info(f"Encontrados {len(products)} produtos para '{query}':")
                for i, product in enumerate(products, 1):
                    logger.info(f"  {i}. {product['name']} (Score: {product['score']:.2f})")
            else:
                logger.info(f"Nenhum produto encontrado para '{query}'")
                
        # Testar busca de regras de negócio
        rule_queries = [
            "política de devolução",
            "garantia de produtos",
            "formas de pagamento"
        ]
        
        for query in rule_queries:
            logger.info(f"Realizando busca de regras para: '{query}'")
            
            # Buscar regras
            rules = search_service.search_business_rules(query, limit=2)
            
            if rules:
                logger.info(f"Encontradas {len(rules)} regras para '{query}':")
                for i, rule in enumerate(rules, 1):
                    logger.info(f"  {i}. {rule['name']} (Score: {rule['score']:.2f})")
            else:
                logger.info(f"Nenhuma regra encontrada para '{query}'")
                
        logger.info("Teste do serviço de busca concluído com sucesso!")
        
    except Exception as e:
        logger.error(f"Erro durante o teste de busca: {e}")

async def main():
    """
    Função principal para executar os testes.
    """
    logger = logging.getLogger("main")
    logger.info("Iniciando testes dos serviços de sincronização e busca...")
    
    # Verificar variáveis de ambiente necessárias
    required_env_vars = ["DATABASE_URL", "QDRANT_URL", "OPENAI_API_KEY"]
    missing_vars = [var for var in required_env_vars if not os.environ.get(var)]
    
    if missing_vars:
        logger.error(f"Variáveis de ambiente necessárias não encontradas: {', '.join(missing_vars)}")
        logger.error("Por favor, defina as variáveis de ambiente necessárias e tente novamente.")
        return
    
    # Executar testes
    await test_data_sync()
    print("\n" + "-" * 80 + "\n")
    await test_product_search()
    
    logger.info("Todos os testes concluídos!")

if __name__ == "__main__":
    asyncio.run(main())
