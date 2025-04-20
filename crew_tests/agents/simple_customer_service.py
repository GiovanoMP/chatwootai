"""
Agente de atendimento ao cliente simplificado usando o decorador @tool.

Este módulo implementa uma versão simplificada do agente de atendimento ao cliente
com foco em respostas rápidas (menos de 3 segundos) e prevenção de alucinações.
"""

import os
import logging
from crewai import Agent, Task, LLM

logger = logging.getLogger(__name__)

from ..tools import busca_qdrant


def create_simple_customer_service_agent(account_id: str) -> Agent:
    """
    Cria um agente simplificado para atendimento ao cliente com baixa latência.

    Args:
        account_id: ID da conta do cliente

    Returns:
        Agente otimizado para atendimento ao cliente
    """
    # Configurar LLM com GPT-4o mini para baixa latência
    llm = LLM(
        model="gpt-4o-mini",  # Modelo mais rápido
        temperature=0.1,      # Temperatura baixa para reduzir criatividade e alucinações
        max_tokens=300,       # Limitar tamanho da resposta
        timeout=5,            # Timeout curto para garantir resposta rápida
        api_key=os.getenv("OPENAI_API_KEY")  # Usar a chave da API do OpenAI
    )

    # Agente único otimizado
    agent = Agent(
        role="Atendente de Suporte ao Cliente",
        goal="Fornecer respostas rápidas, precisas e factuais baseadas APENAS nos dados do Qdrant",
        backstory="""
        Você é um atendente de suporte ao cliente eficiente e preciso.
        Sua função é fornecer respostas rápidas e precisas com base APENAS
        nas informações encontradas no Qdrant. Você NUNCA inventa informações
        e sempre indica quando não tem dados suficientes para responder.
        """,
        tools=[busca_qdrant],
        llm=llm,
        verbose=False,  # Desativar verbose para reduzir overhead
        allow_delegation=False  # Desativar delegação para reduzir latência
    )

    return agent


def create_simple_customer_service_task(agent: Agent, query: str, account_id: str) -> Task:
    """
    Cria uma tarefa simplificada para o agente de atendimento ao cliente.

    Args:
        agent: Agente de atendimento ao cliente
        query: Consulta do cliente
        account_id: ID da conta do cliente

    Returns:
        Tarefa otimizada
    """
    # Tarefa única otimizada
    task = Task(
        description=f"""
        Responda à consulta do cliente: "{query}" usando APENAS dados do Qdrant.

        INSTRUÇÕES RÁPIDAS:
        1. Busque metadados da empresa: use busca_qdrant com collection_name="company_metadata", account_id="{account_id}"
        2. Busque regras relevantes: use busca_qdrant com collection_name="business_rules", account_id="{account_id}"
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


def get_simple_response(query: str, account_id: str = "account_1") -> str:
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
        agent = create_simple_customer_service_agent(account_id)
        logger.info("Agente criado com sucesso")

        logger.info(f"Criando tarefa para query='{query}'")
        task = create_simple_customer_service_task(agent, query, account_id)
        logger.info("Tarefa criada com sucesso")

        # Executar tarefa usando o agente diretamente
        # Isso reduz o overhead de comunicação entre agentes
        logger.info("Executando tarefa...")
        result = agent.run(task.description)
        logger.info("Tarefa executada com sucesso")

        return result
    except Exception as e:
        logger.error(f"Erro em get_simple_response: {e}", exc_info=True)
        raise
