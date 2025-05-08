#!/usr/bin/env python3
"""
Módulo de cliente Redis e cache em memória para o ChatwootAI

Este módulo fornece uma interface unificada para conexão com o Redis,
garantindo que apenas uma conexão seja estabelecida e reutilizada em todo o sistema.
Também fornece uma implementação de cache em memória para uso quando o Redis não está disponível.
"""

import os
import logging
import redis
import redis.asyncio
import asyncio
from typing import Optional, Dict, Any, Union

# Configurar logging
logger = logging.getLogger(__name__)

# Singletons para as conexões Redis
_redis_client = None
_redis_async_client = None

def get_redis_client(force_new=False) -> Optional[redis.Redis]:
    """
    Obtém uma conexão síncrona com o Redis, criando-a se necessário.

    Args:
        force_new: Se True, força a criação de uma nova conexão

    Returns:
        Cliente Redis ou None se não for possível conectar
    """
    global _redis_client

    # Se já existe uma conexão e não estamos forçando nova, retornar a existente
    if _redis_client is not None and not force_new:
        return _redis_client

    try:
        # Configurações do Redis - priorizando variáveis de ambiente
        redis_config = {
            'host': os.environ.get('REDIS_HOST', 'localhost'),
            'port': int(os.environ.get('REDIS_PORT', '6379')),
            'db': int(os.environ.get('REDIS_DB', '0')),
            'password': os.environ.get('REDIS_PASSWORD', None)
        }

        # Conectar ao Redis
        client = redis.Redis(
            host=redis_config['host'],
            port=redis_config['port'],
            db=redis_config['db'],
            password=redis_config['password'],
            decode_responses=True,
            socket_timeout=2.0
        )

        # Testar a conexão
        client.ping()

        logger.info(f"Conexão síncrona com Redis estabelecida: {redis_config['host']}:{redis_config['port']}")

        # Armazenar o cliente no singleton
        _redis_client = client
        return client

    except ImportError:
        logger.error("Módulo redis não está instalado. Execute: pip install redis")
        return None
    except Exception as e:
        logger.error(f"Erro ao conectar ao Redis: {str(e)}")
        return None

async def get_aioredis_client(force_new=False) -> Optional[redis.asyncio.Redis]:
    """
    Obtém uma conexão assíncrona com o Redis, criando-a se necessário.

    Args:
        force_new: Se True, força a criação de uma nova conexão

    Returns:
        Cliente Redis assíncrono ou None se não for possível conectar
    """
    global _redis_async_client

    # Se já existe uma conexão e não estamos forçando nova, retornar a existente
    if _redis_async_client is not None and not force_new:
        return _redis_async_client

    try:
        # Configurações do Redis - priorizando variáveis de ambiente
        redis_config = {
            'host': os.environ.get('REDIS_HOST', 'localhost'),
            'port': int(os.environ.get('REDIS_PORT', '6379')),
            'db': int(os.environ.get('REDIS_DB', '0')),
            'password': os.environ.get('REDIS_PASSWORD', None)
        }

        # Conectar ao Redis de forma assíncrona
        client = redis.asyncio.Redis(
            host=redis_config['host'],
            port=redis_config['port'],
            db=redis_config['db'],
            password=redis_config['password'],
            decode_responses=True,
            socket_timeout=2.0
        )

        # Testar a conexão
        await client.ping()

        logger.info(f"Conexão assíncrona com Redis estabelecida: {redis_config['host']}:{redis_config['port']}")

        # Armazenar o cliente no singleton
        _redis_async_client = client
        return client

    except ImportError:
        logger.error("Módulo redis.asyncio não está disponível. Execute: pip install redis[hiredis]")
        return None
    except Exception as e:
        logger.error(f"Erro ao conectar ao Redis de forma assíncrona: {str(e)}")
        return None


class RedisCache:
    """
    Classe de utilitário para operações de cache no Redis.

    Fornece métodos de alto nível para operações comuns de cache,
    seguindo as convenções de nomenclatura para o sistema multi-tenant.
    """

    def __init__(self, redis_client=None):
        """
        Inicializa o cache Redis.

        Args:
            redis_client: Cliente Redis opcional. Se não fornecido, usa o singleton.
        """
        self.redis_client = redis_client or get_redis_client()
        self.aioredis_client = None  # Será inicializado sob demanda

    async def _get_async_client(self):
        """
        Obtém o cliente Redis assíncrono, inicializando-o se necessário.

        Returns:
            Cliente Redis assíncrono
        """
        if self.aioredis_client is None:
            self.aioredis_client = await get_aioredis_client()
        return self.aioredis_client

    def store_domain_config(self, domain_name: str, config: Dict[str, Any], ttl: int = 3600) -> bool:
        """
        Armazena a configuração de um domínio no cache (versão síncrona).

        Args:
            domain_name: Nome do domínio
            config: Configuração a ser armazenada
            ttl: Tempo de vida em segundos (padrão: 1 hora)

        Returns:
            True se armazenado com sucesso, False caso contrário
        """
        if not self.redis_client:
            return False

        try:
            import json
            key = f"domain:config:{domain_name}"
            self.redis_client.set(key, json.dumps(config), ex=ttl)
            return True
        except Exception as e:
            logger.error(f"Erro ao armazenar configuração de domínio: {str(e)}")
            return False

    async def store_domain_config_async(self, domain_name: str, config: Dict[str, Any], ttl: int = 3600) -> bool:
        """
        Armazena a configuração de um domínio no cache (versão assíncrona).

        Args:
            domain_name: Nome do domínio
            config: Configuração a ser armazenada
            ttl: Tempo de vida em segundos (padrão: 1 hora)

        Returns:
            True se armazenado com sucesso, False caso contrário
        """
        client = await self._get_async_client()
        if not client:
            return False

        try:
            import json
            key = f"domain:config:{domain_name}"
            await client.set(key, json.dumps(config), ex=ttl)
            return True
        except Exception as e:
            logger.error(f"Erro ao armazenar configuração de domínio de forma assíncrona: {str(e)}")
            return False

    def get_domain_config(self, domain_name: str) -> Optional[Dict[str, Any]]:
        """
        Recupera a configuração de um domínio do cache (versão síncrona).

        Args:
            domain_name: Nome do domínio

        Returns:
            Configuração do domínio ou None se não encontrada
        """
        if not self.redis_client:
            return None

        try:
            import json
            key = f"domain:config:{domain_name}"
            data = self.redis_client.get(key)

            if not data:
                return None

            return json.loads(data)
        except Exception as e:
            logger.error(f"Erro ao recuperar configuração de domínio: {str(e)}")
            return None

    async def get_domain_config_async(self, domain_name: str) -> Optional[Dict[str, Any]]:
        """
        Recupera a configuração de um domínio do cache (versão assíncrona).

        Args:
            domain_name: Nome do domínio

        Returns:
            Configuração do domínio ou None se não encontrada
        """
        client = await self._get_async_client()
        if not client:
            return None

        try:
            import json
            key = f"domain:config:{domain_name}"
            data = await client.get(key)

            if not data:
                return None

            return json.loads(data)
        except Exception as e:
            logger.error(f"Erro ao recuperar configuração de domínio de forma assíncrona: {str(e)}")
            return None

    async def set_conversation_domain_async(self, conversation_id: str, domain_name: str, ttl: int = 86400) -> bool:
        """
        Define o domínio para uma conversa específica (versão assíncrona).

        Args:
            conversation_id: ID da conversa
            domain_name: Nome do domínio
            ttl: Tempo de vida em segundos (padrão: 24 horas)

        Returns:
            True se definido com sucesso, False caso contrário
        """
        client = await self._get_async_client()
        if not client:
            return False

        try:
            key = f"domain:conversation:{conversation_id}"
            await client.set(key, domain_name, ex=ttl)
            return True
        except Exception as e:
            logger.error(f"Erro ao definir domínio para conversa de forma assíncrona: {str(e)}")
            return False

    async def get_conversation_domain_async(self, conversation_id: str) -> Optional[str]:
        """
        Obtém o domínio associado a uma conversa (versão assíncrona).

        Args:
            conversation_id: ID da conversa

        Returns:
            Nome do domínio ou None se não encontrado
        """
        client = await self._get_async_client()
        if not client:
            return None

        try:
            key = f"domain:conversation:{conversation_id}"
            domain = await client.get(key)
            return domain
        except Exception as e:
            logger.error(f"Erro ao obter domínio para conversa de forma assíncrona: {str(e)}")
            return None

    async def store_agent_state_async(self, agent_id: str, domain_name: str, conversation_id: str,
                                    state: Dict[str, Any], ttl: int = 86400) -> bool:
        """
        Armazena o estado de um agente para uma conversa específica (versão assíncrona).

        Args:
            agent_id: ID do agente
            domain_name: Nome do domínio
            conversation_id: ID da conversa
            state: Estado do agente
            ttl: Tempo de vida em segundos (padrão: 24 horas)

        Returns:
            True se armazenado com sucesso, False caso contrário
        """
        client = await self._get_async_client()
        if not client:
            return False

        try:
            import json
            key = f"agent:state:{domain_name}:{agent_id}:{conversation_id}"
            await client.set(key, json.dumps(state), ex=ttl)
            return True
        except Exception as e:
            logger.error(f"Erro ao armazenar estado do agente de forma assíncrona: {str(e)}")
            return False

    async def get_agent_state_async(self, agent_id: str, domain_name: str, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        Recupera o estado de um agente para uma conversa específica (versão assíncrona).

        Args:
            agent_id: ID do agente
            domain_name: Nome do domínio
            conversation_id: ID da conversa

        Returns:
            Estado do agente ou None se não encontrado
        """
        client = await self._get_async_client()
        if not client:
            return None

        try:
            import json
            key = f"agent:state:{domain_name}:{agent_id}:{conversation_id}"
            data = await client.get(key)

            if not data:
                return None

            return json.loads(data)
        except Exception as e:
            logger.error(f"Erro ao recuperar estado do agente de forma assíncrona: {str(e)}")
            return None

    async def invalidate_domain_config_async(self, domain_name: str) -> bool:
        """
        Invalida a configuração de um domínio no cache (versão assíncrona).

        Args:
            domain_name: Nome do domínio

        Returns:
            True se invalidado com sucesso, False caso contrário
        """
        client = await self._get_async_client()
        if not client:
            return False

        try:
            key = f"domain:config:{domain_name}"
            await client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Erro ao invalidar configuração de domínio de forma assíncrona: {str(e)}")
            return False

    # Mantendo os métodos síncronos originais para compatibilidade

    def set_conversation_domain(self, conversation_id: str, domain_name: str, ttl: int = 86400) -> bool:
        """
        Define o domínio para uma conversa específica.

        Args:
            conversation_id: ID da conversa
            domain_name: Nome do domínio
            ttl: Tempo de vida em segundos (padrão: 24 horas)

        Returns:
            True se definido com sucesso, False caso contrário
        """
        if not self.redis_client:
            return False

        try:
            key = f"domain:conversation:{conversation_id}"
            self.redis_client.set(key, domain_name, ex=ttl)
            return True
        except Exception as e:
            logger.error(f"Erro ao definir domínio para conversa: {str(e)}")
            return False

    def get_conversation_domain(self, conversation_id: str) -> Optional[str]:
        """
        Obtém o domínio associado a uma conversa.

        Args:
            conversation_id: ID da conversa

        Returns:
            Nome do domínio ou None se não encontrado
        """
        if not self.redis_client:
            return None

        try:
            key = f"domain:conversation:{conversation_id}"
            domain = self.redis_client.get(key)
            return domain
        except Exception as e:
            logger.error(f"Erro ao obter domínio para conversa: {str(e)}")
            return None

    def store_agent_state(self, agent_id: str, domain_name: str, conversation_id: str,
                         state: Dict[str, Any], ttl: int = 86400) -> bool:
        """
        Armazena o estado de um agente para uma conversa específica.

        Args:
            agent_id: ID do agente
            domain_name: Nome do domínio
            conversation_id: ID da conversa
            state: Estado do agente
            ttl: Tempo de vida em segundos (padrão: 24 horas)

        Returns:
            True se armazenado com sucesso, False caso contrário
        """
        if not self.redis_client:
            return False

        try:
            import json
            key = f"agent:state:{domain_name}:{agent_id}:{conversation_id}"
            self.redis_client.set(key, json.dumps(state), ex=ttl)
            return True
        except Exception as e:
            logger.error(f"Erro ao armazenar estado do agente: {str(e)}")
            return False

    def get_agent_state(self, agent_id: str, domain_name: str, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        Recupera o estado de um agente para uma conversa específica.

        Args:
            agent_id: ID do agente
            domain_name: Nome do domínio
            conversation_id: ID da conversa

        Returns:
            Estado do agente ou None se não encontrado
        """
        if not self.redis_client:
            return None

        try:
            import json
            key = f"agent:state:{domain_name}:{agent_id}:{conversation_id}"
            data = self.redis_client.get(key)

            if not data:
                return None

            return json.loads(data)
        except Exception as e:
            logger.error(f"Erro ao recuperar estado do agente: {str(e)}")
            return None

    def invalidate_domain_config(self, domain_name: str) -> bool:
        """
        Invalida a configuração de um domínio no cache.

        Args:
            domain_name: Nome do domínio

        Returns:
            True se invalidado com sucesso, False caso contrário
        """
        if not self.redis_client:
            return False

        try:
            key = f"domain:config:{domain_name}"
            self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Erro ao invalidar configuração de domínio: {str(e)}")
            return False
