"""
Agente de vendas adaptável para diferentes domínios de negócio.
"""
from typing import Dict, List, Any, Optional, Type, Union
import logging
from pydantic import Field, PrivateAttr

from crewai import Agent, Task
from crewai.tools.base_tool import BaseTool
from src.agents.base.adaptable_agent import AdaptableAgent
from src.api.erp import OdooClient
from src.core.data_proxy_agent import DataProxyAgent

logger = logging.getLogger(__name__)


"""
Agente de vendas adaptável para diferentes domínios de negócio.

Especializado em processar consultas relacionadas a vendas, produtos,
preços e promoções, adaptando-se ao domínio de negócio ativo.
"""
class SalesAgent(AdaptableAgent):
    # Atributos privados que não são parte do modelo Pydantic
    _odoo_client: Optional[OdooClient] = PrivateAttr(default=None)
    _crew_agent: Optional[Agent] = PrivateAttr(default=None)
    
    # Garantir que a configuração do modelo Pydantic seja herdada corretamente
    model_config = {"arbitrary_types_allowed": True, "extra": "allow"}
    
    def get_agent_type(self) -> str:
        """
        Obtém o tipo do agente.
        
        Returns:
            str: Tipo do agente
        """
        return "sales"
    
    def initialize(self):
        """
        Inicializa o agente com ferramentas específicas para vendas.
        """
        # Inicializa o cliente Odoo
        self._odoo_client = OdooClient()
        
        # Verificar se temos acesso ao DataProxyAgent
        if not self.data_proxy_agent:
            logger.warning("DataProxyAgent não disponível para o SalesAgent. Algumas funcionalidades estarão limitadas.")
    
    def get_crew_agent(self):
        """
        Cria e retorna um agente CrewAI configurado para vendas.
        
        Returns:
            Agent: Um agente CrewAI configurado para vendas
        """
        
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
        domain_config = self.domain_config if hasattr(self, 'domain_config') else {}
        
        # Configuração padrão que será sobrescrita pela configuração do domínio se disponível
        role = f"Especialista em vendas para {domain_name}"
        goal = f"Auxiliar clientes com consultas de vendas no domínio de {domain_name}"
        backstory = f"Você é um especialista em produtos e serviços de {domain_name}, com amplo conhecimento sobre preços, promoções e características dos produtos."
        
        # Sobrescrever com valores do domínio se disponíveis
        if domain_config:
            role = domain_config.get('sales_agent_role', role)
            goal = domain_config.get('sales_agent_goal', goal)
            backstory = domain_config.get('sales_agent_backstory', backstory)
        
        # Criar um agente CrewAI
        agent = Agent(
            role=role,
            goal=goal,
            backstory=backstory,
            tools=tools,
            verbose=True
        )
        
        return agent
    
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
