"""
ProductDataService - Serviço para acesso e gerenciamento de dados de produtos.

Este serviço implementa funcionalidades específicas para produtos,
incluindo busca por categorias, filtragem por atributos e integração
com busca vetorial.
"""

import logging
from typing import Dict, Any, List, Union, Optional

from .base_data_service import BaseDataService

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProductDataService(BaseDataService):
    """
    Serviço de dados especializado em produtos.
    
    Implementa operações específicas para produtos, incluindo:
    - Busca por categorias
    - Filtragem por atributos
    - Integração com busca vetorial (Qdrant)
    - Gerenciamento de estoque
    """
    
    def __init__(self, data_service_hub, qdrant_client=None):
        """
        Inicializa o serviço de dados de produtos.
        
        Args:
            data_service_hub: Instância do DataServiceHub.
            qdrant_client: Cliente Qdrant para busca vetorial (opcional).
        """
        super().__init__(data_service_hub)
        self.qdrant_client = qdrant_client
        self.collection_name = "products"
        
        logger.info("ProductDataService inicializado")
    
    def get_entity_type(self) -> str:
        """
        Retorna o tipo de entidade gerenciada por este serviço.
        
        Returns:
            String representando o tipo de entidade.
        """
        return "products"
    
    def get_by_category(self, category_id: int, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Obtém produtos por categoria.
        
        Args:
            category_id: ID da categoria.
            limit: Limite de resultados.
            offset: Deslocamento para paginação.
            
        Returns:
            Lista de produtos na categoria.
        """
        query = """
            SELECT p.* FROM products p
            JOIN product_categories pc ON p.id = pc.product_id
            WHERE pc.category_id = %(category_id)s
            ORDER BY p.name
            LIMIT %(limit)s OFFSET %(offset)s
        """
        
        params = {
            "category_id": category_id,
            "limit": limit,
            "offset": offset
        }
        
        return self.hub.execute_query(query, params) or []
    
    def get_by_attributes(self, attributes: Dict[str, Any], limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Obtém produtos que correspondem aos atributos especificados.
        
        Args:
            attributes: Dicionário de atributos e valores.
            limit: Limite de resultados.
            offset: Deslocamento para paginação.
            
        Returns:
            Lista de produtos que correspondem aos atributos.
        """
        # Construir cláusulas WHERE para cada atributo
        where_clauses = []
        params = {}
        
        for idx, (key, value) in enumerate(attributes.items()):
            param_name = f"attr_{idx}"
            param_value = f"value_{idx}"
            
            where_clauses.append(f"(pa.attribute_name = %({param_name})s AND pa.attribute_value = %({param_value})s)")
            params[param_name] = key
            params[param_value] = value
        
        # Construir consulta
        where_clause = " OR ".join(where_clauses)
        
        query = f"""
            SELECT p.*, COUNT(DISTINCT pa.attribute_name) as match_count
            FROM products p
            JOIN product_attributes pa ON p.id = pa.product_id
            WHERE {where_clause}
            GROUP BY p.id
            HAVING COUNT(DISTINCT pa.attribute_name) = %(attr_count)s
            ORDER BY p.name
            LIMIT %(limit)s OFFSET %(offset)s
        """
        
        params["attr_count"] = len(attributes)
        params["limit"] = limit
        params["offset"] = offset
        
        return self.hub.execute_query(query, params) or []
    
    def search_by_text(self, query_text: str, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Realiza busca textual em produtos.
        
        Args:
            query_text: Texto de consulta.
            limit: Limite de resultados.
            offset: Deslocamento para paginação.
            
        Returns:
            Lista de produtos que correspondem à consulta.
        """
        # Utilizando ILIKE para busca simples
        # Em uma implementação real, você pode usar recursos mais avançados como
        # Full Text Search do PostgreSQL ou Elasticsearch
        
        search_query = f"""
            SELECT * FROM products
            WHERE 
                name ILIKE %(search_term)s OR
                description ILIKE %(search_term)s OR
                detailed_description ILIKE %(search_term)s
            ORDER BY name
            LIMIT %(limit)s OFFSET %(offset)s
        """
        
        params = {
            "search_term": f"%{query_text}%",
            "limit": limit,
            "offset": offset
        }
        
        logger.info(f"Realizando busca de produtos com texto: '{query_text}'")
        result = self.hub.execute_query(search_query, params) or []
        logger.info(f"Busca retornou {len(result)} resultados")
        return result
    
    def vector_search(self, query_text: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Realiza busca vetorial em produtos usando Qdrant.
        
        Args:
            query_text: Texto de consulta.
            limit: Limite de resultados.
            
        Returns:
            Lista de produtos semanticamente similares à consulta.
        """
        if not self.qdrant_client:
            logger.warning("Tentativa de busca vetorial sem cliente Qdrant configurado")
            return []
        
        try:
            # Aqui você precisaria:
            # 1. Converter o query_text para um vetor usando um modelo de embeddings
            # 2. Realizar a busca no Qdrant
            # 3. Recuperar os produtos pelo ID
            
            # Exemplo conceitual (não funcional):
            # embedding = self.get_embedding(query_text)
            # search_result = self.qdrant_client.search(
            #     collection_name=self.collection_name,
            #     query_vector=embedding,
            #     limit=limit
            # )
            # product_ids = [hit.id for hit in search_result]
            
            # Como não temos o código completo da integração com Qdrant,
            # retornaremos uma lista vazia por enquanto
            logger.info(f"Busca vetorial para: '{query_text}'")
            return []
        
        except Exception as e:
            logger.error(f"Erro na busca vetorial: {str(e)}")
            return []
    
    def hybrid_search(self, query_text: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Realiza busca híbrida combinando resultados textuais e vetoriais.
        
        Args:
            query_text: Texto de consulta.
            limit: Limite de resultados.
            
        Returns:
            Lista combinada de produtos, ordenados por relevância.
        """
        # Obter resultados de busca textual
        text_results = self.search_by_text(query_text, limit=limit)
        
        # Obter resultados de busca vetorial
        vector_results = self.vector_search(query_text, limit=limit)
        
        # Em uma implementação real, você combinaria e reordenaria os resultados
        # com base em um algoritmo de relevância. Por simplicidade, vamos
        # apenas concatenar e limitar os resultados.
        
        # Criar um dicionário para eliminar duplicatas (por ID)
        combined_results = {}
        
        # Adicionar resultados textuais
        for product in text_results:
            combined_results[product['id']] = product
        
        # Adicionar resultados vetoriais
        for product in vector_results:
            if product['id'] not in combined_results:
                combined_results[product['id']] = product
        
        # Converter de volta para lista e limitar
        results = list(combined_results.values())
        
        return results[:limit]
    
    def get_stock_status(self, product_id: int) -> Dict[str, Any]:
        """
        Obtém o status de estoque de um produto.
        
        Args:
            product_id: ID do produto.
            
        Returns:
            Informações de estoque do produto.
        """
        query = """
            SELECT 
                p.id, 
                p.name, 
                i.quantity, 
                i.last_updated,
                i.status
            FROM products p
            JOIN inventory i ON p.id = i.product_id
            WHERE p.id = %(product_id)s
        """
        
        params = {"product_id": product_id}
        
        result = self.hub.execute_query(query, params, fetch_all=False)
        
        if not result:
            return {
                "product_id": product_id,
                "in_stock": False,
                "quantity": 0,
                "status": "unavailable"
            }
        
        return {
            "product_id": product_id,
            "product_name": result.get("name"),
            "in_stock": result.get("quantity", 0) > 0,
            "quantity": result.get("quantity", 0),
            "last_updated": result.get("last_updated"),
            "status": result.get("status", "unavailable")
        }
    
    def get_related_products(self, product_id: int, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Obtém produtos relacionados a um produto específico.
        
        Args:
            product_id: ID do produto.
            limit: Número máximo de produtos relacionados.
            
        Returns:
            Lista de produtos relacionados.
        """
        # Buscar produtos relacionados com base em categorias comuns
        query = """
            SELECT p.* FROM products p
            JOIN product_categories pc1 ON p.id = pc1.product_id
            JOIN product_categories pc2 ON pc1.category_id = pc2.category_id
            WHERE 
                pc2.product_id = %(product_id)s AND
                p.id != %(product_id)s
            GROUP BY p.id
            ORDER BY COUNT(DISTINCT pc1.category_id) DESC, p.name
            LIMIT %(limit)s
        """
        
        params = {
            "product_id": product_id,
            "limit": limit
        }
        
        return self.hub.execute_query(query, params) or []
