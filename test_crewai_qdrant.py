#!/usr/bin/env python
"""
Script simplificado para testar a integração do CrewAI com o Qdrant.
"""

import os
import asyncio
from typing import List, Dict, Any
from crewai import Agent, Task, Crew
from qdrant_client import QdrantClient
from qdrant_client.http import models
from openai import OpenAI

# Importar o serviço de vetores existente
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


def create_crew_with_qdrant_data(query: str, business_rules: List[Dict[str, Any]], company_metadata: Dict[str, Any]) -> Crew:
    """
    Cria uma crew com dados do Qdrant.

    Args:
        query: A consulta do usuário
        business_rules: Lista de regras de negócio
        company_metadata: Metadados da empresa

    Returns:
        Crew criada
    """
    # Formatar regras de negócio para o prompt
    rules_text = ""
    for i, rule in enumerate(business_rules, 1):
        rule_type = "[PROMOÇÃO TEMPORÁRIA]" if rule.get("is_temporary", False) else "[REGRA PERMANENTE]"
        rules_text += f"{i}. {rule_type} {rule.get('text', '')}\n"

    # Formatar metadados da empresa para o prompt
    company_text = f"""
    Nome da empresa: {company_metadata.get('company_name', 'Sandra Cosméticos')}
    Saudação oficial: {company_metadata.get('greeting_message', 'Olá, como posso ajudar?')}
    Descrição: {company_metadata.get('text', '')}
    """

    # Criar agente de análise
    analysis_agent = Agent(
        role="Analista de Regras de Negócio",
        goal="Analisar regras de negócio para fornecer informações precisas",
        backstory="""
        Você é um analista especializado em interpretar regras de negócio e políticas da empresa.
        Sua habilidade está em entender as nuances das regras e extrair as informações mais
        relevantes para o contexto atual.
        """,
        verbose=True
    )

    # Criar agente de atendimento ao cliente
    customer_service_agent = Agent(
        role="Atendente de Suporte ao Cliente",
        goal="Fornecer respostas precisas e amigáveis aos clientes",
        backstory="""
        Você é um atendente de suporte ao cliente da Sandra Cosméticos.
        Sua missão é fornecer respostas precisas, amigáveis e úteis aos clientes,
        com base nas regras de negócio e informações da empresa.
        """,
        verbose=True
    )

    # Criar tarefa de análise
    analysis_task = Task(
        description=f"""
        Analise as seguintes regras de negócio e identifique as mais relevantes para a consulta: "{query}"

        Regras de negócio:
        {rules_text}

        Informações da empresa:
        {company_text}

        Priorize regras temporárias (promoções) quando a consulta for sobre promoções.
        """,
        agent=analysis_agent,
        expected_output="Uma análise detalhada das regras de negócio mais relevantes para a consulta."
    )

    # Criar tarefa de atendimento ao cliente
    customer_service_task = Task(
        description=f"""
        Gere uma resposta amigável e precisa para o cliente com base na análise das regras de negócio.

        Consulta do cliente: "{query}"

        Informações da empresa:
        {company_text}

        Use a saudação oficial da empresa e responda à consulta do cliente com base nas regras de negócio analisadas.
        Mencione datas de validade de promoções quando disponíveis.
        """,
        agent=customer_service_agent,
        expected_output="Uma resposta completa e bem formatada para o cliente."
    )

    # Criar crew
    crew = Crew(
        agents=[analysis_agent, customer_service_agent],
        tasks=[analysis_task, customer_service_task],
        verbose=True
    )

    return crew


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

    print(f"Encontradas {len(business_rules)} regras de negócio relevantes")
    print(f"Metadados da empresa: {company_metadata.get('company_name')}")

    # Criar crew
    crew = create_crew_with_qdrant_data(query, business_rules, company_metadata)

    # Executar crew
    result = crew.kickoff()

    return {
        "query": query,
        "response": result,
        "account_id": account_id
    }


def main():
    """Função principal."""
    # Consulta de teste
    query = "Vocês têm alguma promoção de shampoo?"
    account_id = "account_1"

    print(f"Processando consulta: '{query}' para a conta: '{account_id}'")

    # Processar consulta
    result = asyncio.run(process_query(query, account_id))

    # Exibir resultado
    print(f"\nResposta para '{query}':\n{result['response']}")


if __name__ == "__main__":
    main()
