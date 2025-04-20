#!/usr/bin/env python
"""
Teste simplificado da crew de atendimento ao cliente.

Este script demonstra como usar o CrewAI para processar consultas de clientes
usando agentes especializados e acessando o Qdrant diretamente.
"""

import asyncio
import argparse
from typing import List, Dict, Any
from crewai import Agent, Task, Crew, Process
from qdrant_client.http import models

from odoo_api.services.vector_service import get_vector_service


async def search_business_rules(query: str, account_id: str = "account_1", limit: int = 5) -> List[Dict[str, Any]]:
    """
    Busca regras de negócio no Qdrant.

    Args:
        query: A consulta do usuário
        account_id: ID da conta do cliente
        limit: Número máximo de resultados

    Returns:
        Lista de regras de negócio
    """
    print(f"Buscando regras de negócio para a consulta: '{query}'")

    # Inicializar o serviço de vetores
    vector_service = await get_vector_service()

    # Gerar embedding para a consulta
    query_embedding = await vector_service.generate_embedding(query)

    # Buscar regras de negócio relevantes
    search_results = vector_service.qdrant_client.search(
        collection_name="business_rules",
        query_vector=query_embedding,
        query_filter=models.Filter(
            must=[
                models.FieldCondition(
                    key="account_id",
                    match=models.MatchValue(
                        value=account_id
                    )
                )
            ]
        ),
        limit=limit
    )

    # Extrair informações relevantes
    results = []
    for hit in search_results:
        results.append({
            "text": hit.payload.get("text", ""),
            "score": hit.score,
            "id": hit.id,
            "is_temporary": hit.payload.get("is_temporary", False),
            "priority": hit.payload.get("priority", 3)
        })

    # Ordenar por prioridade (menor número = maior prioridade) e depois por score (maior = melhor)
    results.sort(key=lambda x: (x.get("priority", 3), -x.get("score", 0)))

    return results


async def get_company_metadata(account_id: str = "account_1") -> Dict[str, Any]:
    """
    Recupera os metadados da empresa.

    Args:
        account_id: ID da conta do cliente

    Returns:
        Metadados da empresa
    """
    print(f"Recuperando metadados da empresa para a conta: '{account_id}'")

    # Inicializar o serviço de vetores
    vector_service = await get_vector_service()

    try:
        # Buscar metadados da empresa usando scroll
        scroll_results = vector_service.qdrant_client.scroll(
            collection_name="company_metadata",
            scroll_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="account_id",
                        match=models.MatchValue(
                            value=account_id
                        )
                    )
                ]
            ),
            limit=1
        )

        if scroll_results and len(scroll_results) > 0 and scroll_results[0]:
            point = scroll_results[0][0]  # Primeiro ponto do primeiro batch
            return {
                "text": point.payload.get("text", ""),
                "company_name": point.payload.get("company_name", "Sandra Cosméticos"),
                "greeting_message": point.payload.get("greeting_message", "Olá, obrigada por entrar em contato com a Sandra Cosméticos! Como posso ajudar hoje?")
            }
    except Exception as e:
        print(f"Erro ao buscar metadados da empresa: {e}")

    # Valores padrão se não encontrar nada
    return {
        "text": "Comercializamos cosméticos online e presencialmente, nossos canais de venda são Instagram, Facebook, Mercado Livre e WhatsApp.",
        "company_name": "Sandra Cosméticos",
        "greeting_message": "Olá, obrigada por entrar em contato com a Sandra Cosméticos! Como posso ajudar hoje?"
    }


async def process_query(query: str, account_id: str = "account_1") -> Dict[str, Any]:
    """
    Processa uma consulta do usuário.

    Args:
        query: A consulta do usuário
        account_id: ID da conta do cliente

    Returns:
        Resultado do processamento
    """
    # Buscar informações relevantes
    business_rules = await search_business_rules(query, account_id)
    company_metadata = await get_company_metadata(account_id)

    # Criar a crew
    data_agent = Agent(
        role="Especialista em Dados",
        goal="Analisar e interpretar dados para fornecer informações precisas",
        backstory="""
        Você é um especialista em análise de dados com vasta experiência em interpretar
        informações de regras de negócio e políticas da empresa.
        """,
        verbose=True,
        allow_delegation=False,
    )

    customer_service_agent = Agent(
        role="Atendente de Suporte ao Cliente",
        goal="Fornecer respostas precisas e amigáveis aos clientes",
        backstory="""
        Você é um atendente de suporte ao cliente da Sandra Cosméticos.
        Sua missão é fornecer respostas precisas, amigáveis e úteis aos clientes,
        com base nas regras de negócio e informações da empresa.
        Você sempre prioriza as regras temporárias (promoções) e menciona datas de validade quando disponíveis.
        """,
        verbose=True,
        allow_delegation=False,
    )

    # Não precisamos mais do contexto como dicionário, pois incluímos as informações diretamente nas descrições das tarefas

    # Criar tarefas
    analyze_task = Task(
        description=f"""
        Analise as seguintes regras de negócio e identifique as mais relevantes para a consulta: "{query}".

        Regras de negócio:
        {[rule.get('text', '') for rule in business_rules]}

        Priorize regras temporárias (promoções) quando a consulta for sobre promoções.

        Informações da empresa:
        - Nome: {company_metadata.get('company_name', 'Sandra Cosméticos')}
        - Saudação: {company_metadata.get('greeting_message', 'Olá, como posso ajudar?')}
        - Descrição: {company_metadata.get('text', '')}
        """,
        agent=data_agent,
        expected_output="Uma análise detalhada das regras de negócio mais relevantes para a consulta."
    )

    response_task = Task(
        description=f"""
        Gere uma resposta amigável e precisa para o cliente com base nas regras de negócio e informações da empresa.

        Consulta do cliente: "{query}"

        Informações da empresa:
        - Nome: {company_metadata.get('company_name', 'Sandra Cosméticos')}
        - Saudação: {company_metadata.get('greeting_message', 'Olá, como posso ajudar?')}
        - Descrição: {company_metadata.get('text', '')}

        Use a saudação oficial da empresa e responda à consulta do cliente com base nas regras de negócio analisadas.
        Mencione datas de validade de promoções quando disponíveis.
        """,
        agent=customer_service_agent,
        expected_output="Uma resposta completa e bem formatada para o cliente.",
        context=[analyze_task.output]
    )

    # Criar a crew
    crew = Crew(
        agents=[data_agent, customer_service_agent],
        tasks=[analyze_task, response_task],
        process=Process.sequential,
        verbose=True,
    )

    # Executar a crew
    result = crew.kickoff()

    return {
        "query": query,
        "response": result,
        "account_id": account_id
    }


def main():
    """Função principal."""
    parser = argparse.ArgumentParser(description="Teste simplificado da crew de atendimento ao cliente")
    parser.add_argument("--account_id", type=str, default="account_1", help="ID da conta do cliente")
    parser.add_argument("--query", type=str, help="Consulta do usuário")
    args = parser.parse_args()

    # Se a consulta foi fornecida como argumento, processá-la
    if args.query:
        result = asyncio.run(process_query(args.query, args.account_id))
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
        result = asyncio.run(process_query(query, args.account_id))

        # Exibir a resposta
        print(f"\nResposta do agente:\n{result['response']}")

    print("Obrigado por usar o teste da crew de atendimento ao cliente!")


if __name__ == "__main__":
    main()
