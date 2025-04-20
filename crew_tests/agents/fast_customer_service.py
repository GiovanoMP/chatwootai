"""
Agentes de atendimento ao cliente otimizados para baixa latência usando GPT-4o mini.

Este módulo implementa uma versão otimizada dos agentes de atendimento ao cliente
com foco em respostas rápidas (menos de 3 segundos) e prevenção de alucinações.
"""

import os
import logging
from typing import Dict, List, Any, Optional
from crewai import Agent, Task, LLM

logger = logging.getLogger(__name__)

from ..tools import FastQdrantSearchTool


def create_fast_customer_service_agent(account_id: str) -> Agent:
    """
    Cria um único agente otimizado para atendimento ao cliente com baixa latência.

    Args:
        account_id: ID da conta do cliente

    Returns:
        Agente otimizado para atendimento ao cliente
    """
    # Criar ferramenta de busca vetorial otimizada
    qdrant_tool = FastQdrantSearchTool()

    # Configurar LLM com GPT-4o mini para baixa latência
    llm = LLM(
        model="gpt-4o-mini",  # Modelo mais rápido
        temperature=0.1,      # Temperatura baixa para reduzir criatividade e alucinações
        max_tokens=300,       # Limitar tamanho da resposta
        timeout=5,            # Timeout curto para garantir resposta rápida
        api_key=os.getenv("OPENAI_API_KEY")
    )

    # Agente único otimizado
    fast_agent = Agent(
        role="Atendente de Suporte ao Cliente",
        goal="Fornecer respostas rápidas, precisas e factuais baseadas APENAS nos dados do Qdrant",
        backstory="""
        Você é um atendente de suporte ao cliente eficiente e preciso.
        Sua função é fornecer respostas rápidas e precisas com base APENAS
        nas informações encontradas no Qdrant. Você NUNCA inventa informações
        e sempre indica quando não tem dados suficientes para responder.
        """,
        tools=[qdrant_tool],
        llm=llm,
        verbose=False,  # Desativar verbose para reduzir overhead
        allow_delegation=False  # Desativar delegação para reduzir latência
    )

    return fast_agent


def create_fast_customer_service_task(agent: Agent, query: str, account_id: str) -> Task:
    """
    Cria uma única tarefa otimizada para o agente de atendimento ao cliente.

    Args:
        agent: Agente de atendimento ao cliente
        query: Consulta do cliente
        account_id: ID da conta do cliente

    Returns:
        Tarefa otimizada
    """
    # Tarefa única otimizada
    fast_task = Task(
        description=f"""
        Responda à consulta do cliente: "{query}" usando APENAS dados do Qdrant.

        INSTRUÇÕES RÁPIDAS:
        1. Busque metadados da empresa: use fast_qdrant_search com collection_name="company_metadata", account_id="{account_id}"
        2. Busque regras relevantes: use fast_qdrant_search com collection_name="business_rules", account_id="{account_id}"
        3. Priorize regras temporárias (is_temporary=true) para consultas sobre promoções
        4. Responda APENAS com base nos dados encontrados
        5. Se não encontrar informações, diga claramente que não tem essa informação
        6. Seja breve e direto - limite sua resposta a 2-3 frases

        FORMATO DA RESPOSTA:
        [Saudação da empresa]
        [Resposta direta e concisa baseada apenas nos dados encontrados]
        """,
        agent=agent,
        expected_output="Resposta concisa baseada apenas nos dados do Qdrant"
    )

    return fast_task


def get_fast_response(query: str, account_id: str = "account_1") -> str:
    """
    Função de conveniência para obter uma resposta rápida para uma consulta.

    Args:
        query: Consulta do cliente
        account_id: ID da conta do cliente

    Returns:
        Resposta para a consulta
    """
    try:
        logger.info(f"Criando agente para account_id={account_id}")
        # Criar agente e tarefa
        agent = create_fast_customer_service_agent(account_id)
        logger.info("Agente criado com sucesso")

        logger.info(f"Criando tarefa para query='{query}'")
        task = create_fast_customer_service_task(agent, query, account_id)
        logger.info("Tarefa criada com sucesso")

        # Executar tarefa diretamente sem criar uma crew
        # Isso reduz o overhead de comunicação entre agentes
        logger.info("Executando tarefa...")
        result = task.execute()
        logger.info("Tarefa executada com sucesso")

        return result
    except Exception as e:
        logger.error(f"Erro em get_fast_response: {e}", exc_info=True)
        raise
