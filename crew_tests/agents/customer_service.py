"""
Agentes de atendimento ao cliente para o CrewAI.
"""

from typing import Dict, List, Any
from crewai import Agent, Task

from ..tools import QdrantMultiTenantSearchTool


def create_customer_service_agents(account_id: str) -> Dict[str, Agent]:
    """
    Cria agentes de atendimento ao cliente para uma conta específica.
    
    Args:
        account_id: ID da conta do cliente
        
    Returns:
        Dicionário com os agentes criados
    """
    # Criar ferramenta de busca vetorial
    qdrant_tool = QdrantMultiTenantSearchTool()
    
    # Agente de pesquisa
    research_agent = Agent(
        role="Especialista em Pesquisa",
        goal="Encontrar informações relevantes nas regras de negócio e metadados da empresa",
        backstory="""
        Você é um especialista em pesquisa com vasta experiência em analisar e encontrar 
        informações relevantes em documentos corporativos. Sua especialidade é encontrar 
        regras de negócio, políticas da empresa e informações sobre produtos.
        """,
        tools=[qdrant_tool],
        verbose=True
    )
    
    # Agente de análise
    analysis_agent = Agent(
        role="Analista de Regras de Negócio",
        goal="Analisar e interpretar regras de negócio para fornecer informações precisas",
        backstory="""
        Você é um analista especializado em interpretar regras de negócio e políticas da empresa.
        Sua habilidade está em entender as nuances das regras e extrair as informações mais 
        relevantes para o contexto atual.
        """,
        tools=[qdrant_tool],
        verbose=True
    )
    
    # Agente de atendimento ao cliente
    customer_service_agent = Agent(
        role="Atendente de Suporte ao Cliente",
        goal="Fornecer respostas precisas e amigáveis aos clientes",
        backstory="""
        Você é um atendente de suporte ao cliente experiente. Sua missão é fornecer 
        respostas precisas, amigáveis e úteis aos clientes, com base nas regras de 
        negócio e informações da empresa. Você sempre prioriza a satisfação do cliente 
        e busca resolver suas dúvidas de forma eficiente.
        """,
        verbose=True
    )
    
    return {
        "research": research_agent,
        "analysis": analysis_agent,
        "customer_service": customer_service_agent
    }


def create_customer_service_tasks(agents: Dict[str, Agent], query: str, account_id: str) -> List[Task]:
    """
    Cria tarefas para os agentes de atendimento ao cliente.
    
    Args:
        agents: Dicionário com os agentes
        query: Consulta do cliente
        account_id: ID da conta do cliente
        
    Returns:
        Lista de tarefas
    """
    # Tarefa de pesquisa
    research_task = Task(
        description=f"""
        Buscar informações relevantes para a consulta do cliente: "{query}"
        
        1. Busque metadados da empresa para contextualização
           - Use a ferramenta qdrant_multi_tenant_search com collection_name="company_metadata" e account_id="{account_id}"
        
        2. Busque regras de negócio relevantes para a consulta
           - Use a ferramenta qdrant_multi_tenant_search com collection_name="business_rules" e account_id="{account_id}"
           - Priorize regras temporárias (promoções) quando a consulta for sobre promoções
        
        3. Busque documentos de suporte relevantes para a consulta
           - Use a ferramenta qdrant_multi_tenant_search com collection_name="support_documents" e account_id="{account_id}"
        
        Retorne todas as informações encontradas de forma organizada.
        """,
        agent=agents["research"],
        expected_output="""
        Um relatório detalhado contendo:
        1. Metadados da empresa (nome, saudação, etc.)
        2. Lista de regras de negócio relevantes, com prioridade para regras temporárias
        3. Lista de documentos de suporte relevantes
        """
    )
    
    # Tarefa de análise
    analysis_task = Task(
        description=f"""
        Analisar as informações encontradas e identificar as mais relevantes para a consulta: "{query}"
        
        1. Analise as regras de negócio encontradas
           - Identifique as regras mais relevantes para a consulta
           - Priorize regras temporárias (promoções) quando a consulta for sobre promoções
           - Identifique conflitos entre regras e resolva-os
        
        2. Extraia informações importantes dos metadados da empresa
           - Nome da empresa, saudação oficial, etc.
        
        3. Identifique informações relevantes nos documentos de suporte
        
        Retorne uma análise detalhada das informações mais relevantes.
        """,
        agent=agents["analysis"],
        expected_output="""
        Uma análise detalhada contendo:
        1. Regras de negócio mais relevantes para a consulta
        2. Informações importantes da empresa
        3. Informações relevantes dos documentos de suporte
        """,
        context=[research_task.output]
    )
    
    # Tarefa de atendimento ao cliente
    customer_service_task = Task(
        description=f"""
        Gerar uma resposta amigável e precisa para o cliente com base na análise das informações.
        
        Consulta do cliente: "{query}"
        
        1. Use a saudação oficial da empresa
        2. Responda à consulta do cliente com base nas regras de negócio analisadas
        3. Mencione datas de validade de promoções quando disponíveis
        4. Mantenha um tom amigável e prestativo
        
        Retorne uma resposta completa e bem formatada.
        """,
        agent=agents["customer_service"],
        expected_output="""
        Uma resposta completa e bem formatada para o cliente, incluindo:
        1. Saudação oficial da empresa
        2. Resposta à consulta com base nas regras de negócio
        3. Menção a datas de validade de promoções, quando aplicável
        4. Fechamento amigável
        """,
        context=[analysis_task.output]
    )
    
    return [research_task, analysis_task, customer_service_task]
