"""
Exemplo de uso do plugin de busca de produtos em um agente de vendas.

Este arquivo demonstra como um agente de vendas pode utilizar o plugin
de busca semântica para encontrar produtos relevantes para as perguntas
dos clientes.
"""
import logging
from typing import Dict, Any, List, Optional

from ..plugins.product_search_plugin import ProductSearchPlugin

class SalesAgentExample:
    """
    Exemplo de agente de vendas que utiliza busca semântica de produtos.
    
    Este é um exemplo simplificado para demonstrar como um agente pode
    utilizar o plugin de busca de produtos para responder às perguntas
    dos clientes de forma relevante e precisa.
    """
    
    def __init__(self):
        """Inicializa o agente de vendas de exemplo."""
        self.logger = logging.getLogger(__name__)
        self.product_search_plugin = ProductSearchPlugin()
        
        # Inicializar o plugin com uma configuração de domínio fictícia
        # Em um caso real, isso seria feito pelo DomainManager
        self.product_search_plugin.initialize({
            "name": "cosmetics",
            "description": "Empresa de cosméticos"
        })
    
    def answer_product_query(self, customer_query: str) -> str:
        """
        Responde a uma pergunta do cliente sobre produtos.
        
        Este método:
        1. Analisa a pergunta do cliente
        2. Busca produtos relevantes usando o plugin de busca
        3. Formata uma resposta com os produtos encontrados
        
        Args:
            customer_query: Pergunta do cliente (ex: "Você tem algo para pele oleosa?")
            
        Returns:
            Resposta formatada com os produtos relevantes
        """
        self.logger.info(f"Recebida pergunta do cliente: '{customer_query}'")
        
        # Buscar produtos relevantes para a pergunta
        products = self.product_search_plugin.search_products(
            query=customer_query,
            limit=3,  # Limitar a 3 produtos para não sobrecarregar o cliente
            min_score=0.7  # Apenas produtos com boa relevância
        )
        
        # Formatar resposta com os produtos encontrados
        response = self.product_search_plugin.format_product_results(products)
        
        return response
    
    def answer_category_query(self, customer_query: str, category: str) -> str:
        """
        Responde a uma pergunta do cliente sobre produtos em uma categoria específica.
        
        Args:
            customer_query: Pergunta do cliente
            category: Categoria de produtos
            
        Returns:
            Resposta formatada com os produtos relevantes na categoria
        """
        self.logger.info(f"Recebida pergunta sobre categoria '{category}': '{customer_query}'")
        
        # Buscar produtos na categoria especificada
        products = self.product_search_plugin.search_products_by_category(
            query=customer_query,
            category=category,
            limit=3
        )
        
        # Formatar resposta com os produtos encontrados
        response = self.product_search_plugin.format_product_results(products)
        
        return response
    
    def answer_price_range_query(self, customer_query: str, min_price: float, max_price: float) -> str:
        """
        Responde a uma pergunta do cliente sobre produtos em uma faixa de preço.
        
        Args:
            customer_query: Pergunta do cliente
            min_price: Preço mínimo
            max_price: Preço máximo
            
        Returns:
            Resposta formatada com os produtos relevantes na faixa de preço
        """
        self.logger.info(f"Recebida pergunta sobre faixa de preço R${min_price:.2f}-R${max_price:.2f}: '{customer_query}'")
        
        # Buscar produtos na faixa de preço especificada
        products = self.product_search_plugin.search_products_by_price_range(
            query=customer_query,
            min_price=min_price,
            max_price=max_price,
            limit=3
        )
        
        # Formatar resposta com os produtos encontrados
        response = self.product_search_plugin.format_product_results(products)
        
        return response
    
    def process_customer_message(self, message: str) -> str:
        """
        Processa uma mensagem do cliente e retorna uma resposta apropriada.
        
        Este método simula um processamento mais completo que poderia ser
        feito por um agente real, incluindo detecção de intenção, extração
        de entidades, etc.
        
        Args:
            message: Mensagem do cliente
            
        Returns:
            Resposta do agente
        """
        # Exemplo simplificado - em um caso real, usaríamos NLU para detectar intenções
        message_lower = message.lower()
        
        # Detectar perguntas sobre categorias
        if "hidratante" in message_lower and "corpo" in message_lower:
            return self.answer_category_query(message, "Hidratantes Corporais")
        elif "shampoo" in message_lower or "cabelo" in message_lower:
            return self.answer_category_query(message, "Cuidados com o Cabelo")
        elif "maquiagem" in message_lower:
            return self.answer_category_query(message, "Maquiagem")
            
        # Detectar perguntas sobre faixa de preço
        if "barato" in message_lower or "econômico" in message_lower:
            return self.answer_price_range_query(message, 0, 50)
        elif "caro" in message_lower or "premium" in message_lower:
            return self.answer_price_range_query(message, 100, 1000)
            
        # Caso padrão: busca geral de produtos
        return self.answer_product_query(message)


# Exemplo de uso
if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Criar agente
    agent = SalesAgentExample()
    
    # Exemplos de perguntas de clientes
    example_queries = [
        "Você tem algum produto para pele oleosa?",
        "Estou procurando um hidratante para o corpo",
        "Quero um shampoo para cabelos cacheados",
        "Vocês têm algum produto barato para limpeza facial?",
        "Estou procurando um perfume premium"
    ]
    
    # Processar cada pergunta
    print("=== EXEMPLOS DE INTERAÇÕES COM O AGENTE DE VENDAS ===\n")
    
    for query in example_queries:
        print(f"Cliente: {query}")
        response = agent.process_customer_message(query)
        print(f"Agente: {response}\n")
        print("-" * 80)
        print()
