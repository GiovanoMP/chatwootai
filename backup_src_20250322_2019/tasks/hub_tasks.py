"""
Tasks para o Hub Crew.

Este módulo define as tasks específicas para o Hub Crew, que é responsável
por orquestrar a comunicação entre as crews de canal e as crews funcionais.
"""

import logging
from typing import Dict, Any, List, Optional
from crewai import Task
from crewai.agent import Agent

logger = logging.getLogger(__name__)


def create_message_routing_task(agent: Agent) -> Task:
    """
    Cria uma task para roteamento de mensagens.
    
    Esta task analisa a mensagem e determina qual crew funcional
    deve processá-la com base na intenção detectada.
    
    Args:
        agent: O agente responsável por executar a task
        
    Returns:
        Task: A task de roteamento de mensagens
    """
    return Task(
        description="""
        Analise a mensagem e determine qual crew funcional deve processá-la.
        
        Considere as seguintes crews funcionais:
        - sales: Vendas e promoções
        - support: Suporte técnico e resolução de problemas
        - info: Informações gerais sobre produtos e serviços
        - scheduling: Agendamentos e reservas
        
        Com base na intenção detectada e no conteúdo da mensagem,
        determine a crew mais adequada para processar a mensagem.
        
        Considere também:
        - Histórico da conversa
        - Perfil do cliente
        - Contexto do negócio
        """,
        expected_output="""
        {
            "target_crew": "Nome da crew funcional",
            "routing_confidence": 0.95,
            "alternative_crews": ["Crew alternativa 1", "Crew alternativa 2"],
            "routing_rationale": "Explicação detalhada do motivo da escolha",
            "special_instructions": "Instruções especiais para a crew funcional"
        }
        """,
        agent=agent,
        name="Roteamento de Mensagem para Crew Funcional"
    )


def create_context_enrichment_task(agent: Agent) -> Task:
    """
    Cria uma task para enriquecimento de contexto.
    
    Esta task adiciona informações contextuais à mensagem para
    facilitar o processamento pela crew funcional.
    
    Args:
        agent: O agente responsável por executar a task
        
    Returns:
        Task: A task de enriquecimento de contexto
    """
    return Task(
        description="""
        Enriqueça o contexto da mensagem com informações adicionais.
        
        Adicione as seguintes informações ao contexto:
        1. Informações do cliente (histórico, preferências, perfil)
        2. Contexto da conversa atual (tópicos, sentimento, entidades)
        3. Contexto do negócio (produtos relevantes, promoções ativas)
        4. Informações sazonais (feriados, eventos especiais)
        
        Utilize as ferramentas disponíveis (banco de dados, vetores, cache)
        para obter informações relevantes que possam ajudar no processamento.
        """,
        expected_output="""
        {
            "customer_info": {
                "id": "ID do cliente",
                "name": "Nome do cliente",
                "profile": "Perfil do cliente",
                "preferences": ["Preferência 1", "Preferência 2"],
                "interaction_history": ["Histórico 1", "Histórico 2"]
            },
            "conversation_context": {
                "current_topic": "Tópico atual",
                "previous_topics": ["Tópico anterior 1", "Tópico anterior 2"],
                "sentiment": "Sentimento detectado",
                "important_entities": ["Entidade 1", "Entidade 2"]
            },
            "business_context": {
                "relevant_products": ["Produto 1", "Produto 2"],
                "relevant_services": ["Serviço 1", "Serviço 2"],
                "active_promotions": ["Promoção 1", "Promoção 2"]
            },
            "seasonal_context": {
                "current_season": "Estação atual",
                "upcoming_holidays": ["Feriado 1", "Feriado 2"],
                "special_events": ["Evento 1", "Evento 2"]
            }
        }
        """,
        agent=agent,
        name="Enriquecimento de Contexto da Mensagem"
    )


def create_external_integration_task(agent: Agent) -> Task:
    """
    Cria uma task para integração com sistemas externos.
    
    Esta task consulta sistemas externos (ERP, CRM, etc.) para obter
    informações adicionais ou executar ações necessárias.
    
    Args:
        agent: O agente responsável por executar a task
        
    Returns:
        Task: A task de integração com sistemas externos
    """
    return Task(
        description="""
        Integre com sistemas externos para obter informações adicionais ou executar ações.
        
        Considere os seguintes sistemas:
        - ERP (Odoo): Produtos, estoque, pedidos
        - CRM: Informações do cliente, histórico de interações
        - Sistemas de agendamento: Disponibilidade, reservas
        - Bases de conhecimento: Artigos, FAQs, manuais
        
        Consulte os sistemas relevantes com base na intenção da mensagem
        e no contexto da conversa, e obtenha as informações necessárias
        para o processamento adequado.
        """,
        expected_output="""
        {
            "integration_results": {
                "erp_data": {
                    "products": ["Produto 1", "Produto 2"],
                    "inventory": {"Produto 1": 10, "Produto 2": 5},
                    "orders": ["Pedido 1", "Pedido 2"]
                },
                "crm_data": {
                    "customer_status": "Status do cliente",
                    "open_tickets": ["Ticket 1", "Ticket 2"],
                    "lifetime_value": 1000
                },
                "scheduling_data": {
                    "available_slots": ["Slot 1", "Slot 2"],
                    "booked_appointments": ["Agendamento 1", "Agendamento 2"]
                },
                "knowledge_base_data": {
                    "relevant_articles": ["Artigo 1", "Artigo 2"],
                    "faqs": ["FAQ 1", "FAQ 2"]
                }
            },
            "actions_performed": [
                {
                    "system": "Sistema afetado",
                    "action": "Ação executada",
                    "status": "Status da ação",
                    "details": "Detalhes adicionais"
                }
            ]
        }
        """,
        agent=agent,
        name="Integração com Sistemas Externos"
    )


def create_coordination_task(agent: Agent) -> Task:
    """
    Cria uma task para coordenação do processamento.
    
    Esta task coordena o fluxo de processamento, utilizando os resultados
    das tasks anteriores para determinar os próximos passos.
    
    Args:
        agent: O agente responsável por executar a task
        
    Returns:
        Task: A task de coordenação
    """
    return Task(
        description="""
        Coordene o processamento da mensagem, utilizando as informações de rota,
        contexto enriquecido e resultados de integração.
        
        Determine:
        - A crew funcional que deve processar a mensagem
        - Os parâmetros a serem passados para a crew funcional
        - As instruções específicas para o processamento
        - A prioridade e o tempo esperado de resposta
        
        Combine todas as informações obtidas nas tasks anteriores
        e prepare as instruções finais para o processamento.
        """,
        expected_output="""
        {
            "target_crew": "Nome da crew funcional",
            "processing_parameters": {
                "priority": "Alta/Média/Baixa",
                "special_instructions": "Instruções especiais",
                "expected_response_time": "Tempo esperado de resposta"
            },
            "message_metadata": {
                "processed_by_hub": true,
                "processing_timestamp": "Data e hora do processamento",
                "confidence_score": 0.95
            },
            "processing_context": {
                "customer_context": {},
                "business_context": {},
                "integration_results": {}
            }
        }
        """,
        agent=agent,
        name="Coordenação do Processamento de Mensagem"
    )


def create_hub_tasks(orchestrator_agent: Agent, context_manager_agent: Agent, integration_agent: Agent) -> List[Task]:
    """
    Cria todas as tasks necessárias para o Hub Crew.
    
    Args:
        orchestrator_agent: Agente orquestrador
        context_manager_agent: Agente de gerenciamento de contexto
        integration_agent: Agente de integração
        
    Returns:
        List[Task]: Lista de todas as tasks para o Hub Crew
    """
    tasks = [
        create_message_routing_task(orchestrator_agent),
        create_context_enrichment_task(context_manager_agent),
        create_external_integration_task(integration_agent),
        create_coordination_task(orchestrator_agent)
    ]
    
    return tasks
