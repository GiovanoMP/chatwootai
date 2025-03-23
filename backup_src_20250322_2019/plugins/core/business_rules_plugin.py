"""
Plugin para consulta de regras de negócio.

Este plugin integra o DomainRulesService ao sistema de plugins do ChatwootAI,
permitindo que os agentes consultem regras de negócio, FAQs e políticas.
"""
import logging
from typing import List, Dict, Any, Optional, Union

from .base.base_plugin import BasePlugin

class BusinessRulesPlugin(BasePlugin):
    """
    Plugin para consulta de regras de negócio.
    
    Este plugin permite que os agentes consultem regras de negócio,
    FAQs e políticas usando o DomainRulesService.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Inicializa o plugin de regras de negócio.
        
        Args:
            config: Configuração do plugin
        """
        self.logger = logging.getLogger(__name__)
        self._rules_service = None
        super().__init__(config)
        
    def initialize(self):
        """
        Inicializa o plugin.
        """
        self.logger.info("Inicializando plugin de regras de negócio")
    
    @property
    def rules_service(self):
        """
        Obtém o serviço de regras de negócio, inicializando-o se necessário.
        
        Returns:
            Instância do serviço de regras de negócio.
        """
        if self._rules_service is None:
            # Obter do hub de dados global via injeção, quando disponível
            # Por enquanto, import direto
            try:
                from ..services.data.data_service_hub import DataServiceHub
                # Obter instância global do DataServiceHub
                data_service_hub = DataServiceHub.get_instance()
                self._rules_service = data_service_hub.get_service("domain_rules")
            except (ImportError, AttributeError) as e:
                self.logger.error(f"Erro ao obter DomainRulesService: {str(e)}")
                return None
                
        return self._rules_service
    
    def query_rules(self, query: str, rule_type: Optional[str] = None, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Consulta regras de negócio relevantes para a pergunta do cliente.
        
        Args:
            query: Pergunta ou consulta do cliente
            rule_type: Tipo de regra (product, sales, support, etc.)
            limit: Número máximo de resultados
            
        Returns:
            Lista de regras relevantes para a consulta
        """
        self.logger.info(f"Consultando regras para: '{query}' (tipo: {rule_type or 'todos'})")
        
        if not self.rules_service:
            self.logger.error("Serviço de regras não disponível")
            return []
        
        try:
            results = self.rules_service.query_rules(query, rule_type, limit=limit)
            self.logger.info(f"Encontradas {len(results)} regras relevantes")
            return results
        except Exception as e:
            self.logger.error(f"Erro ao consultar regras: {str(e)}")
            return []
    
    def get_faqs(self, query: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Obtém FAQs relevantes para a pergunta do cliente.
        
        Args:
            query: Pergunta do cliente (opcional)
            limit: Número máximo de resultados
            
        Returns:
            Lista de FAQs relevantes
        """
        self.logger.info(f"Buscando FAQs para: '{query or 'todos'}'")
        
        if not self.rules_service:
            self.logger.error("Serviço de regras não disponível")
            return []
        
        try:
            if query:
                # Busca semântica de FAQs
                return self.rules_service.query_rules(query, "support", limit=limit)
            else:
                # Retorna todas as FAQs
                all_faqs = self.rules_service.get_support_faqs()
                return all_faqs[:limit]
        except Exception as e:
            self.logger.error(f"Erro ao buscar FAQs: {str(e)}")
            return []
    
    def get_product_policy(self, policy_type: str) -> Optional[Dict[str, Any]]:
        """
        Obtém uma política específica relacionada a produtos.
        
        Args:
            policy_type: Tipo de política (warranty, return, shipping, etc.)
            
        Returns:
            Política encontrada ou None
        """
        self.logger.info(f"Buscando política de produto: '{policy_type}'")
        
        if not self.rules_service:
            self.logger.error("Serviço de regras não disponível")
            return None
        
        try:
            query = f"{policy_type} policy"
            rules = self.rules_service.query_rules(query, "product", limit=1)
            return rules[0] if rules else None
        except Exception as e:
            self.logger.error(f"Erro ao buscar política de produto: {str(e)}")
            return None
    
    def get_active_promotions(self) -> List[Dict[str, Any]]:
        """
        Obtém promoções ativas do domínio atual.
        
        Returns:
            Lista de promoções ativas
        """
        self.logger.info("Buscando promoções ativas")
        
        if not self.rules_service:
            self.logger.error("Serviço de regras não disponível")
            return []
        
        try:
            # Buscar regras de vendas relacionadas a promoções
            sales_rules = self.rules_service.get_sales_rules()
            
            # Filtrar para obter apenas promoções ativas
            active_promotions = []
            for rule in sales_rules:
                if (rule.get('category') == 'promotion' and 
                    rule.get('active', True) and
                    'start_date' in rule and 'end_date' in rule):
                    
                    # No futuro, validar datas de início e fim
                    active_promotions.append(rule)
                    
            return active_promotions
        except Exception as e:
            self.logger.error(f"Erro ao buscar promoções ativas: {str(e)}")
            return []
    
    def get_product_rules(self, domain_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Obtém regras específicas para produtos.
        
        Args:
            domain_id: ID do domínio de negócio (opcional)
            
        Returns:
            Lista de regras de produtos
        """
        self.logger.info(f"Buscando regras de produtos para o domínio: {domain_id or 'ativo'}")
        
        if not self.rules_service:
            self.logger.error("Serviço de regras não disponível")
            return []
        
        try:
            # Reutiliza o método especializado do DomainRulesService
            results = self.rules_service.get_product_rules(domain_id)
            self.logger.info(f"Encontradas {len(results)} regras de produtos")
            return results
        except Exception as e:
            self.logger.error(f"Erro ao obter regras de produtos: {str(e)}")
            return []
    
    def execute(self, action: str, *args, **kwargs) -> Any:
        """
        Executa uma ação específica do plugin.
        
        Args:
            action: Ação a ser executada
            args/kwargs: Argumentos para a ação
            
        Returns:
            Resultado da ação ou None se a ação não for reconhecida
        """
        self.logger.info(f"Executando ação: {action}")
        
        actions = {
            'query_rules': self.query_rules,
            'get_faqs': self.get_faqs,
            'get_product_policy': self.get_product_policy,
            'get_active_promotions': self.get_active_promotions,
            'get_product_rules': self.get_product_rules
        }
        
        if action in actions:
            return actions[action](*args, **kwargs)
        else:
            self.logger.error(f"Ação não reconhecida: {action}")
            return None
