#!/usr/bin/env python
"""
Script para testar o agente otimizado para atendimento ao cliente.

Este script mede o tempo de resposta do agente otimizado para garantir
que as respostas sejam entregues em menos de 3 segundos.
"""

import time
import argparse
import logging
import sys
import json

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

from crew_tests.agents.optimized_agent import get_optimized_response


def parse_args():
    """
    Analisa os argumentos da linha de comando.
    
    Returns:
        Argumentos analisados
    """
    parser = argparse.ArgumentParser(description="Teste de resposta otimizada")
    parser.add_argument("--account_id", type=str, default="account_1", help="ID da conta do cliente")
    parser.add_argument("--query", type=str, help="Consulta do cliente")
    parser.add_argument("--benchmark", action="store_true", help="Executar benchmark com múltiplas consultas")
    return parser.parse_args()


def run_benchmark(account_id: str):
    """
    Executa um benchmark com múltiplas consultas.
    
    Args:
        account_id: ID da conta do cliente
    """
    # Lista de consultas para benchmark
    queries = [
        "Vocês têm alguma promoção de shampoo?",
        "Qual o horário de funcionamento da loja?",
        "Como faço para devolver um produto?",
        "Vocês aceitam cartão de crédito?",
        "Quais são as formas de pagamento aceitas?"
    ]
    
    # Resultados do benchmark
    results = []
    
    # Executar benchmark
    print("\n=== INICIANDO BENCHMARK ===\n")
    
    for i, query in enumerate(queries, 1):
        print(f"Consulta {i}/{len(queries)}: '{query}'")
        
        # Medir tempo de resposta
        start_time = time.time()
        try:
            result = get_optimized_response(query, account_id)
            success = True
        except Exception as e:
            logger.error(f"Erro ao processar consulta: {e}", exc_info=True)
            result = f"Erro: {str(e)}"
            success = False
        end_time = time.time()
        
        # Calcular tempo de resposta
        response_time = end_time - start_time
        
        # Exibir resultado
        print(f"Resposta (tempo: {response_time:.2f}s):\n{result}")
        
        # Verificar se o tempo de resposta está dentro do limite
        within_limit = response_time <= 3.0
        if within_limit:
            print("\n✅ Resposta entregue dentro do limite de 3 segundos!")
        else:
            print(f"\n❌ Resposta excedeu o limite de 3 segundos ({response_time:.2f}s)")
        
        # Adicionar resultado ao benchmark
        results.append({
            "query": query,
            "response_time": response_time,
            "within_limit": within_limit,
            "success": success
        })
        
        print("\n" + "-" * 50 + "\n")
    
    # Exibir resultados do benchmark
    print("\n=== RESULTADOS DO BENCHMARK ===\n")
    
    # Calcular estatísticas
    total_queries = len(results)
    successful_queries = sum(1 for r in results if r["success"])
    within_limit_queries = sum(1 for r in results if r["within_limit"])
    avg_response_time = sum(r["response_time"] for r in results) / total_queries
    
    print(f"Total de consultas: {total_queries}")
    print(f"Consultas bem-sucedidas: {successful_queries} ({successful_queries/total_queries*100:.1f}%)")
    print(f"Consultas dentro do limite de 3s: {within_limit_queries} ({within_limit_queries/total_queries*100:.1f}%)")
    print(f"Tempo médio de resposta: {avg_response_time:.2f}s")
    
    # Exibir resultados detalhados
    print("\nResultados detalhados:")
    for i, r in enumerate(results, 1):
        status = "✅" if r["within_limit"] else "❌"
        print(f"{i}. {status} '{r['query']}' - {r['response_time']:.2f}s")


def main():
    """Função principal."""
    # Analisar argumentos
    args = parse_args()
    
    # Executar benchmark se solicitado
    if args.benchmark:
        run_benchmark(args.account_id)
        return
    
    # Se a consulta foi fornecida como argumento, processá-la
    if args.query:
        print(f"Processando consulta: '{args.query}'")
        logger.info(f"Iniciando processamento da consulta: '{args.query}'")
        
        # Medir tempo de resposta
        start_time = time.time()
        try:
            logger.info("Chamando get_optimized_response")
            result = get_optimized_response(args.query, args.account_id)
            logger.info("get_optimized_response concluído com sucesso")
        except Exception as e:
            logger.error(f"Erro ao processar consulta: {e}", exc_info=True)
            result = f"Erro: {str(e)}"
        end_time = time.time()
        
        # Calcular tempo de resposta
        response_time = end_time - start_time
        
        # Exibir resultado
        print(f"\nResposta (tempo: {response_time:.2f}s):\n{result}")
        
        # Verificar se o tempo de resposta está dentro do limite
        if response_time <= 3.0:
            print("\n✅ Resposta entregue dentro do limite de 3 segundos!")
        else:
            print(f"\n❌ Resposta excedeu o limite de 3 segundos ({response_time:.2f}s)")
        
        return
    
    # Caso contrário, iniciar um loop interativo
    print(f"Bem-vindo ao teste de resposta otimizada para a conta {args.account_id}")
    print("Este chat foi projetado para fornecer respostas em menos de 3 segundos.")
    print("Digite 'sair' para encerrar o chat")
    print("Digite 'benchmark' para executar um benchmark com múltiplas consultas")
    print()
    
    # Loop de chat
    while True:
        # Obter consulta do usuário
        query = input("\n\033[1;32mVocê:\033[0m ")
        
        if query.lower() in ["sair", "exit", "quit"]:
            break
        
        if query.lower() == "benchmark":
            run_benchmark(args.account_id)
            continue
        
        # Medir tempo de resposta
        start_time = time.time()
        try:
            result = get_optimized_response(query, args.account_id)
        except Exception as e:
            logger.error(f"Erro ao processar consulta: {e}", exc_info=True)
            result = f"Erro: {str(e)}"
        end_time = time.time()
        
        # Calcular tempo de resposta
        response_time = end_time - start_time
        
        # Exibir resultado
        print(f"\n\033[1;36mAtendente\033[0m (tempo: {response_time:.2f}s):\n{result}")
        
        # Verificar se o tempo de resposta está dentro do limite
        if response_time <= 3.0:
            print("\n\033[0;32m✅ Resposta entregue dentro do limite de 3 segundos!\033[0m")
        else:
            print(f"\n\033[0;31m❌ Resposta excedeu o limite de 3 segundos ({response_time:.2f}s)\033[0m")
    
    print("\nObrigado por usar o teste de resposta otimizada!")


if __name__ == "__main__":
    main()
