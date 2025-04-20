"""
Agente otimizado para atendimento ao cliente com foco em baixa latência.

Este módulo implementa um agente otimizado para atendimento ao cliente
que utiliza a ferramenta OptimizedQdrantTool para buscar informações
no Qdrant com baixa latência.
"""

import os
import logging
from typing import Dict, Any
from crewai import Agent, Task, Crew, Process, LLM

logger = logging.getLogger(__name__)

from ..tools import OptimizedQdrantTool


def create_optimized_agent(account_id: str = "account_1") -> Agent:
    """
    Cria um agente otimizado para atendimento ao cliente.

    Args:
        account_id: ID da conta do cliente

    Returns:
        Agente otimizado para atendimento ao cliente
    """
    # Criar ferramenta otimizada
    qdrant_tool = OptimizedQdrantTool()

    # Configurar LLM com GPT-4o mini para baixa latência
    llm = LLM(
        model="gpt-4o-mini",  # Modelo mais rápido
        temperature=0.0,      # Temperatura zero para eliminar criatividade e alucinações
        max_tokens=150,       # Limitar tamanho da resposta ao mínimo necessário
        timeout=1.5,          # Timeout mais curto para garantir resposta rápida
        api_key=os.getenv("OPENAI_API_KEY")  # Usar a chave da API do OpenAI
    )

    # Criar agente otimizado
    agent = Agent(
        role="Especialista em Atendimento ao Cliente",
        goal="Fornecer respostas precisas, rápidas e factuais baseadas APENAS nos dados do Qdrant",
        backstory="""
        Você é um especialista em atendimento ao cliente altamente eficiente.
        Sua função é fornecer respostas rápidas e precisas com base APENAS
        nas informações encontradas no Qdrant. Você NUNCA inventa informações
        e sempre indica quando não tem dados suficientes para responder.
        Você é direto e conciso em suas respostas.
        """,
        tools=[qdrant_tool],
        llm=llm,
        verbose=False,  # Desativar verbose para reduzir overhead
        allow_delegation=False  # Desativar delegação para reduzir latência
    )

    return agent


def create_optimized_task(query: str, account_id: str = "account_1") -> Task:
    """
    Cria uma tarefa otimizada para o agente.

    Args:
        query: Consulta do cliente
        account_id: ID da conta do cliente

    Returns:
        Tarefa otimizada
    """
    # Criar agente
    agent = create_optimized_agent(account_id)

    # Criar tarefa
    task = Task(
        description=f"""
        Responda à consulta do cliente: "{query}" usando APENAS dados do Qdrant.

        INSTRUÇÕES RÁPIDAS:
        1. Busque metadados da empresa: use optimized_qdrant_search com collection_name="company_metadata", account_id="{account_id}"
        2. Busque regras relevantes: use optimized_qdrant_search com collection_name="business_rules", account_id="{account_id}"
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

    return task


def create_optimized_crew(query: str, account_id: str = "account_1") -> Crew:
    """
    Cria uma crew otimizada com um único agente.

    Args:
        query: Consulta do cliente
        account_id: ID da conta do cliente

    Returns:
        Crew otimizada
    """
    # Criar tarefa
    task = create_optimized_task(query, account_id)

    # Criar crew com um único agente
    # Configurada para máxima eficiência
    crew = Crew(
        agents=[task.agent],
        tasks=[task],
        process=Process.sequential,  # Processo sequencial para um único agente
        verbose=False,  # Desativar verbose para reduzir overhead
        memory=False    # Desativar memória para reduzir overhead
    )

    # Executar crew
    return crew.kickoff()


def get_optimized_response(query: str, account_id: str = "account_1") -> str:
    """
    Obtém uma resposta otimizada para uma consulta.

    Args:
        query: Consulta do cliente
        account_id: ID da conta do cliente

    Returns:
        Resposta otimizada
    """
    try:
        logger.info(f"Obtendo resposta otimizada para query='{query}', account_id='{account_id}'")

        # Executar tarefa diretamente
        logger.info("Executando tarefa otimizada")
        result = create_optimized_crew(query, account_id)
        logger.info("Tarefa executada com sucesso")

        return result
    except Exception as e:
        logger.error(f"Erro ao obter resposta otimizada: {e}", exc_info=True)
        raise
