"""
Serviço de Busca Híbrida para produtos.
Este serviço combina busca semântica no Qdrant com filtragem no PostgreSQL
para fornecer resultados relevantes e atualizados.
"""
import os
import logging
import json
from typing import List, Dict, Any, Optional, Tuple
from qdrant_client import QdrantClient
from qdrant_client.http import models

from .embedding_service import EmbeddingService
from .sync_service import PostgreSQLClient

class ProductSearchService:
    """
    Serviço de busca híbrida para produtos.
    
    Este serviço implementa uma estratégia de busca híbrida que combina:
    1. Busca semântica no banco vetorial (Qdrant)
    2. Filtragem e enriquecimento no banco relacional (PostgreSQL)
    
    Isso garante que os resultados sejam semanticamente relevantes para a consulta
    do usuário e também estejam atualizados em termos de disponibilidade, preço, etc.
    """
    
    def __init__(self, 
                 postgres_client: Optional[PostgreSQLClient] = None,
                 qdrant_client: Optional[QdrantClient] = None,
                 embedding_service: Optional[EmbeddingService] = None,
                 use_redis: bool = True):
        """
        Inicializa o serviço de busca híbrida.
        
        Args:
            postgres_client: Cliente PostgreSQL. Se não fornecido, será criado um novo.
            qdrant_client: Cliente Qdrant. Se não fornecido, será criado um novo.
            embedding_service: Serviço de embeddings. Se não fornecido, será criado um novo.
            use_redis: Se True, tentará usar Redis para cache. Se False, desativa o cache.
        """
        self.postgres = postgres_client or PostgreSQLClient()
        
        qdrant_url = os.environ.get("QDRANT_URL", "http://qdrant:6333")
        self.qdrant = qdrant_client or QdrantClient(url=qdrant_url)
        
        self.embedding_service = embedding_service or EmbeddingService()
        self.logger = logging.getLogger(__name__)
        
        # Configurar Redis para cache (opcional)
        self.redis = None
        if use_redis:
            try:
                import redis
                redis_url = os.environ.get("REDIS_URL")
                if redis_url:
                    self.redis = redis.from_url(redis_url)
                    self.logger.info("Cache Redis configurado com sucesso")
                else:
                    self.logger.warning("REDIS_URL não configurada, cache desativado")
            except ImportError:
                self.logger.warning("Pacote redis não instalado, cache desativado")
            except Exception as e:
                self.logger.error(f"Erro ao configurar Redis: {str(e)}")
        
        self.logger.info("Serviço de Busca Híbrida inicializado")
        
    def search_products(self, query: str, limit: int = 10, 
                        min_score: float = 0.7, 
                        filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Realiza busca híbrida por produtos.
        
        Este método:
        1. Converte a consulta em um embedding
        2. Busca produtos semanticamente relevantes no Qdrant
        3. Verifica disponibilidade e obtém dados atualizados no PostgreSQL
        4. Retorna os resultados ordenados por relevância
        
        Args:
            query: Consulta do usuário.
            limit: Número máximo de resultados a retornar.
            min_score: Pontuação mínima de relevância (0-1).
            filters: Filtros adicionais (categoria, faixa de preço, etc).
            
        Returns:
            Lista de produtos relevantes para a consulta.
        """
        # Verificar cache
        cache_key = None
        if self.redis:
            cache_key = f"product_search:{query}:{limit}:{min_score}:{json.dumps(filters) if filters else ''}"
            cached = self.redis.get(cache_key)
            if cached:
                try:
                    return json.loads(cached)
                except Exception as e:
                    self.logger.error(f"Erro ao carregar do cache: {str(e)}")
        
        # Gerar embedding para a consulta
        query_embedding = self.embedding_service.get_embedding(query)
        
        # Construir filtro para o Qdrant
        qdrant_filter = self._build_qdrant_filter(filters)
        
        # Buscar no Qdrant com filtro
        search_result = self.qdrant.search(
            collection_name="products",
            query_vector=query_embedding,
            query_filter=qdrant_filter,
            limit=limit * 2,  # Buscamos mais para compensar possíveis filtros
            score_threshold=min_score  # Filtra resultados com baixa relevância
        )
        
        if not search_result:
            return []
            
        # Extrair IDs e scores
        product_ids_with_scores = [(int(hit.id), hit.score) for hit in search_result]
        product_ids = [id for id, _ in product_ids_with_scores]
        
        if not product_ids:
            return []
        
        # Verificar disponibilidade e obter dados completos no PostgreSQL
        sql_filters = self._build_sql_filters(filters)
        
        query_parts = ["""
            SELECT p.id, p.name, p.description, p.price, p.detailed_information,
                   pc.name as category_name, COALESCE(i.quantity, 0) as stock
            FROM products p
            LEFT JOIN product_categories pc ON p.category_id = pc.id
            LEFT JOIN inventory i ON p.id = i.product_id
            WHERE p.id IN %s AND p.active = TRUE AND COALESCE(i.quantity, 0) > 0
        """]
        
        params = [tuple(product_ids)]
        
        # Adicionar filtros SQL adicionais
        if sql_filters:
            for sql_filter, filter_params in sql_filters:
                query_parts.append(sql_filter)
                params.extend(filter_params)
                
        query_sql = " AND ".join(query_parts)
        query_sql += " ORDER BY p.id"
        
        available_products = self.postgres.execute_query(query_sql, tuple(params))
        
        # Mapear IDs disponíveis
        available_ids = {p['id'] for p in available_products}
        
        # Filtrar e ordenar por relevância
        results = []
        for product_id, score in product_ids_with_scores:
            if product_id in available_ids:
                # Encontrar o produto completo
                for product in available_products:
                    if product['id'] == product_id:
                        product['relevance_score'] = score
                        results.append(product)
                        break
        
        # Armazenar em cache
        if self.redis and results and cache_key:
            try:
                self.redis.setex(
                    cache_key,
                    300,  # 5 minutos de cache
                    json.dumps(results)
                )
            except Exception as e:
                self.logger.error(f"Erro ao armazenar no cache: {str(e)}")
            
        return results[:limit]  # Garantir que não exceda o limite solicitado
    
    def _build_qdrant_filter(self, filters: Optional[Dict[str, Any]] = None) -> Optional[models.Filter]:
        """
        Constrói um filtro para o Qdrant com base nos filtros fornecidos.
        
        Args:
            filters: Dicionário de filtros.
            
        Returns:
            Filtro para o Qdrant ou None se não houver filtros.
        """
        must_conditions = [
            models.FieldCondition(key="active", match={"value": True})
        ]
        
        if not filters:
            return models.Filter(must=must_conditions)
            
        # Filtro por categoria
        if 'category' in filters:
            must_conditions.append(
                models.FieldCondition(key="category", match={"value": filters['category']})
            )
            
        # Filtro por faixa de preço
        if 'price_min' in filters or 'price_max' in filters:
            price_range = {}
            if 'price_min' in filters:
                price_range['gte'] = float(filters['price_min'])
            if 'price_max' in filters:
                price_range['lte'] = float(filters['price_max'])
                
            must_conditions.append(
                models.FieldCondition(key="price", range=models.Range(**price_range))
            )
            
        return models.Filter(must=must_conditions)
    
    def _build_sql_filters(self, filters: Optional[Dict[str, Any]] = None) -> List[Tuple[str, List[Any]]]:
        """
        Constrói filtros SQL com base nos filtros fornecidos.
        
        Args:
            filters: Dicionário de filtros.
            
        Returns:
            Lista de tuplas (condição SQL, parâmetros).
        """
        if not filters:
            return []
            
        sql_filters = []
        
        # Filtro por categoria
        if 'category' in filters:
            sql_filters.append(("pc.name = %s", [filters['category']]))
            
        # Filtro por faixa de preço
        if 'price_min' in filters:
            sql_filters.append(("p.price >= %s", [float(filters['price_min'])]))
        if 'price_max' in filters:
            sql_filters.append(("p.price <= %s", [float(filters['price_max'])]))
            
        return sql_filters
