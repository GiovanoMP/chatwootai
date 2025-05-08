#!/usr/bin/env python3
"""
WhatsAppCrew para o ChatwootAI

Este módulo implementa a crew específica para o canal WhatsApp,
otimizada para as particularidades deste canal.
"""

import logging
from typing import Dict, Any, List, Optional

from crewai import Agent, Task
from src.core.crews.base_crew import BaseCrew

# Configurar logging
logger = logging.getLogger(__name__)

class WhatsAppCrew(BaseCrew):
    """
    Crew específica para o canal WhatsApp.
    
    Esta classe implementa uma crew otimizada para processar mensagens
    do WhatsApp, considerando suas particularidades como limitações de
    formatação, suporte a emojis, etc.
    """
    
    def __init__(self, config: Dict[str, Any], domain_name: str, account_id: str):
        """
        Inicializa a crew de WhatsApp.
        
        Args:
            config: Configuração da crew
            domain_name: Nome do domínio
            account_id: ID da conta
        """
        # Atualizar metadados antes de chamar o construtor da classe pai
        self.metadata = {
            "domain_name": domain_name,
            "account_id": account_id,
            "type": "whatsapp",
            "channel": "whatsapp"
        }
        
        # Chamar o construtor da classe pai
        super().__init__(config, domain_name, account_id)
        
        logger.info(f"WhatsAppCrew inicializada para {domain_name}/{account_id}")
    
    def _create_agents(self) -> List[Agent]:
        """
        Cria os agentes específicos para WhatsApp.
        
        Returns:
            Lista de agentes
        """
        agents = []
        
        # Configurações comuns para todos os canais
        common_config = self.config.get("customer_service", {})
        
        # Configurações específicas para WhatsApp
        whatsapp_config = self.config.get("channels", {}).get("whatsapp", {})
        
        # Mesclar configurações, priorizando as específicas do WhatsApp
        agent_config = {**common_config, **whatsapp_config}
        
        # Estilo de comunicação
        communication_style = agent_config.get("communication_style", "friendly")
        
        # Uso de emojis
        emoji_usage = agent_config.get("emoji_usage", "moderate")
        
        # Mensagem de saudação
        greeting_message = agent_config.get("greeting_message", "Olá! Como posso ajudar?")
        
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
        
        logger.info(f"Criados {len(agents)} agentes para WhatsAppCrew")
        return agents
    
    def _create_intention_agent(self, greeting: str, style: str, emoji_usage: str) -> Agent:
        """
        Cria o agente de intenção otimizado para WhatsApp.
        
        Args:
            greeting: Mensagem de saudação
            style: Estilo de comunicação
            emoji_usage: Nível de uso de emojis
            
        Returns:
            Agente de intenção
        """
        # Backstory adaptado para WhatsApp
        backstory = f"""
        Você é um assistente especializado em atendimento via WhatsApp.
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
        # Backstory adaptado para busca de informações
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
        # Backstory adaptado para integração com Odoo
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
        Cria o agente de resposta otimizado para WhatsApp.
        
        Args:
            style: Estilo de comunicação
            emoji_usage: Nível de uso de emojis
            
        Returns:
            Agente de resposta
        """
        # Backstory adaptado para WhatsApp
        backstory = f"""
        Você é um especialista em comunicação via WhatsApp.
        Você utiliza um estilo de comunicação {style} e {emoji_usage} emojis.
        Sua função é gerar respostas claras e concisas, adaptadas para o formato do WhatsApp.
        
        Diretrizes para WhatsApp:
        - Mensagens curtas e diretas
        - Parágrafos pequenos
        - Evitar formatação complexa
        - Usar emojis com moderação
        - Evitar links muito longos
        """
        
        # Criar o agente
        agent = Agent(
            role="Agente de Resposta",
            goal="Gerar respostas claras e adaptadas para WhatsApp",
            backstory=backstory,
            verbose=True
        )
        
        return agent
    
    def _create_tasks(self) -> List[Task]:
        """
        Cria as tarefas para a crew de WhatsApp.
        
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
            description="Gere uma resposta clara e adaptada para WhatsApp",
            expected_output="Resposta final para o cliente",
            agent=self.agents[3],  # Agente de resposta
            context=[intention_task, search_task, mcp_task]
        )
        tasks.append(response_task)
        
        logger.info(f"Criadas {len(tasks)} tarefas para WhatsAppCrew")
        return tasks
    
    def _prepare_crew_input(self, message: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepara o input para a crew de WhatsApp.
        
        Args:
            message: Mensagem a ser processada
            context: Contexto da conversa
            
        Returns:
            Input para a crew
        """
        # Input base da classe pai
        crew_input = super()._prepare_crew_input(message, context)
        
        # Adicionar informações específicas para WhatsApp
        crew_input["channel"] = "whatsapp"
        crew_input["format"] = "whatsapp"
        
        # Adicionar configurações de estilo
        customer_service = self.config.get("customer_service", {})
        crew_input["communication_style"] = customer_service.get("communication_style", "friendly")
        crew_input["emoji_usage"] = customer_service.get("emoji_usage", "moderate")
        
        return crew_input
    
    def _process_result(self, result: Any) -> Dict[str, Any]:
        """
        Processa o resultado da crew de WhatsApp.
        
        Args:
            result: Resultado da crew
            
        Returns:
            Resultado processado
        """
        # Processamento base da classe pai
        processed_result = super()._process_result(result)
        
        # Adicionar informações específicas para WhatsApp
        processed_result["channel"] = "whatsapp"
        
        # Se houver conteúdo, garantir que está formatado para WhatsApp
        if "content" in processed_result:
            processed_result["content"] = self._format_for_whatsapp(processed_result["content"])
        
        return processed_result
    
    def _format_for_whatsapp(self, content: str) -> str:
        """
        Formata o conteúdo para WhatsApp.
        
        Args:
            content: Conteúdo a ser formatado
            
        Returns:
            Conteúdo formatado
        """
        # Implementação básica - pode ser expandida
        # Remover formatação Markdown complexa
        # Limitar tamanho de parágrafos
        # etc.
        
        return content
