#!/usr/bin/env python3
"""
DefaultCrew para o ChatwootAI

Este módulo implementa a crew padrão para canais genéricos,
utilizada quando não há uma crew específica para o canal.
"""

import logging
from typing import Dict, Any, List, Optional

from crewai import Agent, Task
from src.core.crews.base_crew import BaseCrew

# Configurar logging
logger = logging.getLogger(__name__)

class DefaultCrew(BaseCrew):
    """
    Crew padrão para canais genéricos.
    
    Esta classe implementa uma crew genérica para processar mensagens
    de canais que não possuem uma implementação específica.
    """
    
    def __init__(self, config: Dict[str, Any], domain_name: str, account_id: str):
        """
        Inicializa a crew padrão.
        
        Args:
            config: Configuração da crew
            domain_name: Nome do domínio
            account_id: ID da conta
        """
        # Atualizar metadados antes de chamar o construtor da classe pai
        self.metadata = {
            "domain_name": domain_name,
            "account_id": account_id,
            "type": "default",
            "channel": "default"
        }
        
        # Chamar o construtor da classe pai
        super().__init__(config, domain_name, account_id)
        
        logger.info(f"DefaultCrew inicializada para {domain_name}/{account_id}")
    
    def _create_agents(self) -> List[Agent]:
        """
        Cria os agentes para a crew padrão.
        
        Returns:
            Lista de agentes
        """
        agents = []
        
        # Configurações comuns
        common_config = self.config.get("customer_service", {})
        
        # Estilo de comunicação
        communication_style = common_config.get("communication_style", "friendly")
        
        # Uso de emojis
        emoji_usage = common_config.get("emoji_usage", "moderate")
        
        # Mensagem de saudação
        greeting_message = common_config.get("greeting_message", "Olá! Como posso ajudar?")
        
        # Criar agente de intenção
        intention_agent = self._create_intention_agent(
            greeting=greeting_message,
            style=communication_style,
            emoji_usage=emoji_usage
        )
        agents.append(intention_agent)
        
        # Criar agente de busca vetorial
        vector_agent = self._create_vector_agent()
        agents.append(vector_agent)
        
        # Criar agente MCP
        mcp_agent = self._create_mcp_agent()
        agents.append(mcp_agent)
        
        # Criar agente de resposta
        response_agent = self._create_response_agent(
            style=communication_style,
            emoji_usage=emoji_usage
        )
        agents.append(response_agent)
        
        logger.info(f"Criados {len(agents)} agentes para DefaultCrew")
        return agents
    
    def _create_intention_agent(self, greeting: str, style: str, emoji_usage: str) -> Agent:
        """
        Cria o agente de intenção.
        
        Args:
            greeting: Mensagem de saudação
            style: Estilo de comunicação
            emoji_usage: Nível de uso de emojis
            
        Returns:
            Agente de intenção
        """
        # Backstory genérico
        backstory = f"""
        Você é um assistente especializado em atendimento ao cliente.
        Você utiliza um estilo de comunicação {style} e {emoji_usage} emojis.
        Sua função é entender a intenção do cliente e direcionar para o agente apropriado.
        """
        
        # Criar o agente
        agent = Agent(
            role="Agente de Intenção",
            goal="Identificar corretamente a intenção do cliente",
            backstory=backstory,
            verbose=True
        )
        
        return agent
    
    def _create_vector_agent(self) -> Agent:
        """
        Cria o agente de busca vetorial.
        
        Returns:
            Agente de busca vetorial
        """
        # Backstory genérico
        backstory = """
        Você é um especialista em encontrar informações relevantes na base de conhecimento.
        Sua função é buscar documentos, regras de negócio e informações que possam ajudar
        a responder às perguntas do cliente.
        """
        
        # Criar o agente
        agent = Agent(
            role="Agente de Busca Vetorial",
            goal="Encontrar informações relevantes na base de conhecimento",
            backstory=backstory,
            verbose=True
        )
        
        return agent
    
    def _create_mcp_agent(self) -> Agent:
        """
        Cria o agente MCP para integração com Odoo.
        
        Returns:
            Agente MCP
        """
        # Backstory genérico
        backstory = f"""
        Você é um especialista em integração com o sistema Odoo para o account_id {self.account_id}.
        Sua função é executar operações no Odoo quando necessário, como consultar produtos,
        verificar estoque, criar pedidos, etc.
        """
        
        # Criar o agente
        agent = Agent(
            role="Agente MCP",
            goal="Executar operações no sistema Odoo",
            backstory=backstory,
            verbose=True
        )
        
        return agent
    
    def _create_response_agent(self, style: str, emoji_usage: str) -> Agent:
        """
        Cria o agente de resposta.
        
        Args:
            style: Estilo de comunicação
            emoji_usage: Nível de uso de emojis
            
        Returns:
            Agente de resposta
        """
        # Backstory genérico
        backstory = f"""
        Você é um especialista em comunicação com clientes.
        Você utiliza um estilo de comunicação {style} e {emoji_usage} emojis.
        Sua função é gerar respostas claras e concisas para o cliente.
        """
        
        # Criar o agente
        agent = Agent(
            role="Agente de Resposta",
            goal="Gerar respostas claras e concisas",
            backstory=backstory,
            verbose=True
        )
        
        return agent
    
    def _create_tasks(self) -> List[Task]:
        """
        Cria as tarefas para a crew padrão.
        
        Returns:
            Lista de tarefas
        """
        tasks = []
        
        # Tarefa de identificação de intenção
        intention_task = Task(
            description="Identifique a intenção do cliente na mensagem",
            expected_output="Classificação da intenção do cliente",
            agent=self.agents[0]  # Agente de intenção
        )
        tasks.append(intention_task)
        
        # Tarefa de busca de informações
        search_task = Task(
            description="Busque informações relevantes na base de conhecimento",
            expected_output="Informações encontradas na base de conhecimento",
            agent=self.agents[1],  # Agente de busca vetorial
            context=[intention_task]
        )
        tasks.append(search_task)
        
        # Tarefa de integração com Odoo
        mcp_task = Task(
            description="Execute operações no Odoo se necessário",
            expected_output="Resultado das operações no Odoo",
            agent=self.agents[2],  # Agente MCP
            context=[intention_task, search_task]
        )
        tasks.append(mcp_task)
        
        # Tarefa de geração de resposta
        response_task = Task(
            description="Gere uma resposta clara e concisa para o cliente",
            expected_output="Resposta final para o cliente",
            agent=self.agents[3],  # Agente de resposta
            context=[intention_task, search_task, mcp_task]
        )
        tasks.append(response_task)
        
        logger.info(f"Criadas {len(tasks)} tarefas para DefaultCrew")
        return tasks
