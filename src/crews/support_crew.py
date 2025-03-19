"""
Crew funcional de Suporte para a arquitetura hub-and-spoke.

Esta crew é especializada em processar mensagens relacionadas a suporte,
dúvidas técnicas, problemas com produtos e solicitações de ajuda.
"""

import logging
from typing import Dict, List, Any, Optional

from crewai import Agent, Task

from src.crews.functional_crew import FunctionalCrew
from src.agents.adaptable.support_agent import SupportAgent
from src.core.domain import DomainManager
from src.plugins.plugin_manager import PluginManager

logger = logging.getLogger(__name__)


class SupportCrew(FunctionalCrew):
    """
    Crew funcional de Suporte.
    
    Esta crew é especializada em processar mensagens relacionadas a suporte,
    dúvidas técnicas, problemas com produtos e solicitações de ajuda.
    """
    
    def __init__(self, **kwargs):
        """
        Inicializa a crew de suporte.
        
        Args:
            **kwargs: Argumentos adicionais para a classe base
        """
        # Inicializa os gerenciadores de domínio e plugins
        self.domain_manager = kwargs.pop('domain_manager', DomainManager())
        self.plugin_manager = kwargs.pop('plugin_manager', PluginManager(config={}))
        
        # Inicializa a classe base
        super().__init__(crew_type="support", **kwargs)
    
    def _create_agents(self) -> List[Agent]:
        """
        Cria os agentes necessários para a crew de suporte.
        
        Returns:
            List[Agent]: Lista de agentes
        """
        # Agente principal de suporte (adaptável ao domínio)
        agent_config = {
            "function_type": "support",
            "role": "Especialista em Suporte",
            "goal": "Resolver problemas e dúvidas dos clientes com eficiência e empatia",
            "backstory": """Você é um especialista em suporte com amplo conhecimento sobre 
            os produtos da empresa e como resolver problemas comuns. Seu objetivo é 
            ajudar os clientes a solucionar suas dúvidas e problemas de forma rápida e eficaz.""",
            "additional_tools": self.additional_tools
        }
        
        support_agent = SupportAgent(
            agent_config=agent_config,
            memory_system=self.memory_system,
            data_proxy_agent=self.data_service_hub.get_data_proxy_agent(),
            domain_manager=self.domain_manager,
            plugin_manager=self.plugin_manager
        )
        
        # Agente de diagnóstico de problemas
        troubleshooting_agent = Agent(
            role="Especialista em Diagnóstico de Problemas",
            goal="Identificar a causa raiz dos problemas relatados pelos clientes",
            backstory="""Você é especializado em analisar problemas relatados pelos clientes
            e identificar suas causas raiz. Você conhece profundamente os produtos da empresa
            e os problemas mais comuns que podem ocorrer.""",
            tools=[self.data_service_hub.get_data_proxy_agent()],
            verbose=True
        )
        
        # Agente de base de conhecimento
        knowledge_base_agent = Agent(
            role="Especialista em Base de Conhecimento",
            goal="Fornecer informações precisas e detalhadas da base de conhecimento",
            backstory="""Você tem acesso à base de conhecimento completa da empresa.
            Seu objetivo é fornecer informações precisas e detalhadas para ajudar
            a resolver problemas e responder a dúvidas técnicas.""",
            tools=[self.data_service_hub.get_data_proxy_agent()],
            verbose=True
        )
        
        return [support_agent, troubleshooting_agent, knowledge_base_agent]
    
    def _create_tasks(self) -> List[Task]:
        """
        Cria as tarefas necessárias para a crew de suporte.
        
        Returns:
            List[Task]: Lista de tarefas
        """
        # Tarefa para analisar a intenção da mensagem
        analyze_intent_task = Task(
            description="""
            Analise a mensagem do cliente e identifique a intenção principal relacionada a suporte.
            
            Possíveis intenções:
            - Problema com produto
            - Dúvida técnica
            - Reclamação
            - Solicitação de informação
            - Acompanhamento de caso
            - Feedback
            
            Retorne a intenção identificada e o nível de confiança.
            """,
            expected_output="""
            {
                "intent": "nome_da_intencao",
                "confidence": 0.95,
                "entities": [
                    {"type": "produto", "value": "nome_do_produto"},
                    {"type": "problema", "value": "descricao_do_problema"}
                ]
            }
            """,
            agent=self.agents[0]  # Support Agent
        )
        
        # Tarefa para diagnóstico de problemas
        troubleshooting_task = Task(
            description="""
            Com base na intenção e entidades identificadas, realize um diagnóstico
            do problema relatado pelo cliente.
            
            Considere:
            - Problemas comuns com o produto mencionado
            - Possíveis causas do problema descrito
            - Soluções conhecidas para problemas similares
            
            Retorne um diagnóstico detalhado com possíveis causas e soluções.
            """,
            expected_output="""
            {
                "problem_analysis": {
                    "product": "Nome do Produto",
                    "reported_issue": "Descrição do problema relatado",
                    "possible_causes": [
                        {"cause": "Causa 1", "probability": "Alta"},
                        {"cause": "Causa 2", "probability": "Média"}
                    ],
                    "recommended_solutions": [
                        {"solution": "Solução 1", "difficulty": "Fácil"},
                        {"solution": "Solução 2", "difficulty": "Média"}
                    ]
                }
            }
            """,
            agent=self.agents[1]  # Troubleshooting Agent
        )
        
        # Tarefa para buscar informações na base de conhecimento
        knowledge_base_task = Task(
            description="""
            Busque informações relevantes na base de conhecimento para ajudar
            a resolver o problema ou responder à dúvida do cliente.
            
            Considere:
            - Artigos da base de conhecimento relacionados ao problema
            - Tutoriais e guias relevantes
            - FAQs relacionadas
            - Documentação técnica aplicável
            
            Retorne as informações mais relevantes da base de conhecimento.
            """,
            expected_output="""
            {
                "knowledge_base_results": [
                    {
                        "title": "Título do Artigo",
                        "summary": "Resumo do conteúdo",
                        "relevance": 0.95,
                        "content": "Conteúdo principal do artigo",
                        "url": "url_do_artigo"
                    }
                ]
            }
            """,
            agent=self.agents[2]  # Knowledge Base Agent
        )
        
        # Tarefa para gerar resposta final
        generate_response_task = Task(
            description="""
            Com base no diagnóstico do problema e nas informações da base de conhecimento,
            gere uma resposta completa e útil para o cliente.
            
            A resposta deve:
            - Ser empática e compreensiva
            - Reconhecer o problema relatado
            - Fornecer explicações claras sobre as possíveis causas
            - Oferecer soluções práticas e passo a passo
            - Incluir links ou referências para recursos adicionais
            - Oferecer assistência adicional, se necessário
            
            Use uma linguagem clara, amigável e profissional.
            """,
            expected_output="""
            {
                "response": "Texto da resposta ao cliente",
                "suggested_actions": [
                    {"type": "link", "text": "Ver artigo completo", "url": "url_do_artigo"},
                    {"type": "button", "text": "Abrir ticket de suporte"}
                ]
            }
            """,
            agent=self.agents[0]  # Support Agent
        )
        
        return [analyze_intent_task, troubleshooting_task, knowledge_base_task, generate_response_task]
    
    def _get_process_type(self) -> str:
        """
        Obtém o tipo de processamento da crew.
        
        Returns:
            str: Tipo de processamento
        """
        # Usa processamento sequencial para garantir que as tarefas sejam executadas na ordem correta
        return "sequential"
