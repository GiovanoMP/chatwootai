"""
Crew funcional de Informações para a arquitetura hub-and-spoke.

Esta crew é especializada em processar mensagens relacionadas a informações gerais,
perguntas sobre a empresa, produtos, serviços e políticas.
"""

import logging
from typing import Dict, List, Any, Optional

from crewai import Agent, Task

from src.crews.functional_crew import FunctionalCrew
from src.core.domain import DomainManager
from src.plugins.plugin_manager import PluginManager

logger = logging.getLogger(__name__)


class InfoCrew(FunctionalCrew):
    """
    Crew funcional de Informações.
    
    Esta crew é especializada em processar mensagens relacionadas a informações gerais,
    perguntas sobre a empresa, produtos, serviços e políticas.
    """
    
    def __init__(self, **kwargs):
        """
        Inicializa a crew de informações.
        
        Args:
            **kwargs: Argumentos adicionais para a classe base
        """
        # Inicializa os gerenciadores de domínio e plugins
        self.domain_manager = kwargs.pop('domain_manager', DomainManager())
        self.plugin_manager = kwargs.pop('plugin_manager', PluginManager(config={}))
        
        # Inicializa a classe base
        super().__init__(crew_type="info", **kwargs)
    
    def _create_agents(self) -> List[Agent]:
        """
        Cria os agentes necessários para a crew de informações.
        
        Returns:
            List[Agent]: Lista de agentes
        """
        # Agente principal de informações
        info_agent = Agent(
            role="Especialista em Informações",
            goal="Fornecer informações precisas e completas sobre a empresa, produtos e serviços",
            backstory="""Você é um especialista em informações com conhecimento abrangente 
            sobre a empresa, seus produtos, serviços, políticas e procedimentos. Seu objetivo 
            é fornecer informações precisas e úteis para os clientes.""",
            tools=[self.data_service_hub.get_data_proxy_agent()] + self.additional_tools,
            verbose=True
        )
        
        # Agente de FAQ
        faq_agent = Agent(
            role="Especialista em Perguntas Frequentes",
            goal="Responder às perguntas mais comuns dos clientes de forma clara e concisa",
            backstory="""Você conhece todas as perguntas frequentes e suas respostas.
            Seu objetivo é fornecer respostas rápidas e precisas para as dúvidas mais comuns
            dos clientes.""",
            tools=[self.data_service_hub.get_data_proxy_agent()],
            verbose=True
        )
        
        # Agente de pesquisa de conteúdo
        content_search_agent = Agent(
            role="Especialista em Pesquisa de Conteúdo",
            goal="Encontrar informações relevantes em diversas fontes de conteúdo",
            backstory="""Você é especializado em pesquisar e encontrar informações relevantes
            em diversas fontes de conteúdo, como site, blog, redes sociais e materiais promocionais
            da empresa.""",
            tools=[self.data_service_hub.get_data_proxy_agent()],
            verbose=True
        )
        
        return [info_agent, faq_agent, content_search_agent]
    
    def _create_tasks(self) -> List[Task]:
        """
        Cria as tarefas necessárias para a crew de informações.
        
        Returns:
            List[Task]: Lista de tarefas
        """
        # Tarefa para analisar a intenção da mensagem
        analyze_intent_task = Task(
            description="""
            Analise a mensagem do cliente e identifique a intenção principal relacionada a informações.
            
            Possíveis intenções:
            - Pergunta sobre a empresa
            - Pergunta sobre produtos ou serviços
            - Pergunta sobre políticas
            - Pergunta sobre horários ou locais
            - Pergunta sobre eventos ou promoções
            - Pergunta sobre procedimentos
            
            Retorne a intenção identificada e o nível de confiança.
            """,
            expected_output="""
            {
                "intent": "nome_da_intencao",
                "confidence": 0.95,
                "entities": [
                    {"type": "topico", "value": "nome_do_topico"},
                    {"type": "subtopico", "value": "nome_do_subtopico"}
                ],
                "question_type": "tipo_de_pergunta"
            }
            """,
            agent=self.agents[0]  # Info Agent
        )
        
        # Tarefa para verificar se é uma pergunta frequente
        check_faq_task = Task(
            description="""
            Verifique se a pergunta do cliente corresponde a uma pergunta frequente (FAQ).
            
            Se for uma pergunta frequente, retorne a resposta padrão da FAQ.
            Caso contrário, indique que não é uma pergunta frequente.
            
            Use a base de conhecimento de FAQs para esta verificação.
            """,
            expected_output="""
            {
                "is_faq": true,
                "faq_match": {
                    "question": "Pergunta original da FAQ",
                    "answer": "Resposta padrão da FAQ",
                    "confidence": 0.95
                }
            }
            """,
            agent=self.agents[1]  # FAQ Agent
        )
        
        # Tarefa para buscar informações relevantes
        search_info_task = Task(
            description="""
            Busque informações relevantes para responder à pergunta do cliente.
            
            Considere:
            - Informações sobre a empresa
            - Detalhes sobre produtos ou serviços
            - Políticas e procedimentos
            - Conteúdo do site e blog
            - Materiais promocionais
            
            Retorne as informações mais relevantes encontradas.
            """,
            expected_output="""
            {
                "search_results": [
                    {
                        "source": "Nome da fonte",
                        "title": "Título do conteúdo",
                        "content": "Conteúdo relevante",
                        "relevance": 0.95,
                        "url": "url_do_conteudo"
                    }
                ]
            }
            """,
            agent=self.agents[2]  # Content Search Agent
        )
        
        # Tarefa para gerar resposta final
        generate_response_task = Task(
            description="""
            Com base nas informações coletadas, gere uma resposta completa e informativa para o cliente.
            
            A resposta deve:
            - Ser direta e responder à pergunta específica
            - Incluir informações relevantes e precisas
            - Ser clara e fácil de entender
            - Incluir links ou referências para mais informações, se aplicável
            - Manter um tom amigável e profissional
            
            Se a pergunta for uma FAQ, adapte a resposta padrão para torná-la mais personalizada.
            """,
            expected_output="""
            {
                "response": "Texto da resposta ao cliente",
                "suggested_actions": [
                    {"type": "link", "text": "Saiba mais", "url": "url_para_mais_informacoes"},
                    {"type": "button", "text": "Ver produtos relacionados"}
                ]
            }
            """,
            agent=self.agents[0]  # Info Agent
        )
        
        return [analyze_intent_task, check_faq_task, search_info_task, generate_response_task]
    
    def _get_process_type(self) -> str:
        """
        Obtém o tipo de processamento da crew.
        
        Returns:
            str: Tipo de processamento
        """
        # Usa processamento sequencial para garantir que as tarefas sejam executadas na ordem correta
        return "sequential"
