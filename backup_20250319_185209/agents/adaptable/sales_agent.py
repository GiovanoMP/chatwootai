"""
Agente de vendas adaptável para diferentes domínios de negócio.
"""
from typing import Dict, List, Any, Optional
import logging

from .adaptable_agent import AdaptableAgent
from src.api.erp import OdooClient

logger = logging.getLogger(__name__)


class SalesAgent(AdaptableAgent):
    """
    Agente de vendas adaptável para diferentes domínios de negócio.
    
    Especializado em processar consultas relacionadas a vendas, produtos,
    preços e promoções, adaptando-se ao domínio de negócio ativo.
    """
    
    def get_agent_type(self) -> str:
        """
        Obtém o tipo do agente.
        
        Returns:
            str: Tipo do agente
        """
        return "sales"
    
    def initialize(self):
        """
        Inicializa o agente de vendas.
        """
        super().initialize()
        
        # Obtém configuração do ERP
        erp_config = self.config.get("erp", {})
        
        # Cria cliente Odoo
        try:
            self.erp_client = OdooClient(erp_config)
        except Exception as e:
            logger.error(f"Não foi possível criar cliente Odoo: {str(e)}")
            self.erp_client = None
    
    def process_product_inquiry(self, product_query: str, customer_id: str = None) -> Dict[str, Any]:
        """
        Processa uma consulta sobre produtos.
        
        Args:
            product_query: Consulta sobre produtos
            customer_id: ID do cliente (opcional)
            
        Returns:
            Dict[str, Any]: Informações sobre produtos relevantes
        """
        # Verifica se há plugins específicos para recomendação de produtos
        domain_name = self.domain_manager.active_domain_name
        recommendation_plugin = f"{domain_name}_product_recommendation"
        
        if self.plugin_manager.has_plugin(recommendation_plugin):
            # Usa o plugin específico do domínio para recomendação
            return self.execute_plugin(
                recommendation_plugin, 
                "recommend_products", 
                query=product_query, 
                customer_id=customer_id
            )
        
        # Caso não haja plugin específico, usa a busca padrão
        if self.erp_client:
            return self.erp_client.search_products(product_query, limit=5)
        
        return {"error": "Cliente ERP não disponível"}
    
    def get_product_details(self, product_id: str) -> Dict[str, Any]:
        """
        Obtém detalhes de um produto.
        
        Args:
            product_id: ID do produto
            
        Returns:
            Dict[str, Any]: Detalhes do produto
        """
        if self.erp_client:
            return self.erp_client.get_product(product_id)
        
        return {"error": "Cliente ERP não disponível"}
    
    def check_product_availability(self, product_id: str, quantity: int = 1) -> Dict[str, Any]:
        """
        Verifica a disponibilidade de um produto.
        
        Args:
            product_id: ID do produto
            quantity: Quantidade desejada
            
        Returns:
            Dict[str, Any]: Informações de disponibilidade
        """
        if self.erp_client:
            stock_info = self.erp_client.get_product_stock(product_id)
            
            if "error" in stock_info:
                return stock_info
            
            available_quantity = stock_info.get("quantity", 0)
            is_available = available_quantity >= quantity
            
            return {
                "product_id": product_id,
                "requested_quantity": quantity,
                "available_quantity": available_quantity,
                "is_available": is_available
            }
        
        return {"error": "Cliente ERP não disponível"}
    
    def create_order(self, customer_id: str, products: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """
        Cria um novo pedido.
        
        Args:
            customer_id: ID do cliente
            products: Lista de produtos (cada item deve ter product_id e quantity)
            **kwargs: Parâmetros adicionais do pedido
            
        Returns:
            Dict[str, Any]: Pedido criado
        """
        if self.erp_client:
            order_data = {
                "customer_id": customer_id,
                "products": products,
                **kwargs
            }
            
            # Aplica regras de negócio específicas do domínio
            business_rules = self.get_business_rules("orders")
            
            # Verifica se há regras de desconto
            if "discount_rules" in business_rules:
                # Aplica regras de desconto
                # Implementação depende das regras específicas do domínio
                pass
            
            return self.erp_client.create_order(order_data)
        
        return {"error": "Cliente ERP não disponível"}
    
    def get_promotions(self) -> List[Dict[str, Any]]:
        """
        Obtém promoções ativas.
        
        Returns:
            List[Dict[str, Any]]: Lista de promoções ativas
        """
        # Verifica se há plugins específicos para promoções
        domain_name = self.domain_manager.active_domain_name
        promotions_plugin = f"{domain_name}_promotions"
        
        if self.plugin_manager.has_plugin(promotions_plugin):
            # Usa o plugin específico do domínio para promoções
            return self.execute_plugin(promotions_plugin, "get_active_promotions")
        
        # Caso não haja plugin específico, usa as regras de negócio
        business_rules = self.get_business_rules("promotions")
        
        return business_rules.get("active_promotions", [])
