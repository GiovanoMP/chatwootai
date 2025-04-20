#!/usr/bin/env python
"""
Script de teste para integração do CrewAI com Qdrant.
"""

import os
import argparse
import asyncio
from typing import Dict, Any
from dotenv import load_dotenv
from crewai import Crew, Process
from crewai.memory.entity.entity_memory import EntityMemory
from crewai.memory.short_term.short_term_memory import ShortTermMemory

from crew_tests.config import DEFAULT_ACCOUNT_ID, MEMORY_ENABLED
from crew_tests.agents import create_customer_service_agents, create_customer_service_tasks
from crew_tests.memory import QdrantMultiTenantStorage


def parse_args():
    """
    Analisa os argumentos da linha de comando.

    Returns:
        Argumentos analisados
    """
    parser = argparse.ArgumentParser(description="Teste de integração do CrewAI com Qdrant")
    parser.add_argument("--account_id", type=str, default=DEFAULT_ACCOUNT_ID, help="ID da conta do cliente")
    parser.add_argument("--query", type=str, help="Consulta do cliente")
    parser.add_argument("--no-memory", action="store_true", help="Desabilita o uso de memória")
    return parser.parse_args()


def create_crew(account_id: str, use_memory: bool = True) -> Crew:
    """
    Cria uma crew para atendimento ao cliente.

    Args:
        account_id: ID da conta do cliente
        use_memory: Se deve usar memória

    Returns:
        Crew criada
    """
    # Criar agentes
    agents = create_customer_service_agents(account_id)

    # Configurar memória
    if use_memory:
        return Crew(
            agents=list(agents.values()),
            process=Process.sequential,
            memory=True,
            entity_memory=EntityMemory(
                storage=QdrantMultiTenantStorage("entity", account_id)
            ),
            short_term_memory=ShortTermMemory(
                storage=QdrantMultiTenantStorage("short_term", account_id)
            ),
            verbose=True
        )
    else:
        return Crew(
            agents=list(agents.values()),
            process=Process.sequential,
            memory=False,
            verbose=True
        )


def process_query(query: str, account_id: str, use_memory: bool = True) -> Dict[str, Any]:
    """
    Processa uma consulta do cliente.

    Args:
        query: Consulta do cliente
        account_id: ID da conta do cliente
        use_memory: Se deve usar memória

    Returns:
        Resultado do processamento
    """
    # Criar agentes
    agents = create_customer_service_agents(account_id)

    # Criar tarefas
    tasks = create_customer_service_tasks(agents, query, account_id)

    # Criar crew
    crew = create_crew(account_id, use_memory)
    crew.tasks = tasks

    # Executar crew
    result = crew.kickoff(
        inputs={
            "query": query,
            "account_id": account_id
        }
    )

    return {
        "query": query,
        "response": result,
        "account_id": account_id
    }


def main():
    """Função principal."""
    # Carregar variáveis de ambiente
    load_dotenv()

    # Analisar argumentos
    args = parse_args()

    # Determinar se deve usar memória
    use_memory = MEMORY_ENABLED and not args.no_memory

    # Se a consulta foi fornecida como argumento, processá-la
    if args.query:
        result = process_query(args.query, args.account_id, use_memory)
        print(f"\nResposta para '{args.query}':\n{result['response']}")
        return

    # Caso contrário, iniciar um loop interativo
    print(f"Bem-vindo ao teste de integração do CrewAI com Qdrant para {args.account_id}")
    print("Digite 'sair' para encerrar")

    while True:
        # Obter consulta do usuário
        query = input("\nPergunta do cliente: ")

        if query.lower() in ["sair", "exit", "quit"]:
            break

        # Processar a consulta
        print("\nProcessando...")
        result = process_query(query, args.account_id, use_memory)

        # Exibir a resposta
        print(f"\nResposta do agente:\n{result['response']}")

    print("Obrigado por usar o teste de integração do CrewAI com Qdrant!")


if __name__ == "__main__":
    main()
