"""
Cache tools for the hub-and-spoke architecture.

This module implements a two-level caching system using Redis:
1. Local in-memory cache for fastest access
2. Redis-based distributed cache for shared access
"""

import json
import logging
import time
from typing import Dict, Any, Optional, Union, Callable
from functools import lru_cache
from redis import Redis
from crewai.tools.base_tool import BaseTool

logger = logging.getLogger(__name__)


class RedisCacheTool:
    """Tool for caching data using Redis."""
    
    def __init__(self, 
                 redis_client: Redis,
                 prefix: str = "",
                 default_ttl: int = 3600,
                 local_cache_size: int = 128):
        """
        Initialize the Redis cache tool.
        
        Args:
            redis_client: Redis client instance
            prefix: Prefix for Redis keys
            default_ttl: Default time-to-live in seconds
            local_cache_size: Size of the local LRU cache
        """
        # Verificar e reconectar com o Redis se necessário
        try:
            redis_client.ping()
            logger.info(f"RedisCacheTool: conexão Redis OK")
        except Exception as e:
            logger.error(f"RedisCacheTool: erro na conexão Redis: {e}")
            # Tentar reconectar com endereço IP explícito
            import os
            redis_url = os.getenv('REDIS_URL', 'redis://172.24.0.5:6379/0')
            logger.info(f"RedisCacheTool: tentando reconectar ao Redis usando URL: {redis_url}")
            try:
                redis_client = Redis.from_url(redis_url)
                redis_client.ping()
                logger.info("RedisCacheTool: reconexão com Redis bem-sucedida")
            except Exception as e2:
                logger.error(f"RedisCacheTool: falha na reconexão com Redis: {e2}")
                
        self.redis = redis_client
        self.prefix = prefix
        self.default_ttl = default_ttl
        
        # Create a local cache with LRU eviction
        @lru_cache(maxsize=local_cache_size)
        def cached_get(key: str) -> Optional[Any]:
            try:
                data = self.redis.get(key)
                if data:
                    return json.loads(data)
                return None
            except Exception as e:
                logger.error(f"Error retrieving from Redis cache: {e}")
                return None
        
        self.cached_get = cached_get
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache.
        
        Args:
            key: The key to get
            
        Returns:
            The value or None if not found
        """
        try:
            full_key = f"{self.prefix}{key}" if self.prefix else key
            
            # Try to get from local cache first
            return self.cached_get(full_key)
        except Exception as e:
            logger.error(f"Error retrieving from Redis cache: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set a value in the cache.
        
        Args:
            key: The key to set
            value: The value to set
            ttl: Time-to-live in seconds (None for default)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            full_key = f"{self.prefix}{key}" if self.prefix else key
            ttl = ttl if ttl is not None else self.default_ttl
            
            # Serialize the value
            serialized = json.dumps(value)
            
            # Verificar conexão Redis antes de tentar definir
            try:
                # Verificar conexão com ping (operação leve)
                self.redis.ping()
            except Exception as e:
                logger.warning(f"Redis indisponível para cache.set({key}): {e}")
                # Tentar reconectar com endereço IP explícito
                import os
                redis_url = os.getenv('REDIS_URL', 'redis://172.24.0.5:6379/0')
                try:
                    logger.info(f"Tentando reconectar ao Redis usando URL: {redis_url}")
                    self.redis = Redis.from_url(redis_url)
                    self.redis.ping()
                    logger.info("Reconexão com Redis bem-sucedida")
                except Exception as e2:
                    logger.error(f"Falha na reconexão com Redis: {e2}")
                    return False
            
            # Store in Redis with TTL
            self.redis.setex(full_key, ttl, serialized)
            
            # Invalidate local cache for this key
            self.cached_get.cache_clear()
            
            return True
        except Exception as e:
            logger.error(f"Error setting Redis cache: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        Delete a value from the cache.
        
        Args:
            key: The key to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            full_key = f"{self.prefix}{key}" if self.prefix else key
            
            # Delete from Redis
            self.redis.delete(full_key)
            
            # Invalidate local cache
            self.cached_get.cache_clear()
            
            return True
        except Exception as e:
            logger.error(f"Error deleting from Redis cache: {e}")
            return False
    
    def clear_prefix(self, prefix: Optional[str] = None) -> bool:
        """
        Clear all keys with the given prefix.
        
        Args:
            prefix: Prefix to clear (defaults to instance prefix)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            prefix_to_clear = prefix if prefix is not None else self.prefix
            pattern = f"{prefix_to_clear}*"
            
            # Get all matching keys
            keys = self.redis.keys(pattern)
            
            if keys:
                # Delete all matching keys
                self.redis.delete(*keys)
            
            # Invalidate local cache
            self.cached_get.cache_clear()
            
            return True
        except Exception as e:
            logger.error(f"Error clearing prefix from Redis cache: {e}")
            return False
    
    def cached(self, ttl: Optional[int] = None, key_fn: Optional[Callable] = None):
        """
        Decorator for caching function results.
        
        Args:
            ttl: Time-to-live in seconds (None for default)
            key_fn: Function to generate cache key from args and kwargs
            
        Returns:
            Decorator function
        """
        def decorator(func):
            def wrapper(*args, **kwargs):
                # Generate cache key
                if key_fn:
                    cache_key = key_fn(*args, **kwargs)
                else:
                    # Default key generation
                    arg_str = ":".join(str(arg) for arg in args)
                    kwarg_str = ":".join(f"{k}={v}" for k, v in sorted(kwargs.items()))
                    cache_key = f"{func.__name__}:{arg_str}:{kwarg_str}"
                
                # Try to get from cache
                cached_result = self.get(cache_key)
                if cached_result is not None:
                    return cached_result
                
                # Call the function
                result = func(*args, **kwargs)
                
                # Cache the result
                self.set(cache_key, result, ttl)
                
                return result
            
            return wrapper
        
        return decorator


class TwoLevelCache(BaseTool):
    """Two-level caching system with local and Redis caches."""
    
    name: str = "cache_tool"
    description: str = "Manages data caching with a two-level system (local memory and Redis)."
    
    # Configuração do modelo para permitir tipos arbitrários
    model_config = {"arbitrary_types_allowed": True}
    
    # Definir campos Pydantic
    redis_client: Redis
    prefix: str = ""
    default_ttl: int = 3600
    local_cache_size: int = 1024
    
    # Campos não-Pydantic que serão inicializados no __init__
    redis_cache: Any = None
    memory_cache: Any = None
    local_cache: Dict[str, Dict[str, Any]] = {}
    
    def __init__(self, 
                 redis_client: Redis,
                 prefix: str = "",
                 default_ttl: int = 3600,
                 local_cache_size: int = 1024):
        """
        Initialize the two-level cache.
        
        Args:
            redis_client: Redis client instance
            prefix: Prefix for Redis keys
            default_ttl: Default time-to-live in seconds
            local_cache_size: Size of the local LRU cache
        """
        # Log para depuração da conexão Redis
        logger.info(f"Inicializando TwoLevelCache com Redis: {redis_client}")
        try:
            redis_info = redis_client.info()
            logger.info(f"Redis conectado com sucesso: {redis_info.get('redis_version', 'desconhecido')}")
        except Exception as e:
            logger.error(f"Erro ao conectar ao Redis: {e}")
            # Tentar reconectar com endereço IP explícito
            import os
            redis_url = os.getenv('REDIS_URL', 'redis://172.24.0.5:6379/0')
            logger.info(f"Tentando reconectar ao Redis usando URL: {redis_url}")
            try:
                redis_client = Redis.from_url(redis_url)
                redis_client.ping()
                logger.info("Reconexão com Redis bem-sucedida")
            except Exception as e2:
                logger.error(f"Falha na reconexão com Redis: {e2}")
        
        # Inicializar os campos Pydantic através do construtor da classe pai
        super().__init__(
            redis_client=redis_client,
            prefix=prefix,
            default_ttl=default_ttl,
            local_cache_size=local_cache_size
        )

        # Inicializar o cache Redis
        self.redis_cache = RedisCacheTool(
            redis_client=self.redis_client,
            prefix=self.prefix,
            default_ttl=self.default_ttl,
            local_cache_size=self.local_cache_size
        )
        
        # O local_cache já foi definido como campo da classe
        # Não precisamos redefinir o local_cache_size pois já foi inicializado pelo super().__init__
    
    def _run(self, action: str, key: str, value: str = None, ttl: int = None) -> str:
        """
        Execute the tool as required by BaseTool.
        
        Args:
            action: The cache operation to perform (get, set, delete, clear)
            key: The cache key
            value: The value to set (for 'set' action)
            ttl: Time-to-live in seconds (for 'set' action)
            
        Returns:
            String representation of the operation result
        """
        if action.lower() == 'get':
            result = self.get(key)
            if result is None:
                return f"No value found for key '{key}'"
            if isinstance(result, (dict, list)):
                return f"Value for key '{key}': {json.dumps(result, indent=2)}"
            return f"Value for key '{key}': {result}"
            
        elif action.lower() == 'set':
            # Try to parse value as JSON if it's a string
            if isinstance(value, str):
                try:
                    parsed_value = json.loads(value)
                    success = self.set(key, parsed_value, ttl)
                except json.JSONDecodeError:
                    # If not valid JSON, store as string
                    success = self.set(key, value, ttl)
            else:
                success = self.set(key, value, ttl)
                
            if success:
                return f"Successfully set value for key '{key}'"
            return f"Failed to set value for key '{key}'"
            
        elif action.lower() == 'delete':
            success = self.delete(key)
            if success:
                return f"Successfully deleted key '{key}'"
            return f"Failed to delete key '{key}' or key not found"
            
        elif action.lower() == 'clear':
            success = self.clear(key if key else None)  # Use key as prefix if provided
            if success:
                return f"Successfully cleared cache with prefix '{key or 'all'}'"
            return f"Failed to clear cache with prefix '{key or 'all'}'"
            
        else:
            return f"Unknown action '{action}'. Supported actions: get, set, delete, clear"
    
    def _clean_expired_local(self):
        """Clean expired entries from the local cache."""
        now = time.time()
        expired_keys = [
            key for key, value in self.local_cache.items()
            if value.get("expires_at", 0) < now
        ]
        
        for key in expired_keys:
            del self.local_cache[key]
    
    def _enforce_local_size(self):
        """Enforce the local cache size limit."""
        if len(self.local_cache) > self.local_cache_size:
            # Sort by last_accessed (oldest first)
            sorted_items = sorted(
                self.local_cache.items(),
                key=lambda x: x[1].get("last_accessed", 0)
            )
            
            # Remove oldest items until we're under the limit
            for key, _ in sorted_items[:len(sorted_items) - self.local_cache_size]:
                del self.local_cache[key]
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache.
        
        Args:
            key: The key to get
            
        Returns:
            The value or None if not found
        """
        # Clean expired entries
        self._clean_expired_local()
        
        # Try local cache first
        if key in self.local_cache:
            entry = self.local_cache[key]
            now = time.time()
            
            # Check if expired
            if entry.get("expires_at", 0) > now:
                # Update last accessed time
                entry["last_accessed"] = now
                return entry["value"]
            else:
                # Remove expired entry
                del self.local_cache[key]
        
        # Try Redis cache
        value = self.redis_cache.get(key)
        
        if value is not None:
            # Store in local cache with TTL
            now = time.time()
            self.local_cache[key] = {
                "value": value,
                "last_accessed": now,
                "expires_at": now + self.redis_cache.default_ttl
            }
            
            # Enforce size limit
            self._enforce_local_size()
        
        return value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set a value in the cache.
        
        Args:
            key: The key to set
            value: The value to set
            ttl: Time-to-live in seconds (None for default)
            
        Returns:
            True if successful, False otherwise
        """
        # Set in Redis
        success = self.redis_cache.set(key, value, ttl)
        
        if success:
            # Set in local cache
            now = time.time()
            ttl_value = ttl if ttl is not None else self.redis_cache.default_ttl
            
            self.local_cache[key] = {
                "value": value,
                "last_accessed": now,
                "expires_at": now + ttl_value
            }
            
            # Enforce size limit
            self._enforce_local_size()
        
        return success
    
    def delete(self, key: str) -> bool:
        """
        Delete a value from the cache.
        
        Args:
            key: The key to delete
            
        Returns:
            True if successful, False otherwise
        """
        # Delete from local cache
        if key in self.local_cache:
            del self.local_cache[key]
        
        # Delete from Redis
        return self.redis_cache.delete(key)
    
    def clear_prefix(self, prefix: Optional[str] = None) -> bool:
        """
        Clear all keys with the given prefix.
        
        Args:
            prefix: Prefix to clear (defaults to instance prefix)
            
        Returns:
            True if successful, False otherwise
        """
        # Clear from local cache
        if prefix:
            keys_to_delete = [
                key for key in self.local_cache.keys()
                if key.startswith(prefix)
            ]
            
            for key in keys_to_delete:
                del self.local_cache[key]
        else:
            # Clear all if no prefix specified
            self.local_cache.clear()
        
        # Clear from Redis
        return self.redis_cache.clear_prefix(prefix)
    
    def cached(self, ttl: Optional[int] = None, key_fn: Optional[Callable] = None):
        """
        Decorator for caching function results.
        
        Args:
            ttl: Time-to-live in seconds (None for default)
            key_fn: Function to generate cache key from args and kwargs
            
        Returns:
            Decorator function
        """
        def decorator(func):
            def wrapper(*args, **kwargs):
                # Generate cache key
                if key_fn:
                    cache_key = key_fn(*args, **kwargs)
                else:
                    # Default key generation
                    arg_str = ":".join(str(arg) for arg in args)
                    kwarg_str = ":".join(f"{k}={v}" for k, v in sorted(kwargs.items()))
                    cache_key = f"{func.__name__}:{arg_str}:{kwarg_str}"
                
                # Try to get from cache
                cached_result = self.get(cache_key)
                if cached_result is not None:
                    return cached_result
                
                # Call the function
                result = func(*args, **kwargs)
                
                # Cache the result
                self.set(cache_key, result, ttl)
                
                return result
            
            return wrapper
        
        return decorator


# Alias TwoLevelCache as CacheTool for backward compatibility
CacheTool = TwoLevelCache
