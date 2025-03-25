"""
Crew funcional de Vendas para a arquitetura hub-and-spoke.

Esta crew é especializada em processar mensagens relacionadas a vendas,
produtos, preços, promoções e pedidos.
"""

import logging
from typing import Dict, List, Any, Optional

from crewai import Agent, Task

from src.crews.functional_crew import FunctionalCrew
from src.agents.specialized.sales_agent import SalesAgent
from src.core.domain import DomainManager
from src.plugins.core.plugin_manager import PluginManager

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
        # Inicializa o gerenciador de plugins
        self.plugin_manager = kwargs.pop('plugin_manager', PluginManager(config={}))
        
        # Inicializa a classe base com domain_manager
        # Note que o domain_manager agora é passado diretamente para a classe base
        super().__init__(crew_type="sales", **kwargs)
    
    def _create_agents(self) -> List[Agent]:
        """
        Cria os agentes necessários para a crew de vendas.
        
        Returns:
            List[Agent]: Lista de agentes
        """
        # Obtém as configurações do domínio ativo
        domain_config = self.domain_manager.get_active_domain_config()
        agent_config = domain_config.get("agents", {}).get("sales_agent", {})
        
        logger.info(f"Criando SalesAgent com configuração do domínio: {self.domain_manager.get_active_domain_name()}")
        
        # Agente principal de vendas (usando configurações do domínio)
        sales_agent = SalesAgent(
            agent_config=agent_config,
            memory_system=self.memory_system,
            data_proxy_agent=self.data_service_hub.get_data_proxy_agent(),
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
            tools=[],  # Por enquanto, deixamos sem ferramentas
            verbose=True
        )
        
        # Agente de promoções e ofertas
        promotions_agent = Agent(
            role="Especialista em Promoções",
            goal="Informar sobre as melhores promoções e ofertas disponíveis",
            backstory="""Você conhece todas as promoções e ofertas especiais disponíveis.
            Seu objetivo é garantir que os clientes aproveitem as melhores oportunidades
            de economia em suas compras.""",
            tools=[],  # Por enquanto, deixamos sem ferramentas
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
        
    def process(self, message: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa uma mensagem relacionada a vendas.
        
        Este método é chamado pelo HubCrew quando uma mensagem é roteada para a SalesCrew.
        Ele executa o fluxo completo de processamento da mensagem:
        1. Analisa a intenção do cliente
        2. Busca informações sobre produtos
        3. Verifica promoções aplicáveis
        4. Gera uma resposta personalizada
        
        Args:
            message: A mensagem normalizada a ser processada
            context: Contexto da conversa, incluindo histórico e metadados
            
        Returns:
            Dict[str, Any]: Resultado do processamento, incluindo a resposta para o cliente
        """
        logger.info(f"SalesCrew processando mensagem: {message.get('content', '')[:100]}...")
        
        # Adapta o contexto para incluir o domínio atual
        domain_info = self.domain_manager.get_active_domain_info()
        enriched_context = {**context, "domain": domain_info}
        
        # Cria os inputs para a execução da crew
        inputs = {
            "message": message,
            "context": enriched_context,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # Executa a crew com os inputs fornecidos
            result = self.crew.kickoff(inputs=inputs)
            
            # Extrai a resposta do resultado
            if isinstance(result, dict) and "response" in result:
                response_content = result["response"]
            else:
                # Se o último resultado for um dicionário com uma chave 'response'
                response_content = result
                
                # Tenta extrair do último resultado se for um dict
                if isinstance(result, dict):
                    for key in ["response", "content", "message", "answer"]:
                        if key in result:
                            response_content = result[key]
                            break
            
            # Formata a resposta final
            response = {
                "content": response_content if isinstance(response_content, str) 
                          else json.dumps(response_content, ensure_ascii=False),
                "type": "text",
                "timestamp": datetime.now().isoformat()
            }
            
            # Retorna o resultado completo
            return {
                "response": response,
                "processing_info": {
                    "crew_type": self.crew_type,
                    "domain": domain_info.get("name", "default"),
                    "processing_time": "N/A"  # Em uma implementação real, mediríamos o tempo
                }
            }
            
        except Exception as e:
            logger.error(f"Erro ao processar mensagem na SalesCrew: {str(e)}")
            
            # Retorna uma resposta de erro
            return {
                "response": {
                    "content": "Desculpe, não foi possível processar sua solicitação no momento. Por favor, tente novamente mais tarde.",
                    "type": "text",
                    "timestamp": datetime.now().isoformat()
                },
                "error": str(e)
            }
