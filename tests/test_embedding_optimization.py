#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de teste para validar as otimizações do serviço de embeddings.

Este script demonstra como as estratégias de otimização de custos implementadas
no EmbeddingService reduzem o número de chamadas à API da OpenAI e economizam tokens.
"""
import os
import sys
import time
import dotenv
from typing import List, Dict, Any

# Adicionar o diretório raiz ao path para importar os módulos do projeto
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Carregar variáveis de ambiente
dotenv.load_dotenv()

from src.services.embedding_service import EmbeddingService

def test_cache_effectiveness():
    """
    Testa a efetividade do cache Redis para economizar chamadas à API.
    """
    print("\n=== Teste de Efetividade do Cache ===")
    
    # Inicializar o serviço de embeddings com cache ativado
    embedding_service = EmbeddingService(use_cache=True)
    
    # Textos de exemplo para testar
    test_texts = [
        "Hidratante para pele oleosa",
        "Shampoo para cabelos cacheados",
        "Protetor solar fator 50",
        "Creme anti-rugas para pele madura",
        "Sabonete facial para pele sensível"
    ]
    
    # Primeira execução - deve gerar chamadas à API para todos os textos
    print("\nPrimeira execução (sem cache):")
    start_time = time.time()
    
    # Resetar estatísticas antes de começar
    embedding_service.reset_usage_stats()
    
    # Gerar embeddings para cada texto individualmente
    for text in test_texts:
        embedding = embedding_service.get_embedding(text)
        print(f"Gerado embedding para: '{text}' (dimensão: {len(embedding)})")
    
    # Exibir estatísticas após a primeira execução
    stats = embedding_service.get_usage_stats()
    print(f"\nEstatísticas da primeira execução:")
    print(f"Chamadas à API: {stats['api_calls']}")
    print(f"Tokens utilizados: {stats['tokens_used']}")
    print(f"Custo estimado: ${stats['estimated_cost_usd']:.6f}")
    print(f"Tempo de execução: {time.time() - start_time:.2f} segundos")
    
    # Segunda execução - deve usar o cache para todos os textos
    print("\nSegunda execução (com cache):")
    start_time = time.time()
    
    # Resetar estatísticas antes de começar
    embedding_service.reset_usage_stats()
    
    # Gerar embeddings para os mesmos textos
    for text in test_texts:
        embedding = embedding_service.get_embedding(text)
        print(f"Recuperado embedding para: '{text}' (dimensão: {len(embedding)})")
    
    # Exibir estatísticas após a segunda execução
    stats = embedding_service.get_usage_stats()
    print(f"\nEstatísticas da segunda execução:")
    print(f"Chamadas à API: {stats['api_calls']} (esperado: 0)")
    print(f"Tokens utilizados: {stats['tokens_used']} (esperado: 0)")
    print(f"Custo estimado: ${stats['estimated_cost_usd']:.6f}")
    print(f"Tempo de execução: {time.time() - start_time:.2f} segundos")
    
    return stats['api_calls'] == 0  # Sucesso se não houver chamadas à API na segunda execução

def test_batch_processing():
    """
    Testa a eficiência do processamento em lote comparado com chamadas individuais.
    """
    print("\n=== Teste de Processamento em Lote ===")
    
    # Inicializar o serviço de embeddings sem cache para este teste
    embedding_service = EmbeddingService(use_cache=False)
    
    # Textos de exemplo para testar
    test_texts = [
        "Hidratante facial noturno",
        "Máscara capilar de reconstrução",
        "Sérum facial com vitamina C",
        "Óleo corporal pós-banho",
        "Esfoliante facial com ácido salicílico",
        "Creme para as mãos com manteiga de karité",
        "Protetor térmico para cabelos",
        "Contorno para olhos com cafeína",
        "Desodorante sem alumínio",
        "Batom matte longa duração"
    ]
    
    # Primeira abordagem: chamadas individuais
    print("\nAbordagem 1: Chamadas individuais")
    start_time = time.time()
    
    # Resetar estatísticas antes de começar
    embedding_service.reset_usage_stats()
    
    # Gerar embeddings para cada texto individualmente
    individual_embeddings = []
    for text in test_texts:
        embedding = embedding_service.get_embedding(text)
        individual_embeddings.append(embedding)
    
    # Exibir estatísticas após as chamadas individuais
    stats_individual = embedding_service.get_usage_stats()
    print(f"\nEstatísticas das chamadas individuais:")
    print(f"Chamadas à API: {stats_individual['api_calls']}")
    print(f"Tokens utilizados: {stats_individual['tokens_used']}")
    print(f"Custo estimado: ${stats_individual['estimated_cost_usd']:.6f}")
    print(f"Tempo de execução: {time.time() - start_time:.2f} segundos")
    
    # Segunda abordagem: processamento em lote
    print("\nAbordagem 2: Processamento em lote")
    start_time = time.time()
    
    # Resetar estatísticas antes de começar
    embedding_service.reset_usage_stats()
    
    # Gerar embeddings para todos os textos em uma única chamada
    batch_embeddings = embedding_service.get_batch_embeddings(test_texts)
    
    # Exibir estatísticas após o processamento em lote
    stats_batch = embedding_service.get_usage_stats()
    print(f"\nEstatísticas do processamento em lote:")
    print(f"Chamadas à API: {stats_batch['api_calls']}")
    print(f"Tokens utilizados: {stats_batch['tokens_used']}")
    print(f"Custo estimado: ${stats_batch['estimated_cost_usd']:.6f}")
    print(f"Tempo de execução: {time.time() - start_time:.2f} segundos")
    
    # Calcular a economia
    api_calls_saved = stats_individual['api_calls'] - stats_batch['api_calls']
    tokens_saved = stats_individual['tokens_used'] - stats_batch['tokens_used']
    cost_saved = stats_individual['estimated_cost_usd'] - stats_batch['estimated_cost_usd']
    
    print(f"\nEconomia com processamento em lote:")
    print(f"Chamadas à API economizadas: {api_calls_saved}")
    print(f"Tokens economizados: {tokens_saved}")
    print(f"Custo economizado: ${cost_saved:.6f}")
    
    return stats_batch['api_calls'] < stats_individual['api_calls']

def main():
    """
    Função principal que executa todos os testes.
    """
    print("=== Teste de Otimização do Serviço de Embeddings ===")
    print(f"Modelo de embeddings: {os.environ.get('EMBEDDING_MODEL', 'text-embedding-3-small')}")
    print(f"Cache Redis: {'Ativado' if os.environ.get('REDIS_URL') else 'Desativado'}")
    
    # Executar testes
    cache_test_success = test_cache_effectiveness()
    batch_test_success = test_batch_processing()
    
    # Resumo dos resultados
    print("\n=== Resumo dos Resultados ===")
    print(f"Teste de Cache: {'SUCESSO' if cache_test_success else 'FALHA'}")
    print(f"Teste de Processamento em Lote: {'SUCESSO' if batch_test_success else 'FALHA'}")
    
    # Considerações finais
    print("\n=== Considerações Finais ===")
    print("As estratégias de otimização implementadas no serviço de embeddings são eficazes para:")
    print("1. Reduzir o número de chamadas à API da OpenAI")
    print("2. Economizar tokens e, consequentemente, custos")
    print("3. Melhorar o desempenho através do cache Redis")
    print("4. Otimizar o processamento com lotes em vez de chamadas individuais")
    
    print("\nEstas otimizações são especialmente importantes em ambientes de produção,")
    print("onde o volume de solicitações pode ser alto e os custos podem escalar rapidamente.")

if __name__ == "__main__":
    main()
