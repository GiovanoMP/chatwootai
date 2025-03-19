"""
Crew funcional de Agendamentos para a arquitetura hub-and-spoke.

Esta crew é especializada em processar mensagens relacionadas a agendamentos,
consultas, reservas e gerenciamento de compromissos.
"""

import logging
from typing import Dict, List, Any, Optional

from crewai import Agent, Task

from src.crews.functional_crew import FunctionalCrew
from src.agents.adaptable.scheduling_agent import SchedulingAgent
from src.core.domain import DomainManager
from src.plugins.plugin_manager import PluginManager

logger = logging.getLogger(__name__)


class SchedulingCrew(FunctionalCrew):
    """
    Crew funcional de Agendamentos.
    
    Esta crew é especializada em processar mensagens relacionadas a agendamentos,
    consultas, reservas e gerenciamento de compromissos.
    """
    
    def __init__(self, **kwargs):
        """
        Inicializa a crew de agendamentos.
        
        Args:
            **kwargs: Argumentos adicionais para a classe base
        """
        # Inicializa os gerenciadores de domínio e plugins
        self.domain_manager = kwargs.pop('domain_manager', DomainManager())
        self.plugin_manager = kwargs.pop('plugin_manager', PluginManager(config={}))
        
        # Inicializa a classe base
        super().__init__(crew_type="scheduling", **kwargs)
    
    def _create_agents(self) -> List[Agent]:
        """
        Cria os agentes necessários para a crew de agendamentos.
        
        Returns:
            List[Agent]: Lista de agentes
        """
        # Agente principal de agendamentos (adaptável ao domínio)
        agent_config = {
            "function_type": "scheduling",
            "role": "Especialista em Agendamentos",
            "goal": "Gerenciar agendamentos e reservas de forma eficiente e conveniente",
            "backstory": """Você é um especialista em agendamentos com amplo conhecimento sobre 
            os serviços da empresa e disponibilidade de horários. Seu objetivo é ajudar os 
            clientes a agendar consultas, serviços ou reservas de forma rápida e conveniente.""",
            "additional_tools": self.additional_tools
        }
        
        scheduling_agent = SchedulingAgent(
            agent_config=agent_config,
            memory_system=self.memory_system,
            vector_tool=self.vector_tool,
            db_tool=self.db_tool,
            cache_tool=self.cache_tool,
            domain_manager=self.domain_manager,
            plugin_manager=self.plugin_manager
        )
        
        # Agente de disponibilidade
        availability_agent = Agent(
            role="Especialista em Disponibilidade",
            goal="Verificar e gerenciar a disponibilidade de horários e recursos",
            backstory="""Você é especializado em verificar a disponibilidade de horários,
            profissionais e recursos. Seu objetivo é encontrar os melhores horários
            disponíveis que atendam às necessidades dos clientes.""",
            tools=[self.db_tool, self.cache_tool],
            verbose=True
        )
        
        # Agente de confirmação e lembretes
        confirmation_agent = Agent(
            role="Especialista em Confirmações e Lembretes",
            goal="Gerenciar confirmações, cancelamentos e lembretes de agendamentos",
            backstory="""Você é responsável por gerenciar confirmações, cancelamentos
            e lembretes de agendamentos. Seu objetivo é garantir que os clientes
            estejam cientes de seus compromissos e possam gerenciá-los facilmente.""",
            tools=[self.db_tool, self.cache_tool],
            verbose=True
        )
        
        return [scheduling_agent, availability_agent, confirmation_agent]
    
    def _create_tasks(self) -> List[Task]:
        """
        Cria as tarefas necessárias para a crew de agendamentos.
        
        Returns:
            List[Task]: Lista de tarefas
        """
        # Tarefa para analisar a intenção da mensagem
        analyze_intent_task = Task(
            description="""
            Analise a mensagem do cliente e identifique a intenção principal relacionada a agendamentos.
            
            Possíveis intenções:
            - Novo agendamento
            - Verificação de disponibilidade
            - Alteração de agendamento
            - Cancelamento de agendamento
            - Confirmação de agendamento
            - Consulta de agendamentos existentes
            
            Retorne a intenção identificada e o nível de confiança.
            """,
            expected_output="""
            {
                "intent": "nome_da_intencao",
                "confidence": 0.95,
                "entities": [
                    {"type": "servico", "value": "nome_do_servico"},
                    {"type": "data", "value": "2023-12-15"},
                    {"type": "hora", "value": "14:30"}
                ]
            }
            """,
            agent=self.agents[0]  # Scheduling Agent
        )
        
        # Tarefa para verificar disponibilidade
        check_availability_task = Task(
            description="""
            Com base na intenção e entidades identificadas, verifique a disponibilidade
            para o serviço e período solicitados.
            
            Considere:
            - Disponibilidade de horários
            - Disponibilidade de profissionais
            - Duração do serviço
            - Requisitos especiais
            
            Retorne as opções de horários disponíveis.
            """,
            expected_output="""
            {
                "service": "Nome do Serviço",
                "duration": 60,
                "available_slots": [
                    {
                        "date": "2023-12-15",
                        "time": "14:30",
                        "professional": "Nome do Profissional",
                        "location": "Local"
                    },
                    {
                        "date": "2023-12-15",
                        "time": "16:00",
                        "professional": "Nome do Profissional",
                        "location": "Local"
                    }
                ]
            }
            """,
            agent=self.agents[1]  # Availability Agent
        )
        
        # Tarefa para processar agendamento
        process_scheduling_task = Task(
            description="""
            Com base na intenção do cliente e na disponibilidade verificada,
            processe o agendamento, alteração ou cancelamento conforme necessário.
            
            Para novos agendamentos:
            - Crie o registro de agendamento
            - Verifique informações do cliente
            - Confirme detalhes do serviço
            
            Para alterações:
            - Localize o agendamento existente
            - Verifique a viabilidade da alteração
            - Atualize o registro
            
            Para cancelamentos:
            - Localize o agendamento existente
            - Verifique a política de cancelamento
            - Processe o cancelamento
            
            Retorne o resultado da operação.
            """,
            expected_output="""
            {
                "operation": "tipo_de_operacao",
                "success": true,
                "appointment": {
                    "id": 123,
                    "customer_id": 456,
                    "service": "Nome do Serviço",
                    "date": "2023-12-15",
                    "time": "14:30",
                    "professional": "Nome do Profissional",
                    "location": "Local",
                    "status": "confirmado"
                }
            }
            """,
            agent=self.agents[0]  # Scheduling Agent
        )
        
        # Tarefa para gerenciar confirmações e lembretes
        manage_confirmations_task = Task(
            description="""
            Gerencie confirmações e lembretes para o agendamento processado.
            
            Considere:
            - Envio de confirmação imediata
            - Agendamento de lembretes futuros
            - Instruções especiais para o cliente
            - Informações adicionais relevantes
            
            Retorne as informações de confirmação e lembretes.
            """,
            expected_output="""
            {
                "confirmation": {
                    "message": "Texto da confirmação",
                    "sent": true,
                    "timestamp": "2023-12-01T10:30:00Z"
                },
                "reminders": [
                    {
                        "type": "24h_before",
                        "scheduled_time": "2023-12-14T14:30:00Z",
                        "message": "Texto do lembrete"
                    }
                ]
            }
            """,
            agent=self.agents[2]  # Confirmation Agent
        )
        
        # Tarefa para gerar resposta final
        generate_response_task = Task(
            description="""
            Com base nas informações do agendamento processado, gere uma resposta
            completa e clara para o cliente.
            
            A resposta deve:
            - Confirmar a ação realizada (agendamento, alteração, cancelamento)
            - Incluir todos os detalhes relevantes do agendamento
            - Fornecer instruções claras sobre próximos passos
            - Incluir informações sobre políticas relevantes
            - Oferecer assistência adicional, se necessário
            
            Use uma linguagem clara, amigável e profissional.
            """,
            expected_output="""
            {
                "response": "Texto da resposta ao cliente",
                "suggested_actions": [
                    {"type": "calendar", "text": "Adicionar ao calendário"},
                    {"type": "button", "text": "Confirmar agendamento"}
                ]
            }
            """,
            agent=self.agents[0]  # Scheduling Agent
        )
        
        return [analyze_intent_task, check_availability_task, process_scheduling_task, manage_confirmations_task, generate_response_task]
    
    def _get_process_type(self) -> str:
        """
        Obtém o tipo de processamento da crew.
        
        Returns:
            str: Tipo de processamento
        """
        # Usa processamento sequencial para garantir que as tarefas sejam executadas na ordem correta
        return "sequential"
