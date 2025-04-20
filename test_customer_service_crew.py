#!/usr/bin/env python
"""
Script para testar a crew de atendimento ao cliente.

Este script demonstra como usar a crew de atendimento ao cliente
para processar consultas de usuários e gerar respostas.
"""

import asyncio
import argparse
from crews.test_customer_service import CustomerServiceCrew


def parse_args():
    """
    Analisa os argumentos da linha de comando.
    
    Returns:
        Argumentos analisados
    """
    parser = argparse.ArgumentParser(description="Teste da crew de atendimento ao cliente")
    parser.add_argument("--account_id", type=str, default="account_1", help="ID da conta do cliente")
    parser.add_argument("--query", type=str, help="Consulta do usuário")
    return parser.parse_args()


def main():
    """Função principal."""
    args = parse_args()
    
    # Inicializar a crew
    crew = CustomerServiceCrew(account_id=args.account_id)
    
    # Se a consulta foi fornecida como argumento, processá-la
    if args.query:
        result = crew.process_query(args.query)
        print(f"\nResposta para '{args.query}':\n{result['response']}")
        return
    
    # Caso contrário, iniciar um loop interativo
    print(f"Bem-vindo ao teste da crew de atendimento ao cliente para {args.account_id}")
    print("Digite 'sair' para encerrar")
    
    while True:
        # Obter consulta do usuário
        query = input("\nPergunta do cliente: ")
        
        if query.lower() in ["sair", "exit", "quit"]:
            break
            
        # Processar a consulta
        print("\nProcessando...")
        result = crew.process_query(query)
        
        # Exibir a resposta
        print(f"\nResposta do agente:\n{result['response']}")
    
    print("Obrigado por usar o teste da crew de atendimento ao cliente!")


if __name__ == "__main__":
    main()
