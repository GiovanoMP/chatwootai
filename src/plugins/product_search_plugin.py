"""
Plugin para busca semântica de produtos.

Este plugin integra a busca híbrida (PostgreSQL + Qdrant) ao sistema de plugins
do ChatwootAI, permitindo que os agentes encontrem produtos relevantes para
as perguntas dos clientes.
"""
import logging
from typing import List, Dict, Any, Optional, Union

from .base.base_plugin import BasePlugin
from ..services.product_search_service import ProductSearchService

class ProductSearchPlugin(BasePlugin):
    """
    Plugin para busca semântica de produtos.
    
    Este plugin permite que os agentes realizem buscas semânticas por produtos
    usando a abordagem híbrida que combina o banco vetorial (Qdrant) com o
    banco relacional (PostgreSQL).
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Inicializa o plugin de busca de produtos."""
        self.logger = logging.getLogger(__name__)
        self._search_service = None
        self.name = "product_search"
        self.description = "Realiza busca semântica por produtos relevantes para as perguntas dos clientes"
        super().__init__(config)
        
    @property
    def search_service(self) -> ProductSearchService:
        """
        Obtém o serviço de busca, inicializando-o se necessário.
        
        Returns:
            Instância do serviço de busca de produtos.
        """
        if self._search_service is None:
            self._search_service = ProductSearchService()
        return self._search_service
    
    def initialize(self, domain_config: Dict[str, Any]) -> None:
        """
        Inicializa o plugin com a configuração do domínio.
        
        Args:
            domain_config: Configuração do domínio de negócio ativo.
        """
        self.logger.info(f"Inicializando plugin de busca de produtos para o domínio: {domain_config.get('name', 'desconhecido')}")
        # Aqui poderíamos personalizar o comportamento do plugin com base no domínio
        # Por exemplo, ajustar parâmetros de busca específicos para cada tipo de negócio
    
    def search_products(self, query: str, limit: int = 5, min_score: float = 0.7, category_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Busca produtos relevantes para a consulta do usuário.
        
        Este método utiliza a busca híbrida para encontrar produtos que são:
        1. Semanticamente relevantes para a consulta (via Qdrant)
        2. Disponíveis em estoque (verificado no PostgreSQL)
        
        Args:
            query: Consulta do usuário (ex: "produtos para pele oleosa")
            limit: Número máximo de resultados a retornar
            min_score: Pontuação mínima de relevância (0-1)
            category_id: ID da categoria para filtrar (opcional)
            
        Returns:
            Lista de produtos relevantes para a consulta
        """
        self.logger.info(f"Buscando produtos para a consulta: '{query}'")
        
        try:
            results = self.search_service.search_products(query, limit, min_score, category_id)
            self.logger.info(f"Encontrados {len(results)} produtos relevantes")
            return results
        except Exception as e:
            self.logger.error(f"Erro ao buscar produtos: {str(e)}")
            return []
    
    def search_products_by_category(self, query: str, category_id: int, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Busca produtos em uma categoria específica.
        
        Este método é útil quando o cliente já especificou uma categoria
        e deseja encontrar produtos específicos dentro dela.
        
        Args:
            query: Consulta do usuário
            category_id: ID da categoria de produtos
            limit: Número máximo de resultados
            
        Returns:
            Lista de produtos relevantes na categoria especificada
        """
        self.logger.info(f"Buscando produtos na categoria ID {category_id} para a consulta: '{query}'")
        
        try:
            results = self.search_service.search_products(query, limit, min_score=0.7, category_id=category_id)
            self.logger.info(f"Encontrados {len(results)} produtos na categoria ID {category_id}")
            return results
        except Exception as e:
            self.logger.error(f"Erro ao buscar produtos por categoria: {str(e)}")
            return []
    
    def search_business_rules(self, query: str, limit: int = 3, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Busca regras de negócio relevantes para a consulta do usuário.
        
        Este método utiliza a busca híbrida para encontrar regras de negócio que são
        semanticamente relevantes para a consulta.
        
        Args:
            query: Consulta do usuário (ex: "política de devolução")
            limit: Número máximo de resultados a retornar
            category: Categoria de regras para filtrar (opcional)
            
        Returns:
            Lista de regras de negócio relevantes para a consulta
        """
        self.logger.info(f"Buscando regras de negócio para a consulta: '{query}'")
        
        try:
            results = self.search_service.search_business_rules(query, limit, min_score=0.7, category=category)
            self.logger.info(f"Encontradas {len(results)} regras de negócio relevantes")
            return results
        except Exception as e:
            self.logger.error(f"Erro ao buscar regras de negócio: {str(e)}")
            return []
    
    def get_product_details(self, product_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtém detalhes completos de um produto pelo seu ID.
        
        Args:
            product_id: ID do produto
            
        Returns:
            Detalhes completos do produto ou None se não encontrado
        """
        self.logger.info(f"Obtendo detalhes do produto ID {product_id}")
        
        try:
            result = self.search_service.get_product_details(product_id)
            if result:
                self.logger.info(f"Detalhes obtidos para o produto ID {product_id}")
            else:
                self.logger.warning(f"Produto ID {product_id} não encontrado")
            return result
        except Exception as e:
            self.logger.error(f"Erro ao obter detalhes do produto: {str(e)}")
            return None
    
    def get_recommended_products(self, product_id: int, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Obtém produtos recomendados com base em um produto de referência.
        
        Utiliza similaridade semântica entre produtos para recomendar produtos
        semelhantes ou complementares.
        
        Args:
            product_id: ID do produto de referência
            limit: Número máximo de recomendações
            
        Returns:
            Lista de produtos recomendados
        """
        self.logger.info(f"Obtendo recomendações para o produto ID {product_id}")
        
        try:
            recommendations = self.search_service.get_recommended_products(product_id, limit)
            self.logger.info(f"Encontradas {len(recommendations)} recomendações para o produto ID {product_id}")
            return recommendations
        except Exception as e:
            self.logger.error(f"Erro ao obter recomendações de produtos: {str(e)}")
            return []
    
    def format_product_results(self, products: List[Dict[str, Any]], detailed: bool = False) -> str:
        """
        Formata os resultados da busca de produtos para apresentação ao cliente.
        
        Args:
            products: Lista de produtos retornados pela busca
            detailed: Se True, inclui descrições detalhadas dos produtos
            
        Returns:
            Texto formatado com os produtos encontrados
        """
        # Usar o método de formatação do serviço de busca se disponível
        if hasattr(self.search_service, 'format_product_results'):
            return self.search_service.format_product_results(products)
            
        # Implementação de fallback
        if not products:
            return "Não encontrei produtos que atendam a essa necessidade no momento."
        
        result = "Encontrei os seguintes produtos que podem te interessar:\n\n"
        
        for i, product in enumerate(products, 1):
            # Formatar preço
            price_str = f"R$ {float(product['price']):.2f}" if product.get('price') else "Preço sob consulta"
            
            # Adicionar informações básicas
            result += f"**{i}. {product['name']}** - {price_str}\n"
            
            # Adicionar categoria se disponível
            if product.get('category_name'):
                result += f"Categoria: {product['category_name']}\n"
            
            # Adicionar score de relevância
            if 'score' in product:
                result += f"Relevância: {product['score']:.2f}\n"
            
            # Adicionar descrição básica ou detalhada
            if detailed and product.get('detailed_information'):
                result += f"{product['detailed_information']}\n"
            elif product.get('description'):
                result += f"{product['description']}\n"
            
            # Adicionar informação de estoque
            if 'stock' in product:
                stock = int(product['stock'])
                if stock > 10:
                    result += "✅ Em estoque\n"
                elif stock > 0:
                    result += f"⚠️ Apenas {stock} unidades em estoque\n"
                else:
                    result += "❌ Fora de estoque\n"
            
            # Adicionar separador entre produtos
            result += "\n"
        
        # Adicionar pergunta de follow-up
        result += "Gostaria de mais informações sobre algum desses produtos?"
        
        return result
