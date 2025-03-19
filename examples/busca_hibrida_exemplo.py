#!/usr/bin/env python3
"""
Exemplo de uso da busca híbrida com embeddings da OpenAI.

Este script demonstra como utilizar a solução de busca híbrida implementada
no ChatwootAI para encontrar produtos relevantes para diferentes consultas.

Uso:
    python3 busca_hibrida_exemplo.py

Requisitos:
    - Variáveis de ambiente configuradas (.env)
    - Serviços PostgreSQL e Qdrant em execução
    - Dados de exemplo carregados
"""
import os
import sys
import logging
from dotenv import load_dotenv

# Adicionar o diretório raiz ao PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importar os serviços implementados
from src.services.embedding_service import EmbeddingService
from src.services.search_service import ProductSearchService
from src.plugins.product_search_plugin import ProductSearchPlugin

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()

def demonstrar_busca_simples():
    """Demonstra uma busca simples por produtos."""
    logger.info("=== DEMONSTRAÇÃO DE BUSCA SIMPLES ===")
    
    # Inicializar o serviço de busca
    search_service = ProductSearchService()
    
    # Exemplos de consultas
    consultas = [
        "produtos para pele oleosa",
        "shampoo para cabelos cacheados",
        "hidratante labial",
        "protetor solar para rosto",
        "maquiagem para pele sensível"
    ]
    
    # Realizar buscas para cada consulta
    for consulta in consultas:
        logger.info(f"\nConsulta: '{consulta}'")
        
        # Buscar produtos
        resultados = search_service.search_products(
            query=consulta,
            limit=3,
            min_score=0.7
        )
        
        # Exibir resultados
        if resultados:
            logger.info(f"Encontrados {len(resultados)} produtos relevantes:")
            for i, produto in enumerate(resultados, 1):
                logger.info(f"  {i}. {produto['name']} - R$ {float(produto['price']):.2f}")
                if produto.get('description'):
                    logger.info(f"     {produto['description'][:100]}...")
                logger.info(f"     Relevância: {produto.get('score', 0):.2f}")
        else:
            logger.info("Nenhum produto relevante encontrado.")

def demonstrar_busca_com_filtros():
    """Demonstra uma busca com filtros por categoria e preço."""
    logger.info("\n=== DEMONSTRAÇÃO DE BUSCA COM FILTROS ===")
    
    # Inicializar o serviço de busca
    search_service = ProductSearchService()
    
    # Exemplo 1: Filtro por categoria
    categoria = "Cuidados com o Cabelo"
    consulta = "tratamento para cabelos danificados"
    
    logger.info(f"\nConsulta com filtro de categoria: '{consulta}' na categoria '{categoria}'")
    
    # Buscar produtos na categoria
    filtros = {"category": categoria}
    resultados = search_service.search_products(
        query=consulta,
        limit=3,
        filters=filtros
    )
    
    # Exibir resultados
    if resultados:
        logger.info(f"Encontrados {len(resultados)} produtos na categoria '{categoria}':")
        for i, produto in enumerate(resultados, 1):
            logger.info(f"  {i}. {produto['name']} - R$ {float(produto['price']):.2f}")
            if produto.get('description'):
                logger.info(f"     {produto['description'][:100]}...")
            logger.info(f"     Relevância: {produto.get('score', 0):.2f}")
    else:
        logger.info(f"Nenhum produto relevante encontrado na categoria '{categoria}'.")
    
    # Exemplo 2: Filtro por faixa de preço
    min_price = 20.0
    max_price = 50.0
    consulta = "hidratante facial"
    
    logger.info(f"\nConsulta com filtro de preço: '{consulta}' entre R$ {min_price:.2f} e R$ {max_price:.2f}")
    
    # Buscar produtos na faixa de preço
    filtros = {"price_min": min_price, "price_max": max_price}
    resultados = search_service.search_products(
        query=consulta,
        limit=3,
        filters=filtros
    )
    
    # Exibir resultados
    if resultados:
        logger.info(f"Encontrados {len(resultados)} produtos na faixa de preço:")
        for i, produto in enumerate(resultados, 1):
            logger.info(f"  {i}. {produto['name']} - R$ {float(produto['price']):.2f}")
            if produto.get('description'):
                logger.info(f"     {produto['description'][:100]}...")
            logger.info(f"     Relevância: {produto.get('score', 0):.2f}")
    else:
        logger.info("Nenhum produto relevante encontrado na faixa de preço.")

def demonstrar_uso_plugin():
    """Demonstra o uso do plugin de busca de produtos."""
    logger.info("\n=== DEMONSTRAÇÃO DO PLUGIN DE BUSCA DE PRODUTOS ===")
    
    # Inicializar o plugin
    plugin = ProductSearchPlugin()
    plugin.initialize({"name": "cosmetics", "description": "Empresa de cosméticos"})
    
    # Exemplo de consulta
    consulta = "produtos para cabelos secos e danificados"
    
    logger.info(f"\nConsulta: '{consulta}'")
    
    # Buscar produtos usando o plugin
    produtos = plugin.search_products(consulta, limit=3)
    
    # Formatar e exibir resultados
    resposta = plugin.format_product_results(produtos)
    logger.info("\nResposta formatada para o cliente:")
    logger.info(resposta)
    
    # Exemplo com busca por categoria
    categoria = "Maquiagem"
    consulta = "base para pele seca"
    
    logger.info(f"\nConsulta por categoria: '{consulta}' na categoria '{categoria}'")
    
    # Buscar produtos na categoria usando o plugin
    produtos = plugin.search_products_by_category(consulta, categoria, limit=3)
    
    # Formatar e exibir resultados
    resposta = plugin.format_product_results(produtos, detailed=True)
    logger.info("\nResposta formatada para o cliente (detalhada):")
    logger.info(resposta)

def demonstrar_embedding():
    """Demonstra o funcionamento do serviço de embeddings."""
    logger.info("\n=== DEMONSTRAÇÃO DO SERVIÇO DE EMBEDDINGS ===")
    
    # Inicializar o serviço de embeddings
    embedding_service = EmbeddingService()
    
    # Exemplo de textos
    textos = [
        "Hidratante facial para pele seca",
        "Shampoo para cabelos oleosos",
        "Protetor solar FPS 50"
    ]
    
    # Gerar embedding para um único texto
    logger.info(f"\nGerando embedding para: '{textos[0]}'")
    embedding = embedding_service.generate_embedding(textos[0])
    logger.info(f"Dimensão do embedding: {len(embedding)}")
    logger.info(f"Primeiros 5 valores: {embedding[:5]}")
    
    # Gerar embeddings em lote
    logger.info(f"\nGerando embeddings em lote para {len(textos)} textos")
    embeddings = embedding_service.generate_batch_embeddings(textos)
    logger.info(f"Número de embeddings gerados: {len(embeddings)}")
    for i, emb in enumerate(embeddings):
        logger.info(f"Embedding {i+1}: dimensão {len(emb)}")

if __name__ == "__main__":
    try:
        # Verificar variáveis de ambiente
        required_vars = ["OPENAI_API_KEY", "DATABASE_URL", "QDRANT_URL"]
        missing_vars = [var for var in required_vars if not os.environ.get(var)]
        
        if missing_vars:
            logger.error(f"Variáveis de ambiente ausentes: {', '.join(missing_vars)}")
            logger.error("Configure as variáveis no arquivo .env ou defina-as no ambiente.")
            sys.exit(1)
        
        # Executar demonstrações
        demonstrar_busca_simples()
        demonstrar_busca_com_filtros()
        demonstrar_uso_plugin()
        demonstrar_embedding()
        
        logger.info("\n=== DEMONSTRAÇÕES CONCLUÍDAS COM SUCESSO ===")
        
    except Exception as e:
        logger.error(f"Erro durante a execução das demonstrações: {str(e)}", exc_info=True)
        sys.exit(1)
