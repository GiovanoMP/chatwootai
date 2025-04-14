# -*- coding: utf-8 -*-

"""
Serviço de cache com Redis.
"""

import json
import logging
from typing import Any, Dict, List, Optional, Union
import redis.asyncio as redis
from redis.asyncio.connection import ConnectionPool

from odoo_api.config.settings import settings
from odoo_api.core.exceptions import CacheError

logger = logging.getLogger(__name__)

class CacheService:
    """Serviço de cache com Redis."""
    
    def __init__(self):
        """Inicializa o serviço de cache."""
        self.pool = None
        self.redis = None
        self.default_ttl = settings.CACHE_TTL_DEFAULT
    
    async def connect(self):
        """Conecta ao Redis."""
        try:
            self.pool = ConnectionPool(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD,
                decode_responses=True,
            )
            
            self.redis = redis.Redis(connection_pool=self.pool)
            
            # Verificar conexão
            await self.redis.ping()
            
            logger.info(f"Connected to Redis at {settings.REDIS_HOST}:{settings.REDIS_PORT}")
        
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise CacheError(f"Failed to connect to Redis: {e}")
    
    async def disconnect(self):
        """Desconecta do Redis."""
        if self.pool:
            await self.pool.disconnect()
            logger.info("Disconnected from Redis")
    
    async def get(self, key: str) -> Any:
        """
        Obtém um valor do cache.
        
        Args:
            key: Chave do cache
        
        Returns:
            Valor armazenado ou None se não encontrado
        """
        try:
            if not self.redis:
                await self.connect()
            
            value = await self.redis.get(key)
            
            if value:
                return json.loads(value)
            
            return None
        
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON from cache for key {key}: {e}")
            return None
        
        except Exception as e:
            logger.error(f"Failed to get value from cache for key {key}: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """
        Define um valor no cache.
        
        Args:
            key: Chave do cache
            value: Valor a ser armazenado
            ttl: Tempo de vida em segundos (se None, usa o padrão)
        
        Returns:
            True se a operação for bem-sucedida
        """
        try:
            if not self.redis:
                await self.connect()
            
            serialized = json.dumps(value)
            ttl = ttl or self.default_ttl
            
            await self.redis.set(key, serialized, ex=ttl)
            return True
        
        except Exception as e:
            logger.error(f"Failed to set value in cache for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """
        Remove um valor do cache.
        
        Args:
            key: Chave do cache
        
        Returns:
            True se a operação for bem-sucedida
        """
        try:
            if not self.redis:
                await self.connect()
            
            await self.redis.delete(key)
            return True
        
        except Exception as e:
            logger.error(f"Failed to delete value from cache for key {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """
        Verifica se uma chave existe no cache.
        
        Args:
            key: Chave do cache
        
        Returns:
            True se a chave existir
        """
        try:
            if not self.redis:
                await self.connect()
            
            return await self.redis.exists(key) > 0
        
        except Exception as e:
            logger.error(f"Failed to check if key {key} exists in cache: {e}")
            return False
    
    async def get_ttl(self, key: str) -> Optional[int]:
        """
        Obtém o tempo de vida restante de uma chave.
        
        Args:
            key: Chave do cache
        
        Returns:
            Tempo de vida em segundos ou None se a chave não existir
        """
        try:
            if not self.redis:
                await self.connect()
            
            ttl = await self.redis.ttl(key)
            return ttl if ttl > 0 else None
        
        except Exception as e:
            logger.error(f"Failed to get TTL for key {key}: {e}")
            return None
    
    async def keys(self, pattern: str) -> List[str]:
        """
        Obtém chaves que correspondem a um padrão.
        
        Args:
            pattern: Padrão de chave (ex: "account_1:*")
        
        Returns:
            Lista de chaves
        """
        try:
            if not self.redis:
                await self.connect()
            
            return await self.redis.keys(pattern)
        
        except Exception as e:
            logger.error(f"Failed to get keys matching pattern {pattern}: {e}")
            return []
    
    async def flush_all(self) -> bool:
        """
        Remove todos os valores do cache.
        
        Returns:
            True se a operação for bem-sucedida
        """
        try:
            if not self.redis:
                await self.connect()
            
            await self.redis.flushall()
            return True
        
        except Exception as e:
            logger.error(f"Failed to flush cache: {e}")
            return False
    
    # Métodos específicos para o contexto da aplicação
    
    async def get_account_config(self, account_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtém a configuração de uma conta do cache.
        
        Args:
            account_id: ID da conta
        
        Returns:
            Configuração da conta ou None se não encontrada
        """
        key = f"{account_id}:config"
        return await self.get(key)
    
    async def set_account_config(self, account_id: str, config: Dict[str, Any], ttl: int = None) -> bool:
        """
        Define a configuração de uma conta no cache.
        
        Args:
            account_id: ID da conta
            config: Configuração da conta
            ttl: Tempo de vida em segundos (se None, usa o padrão)
        
        Returns:
            True se a operação for bem-sucedida
        """
        key = f"{account_id}:config"
        return await self.set(key, config, ttl)
    
    async def get_product(self, account_id: str, product_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtém um produto do cache.
        
        Args:
            account_id: ID da conta
            product_id: ID do produto
        
        Returns:
            Dados do produto ou None se não encontrado
        """
        key = f"{account_id}:product:{product_id}"
        return await self.get(key)
    
    async def set_product(self, account_id: str, product_id: int, data: Dict[str, Any], ttl: int = None) -> bool:
        """
        Define um produto no cache.
        
        Args:
            account_id: ID da conta
            product_id: ID do produto
            data: Dados do produto
            ttl: Tempo de vida em segundos (se None, usa o padrão)
        
        Returns:
            True se a operação for bem-sucedida
        """
        key = f"{account_id}:product:{product_id}"
        return await self.set(key, data, ttl or settings.CACHE_TTL_PRODUCT)
    
    async def invalidate_product(self, account_id: str, product_id: int) -> bool:
        """
        Invalida um produto no cache.
        
        Args:
            account_id: ID da conta
            product_id: ID do produto
        
        Returns:
            True se a operação for bem-sucedida
        """
        key = f"{account_id}:product:{product_id}"
        return await self.delete(key)
    
    async def get_temporary_rule(self, account_id: str, rule_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtém uma regra temporária do cache.
        
        Args:
            account_id: ID da conta
            rule_id: ID da regra
        
        Returns:
            Dados da regra ou None se não encontrada
        """
        key = f"{account_id}:temp_rule:{rule_id}"
        return await self.get(key)
    
    async def set_temporary_rule(self, account_id: str, rule_id: int, data: Dict[str, Any], ttl: int = None) -> bool:
        """
        Define uma regra temporária no cache.
        
        Args:
            account_id: ID da conta
            rule_id: ID da regra
            data: Dados da regra
            ttl: Tempo de vida em segundos (se None, usa o padrão)
        
        Returns:
            True se a operação for bem-sucedida
        """
        key = f"{account_id}:temp_rule:{rule_id}"
        return await self.set(key, data, ttl or settings.CACHE_TTL_RULE)
    
    async def invalidate_temporary_rule(self, account_id: str, rule_id: int) -> bool:
        """
        Invalida uma regra temporária no cache.
        
        Args:
            account_id: ID da conta
            rule_id: ID da regra
        
        Returns:
            True se a operação for bem-sucedida
        """
        key = f"{account_id}:temp_rule:{rule_id}"
        return await self.delete(key)
    
    async def get_active_temporary_rules(self, account_id: str) -> List[int]:
        """
        Obtém os IDs das regras temporárias ativas.
        
        Args:
            account_id: ID da conta
        
        Returns:
            Lista de IDs de regras
        """
        key = f"{account_id}:active_temp_rules"
        result = await self.get(key)
        return result or []
    
    async def set_active_temporary_rules(self, account_id: str, rule_ids: List[int], ttl: int = None) -> bool:
        """
        Define os IDs das regras temporárias ativas.
        
        Args:
            account_id: ID da conta
            rule_ids: Lista de IDs de regras
            ttl: Tempo de vida em segundos (se None, usa o padrão)
        
        Returns:
            True se a operação for bem-sucedida
        """
        key = f"{account_id}:active_temp_rules"
        return await self.set(key, rule_ids, ttl or settings.CACHE_TTL_RULE)
    
    async def get_search_results(self, account_id: str, query_hash: str) -> Optional[Dict[str, Any]]:
        """
        Obtém resultados de busca do cache.
        
        Args:
            account_id: ID da conta
            query_hash: Hash da consulta
        
        Returns:
            Resultados da busca ou None se não encontrados
        """
        key = f"{account_id}:search:{query_hash}"
        return await self.get(key)
    
    async def set_search_results(self, account_id: str, query_hash: str, results: Dict[str, Any], ttl: int = None) -> bool:
        """
        Define resultados de busca no cache.
        
        Args:
            account_id: ID da conta
            query_hash: Hash da consulta
            results: Resultados da busca
            ttl: Tempo de vida em segundos (se None, usa o padrão)
        
        Returns:
            True se a operação for bem-sucedida
        """
        key = f"{account_id}:search:{query_hash}"
        return await self.set(key, results, ttl)


# Instância global do serviço de cache
cache_service = CacheService()

# Função para obter o serviço de cache
async def get_cache_service() -> CacheService:
    """
    Obtém o serviço de cache.
    
    Returns:
        Instância do serviço de cache
    """
    if not cache_service.redis:
        await cache_service.connect()
    
    return cache_service
