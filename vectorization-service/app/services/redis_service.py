"""
Serviço para operações com Redis.
"""

import json
import logging
from typing import Any, Dict, List, Optional, Union
import redis.asyncio as redis
from app.core.config import settings
from app.core.exceptions import CacheError

logger = logging.getLogger(__name__)

class RedisService:
    """Serviço para operações com Redis."""
    
    def __init__(self):
        """Inicializa o serviço Redis."""
        self.redis_client = None
    
    async def connect(self):
        """Conecta ao Redis."""
        if self.redis_client is not None:
            return
        
        try:
            self.redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                password=settings.REDIS_PASSWORD,
                db=settings.REDIS_DB,
                decode_responses=True
            )
            
            # Verificar conexão
            await self.redis_client.ping()
            logger.info("Conectado ao Redis")
            
        except Exception as e:
            logger.error(f"Falha ao conectar ao Redis: {e}")
            raise CacheError(f"Falha ao conectar ao Redis: {e}")
    
    async def set(self, key: str, value: str, expiry: Optional[int] = None):
        """
        Define um valor no Redis.
        
        Args:
            key: Chave para armazenar o valor
            value: Valor a ser armazenado
            expiry: Tempo de expiração em segundos (opcional)
        """
        await self.connect()
        
        try:
            if expiry:
                await self.redis_client.setex(key, expiry, value)
            else:
                await self.redis_client.set(key, value)
        except Exception as e:
            logger.error(f"Erro ao definir valor no Redis: {e}")
            raise CacheError(f"Erro ao definir valor no Redis: {e}")
    
    async def get(self, key: str) -> Optional[str]:
        """
        Obtém um valor do Redis.
        
        Args:
            key: Chave do valor a ser obtido
            
        Returns:
            Valor armazenado ou None se não existir
        """
        await self.connect()
        
        try:
            return await self.redis_client.get(key)
        except Exception as e:
            logger.error(f"Erro ao obter valor do Redis: {e}")
            raise CacheError(f"Erro ao obter valor do Redis: {e}")
    
    async def set_json(self, key: str, value: Dict[str, Any], expiry: Optional[int] = None):
        """
        Armazena um objeto JSON no Redis.
        
        Args:
            key: Chave para armazenar o valor
            value: Objeto a ser serializado e armazenado
            expiry: Tempo de expiração em segundos (opcional)
        """
        json_value = json.dumps(value)
        await self.set(key, json_value, expiry)
    
    async def get_json(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Obtém um objeto JSON do Redis.
        
        Args:
            key: Chave do objeto a ser obtido
            
        Returns:
            Objeto deserializado ou None se não existir
        """
        value = await self.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError as e:
                logger.error(f"Erro ao decodificar JSON do Redis: {e}")
                raise CacheError(f"Erro ao decodificar JSON do Redis: {e}")
        return None
    
    async def increment(self, key: str, amount: int = 1) -> int:
        """
        Incrementa um contador no Redis.
        
        Args:
            key: Chave do contador
            amount: Valor a incrementar
            
        Returns:
            Novo valor do contador
        """
        await self.connect()
        
        try:
            return await self.redis_client.incrby(key, amount)
        except Exception as e:
            logger.error(f"Erro ao incrementar contador no Redis: {e}")
            raise CacheError(f"Erro ao incrementar contador no Redis: {e}")
    
    async def keys(self, pattern: str) -> List[str]:
        """
        Obtém todas as chaves que correspondem a um padrão.
        
        Args:
            pattern: Padrão de chave
            
        Returns:
            Lista de chaves correspondentes
        """
        await self.connect()
        
        try:
            return await self.redis_client.keys(pattern)
        except Exception as e:
            logger.error(f"Erro ao obter chaves do Redis: {e}")
            raise CacheError(f"Erro ao obter chaves do Redis: {e}")
    
    async def delete_many(self, keys: List[str]):
        """
        Remove múltiplas chaves do Redis.
        
        Args:
            keys: Lista de chaves a serem removidas
        """
        if not keys:
            return
            
        await self.connect()
        
        try:
            await self.redis_client.delete(*keys)
        except Exception as e:
            logger.error(f"Erro ao remover chaves do Redis: {e}")
            raise CacheError(f"Erro ao remover chaves do Redis: {e}")
    
    async def add_to_list(self, key: str, value: str):
        """
        Adiciona um valor a uma lista no Redis.
        
        Args:
            key: Chave da lista
            value: Valor a ser adicionado
        """
        await self.connect()
        
        try:
            await self.redis_client.rpush(key, value)
        except Exception as e:
            logger.error(f"Erro ao adicionar valor à lista no Redis: {e}")
            raise CacheError(f"Erro ao adicionar valor à lista no Redis: {e}")
    
    async def get_list(self, key: str) -> List[str]:
        """
        Obtém todos os valores de uma lista no Redis.
        
        Args:
            key: Chave da lista
            
        Returns:
            Lista de valores
        """
        await self.connect()
        
        try:
            return await self.redis_client.lrange(key, 0, -1)
        except Exception as e:
            logger.error(f"Erro ao obter lista do Redis: {e}")
            raise CacheError(f"Erro ao obter lista do Redis: {e}")
    
    async def rate_limit_check(self, key: str, limit: int, window: int) -> bool:
        """
        Verifica se uma operação está dentro do limite de taxa.
        
        Args:
            key: Chave para o limitador de taxa
            limit: Número máximo de operações
            window: Janela de tempo em segundos
            
        Returns:
            True se a operação está dentro do limite, False caso contrário
        """
        await self.connect()
        
        try:
            # Obter contagem atual
            count = await self.redis_client.get(key)
            count = int(count) if count else 0
            
            if count >= limit:
                return False
            
            # Incrementar contagem
            pipe = self.redis_client.pipeline()
            pipe.incr(key)
            
            # Definir expiração se for a primeira operação
            if count == 0:
                pipe.expire(key, window)
                
            await pipe.execute()
            return True
        except Exception as e:
            logger.error(f"Erro ao verificar limite de taxa no Redis: {e}")
            # Em caso de erro, permitir a operação
            return True
