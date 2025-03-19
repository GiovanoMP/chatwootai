"""
Crew funcional de Vendas para a arquitetura hub-and-spoke.

Esta crew é especializada em processar mensagens relacionadas a vendas,
produtos, preços, promoções e pedidos.
"""

import logging
from typing import Dict, List, Any, Optional

from crewai import Agent, Task

from src.crews.functional_crew import FunctionalCrew
from src.agents.adaptable.sales_agent import SalesAgent
from src.core.domain import DomainManager
from src.plugins.plugin_manager import PluginManager

logger = logging.getLogger(__name__)


class SalesCrew(FunctionalCrew):
    """
    Crew funcional de Vendas.
    
    Esta crew é especializada em processar mensagens relacionadas a vendas,
    produtos, preços, promoções e pedidos.
    """
    
    def __init__(self, **kwargs):
        """
        Inicializa a crew de vendas.
        
        Args:
            **kwargs: Argumentos adicionais para a classe base
        """
        # Inicializa os gerenciadores de domínio e plugins
        self.domain_manager = kwargs.pop('domain_manager', DomainManager())
        self.plugin_manager = kwargs.pop('plugin_manager', PluginManager(config={}))
        
        # Inicializa a classe base
        super().__init__(crew_type="sales", **kwargs)
    
    def _create_agents(self) -> List[Agent]:
        """
        Cria os agentes necessários para a crew de vendas.
        
        Returns:
            List[Agent]: Lista de agentes
        """
        # Agente principal de vendas (adaptável ao domínio)
        sales_agent = SalesAgent(
            agent_config={
                "function_type": "sales",
                "role": "Especialista em Vendas",
                "goal": "Ajudar clientes com informações sobre produtos, preços e realizar vendas",
                "backstory": """Você é um especialista em vendas com amplo conhecimento sobre 
                os produtos da empresa. Seu objetivo é ajudar os clientes a encontrar os 
                produtos ideais para suas necessidades e facilitar o processo de compra."""
            },
            memory_system=self.memory_system,
            vector_tool=self.vector_tool,
            db_tool=self.db_tool,
            cache_tool=self.cache_tool,
            domain_manager=self.domain_manager,
            plugin_manager=self.plugin_manager
        )
        
        # Agente de recomendação de produtos
        product_recommendation_agent = Agent(
            role="Especialista em Recomendação de Produtos",
            goal="Recomendar os melhores produtos para as necessidades do cliente",
            backstory="""Você é especializado em entender as necessidades dos clientes
            e recomendar os produtos mais adequados. Você conhece profundamente o catálogo
            de produtos e suas características.""",
            tools=[self.vector_tool, self.db_tool, self.cache_tool],
            verbose=True
        )
        
        # Agente de promoções e ofertas
        promotions_agent = Agent(
            role="Especialista em Promoções",
            goal="Informar sobre as melhores promoções e ofertas disponíveis",
            backstory="""Você conhece todas as promoções e ofertas especiais disponíveis.
            Seu objetivo é garantir que os clientes aproveitem as melhores oportunidades
            de economia em suas compras.""",
            tools=[self.db_tool, self.cache_tool],
            verbose=True
        )
        
        return [sales_agent, product_recommendation_agent, promotions_agent]
    
    def _create_tasks(self) -> List[Task]:
        """
        Cria as tarefas necessárias para a crew de vendas.
        
        Returns:
            List[Task]: Lista de tarefas
        """
        # Tarefa para analisar a intenção da mensagem
        analyze_intent_task = Task(
            description="""
            Analise a mensagem do cliente e identifique a intenção principal relacionada a vendas.
            
            Possíveis intenções:
            - Consulta sobre produtos
            - Consulta sobre preços
            - Consulta sobre disponibilidade
            - Consulta sobre promoções
            - Intenção de compra
            - Acompanhamento de pedido
            
            Retorne a intenção identificada e o nível de confiança.
            """,
            expected_output="""
            {
                "intent": "nome_da_intencao",
                "confidence": 0.95,
                "entities": [
                    {"type": "produto", "value": "nome_do_produto"},
                    {"type": "quantidade", "value": 2}
                ]
            }
            """,
            agent=self.agents[0]  # Sales Agent
        )
        
        # Tarefa para buscar informações de produtos
        product_info_task = Task(
            description="""
            Com base na intenção e entidades identificadas, busque informações
            detalhadas sobre os produtos mencionados ou relacionados.
            
            Retorne informações completas sobre os produtos, incluindo:
            - Nome
            - Descrição
            - Preço
            - Disponibilidade
            - Características principais
            - Benefícios
            """,
            expected_output="""
            {
                "products": [
                    {
                        "id": 123,
                        "name": "Nome do Produto",
                        "description": "Descrição detalhada",
                        "price": 99.90,
                        "available": true,
                        "stock_quantity": 50,
                        "features": ["Característica 1", "Característica 2"],
                        "benefits": ["Benefício 1", "Benefício 2"]
                    }
                ]
            }
            """,
            agent=self.agents[1]  # Product Recommendation Agent
        )
        
        # Tarefa para verificar promoções aplicáveis
        check_promotions_task = Task(
            description="""
            Verifique se há promoções ou ofertas especiais aplicáveis aos produtos
            identificados ou à intenção do cliente.
            
            Retorne informações sobre as promoções disponíveis, incluindo:
            - Nome da promoção
            - Descrição
            - Desconto ou benefício
            - Período de validade
            - Condições
            """,
            expected_output="""
            {
                "promotions": [
                    {
                        "name": "Nome da Promoção",
                        "description": "Descrição da promoção",
                        "discount": "20% de desconto",
                        "valid_until": "2023-12-31",
                        "conditions": "Condições aplicáveis"
                    }
                ]
            }
            """,
            agent=self.agents[2]  # Promotions Agent
        )
        
        # Tarefa para gerar resposta final
        generate_response_task = Task(
            description="""
            Com base nas informações coletadas sobre produtos e promoções,
            gere uma resposta completa e persuasiva para o cliente.
            
            A resposta deve:
            - Ser personalizada para o cliente
            - Abordar diretamente a intenção identificada
            - Incluir informações relevantes sobre produtos
            - Mencionar promoções aplicáveis
            - Incentivar a próxima etapa (compra, mais informações, etc.)
            
            Use uma linguagem amigável, profissional e persuasiva.
            """,
            expected_output="""
            {
                "response": "Texto da resposta ao cliente",
                "suggested_actions": [
                    {"type": "link", "text": "Ver produto", "url": "url_do_produto"},
                    {"type": "button", "text": "Adicionar ao carrinho"}
                ]
            }
            """,
            agent=self.agents[0]  # Sales Agent
        )
        
        return [analyze_intent_task, product_info_task, check_promotions_task, generate_response_task]
    
    def _get_process_type(self) -> str:
        """
        Obtém o tipo de processamento da crew.
        
        Returns:
            str: Tipo de processamento
        """
        # Usa processamento sequencial para garantir que as tarefas sejam executadas na ordem correta
        return "sequential"
