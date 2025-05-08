#!/usr/bin/env python3
"""
ConfigRegistry para o ChatwootAI

Este módulo implementa o ConfigRegistry, responsável por gerenciar o acesso
às configurações YAML dos clientes, com suporte a cache em memória e Redis.
"""

import logging
import pickle
import time
import json
from typing import Dict, Any, Optional

from src.utils.redis_client import get_redis_client, get_aioredis_client
from src.core.config.config_loader import ConfigLoader

# Configurar logging
logger = logging.getLogger(__name__)

class ConfigRegistry:
    """
    Registro de configurações com suporte a cache em memória e Redis.

    Esta classe é responsável por gerenciar o acesso às configurações YAML
    dos clientes, garantindo performance através de cache em camadas:
    1. Cache em memória (mais rápido)
    2. Cache em Redis (persistente)
    3. Carregamento do arquivo YAML (fallback)
    """

    def __init__(self, redis_client=None, config_loader=None):
        """
        Inicializa o registro de configurações.

        Args:
            redis_client: Cliente Redis opcional
            config_loader: Carregador de configurações opcional
        """
        self.redis_client = redis_client or get_redis_client()
        self.config_loader = config_loader or ConfigLoader()
        self.redis_async_client = None  # Será inicializado sob demanda

        # Cache em memória para configurações
        self.memory_cache = {}

        logger.info("ConfigRegistry inicializado")

    async def _get_async_redis_client(self):
        """
        Obtém o cliente Redis assíncrono, inicializando-o se necessário.

        Returns:
            Cliente Redis assíncrono ou None se não for possível conectar
        """
        if self.redis_async_client is None:
            self.redis_async_client = await get_aioredis_client()
        return self.redis_async_client

    async def get_config(self, domain_name: str, account_id: str, force_reload: bool = False) -> Dict[str, Any]:
        """
        Obtém a configuração para um domínio e account_id específicos.

        Implementa uma estratégia de cache em camadas:
        1. Verificar cache em memória
        2. Verificar Redis
        3. Carregar do arquivo YAML

        Args:
            domain_name: Nome do domínio
            account_id: ID da conta
            force_reload: Se True, força o recarregamento do arquivo YAML

        Returns:
            Configuração carregada
        """
        # Chave de cache
        cache_key = f"config:{domain_name}:{account_id}"

        # Se não forçar recarregamento, verificar cache em memória
        if not force_reload and cache_key in self.memory_cache:
            logger.debug(f"Configuração encontrada em cache de memória: {domain_name}/{account_id}")
            return self.memory_cache[cache_key]

        # Se não forçar recarregamento, verificar Redis
        if not force_reload and self.redis_client:
            try:
                # Obter cliente Redis assíncrono
                redis_async = await self._get_async_redis_client()
                if redis_async:
                    config_data = await redis_async.get(cache_key)
                    if config_data:
                        try:
                            # Tentar carregar como JSON primeiro (novo formato)
                            config = json.loads(config_data)
                            # Atualizar cache em memória
                            self.memory_cache[cache_key] = config
                            logger.debug(f"Configuração encontrada em Redis (formato JSON): {domain_name}/{account_id}")
                            return config
                        except Exception as json_error:
                            logger.warning(f"Erro ao carregar configuração do Redis como JSON: {json_error}")
                            # Tentar carregar como pickle (formato antigo) - apenas para compatibilidade
                            try:
                                config = pickle.loads(config_data.encode('latin1') if isinstance(config_data, str) else config_data)
                                # Atualizar cache em memória
                                self.memory_cache[cache_key] = config
                                logger.debug(f"Configuração encontrada em Redis (formato pickle): {domain_name}/{account_id}")
                                return config
                            except Exception as pickle_error:
                                logger.warning(f"Erro ao carregar configuração do Redis como pickle: {pickle_error}")
                                # Se ambos falharem, vamos carregar do arquivo
            except Exception as e:
                logger.warning(f"Erro ao acessar Redis para configuração {domain_name}/{account_id}: {e}")

        # Carregar do arquivo YAML
        try:
            config = await self.config_loader.load_config(domain_name, account_id)

            # Atualizar cache em memória
            self.memory_cache[cache_key] = config

            # Atualizar Redis se disponível
            if self.redis_client:
                try:
                    # Obter cliente Redis assíncrono
                    redis_async = await self._get_async_redis_client()
                    if redis_async:
                        # Armazenar como JSON
                        config_data = json.dumps(config)
                        await redis_async.set(cache_key, config_data, ex=3600)  # 1 hora
                except Exception as e:
                    logger.warning(f"Erro ao armazenar configuração em Redis: {e}")

            logger.info(f"Configuração carregada do arquivo YAML: {domain_name}/{account_id}")
            return config

        except Exception as e:
            logger.error(f"Erro ao carregar configuração para {domain_name}/{account_id}: {e}")
            # Retornar configuração vazia em caso de erro
            return {}

    async def invalidate_config(self, domain_name: str, account_id: str) -> bool:
        """
        Invalida o cache de configuração para um domínio e account_id específicos.

        Args:
            domain_name: Nome do domínio
            account_id: ID da conta

        Returns:
            True se invalidado com sucesso, False caso contrário
        """
        # Chave de cache
        cache_key = f"config:{domain_name}:{account_id}"

        # Remover do cache em memória
        if cache_key in self.memory_cache:
            del self.memory_cache[cache_key]

        # Remover do Redis se disponível
        if self.redis_client:
            try:
                await self.redis_client.delete(cache_key)
            except Exception as e:
                logger.warning(f"Erro ao invalidar configuração em Redis: {e}")
                return False

        logger.info(f"Cache de configuração invalidado: {domain_name}/{account_id}")
        return True

    async def get_all_configs(self) -> Dict[str, Dict[str, Any]]:
        """
        Obtém todas as configurações disponíveis.

        Returns:
            Dicionário com todas as configurações, indexado por chave de cache
        """
        # Obter lista de domínios e accounts do ConfigLoader
        domains_accounts = await self.config_loader.list_available_configs()

        # Carregar cada configuração
        configs = {}
        for domain_name, account_ids in domains_accounts.items():
            for account_id in account_ids:
                config = await self.get_config(domain_name, account_id)
                cache_key = f"config:{domain_name}:{account_id}"
                configs[cache_key] = config

        return configs

# Instância singleton
_config_registry = None

def get_config_registry(force_new=False, redis_client=None, config_loader=None) -> ConfigRegistry:
    """
    Obtém a instância singleton do ConfigRegistry.

    Args:
        force_new: Se True, força a criação de uma nova instância
        redis_client: Cliente Redis opcional
        config_loader: Carregador de configurações opcional

    Returns:
        Instância do ConfigRegistry
    """
    global _config_registry

    if _config_registry is None or force_new:
        _config_registry = ConfigRegistry(
            redis_client=redis_client,
            config_loader=config_loader
        )

    return _config_registry
