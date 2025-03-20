"""
Agente de suporte adaptável para diferentes domínios de negócio.
"""
from typing import Dict, List, Any, Optional
import logging

from src.agents.base.adaptable_agent import AdaptableAgent
from src.api.erp import OdooClient
from src.tools.vector_tools import QdrantVectorSearchTool

logger = logging.getLogger(__name__)


class SupportAgent(AdaptableAgent):
    """
    Agente de suporte adaptável para diferentes domínios de negócio.
    
    Especializado em processar consultas relacionadas a suporte, dúvidas,
    problemas e reclamações, adaptando-se ao domínio de negócio ativo.
    """
    
    def get_agent_type(self) -> str:
        """
        Obtém o tipo do agente.
        
        Returns:
            str: Tipo do agente
        """
        return "support"
    
    def initialize(self):
        """
        Inicializa o agente de suporte.
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
        
        # Inicializa cliente de banco de dados vetorial
        vector_db_config = self.config.get("vector_db", {})
        self.vector_db = QdrantVectorSearchTool(**vector_db_config)
    
    def process_support_query(self, query: str, customer_id: str = None) -> Dict[str, Any]:
        """
        Processa uma consulta de suporte.
        
        Args:
            query: Consulta de suporte
            customer_id: ID do cliente (opcional)
            
        Returns:
            Dict[str, Any]: Resposta à consulta
        """
        # Verifica se há plugins específicos para suporte
        domain_name = self.domain_manager.active_domain_name
        support_plugin = f"{domain_name}_support"
        
        if self.plugin_manager.has_plugin(support_plugin):
            # Usa o plugin específico do domínio para suporte
            return self.execute_plugin(
                support_plugin, 
                "process_query", 
                query=query, 
                customer_id=customer_id
            )
        
        # Caso não haja plugin específico, usa a busca semântica
        # Busca regras de negócio relevantes para a consulta
        business_rules = self.get_business_rules()
        
        # Busca documentação relevante no banco de dados vetorial
        vector_results = self.vector_db.search(
            query=query,
            collection=f"{domain_name}_support",
            limit=3
        )
        
        # Combina os resultados
        return {
            "query": query,
            "vector_results": vector_results,
            "business_rules": business_rules
        }
    
    def get_customer_orders(self, customer_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Obtém os pedidos de um cliente.
        
        Args:
            customer_id: ID do cliente
            limit: Limite de resultados
            
        Returns:
            List[Dict[str, Any]]: Lista de pedidos do cliente
        """
        if self.erp_client:
            return self.erp_client.get_customer_orders(customer_id, limit)
        
        return []
    
    def process_return_request(self, order_id: str, items: List[Dict[str, Any]], reason: str) -> Dict[str, Any]:
        """
        Processa uma solicitação de devolução.
        
        Args:
            order_id: ID do pedido
            items: Itens a serem devolvidos (cada item deve ter product_id e quantity)
            reason: Motivo da devolução
            
        Returns:
            Dict[str, Any]: Resultado da solicitação
        """
        # Verifica se há plugins específicos para devoluções
        domain_name = self.domain_manager.active_domain_name
        returns_plugin = f"{domain_name}_returns"
        
        if self.plugin_manager.has_plugin(returns_plugin):
            # Usa o plugin específico do domínio para devoluções
            return self.execute_plugin(
                returns_plugin, 
                "process_return", 
                order_id=order_id,
                items=items,
                reason=reason
            )
        
        # Caso não haja plugin específico, usa a implementação padrão
        # Obtém regras de negócio para devoluções
        return_rules = self.get_business_rules("returns")
        
        # Verifica se a devolução está dentro do prazo
        if self.erp_client:
            order = self.erp_client.get_order(order_id)
            
            if "error" in order:
                return order
            
            # Implementação depende das regras específicas do domínio
            # ...
            
            return {
                "order_id": order_id,
                "items": items,
                "reason": reason,
                "status": "pending",
                "message": "Solicitação de devolução recebida e será analisada."
            }
        
        return {"error": "Cliente ERP não disponível"}
    
    def get_faq(self, category: str = None) -> List[Dict[str, Any]]:
        """
        Obtém perguntas frequentes.
        
        Args:
            category: Categoria específica (opcional)
            
        Returns:
            List[Dict[str, Any]]: Lista de perguntas frequentes
        """
        # Obtém regras de negócio para FAQ
        faq_rules = self.get_business_rules("faq")
        
        if category and category in faq_rules:
            return faq_rules[category]
        
        # Combina todas as categorias
        all_faqs = []
        for cat, faqs in faq_rules.items():
            if isinstance(faqs, list):
                all_faqs.extend(faqs)
        
        return all_faqs
