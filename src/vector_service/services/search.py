"""
Serviço de Busca

Este módulo contém o serviço para busca semântica de produtos.
"""

import openai
import json
from typing import Dict, Any, List, Optional
import logging
import time
import hashlib

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SearchService:
    """
    Serviço para busca semântica de produtos.
    """
    
    def __init__(self, openai_api_key: str, qdrant_client, redis_client=None):
        """
        Inicializa o serviço de busca.
        
        Args:
            openai_api_key: Chave de API do OpenAI
            qdrant_client: Cliente do Qdrant
            redis_client: Cliente do Redis (opcional)
        """
        self.openai_api_key = openai_api_key
        openai.api_key = openai_api_key
        self.qdrant_client = qdrant_client
        self.redis_client = redis_client
        self.embedding_model = "text-embedding-3-small"
        self.cache_ttl = 60 * 60 * 24  # 24 horas em segundos
    
    def search(
        self, 
        account_id: str, 
        query: str, 
        limit: int = 10, 
        filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Realiza busca semântica de produtos.
        
        Args:
            account_id: ID da conta
            query: Consulta em linguagem natural
            limit: Número máximo de resultados
            filter: Filtros adicionais
            
        Returns:
            List[Dict[str, Any]]: Lista de resultados
        """
        start_time = time.time()
        logger.info(f"Searching for '{query}' in account {account_id}")
        
        # Verificar cache se disponível
        results = None
        if self.redis_client:
            cache_key = self._generate_cache_key(account_id, query, limit, filter)
            cached = self.redis_client.get(cache_key)
            if cached:
                try:
                    results = json.loads(cached)
                    logger.info(f"Found cached results for query: {query}")
                    return results
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON in cache for key: {cache_key}")
        
        # Determinar nome da coleção
        collection_name = f"products_{account_id}"
        
        # Verificar se a coleção existe
        try:
            collections = self.qdrant_client.get_collections()
            collection_names = [c.name for c in collections.collections]
            
            if collection_name not in collection_names:
                logger.warning(f"Collection {collection_name} does not exist")
                return []
        except Exception as e:
            logger.error(f"Error checking collections: {str(e)}")
            return []
        
        # Gerar embedding para a consulta
        query_embedding = self._generate_embedding(query)
        
        # Preparar filtros para Qdrant
        qdrant_filter = self._prepare_qdrant_filter(filter)
        
        # Realizar busca no Qdrant
        try:
            search_results = self.qdrant_client.search(
                collection_name=collection_name,
                query_vector=query_embedding,
                limit=limit,
                query_filter=qdrant_filter,
                with_payload=True
            )
            
            # Processar resultados
            results = []
            for result in search_results:
                processed_result = {
                    "id": result.id,
                    "score": result.score,
                    "metadata": result.payload
                }
                results.append(processed_result)
            
            # Armazenar em cache se disponível
            if self.redis_client and results:
                cache_key = self._generate_cache_key(account_id, query, limit, filter)
                self.redis_client.setex(
                    cache_key,
                    self.cache_ttl,
                    json.dumps(results)
                )
            
            elapsed_time = time.time() - start_time
            logger.info(f"Search completed in {elapsed_time:.2f} seconds, found {len(results)} results")
            
            return results
        except Exception as e:
            logger.error(f"Error searching in Qdrant: {str(e)}")
            return []
    
    def _generate_embedding(self, text: str) -> List[float]:
        """
        Gera embedding para o texto usando OpenAI.
        
        Args:
            text: Texto para gerar embedding
            
        Returns:
            List[float]: Vetor de embedding
        """
        try:
            response = openai.Embedding.create(
                model=self.embedding_model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            raise
    
    def _prepare_qdrant_filter(self, filter: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Prepara filtros para o Qdrant.
        
        Args:
            filter: Filtros em formato amigável
            
        Returns:
            Optional[Dict[str, Any]]: Filtros no formato do Qdrant
        """
        if not filter:
            return None
        
        # Exemplo de conversão de filtros simples
        # Na prática, isso seria mais complexo dependendo da estrutura dos filtros
        qdrant_filter = {"must": []}
        
        for key, value in filter.items():
            if isinstance(value, list):
                # Para listas, criar um filtro "should" (OR)
                should_conditions = []
                for item in value:
                    should_conditions.append({
                        "key": f"payload.{key}",
                        "match": {"value": item}
                    })
                if should_conditions:
                    qdrant_filter["must"].append({"should": should_conditions})
            else:
                # Para valores simples, criar um filtro "must" (AND)
                qdrant_filter["must"].append({
                    "key": f"payload.{key}",
                    "match": {"value": value}
                })
        
        return qdrant_filter if qdrant_filter["must"] else None
    
    def _generate_cache_key(
        self, 
        account_id: str, 
        query: str, 
        limit: int, 
        filter: Optional[Dict[str, Any]]
    ) -> str:
        """
        Gera uma chave de cache para a consulta.
        
        Args:
            account_id: ID da conta
            query: Consulta em linguagem natural
            limit: Número máximo de resultados
            filter: Filtros adicionais
            
        Returns:
            str: Chave de cache
        """
        # Normalizar a consulta (lowercase, remover espaços extras)
        normalized_query = " ".join(query.lower().split())
        
        # Serializar filtros de forma determinística
        filter_str = ""
        if filter:
            # Ordenar as chaves para garantir consistência
            sorted_filter = {k: filter[k] for k in sorted(filter.keys())}
            filter_str = json.dumps(sorted_filter, sort_keys=True)
        
        # Combinar os componentes
        combined = f"{account_id}:{normalized_query}:{limit}:{filter_str}"
        
        # Gerar hash MD5
        hash_obj = hashlib.md5(combined.encode())
        hash_str = hash_obj.hexdigest()
        
        return f"search:{hash_str}"
