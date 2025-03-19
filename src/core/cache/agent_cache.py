"""
Implementação de cache para agentes usando Redis.
Este módulo fornece uma implementação de cache para agentes que pode ser usada
como substituto para a classe RedisAgentCache do CrewAI, que não está disponível
na versão atual.
"""

import json
import logging
from typing import Any, Dict, Optional

import redis

logger = logging.getLogger(__name__)

class RedisAgentCache:
    """
    Cache para agentes usando Redis.
    
    Esta classe implementa um cache para agentes usando Redis, similar à
    funcionalidade que seria esperada da classe RedisAgentCache do CrewAI.
    """
    
    def __init__(self, redis_client: Optional[redis.Redis] = None, 
                 prefix: str = "agent_cache:", ttl: int = 3600):
        """
        Inicializa o cache de agentes.
        
        Args:
            redis_client: Cliente Redis a ser usado. Se None, um novo cliente será criado.
            prefix: Prefixo para as chaves no Redis.
            ttl: Tempo de vida das entradas de cache em segundos.
        """
        if not redis_client:
            # Tentar criar um novo cliente Redis com o endereço IP explícito
            import os
            redis_url = os.getenv('REDIS_URL', 'redis://172.24.0.5:6379/0')
            logger.info(f"Criando cliente Redis usando URL: {redis_url}")
            try:
                redis_client = redis.from_url(redis_url)
                # Testar a conexão
                redis_client.ping()
                logger.info("Conexão com Redis estabelecida com sucesso")
            except Exception as e:
                logger.error(f"Erro ao conectar ao Redis: {e}")
                logger.warning("Usando Redis padrão como fallback")
                redis_client = redis.Redis()
        else:
            # Verificar se o cliente fornecido está conectado
            try:
                redis_client.ping()
                logger.info("Cliente Redis fornecido está conectado")
            except Exception as e:
                logger.error(f"Cliente Redis fornecido não está conectado: {e}")
                # Tentar reconectar
                import os
                redis_url = os.getenv('REDIS_URL', 'redis://172.24.0.5:6379/0')
                logger.info(f"Tentando reconectar ao Redis usando URL: {redis_url}")
                try:
                    redis_client = redis.from_url(redis_url)
                    redis_client.ping()
                    logger.info("Reconexão com Redis bem-sucedida")
                except Exception as e2:
                    logger.error(f"Falha na reconexão com Redis: {e2}")
                
        self.redis_client = redis_client
        self.prefix = prefix
        self.ttl = ttl
        logger.info(f"Inicializando RedisAgentCache com prefixo {prefix} e TTL {ttl}s")
    
    def _get_key(self, agent_id: str, input_data: str) -> str:
        """
        Gera uma chave para o cache baseada no ID do agente e nos dados de entrada.
        
        Args:
            agent_id: ID do agente.
            input_data: Dados de entrada para o agente.
            
        Returns:
            Chave para o cache.
        """
        return f"{self.prefix}{agent_id}:{hash(input_data)}"
    
    def get(self, agent_id: str, input_data: str) -> Optional[Dict[str, Any]]:
        """
        Recupera dados do cache.
        
        Args:
            agent_id: ID do agente.
            input_data: Dados de entrada para o agente.
            
        Returns:
            Dados do cache ou None se não encontrado.
        """
        key = self._get_key(agent_id, input_data)
        try:
            # Verificar conexão Redis antes de tentar recuperar
            try:
                self.redis_client.ping()
            except Exception as e:
                logger.warning(f"Redis indisponível para cache.get: {e}")
                # Tentar reconectar com endereço IP explícito
                import os
                redis_url = os.getenv('REDIS_URL', 'redis://172.24.0.5:6379/0')
                logger.info(f"Tentando reconectar ao Redis usando URL: {redis_url}")
                try:
                    self.redis_client = redis.from_url(redis_url)
                    self.redis_client.ping()
                    logger.info("Reconexão com Redis bem-sucedida")
                except Exception as e2:
                    logger.error(f"Falha na reconexão com Redis: {e2}")
                    return None  # Retornar None se não conseguir reconectar
            
            data = self.redis_client.get(key)
            if data:
                logger.debug(f"Cache hit para {key}")
                return json.loads(data)
            logger.debug(f"Cache miss para {key}")
            return None
        except Exception as e:
            logger.error(f"Erro ao recuperar do cache: {e}")
            return None
    
    def set(self, agent_id: str, input_data: str, output_data: Dict[str, Any]) -> bool:
        """
        Armazena dados no cache.
        
        Args:
            agent_id: ID do agente.
            input_data: Dados de entrada para o agente.
            output_data: Dados de saída do agente.
            
        Returns:
            True se os dados foram armazenados com sucesso, False caso contrário.
        """
        key = self._get_key(agent_id, input_data)
        try:
            # Verificar conexão Redis antes de tentar definir
            try:
                self.redis_client.ping()
            except Exception as e:
                logger.warning(f"Redis indisponível para cache.set: {e}")
                # Tentar reconectar com endereço IP explícito
                import os
                redis_url = os.getenv('REDIS_URL', 'redis://172.24.0.5:6379/0')
                logger.info(f"Tentando reconectar ao Redis usando URL: {redis_url}")
                try:
                    self.redis_client = redis.from_url(redis_url)
                    self.redis_client.ping()
                    logger.info("Reconexão com Redis bem-sucedida")
                except Exception as e2:
                    logger.error(f"Falha na reconexão com Redis: {e2}")
                    return False  # Abandonar operação se não conseguir reconectar
            
            self.redis_client.setex(
                key, 
                self.ttl, 
                json.dumps(output_data)
            )
            logger.debug(f"Dados armazenados no cache para {key}")
            return True
        except Exception as e:
            logger.error(f"Erro ao armazenar no cache: {e}")
            return False
    
    def delete(self, agent_id: str, input_data: str) -> bool:
        """
        Remove dados do cache.
        
        Args:
            agent_id: ID do agente.
            input_data: Dados de entrada para o agente.
            
        Returns:
            True se os dados foram removidos com sucesso, False caso contrário.
        """
        key = self._get_key(agent_id, input_data)
        try:
            # Verificar conexão Redis antes de tentar deletar
            try:
                self.redis_client.ping()
            except Exception as e:
                logger.warning(f"Redis indisponível para cache.delete: {e}")
                # Tentar reconectar com endereço IP explícito
                import os
                redis_url = os.getenv('REDIS_URL', 'redis://172.24.0.5:6379/0')
                logger.info(f"Tentando reconectar ao Redis usando URL: {redis_url}")
                try:
                    self.redis_client = redis.from_url(redis_url)
                    self.redis_client.ping()
                    logger.info("Reconexão com Redis bem-sucedida")
                except Exception as e2:
                    logger.error(f"Falha na reconexão com Redis: {e2}")
                    return False  # Retornar False se não conseguir reconectar
            
            self.redis_client.delete(key)
            logger.debug(f"Dados removidos do cache para {key}")
            return True
        except Exception as e:
            logger.error(f"Erro ao remover do cache: {e}")
            return False
    
    def clear(self, agent_id: Optional[str] = None) -> bool:
        """
        Limpa o cache para um agente específico ou para todos os agentes.
        
        Args:
            agent_id: ID do agente. Se None, limpa o cache para todos os agentes.
            
        Returns:
            True se o cache foi limpo com sucesso, False caso contrário.
        """
        pattern = f"{self.prefix}{agent_id}:*" if agent_id else f"{self.prefix}*"
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
                logger.debug(f"Cache limpo para o padrão {pattern}")
            return True
        except Exception as e:
            logger.error(f"Erro ao limpar o cache: {e}")
            return False
