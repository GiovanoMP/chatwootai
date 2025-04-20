#!/usr/bin/env python
"""
Script para testar a resposta rápida do agente de atendimento ao cliente.

Este script mede o tempo de resposta do agente otimizado para garantir
que as respostas sejam entregues em menos de 3 segundos.
"""

import time
import argparse
import logging
import sys

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

from crew_tests.agents.fast_customer_service import get_fast_response


def parse_args():
    """
    Analisa os argumentos da linha de comando.

    Returns:
        Argumentos analisados
    """
    parser = argparse.ArgumentParser(description="Teste de resposta rápida")
    parser.add_argument("--account_id", type=str, default="account_1", help="ID da conta do cliente")
    parser.add_argument("--query", type=str, help="Consulta do cliente")
    return parser.parse_args()


def main():
    """Função principal."""
    # Analisar argumentos
    args = parse_args()

    # Se a consulta foi fornecida como argumento, processá-la
    if args.query:
        print(f"Processando consulta: '{args.query}'")
        logger.info(f"Iniciando processamento da consulta: '{args.query}'")

        # Medir tempo de resposta
        start_time = time.time()
        try:
            logger.info("Chamando get_fast_response")
            result = get_fast_response(args.query, args.account_id)
            logger.info("get_fast_response concluído com sucesso")
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
    print(f"Bem-vindo ao teste de resposta rápida para a conta {args.account_id}")
    print("Este chat foi projetado para fornecer respostas em menos de 3 segundos.")
    print("Digite 'sair' para encerrar o chat")
    print()

    # Loop de chat
    while True:
        # Obter consulta do usuário
        query = input("\n\033[1;32mVocê:\033[0m ")

        if query.lower() in ["sair", "exit", "quit"]:
            break

        # Medir tempo de resposta
        start_time = time.time()
        result = get_fast_response(query, args.account_id)
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

    print("\nObrigado por usar o teste de resposta rápida!")


if __name__ == "__main__":
    main()
