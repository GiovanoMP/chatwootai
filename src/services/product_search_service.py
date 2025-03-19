"""
Serviço de Busca Híbrida de Produtos.
Este serviço implementa a busca híbrida de produtos, combinando o banco de dados
relacional (PostgreSQL) e o banco de dados vetorial (Qdrant).
"""
import os
import logging
import json
from typing import List, Dict, Any, Optional, Tuple
import psycopg2
from psycopg2.extras import RealDictCursor
from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter, FieldCondition, MatchValue

from src.services.embedding_service import EmbeddingService

class ProductSearchService:
    """
    Serviço para busca híbrida de produtos.
    
    Este serviço implementa a estratégia de busca híbrida, combinando o banco de dados
    relacional (PostgreSQL) para informações estruturadas e o banco de dados vetorial
    (Qdrant) para busca semântica.
    """
    
    def __init__(
        self, 
        db_connection_string: Optional[str] = None,
        qdrant_url: Optional[str] = None,
        embedding_service: Optional[EmbeddingService] = None,
        redis_client = None
    ):
        """
        Inicializa o serviço de busca híbrida de produtos.
        
        Args:
            db_connection_string: String de conexão com o PostgreSQL. Se não fornecida,
                                 será buscada na variável de ambiente DATABASE_URL.
            qdrant_url: URL do serviço Qdrant. Se não fornecida, será buscada na
                       variável de ambiente QDRANT_URL.
            embedding_service: Instância do EmbeddingService. Se não fornecida, uma nova
                              instância será criada.
            redis_client: Cliente Redis para cache (opcional).
        """
        self.db_connection_string = db_connection_string or os.environ.get("DATABASE_URL")
        if not self.db_connection_string:
            raise ValueError("String de conexão com o PostgreSQL não fornecida e não encontrada nas variáveis de ambiente")
            
        self.qdrant_url = qdrant_url or os.environ.get("QDRANT_URL")
        if not self.qdrant_url:
            raise ValueError("URL do Qdrant não fornecida e não encontrada nas variáveis de ambiente")
            
        self.embedding_service = embedding_service or EmbeddingService()
        self.redis_client = redis_client
        self.qdrant_client = QdrantClient(url=self.qdrant_url)
        self.logger = logging.getLogger(__name__)
        
        self.logger.info("Serviço de Busca Híbrida de Produtos inicializado")
        
    def _get_db_connection(self):
        """
        Obtém uma conexão com o banco de dados PostgreSQL.
        
        Returns:
            Conexão com o PostgreSQL.
        """
        return psycopg2.connect(self.db_connection_string)
        
    def _get_cache_key(self, query: str, limit: int, min_score: float, category_id: Optional[int] = None) -> str:
        """
        Gera uma chave de cache para a consulta.
        
        Args:
            query: Consulta do usuário.
            limit: Número máximo de resultados.
            min_score: Pontuação mínima para considerar um resultado relevante.
            category_id: ID da categoria para filtrar (opcional).
            
        Returns:
            Chave de cache.
        """
        key_parts = [
            f"query:{query}",
            f"limit:{limit}",
            f"min_score:{min_score}"
        ]
        
        if category_id is not None:
            key_parts.append(f"category_id:{category_id}")
            
        return f"product_search:{':'.join(key_parts)}"
        
    def _check_cache(self, cache_key: str) -> Optional[List[Dict[str, Any]]]:
        """
        Verifica se há resultados em cache para a consulta.
        
        Args:
            cache_key: Chave de cache.
            
        Returns:
            Lista de resultados ou None se não houver cache.
        """
        if not self.redis_client:
            return None
            
        cached = self.redis_client.get(cache_key)
        if cached:
            try:
                return json.loads(cached)
            except Exception as e:
                self.logger.warning(f"Erro ao decodificar cache: {e}")
                
        return None
        
    def _save_to_cache(self, cache_key: str, results: List[Dict[str, Any]], ttl: int = 3600) -> bool:
        """
        Salva resultados no cache.
        
        Args:
            cache_key: Chave de cache.
            results: Lista de resultados.
            ttl: Tempo de vida do cache em segundos (padrão: 1 hora).
            
        Returns:
            True se o cache foi salvo com sucesso, False caso contrário.
        """
        if not self.redis_client:
            return False
            
        try:
            self.redis_client.setex(
                cache_key,
                ttl,
                json.dumps(results)
            )
            return True
        except Exception as e:
            self.logger.warning(f"Erro ao salvar no cache: {e}")
            return False
            
    def search_products(
        self, 
        query: str, 
        limit: int = 5, 
        min_score: float = 0.7,
        category_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Realiza uma busca híbrida por produtos.
        
        Esta função combina a busca semântica do Qdrant com a verificação
        de disponibilidade e informações detalhadas do PostgreSQL.
        
        Args:
            query: Consulta do usuário.
            limit: Número máximo de resultados.
            min_score: Pontuação mínima para considerar um resultado relevante.
            category_id: ID da categoria para filtrar (opcional).
            
        Returns:
            Lista de produtos encontrados, ordenados por relevância.
        """
        # Verificar cache
        cache_key = self._get_cache_key(query, limit, min_score, category_id)
        cached_results = self._check_cache(cache_key)
        if cached_results:
            self.logger.info(f"Resultados encontrados no cache para '{query}'")
            return cached_results
            
        try:
            # 1. Converter a consulta em embedding
            query_embedding = self.embedding_service.get_embedding(query)
            
            # 2. Preparar filtro para o Qdrant
            qdrant_filter = Filter(
                must=[
                    FieldCondition(
                        key="active",
                        match=MatchValue(value=True)
                    )
                ]
            )
            
            # Adicionar filtro de categoria se especificado
            if category_id is not None:
                qdrant_filter.must.append(
                    FieldCondition(
                        key="category_id",
                        match=MatchValue(value=category_id)
                    )
                )
            
            # 3. Buscar no Qdrant produtos semanticamente relevantes
            qdrant_results = self.qdrant_client.search(
                collection_name="products",
                query_vector=query_embedding,
                query_filter=qdrant_filter,
                limit=limit * 2,  # Buscamos mais resultados para compensar possíveis filtros posteriores
                score_threshold=min_score
            )
            
            if not qdrant_results:
                self.logger.info(f"Nenhum produto encontrado no Qdrant para '{query}'")
                return []
                
            # 4. Extrair IDs dos produtos encontrados
            product_ids = [int(result.id) for result in qdrant_results]
            product_scores = {int(result.id): result.score for result in qdrant_results}
            
            # 5. Verificar disponibilidade e obter detalhes no PostgreSQL
            with self._get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    # Construir a consulta SQL
                    sql = """
                        SELECT p.*, pc.name as category_name
                        FROM products p
                        JOIN product_categories pc ON p.category_id = pc.id
                        WHERE p.id = ANY(%s) AND p.active = TRUE
                    """
                    
                    # Adicionar filtro de categoria se especificado
                    params = [product_ids]
                    if category_id is not None:
                        sql += " AND p.category_id = %s"
                        params.append(category_id)
                        
                    # Executar a consulta
                    cursor.execute(sql, params)
                    products = cursor.fetchall()
                    
            # 6. Converter resultados para dicionários e adicionar score
            results = []
            for product in products:
                product_dict = dict(product)
                product_dict["score"] = product_scores.get(product_dict["id"], 0)
                results.append(product_dict)
                
            # 7. Ordenar por relevância (score)
            results.sort(key=lambda x: x["score"], reverse=True)
            
            # 8. Limitar ao número solicitado
            results = results[:limit]
            
            # 9. Salvar no cache
            self._save_to_cache(cache_key, results)
            
            self.logger.info(f"Encontrados {len(results)} produtos para '{query}'")
            return results
            
        except Exception as e:
            self.logger.error(f"Erro ao buscar produtos: {e}")
            return []
            
    def search_business_rules(
        self, 
        query: str, 
        limit: int = 3, 
        min_score: float = 0.7,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Realiza uma busca híbrida por regras de negócio.
        
        Esta função combina a busca semântica do Qdrant com a verificação
        de ativação e informações detalhadas do PostgreSQL.
        
        Args:
            query: Consulta do usuário.
            limit: Número máximo de resultados.
            min_score: Pontuação mínima para considerar um resultado relevante.
            category: Categoria para filtrar (opcional).
            
        Returns:
            Lista de regras de negócio encontradas, ordenadas por relevância.
        """
        # Verificar cache
        cache_key = f"business_rule_search:query:{query}:limit:{limit}:min_score:{min_score}"
        if category:
            cache_key += f":category:{category}"
            
        cached_results = self._check_cache(cache_key)
        if cached_results:
            self.logger.info(f"Resultados encontrados no cache para '{query}'")
            return cached_results
            
        try:
            # 1. Converter a consulta em embedding
            query_embedding = self.embedding_service.get_embedding(query)
            
            # 2. Preparar filtro para o Qdrant
            qdrant_filter = Filter(
                must=[
                    FieldCondition(
                        key="active",
                        match=MatchValue(value=True)
                    )
                ]
            )
            
            # Adicionar filtro de categoria se especificado
            if category:
                qdrant_filter.must.append(
                    FieldCondition(
                        key="category",
                        match=MatchValue(value=category)
                    )
                )
            
            # 3. Buscar no Qdrant regras semanticamente relevantes
            qdrant_results = self.qdrant_client.search(
                collection_name="business_rules",
                query_vector=query_embedding,
                query_filter=qdrant_filter,
                limit=limit * 2,  # Buscamos mais resultados para compensar possíveis filtros posteriores
                score_threshold=min_score
            )
            
            if not qdrant_results:
                self.logger.info(f"Nenhuma regra de negócio encontrada no Qdrant para '{query}'")
                return []
                
            # 4. Extrair IDs das regras encontradas
            rule_ids = [int(result.id) for result in qdrant_results]
            rule_scores = {int(result.id): result.score for result in qdrant_results}
            
            # 5. Verificar ativação e obter detalhes no PostgreSQL
            with self._get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    # Construir a consulta SQL
                    sql = """
                        SELECT *
                        FROM business_rules
                        WHERE id = ANY(%s) AND active = TRUE
                    """
                    
                    # Adicionar filtro de categoria se especificado
                    params = [rule_ids]
                    if category:
                        sql += " AND category = %s"
                        params.append(category)
                        
                    # Executar a consulta
                    cursor.execute(sql, params)
                    rules = cursor.fetchall()
                    
            # 6. Converter resultados para dicionários e adicionar score
            results = []
            for rule in rules:
                rule_dict = dict(rule)
                rule_dict["score"] = rule_scores.get(rule_dict["id"], 0)
                results.append(rule_dict)
                
            # 7. Ordenar por relevância (score)
            results.sort(key=lambda x: x["score"], reverse=True)
            
            # 8. Limitar ao número solicitado
            results = results[:limit]
            
            # 9. Salvar no cache
            self._save_to_cache(cache_key, results)
            
            self.logger.info(f"Encontradas {len(results)} regras de negócio para '{query}'")
            return results
            
        except Exception as e:
            self.logger.error(f"Erro ao buscar regras de negócio: {e}")
            return []
            
    def format_product_results(self, products: List[Dict[str, Any]]) -> str:
        """
        Formata os resultados da busca de produtos para exibição.
        
        Args:
            products: Lista de produtos encontrados.
            
        Returns:
            String formatada com os resultados.
        """
        if not products:
            return "Não foram encontrados produtos que correspondam à sua busca."
            
        result = "Encontrei os seguintes produtos que podem te interessar:\n\n"
        
        for i, product in enumerate(products, 1):
            result += f"**{i}. {product['name']}**\n"
            result += f"Categoria: {product.get('category_name', 'N/A')}\n"
            result += f"Preço: R$ {float(product['price']):.2f}\n"
            
            if product.get('description'):
                result += f"Descrição: {product['description']}\n"
                
            if product.get('benefits'):
                result += f"Benefícios: {product['benefits']}\n"
                
            result += f"Relevância: {product['score']:.2f}\n\n"
            
        return result
        
    def format_business_rule_results(self, rules: List[Dict[str, Any]]) -> str:
        """
        Formata os resultados da busca de regras de negócio para exibição.
        
        Args:
            rules: Lista de regras de negócio encontradas.
            
        Returns:
            String formatada com os resultados.
        """
        if not rules:
            return "Não foram encontradas regras de negócio que correspondam à sua busca."
            
        result = "Encontrei as seguintes regras de negócio relevantes:\n\n"
        
        for i, rule in enumerate(rules, 1):
            result += f"**{i}. {rule['name']}**\n"
            result += f"Categoria: {rule.get('category', 'N/A')}\n"
            
            if rule.get('description'):
                result += f"Descrição: {rule['description']}\n"
                
            if rule.get('rule_text'):
                result += f"Regra:\n{rule['rule_text']}\n"
                
            result += f"Relevância: {rule['score']:.2f}\n\n"
            
        return result
