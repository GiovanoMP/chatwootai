"""
Crew de teste para atendimento ao cliente.

Esta crew demonstra como usar o CrewAI para melhorar o atendimento ao cliente
usando agentes especializados e ferramentas personalizadas.
"""

from typing import Dict, Any
from crewai import Agent, Task, Crew, Process

from .tools import VectorSearchTool, RuleProcessorTool


class CustomerServiceCrew:
    """Crew de atendimento ao cliente."""
    
    def __init__(self, account_id: str = "account_1"):
        """
        Inicializa a crew de atendimento ao cliente.
        
        Args:
            account_id: ID da conta do cliente
        """
        self.account_id = account_id
        self.vector_search_tool = VectorSearchTool()
        self.rule_processor_tool = RuleProcessorTool()
        
        # Inicializar agentes
        self.data_agent = self._create_data_agent()
        self.rule_agent = self._create_rule_agent()
        self.customer_service_agent = self._create_customer_service_agent()
        
        # Inicializar tarefas
        self.search_task = self._create_search_task()
        self.process_task = self._create_process_task()
        self.response_task = self._create_response_task()
        
        # Inicializar crew
        self.crew = self._create_crew()
    
    def _create_data_agent(self) -> Agent:
        """
        Cria o agente de busca de dados.
        
        Returns:
            Agente de busca de dados
        """
        return Agent(
            role="Especialista em Busca de Dados",
            goal="Encontrar todas as informações relevantes no banco de dados vetorial",
            backstory="""
            Você é um especialista em buscar informações precisas no banco de dados vetorial Qdrant.
            Sua missão é encontrar todas as regras de negócio, documentos de suporte e metadados da empresa
            que sejam relevantes para a consulta do usuário.
            """,
            verbose=True,
            allow_delegation=False,
            tools=[self.vector_search_tool],
        )
    
    def _create_rule_agent(self) -> Agent:
        """
        Cria o agente de processamento de regras.
        
        Returns:
            Agente de processamento de regras
        """
        return Agent(
            role="Especialista em Regras de Negócio",
            goal="Interpretar e priorizar regras de negócio relevantes para a consulta",
            backstory="""
            Você é um especialista em regras de negócio e políticas da empresa.
            Sua missão é analisar as regras encontradas e identificar as mais relevantes para a consulta do usuário,
            priorizando regras temporárias (promoções) quando apropriado.
            """,
            verbose=True,
            allow_delegation=False,
            tools=[self.rule_processor_tool],
        )
    
    def _create_customer_service_agent(self) -> Agent:
        """
        Cria o agente de atendimento ao cliente.
        
        Returns:
            Agente de atendimento ao cliente
        """
        return Agent(
            role="Atendente de Suporte ao Cliente",
            goal="Fornecer respostas precisas e amigáveis aos clientes",
            backstory="""
            Você é um atendente de suporte ao cliente da Sandra Cosméticos.
            Sua missão é fornecer respostas precisas, amigáveis e úteis aos clientes,
            com base nas regras de negócio e informações da empresa.
            Você sempre prioriza as regras temporárias (promoções) e menciona datas de validade quando disponíveis.
            """,
            verbose=True,
            allow_delegation=False,
        )
    
    def _create_search_task(self) -> Task:
        """
        Cria a tarefa de busca de dados.
        
        Returns:
            Tarefa de busca de dados
        """
        return Task(
            description="""
            Buscar todas as informações relevantes para a consulta do usuário.
            
            1. Buscar metadados da empresa para contextualização
            2. Buscar regras de negócio relevantes para a consulta
            3. Buscar documentos de suporte relevantes para a consulta
            
            Retorne todas as informações encontradas de forma organizada.
            """,
            agent=self.data_agent,
            expected_output="""
            Um relatório detalhado contendo:
            1. Metadados da empresa (nome, saudação, etc.)
            2. Lista de regras de negócio relevantes, com prioridade para regras temporárias
            3. Lista de documentos de suporte relevantes
            """,
        )
    
    def _create_process_task(self) -> Task:
        """
        Cria a tarefa de processamento de regras.
        
        Returns:
            Tarefa de processamento de regras
        """
        return Task(
            description="""
            Analisar as regras de negócio encontradas e identificar as mais relevantes para a consulta do usuário.
            
            1. Processar as regras de negócio encontradas
            2. Priorizar regras temporárias (promoções) quando a consulta for sobre promoções
            3. Identificar conflitos entre regras e resolvê-los
            
            Retorne as regras mais relevantes, organizadas por prioridade.
            """,
            agent=self.rule_agent,
            expected_output="""
            Um relatório contendo:
            1. Lista de regras priorizadas, com explicação da relevância
            2. Identificação de regras temporárias (promoções) e suas datas de validade
            3. Resolução de conflitos entre regras, se houver
            """,
            context=[
                self.search_task
            ],
        )
    
    def _create_response_task(self) -> Task:
        """
        Cria a tarefa de resposta ao cliente.
        
        Returns:
            Tarefa de resposta ao cliente
        """
        return Task(
            description="""
            Gerar uma resposta amigável e precisa para o cliente com base nas regras de negócio e informações da empresa.
            
            1. Usar a saudação oficial da empresa
            2. Responder à consulta do cliente com base nas regras de negócio priorizadas
            3. Mencionar datas de validade de promoções quando disponíveis
            4. Manter um tom amigável e prestativo
            
            Retorne uma resposta completa e bem formatada.
            """,
            agent=self.customer_service_agent,
            expected_output="""
            Uma resposta completa e bem formatada para o cliente, incluindo:
            1. Saudação oficial da empresa
            2. Resposta à consulta com base nas regras de negócio
            3. Menção a datas de validade de promoções, quando aplicável
            4. Fechamento amigável
            """,
            context=[
                self.search_task,
                self.process_task
            ],
        )
    
    def _create_crew(self) -> Crew:
        """
        Cria a crew de atendimento ao cliente.
        
        Returns:
            Crew de atendimento ao cliente
        """
        return Crew(
            agents=[
                self.data_agent,
                self.rule_agent,
                self.customer_service_agent
            ],
            tasks=[
                self.search_task,
                self.process_task,
                self.response_task
            ],
            process=Process.sequential,
            verbose=True,
        )
    
    def process_query(self, query: str) -> Dict[str, Any]:
        """
        Processa uma consulta do usuário.
        
        Args:
            query: Consulta do usuário
            
        Returns:
            Resultado do processamento
        """
        result = self.crew.kickoff(
            inputs={
                "query": query,
                "account_id": self.account_id
            }
        )
        
        return {
            "query": query,
            "response": result,
            "account_id": self.account_id
        }
