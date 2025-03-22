"""
Agente de vendas adaptável para diferentes domínios de negócio.
"""
from typing import Dict, List, Any, Optional, Type, Union
import logging
from pydantic import Field, ConfigDict, validate_call

from crewai import Agent, Task, Crew
from crewai.tools.base_tool import BaseTool
from src.agents.base.adaptable_agent import AdaptableAgent
from src.api.erp import OdooClient
from src.core.data_proxy_agent import DataProxyAgent
from src.core.memory import MemorySystem
from src.core.domain.domain_manager import DomainManager
from src.plugins.core.plugin_manager import PluginManager

logger = logging.getLogger(__name__)

class SalesAgent(AdaptableAgent):
    """
    Agente especializado em vendas, adaptando-se ao domínio de negócio ativo.
    
    Processa consultas relacionadas a vendas, produtos, preços e promoções.
    """
    # Configuração do modelo Pydantic
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    def __init__(self, agent_config: Dict[str, Any], 
                 memory_system: Optional[MemorySystem] = None,
                 data_proxy_agent: Optional[DataProxyAgent] = None,
                 domain_manager: Optional[DomainManager] = None,
                 plugin_manager: Optional[PluginManager] = None):
        # Validar a configuração do agente usando um método separado
        self._validate_agent_config(agent_config)
        """
        Inicializa o agente de vendas.
        
        Args:
            agent_config: Configuração do agente
            memory_system: Sistema de memória compartilhada
            data_proxy_agent: Agente proxy para acesso a dados
            domain_manager: Gerenciador de domínios de negócio
            plugin_manager: Gerenciador de plugins
        """
        # Adiciona o tipo de função ao config se não estiver presente
        if "function_type" not in agent_config:
            agent_config["function_type"] = "sales"
            
        # Chama o construtor da classe pai
        super().__init__(agent_config, memory_system, data_proxy_agent, domain_manager, plugin_manager)
        
        # Inicializa atributos adicionais usando o dicionário privado
        # Isso evita problemas com a validação do Pydantic
        self.__dict__["_odoo_client"] = None
        self.__dict__["_crew_agent"] = None
        self.__dict__["_tools"] = []
        self.__dict__["_domain_config"] = {}
        
        # Valida a configuração e inicializa o agente
        self._validate_config(agent_config)
        self.initialize()

    @validate_call
    def _validate_agent_config(self, config: Dict[str, Any]):
        """Valida a configuração do agente usando o decorator @validate_call do Pydantic.
        
        Esta abordagem permite validar apenas o parâmetro config, evitando problemas com
        tipos complexos como MemorySystem, DataProxyAgent, etc.
        
        Args:
            config: Dicionário de configuração do agente
            
        Raises:
            ValueError: Se a configuração não contiver as chaves obrigatórias
        """
        # Chamamos o método original de validação
        self._validate_config(config)
    
    def _validate_config(self, config: Dict[str, Any]):
        """Valida a configuração do agente antes da inicialização."""
        required_keys = ['role', 'goal', 'backstory']
        for key in required_keys:
            if key not in config:
                raise ValueError(f"Configuração do agente deve conter '{key}'")
    
    def initialize(self):
        """Inicializa o agente com ferramentas específicas para vendas."""
        try:
            # Inicializa o cliente Odoo
            self.__dict__["_odoo_client"] = OdooClient()
            
            # Verifica se temos acesso ao DataProxyAgent
            if not self.data_proxy_agent:
                logger.warning("DataProxyAgent não disponível para o SalesAgent. Algumas funcionalidades estarão limitadas.")
            else:
                # Obtém as ferramentas do DataProxyAgent
                self.__dict__["_tools"] = self.data_proxy_agent.get_tools()
                logger.info(f"Obtidas {len(self.tools)} ferramentas do DataProxyAgent")
        except Exception as e:
            logger.error(f"Erro na inicialização do SalesAgent: {str(e)}")
            raise
    
    def get_agent_type(self) -> str:
        """
        Obtém o tipo do agente.
        
        Returns:
            str: Tipo do agente
        """
        return "sales"
    
    # Propriedades para acessar os atributos privados
    @property
    def odoo_client(self):
        """Retorna o cliente Odoo."""
        return self.__dict__.get("_odoo_client")
    
    @property
    def crew_agent(self):
        """Retorna o agente CrewAI."""
        return self.__dict__.get("_crew_agent")
    
    @crew_agent.setter
    def crew_agent(self, value):
        """Define o agente CrewAI."""
        self.__dict__["_crew_agent"] = value
    
    @property
    def tools(self):
        """Retorna as ferramentas do agente."""
        return self.__dict__.get("_tools", [])
    
    @property
    def domain_config(self):
        """Retorna a configuração do domínio."""
        return self.__dict__.get("_domain_config", {})
    
    @domain_config.setter
    def domain_config(self, value):
        """Define a configuração do domínio."""
        self.__dict__["_domain_config"] = value
    
    def get_crew_agent(self):
        """
        Cria e retorna um agente CrewAI configurado para vendas.
        
        Returns:
            Agent: Um agente CrewAI configurado para vendas
        """
        # Se já temos um agente criado, retorna-o
        if self.crew_agent:
            return self.crew_agent
            
        # Garantir que temos data_proxy_agent
        if not self.data_proxy_agent:
            logger.warning("DataProxyAgent não disponível para o SalesAgent. O agente CrewAI não terá acesso às ferramentas de consulta de dados.")
            tools = []
        else:
            # Obter ferramentas do DataProxyAgent
            tools = self.data_proxy_agent.get_tools()
            logger.info(f"Ferramentas obtidas do DataProxyAgent: {[t.name for t in tools]}")
        
        # Adaptar a configuração ao domínio ativo
        domain_name = self.domain_manager.get_active_domain() if self.domain_manager else "default"
        
        # Configuração padrão que será sobrescrita pela configuração do domínio se disponível
        role = f"Especialista em vendas para {domain_name}"
        goal = f"Auxiliar clientes com consultas de vendas no domínio de {domain_name}"
        backstory = f"Você é um especialista em produtos e serviços de {domain_name}, com amplo conhecimento sobre preços, promoções e características dos produtos."
        
        # Sobrescrever com valores do domínio se disponíveis
        if self.domain_config:
            role = self.domain_config.get('sales_agent_role', role)
            goal = self.domain_config.get('sales_agent_goal', goal)
            backstory = self.domain_config.get('sales_agent_backstory', backstory)
        
        # Criar um agente CrewAI
        crew_agent = Agent(
            role=role,
            goal=goal,
            backstory=backstory,
            tools=tools,
            verbose=True
        )
        
        # Armazenar o agente criado
        self.crew_agent = crew_agent
        
        logger.info(f"Agente CrewAI criado para o domínio {domain_name}")
        return crew_agent
    
    def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa uma mensagem relacionada a vendas.
        
        Args:
            message: Mensagem a ser processada
            
        Returns:
            Dict[str, Any]: Resposta processada
        """
        # Extrai conteúdo da mensagem
        content = message.get("content", "")
        
        # Adapta o prompt com base no domínio
        prompt = self.adapt_prompt(
            f"""Você é um especialista em vendas para {"{domain_name}"}.
            
            {"{domain_description}"}
            
            Por favor, responda à seguinte mensagem do cliente:
            
            {content}
            
            Siga estas diretrizes específicas para {"{domain_name}"}:
            - {"{sales_greeting_style}"}
            - {"{sales_response_format}"}
            - {"{sales_closing_style}"}
            
            Certifique-se de mencionar produtos relevantes, ofertas e políticas de preços 
            de acordo com o domínio atual.
            """
        )
        
        # Consulta informações de produtos se necessário
        products = []
        if self._should_query_products(content):
            products = self._query_products(content)
        
        # Consulta informações de preço se necessário
        pricing = {}
        if self._should_query_pricing(content):
            product_ids = [p.get("id") for p in products if "id" in p]
            pricing = self._query_pricing(product_ids)
        
        # Consulta informações de promoções se necessário
        promotions = []
        if self._should_query_promotions(content):
            promotions = self._query_promotions()
        
        # Gera a resposta com base nas informações consultadas
        context = {
            "products": products,
            "pricing": pricing,
            "promotions": promotions,
            "domain": self.domain_manager.get_active_domain() if self.domain_manager else "default"
        }
        
        # Criar o agente CrewAI e executar a tarefa
        try:
            # Obter o agente CrewAI
            crew_agent = self.get_crew_agent()
            
            # Montar um prompt contextualizado com as informações coletadas
            contextual_prompt = f"{prompt}\n\n"
            
            if products:
                contextual_prompt += "\nInformações de produtos disponíveis:\n"
                for p in products:
                    contextual_prompt += f"- {p.get('name', 'Produto')}\n"
            
            if pricing:
                contextual_prompt += "\nInformações de preços:\n"
                for pid, price in pricing.items():
                    contextual_prompt += f"- ID {pid}: R$ {price}\n"
            
            if promotions:
                contextual_prompt += "\nPromoções atuais:\n"
                for promo in promotions:
                    contextual_prompt += f"- {promo.get('name', 'Promoção')}: {promo.get('description', '')}\n"
            
            # Criar a tarefa com o prompt contextualizado
            task = Task(
                description=contextual_prompt,
                expected_output="Resposta detalhada para o cliente sobre produtos, preços ou promoções"
            )
        except Exception as e:
            logger.error(f"Erro ao criar agente CrewAI ou tarefa: {str(e)}")
            # Criar uma tarefa simples como fallback
            task = Task(
                description=f"Responda à seguinte mensagem do cliente: {content}",
                expected_output="Resposta para o cliente"
            )
        
        response_content = self.execute_task(task)
        
        # Adapta a resposta com base no domínio
        response_content = self.adapt_response(response_content)
        
        return {
            "status": "success",
            "response": response_content,
            "context": context
        }
    
    def _should_query_products(self, content: str) -> bool:
        """
        Verifica se deve consultar informações de produtos.
        
        Args:
            content: Conteúdo da mensagem
            
        Returns:
            bool: True se deve consultar, False caso contrário
        """
        # Lógica simplificada para decidir se consulta produtos
        product_keywords = ["produto", "item", "comprar", "preço", 
                          "valor", "custo", "quanto custa", "disponível"]
        
        return any(keyword in content.lower() for keyword in product_keywords)
    
    def _query_products(self, content: str) -> List[Dict[str, Any]]:
        """
        Consulta informações de produtos.
        
        Args:
            content: Conteúdo da mensagem
            
        Returns:
            List[Dict[str, Any]]: Lista de produtos
        """
        # Simulação de consulta de produtos
        if self.data_proxy_agent:
            try:
                return self.data_proxy_agent.query_data(
                    query=f"Encontre produtos relacionados a: {content}",
                    data_type="products",
                    limit=5
                )
            except Exception as e:
                logger.error(f"Erro ao consultar produtos: {e}")
        
        return []
    
    def _should_query_pricing(self, content: str) -> bool:
        """
        Verifica se deve consultar informações de preço.
        
        Args:
            content: Conteúdo da mensagem
            
        Returns:
            bool: True se deve consultar, False caso contrário
        """
        # Lógica simplificada para decidir se consulta preços
        price_keywords = ["preço", "valor", "custo", "quanto custa", 
                        "promoção", "desconto", "oferta"]
        
        return any(keyword in content.lower() for keyword in price_keywords)
    
    def _query_pricing(self, product_ids: List[str]) -> Dict[str, Any]:
        """
        Consulta informações de preço.
        
        Args:
            product_ids: IDs dos produtos
            
        Returns:
            Dict[str, Any]: Informações de preço
        """
        # Simulação de consulta de preços
        if self.data_proxy_agent and product_ids:
            try:
                return self.data_proxy_agent.query_data(
                    query=f"Obtenha preços para os produtos: {','.join(product_ids)}",
                    data_type="pricing",
                    product_ids=product_ids
                )
            except Exception as e:
                logger.error(f"Erro ao consultar preços: {e}")
        
        return {}
    
    def _should_query_promotions(self, content: str) -> bool:
        """
        Verifica se deve consultar informações de promoções.
        
        Args:
            content: Conteúdo da mensagem
            
        Returns:
            bool: True se deve consultar, False caso contrário
        """
        # Lógica simplificada para decidir se consulta promoções
        promotion_keywords = ["promoção", "desconto", "oferta", "cupom", 
                            "especial", "campanha", "black friday"]
        
        return any(keyword in content.lower() for keyword in promotion_keywords)
    
    def _query_promotions(self) -> List[Dict[str, Any]]:
        """
        Consulta informações de promoções.
        
        Returns:
            List[Dict[str, Any]]: Lista de promoções
        """
        # Simulação de consulta de promoções
        if self.data_proxy_agent:
            try:
                return self.data_proxy_agent.query_data(
                    query="Liste as promoções ativas",
                    data_type="promotions",
                    is_active=True
                )
            except Exception as e:
                logger.error(f"Erro ao consultar promoções: {e}")
        
        return []
    
    def adapt_prompt(self, prompt: str) -> str:
        """
        Adapta um prompt de acordo com o domínio de negócio.
        
        Args:
            prompt: Prompt original
            
        Returns:
            str: Prompt adaptado
        """
        # Obtemos o domínio ativo
        domain_name = self.domain_manager.get_active_domain() if self.domain_manager else "default"
        
        # Substitui placeholders no prompt
        adapted_prompt = prompt.replace("{domain_name}", domain_name)
        
        # Adiciona regras específicas do domínio se disponíveis
        if self.domain_config and "description" in self.domain_config:
            adapted_prompt = adapted_prompt.replace("{domain_description}", self.domain_config["description"])
        else:
            adapted_prompt = adapted_prompt.replace("{domain_description}", f"Domínio de vendas para {domain_name}")
        
        # Substitui outros placeholders com valores padrão se não estiverem no domínio
        placeholders = {
            "{sales_greeting_style}": "Cumprimente o cliente de forma cordial e profissional",
            "{sales_response_format}": "Forneça informações claras e concisas sobre produtos e preços",
            "{sales_closing_style}": "Encerre a mensagem convidando o cliente a fazer perguntas adicionais"
        }
        
        for placeholder, default_value in placeholders.items():
            if placeholder in adapted_prompt:
                key = placeholder.strip("{}")
                if self.domain_config and key in self.domain_config:
                    adapted_prompt = adapted_prompt.replace(placeholder, self.domain_config[key])
                else:
                    adapted_prompt = adapted_prompt.replace(placeholder, default_value)
        
        return adapted_prompt
    
    def adapt_response(self, response: str) -> str:
        """
        Adapta uma resposta de acordo com o domínio de negócio.
        
        Args:
            response: Resposta original
            
        Returns:
            str: Resposta adaptada
        """
        # Personaliza a resposta com base no domínio
        domain_name = self.domain_manager.get_active_domain() if self.domain_manager else "default"
        
        # Adiciona assinatura personalizada com base no domínio
        if self.domain_config and "signature" in self.domain_config:
            response += f"\n\n{self.domain_config['signature']}"
        else:
            response += f"\n\nEquipe de Vendas - {domain_name}"
        
        return response
    
    def execute_task(self, task: Task) -> str:
        """
        Executa uma tarefa usando o agente CrewAI.
        
        Args:
            task: Tarefa a ser executada
            
        Returns:
            str: Resultado da execução da tarefa
        """
        try:
            # Obtém o agente CrewAI
            crew_agent = self.get_crew_agent()
            
            # Cria uma crew com apenas este agente
            crew = Crew(
                agents=[crew_agent],
                tasks=[task],
                verbose=True
            )
            
            # Executa a tarefa
            result = crew.kickoff()
            logger.info(f"Tarefa executada com sucesso: {task.description[:50]}...")
            return result
        except Exception as e:
            logger.error(f"Erro ao executar tarefa: {str(e)}")
            return f"Desculpe, não foi possível processar sua solicitação. Erro: {str(e)}"
