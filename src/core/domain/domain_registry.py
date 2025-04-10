#!/usr/bin/env python3
"""
Registro de Domínios para o ChatwootAI

Este módulo implementa o DomainRegistry, responsável por gerenciar o carregamento,
cache e persistência das configurações de domínio, garantindo que sejam carregadas
apenas uma vez e reutilizadas em todo o sistema.
"""

import json
import logging
from typing import Dict, Any, Optional

from src.core.domain.domain_loader import DomainLoader
from src.utils.redis_client import get_redis_client, RedisCache

# Configurar logging
logger = logging.getLogger(__name__)

class DomainRegistry:
    """
    Registro centralizado de configurações de domínio.
    
    Responsável por gerenciar o carregamento, cache e persistência das 
    configurações de domínio, garantindo que sejam carregadas apenas uma vez
    e reutilizadas em todo o sistema.
    """
    
    def __init__(self, redis_client=None, domains_dir=None):
        """
        Inicializa o registro de domínios.
        
        Args:
            redis_client: Cliente Redis para persistência (opcional)
            domains_dir: Diretório contendo os domínios
        """
        self._configs = {}  # Cache em memória
        self.redis_client = redis_client or get_redis_client()
        self.redis_cache = RedisCache(self.redis_client)
        self.loader = DomainLoader(domains_dir)
        
        logger.info("DomainRegistry inicializado")
    
    def get_domain_config(self, domain_name: str, force_reload: bool = False) -> Dict[str, Any]:
        """
        Obtém configuração do domínio, usando cache quando possível.
        
        Args:
            domain_name: Nome do domínio a ser carregado
            force_reload: Se True, ignora o cache e força o recarregamento
            
        Returns:
            Configuração completa do domínio
        """
        # Se forçar recarga, ignorar cache
        if force_reload:
            return self._load_and_cache_domain(domain_name)
            
        # Verificar cache em memória primeiro
        if domain_name in self._configs:
            logger.debug(f"Usando configuração em cache para domínio '{domain_name}'")
            return self._configs[domain_name]
        
        # Verificar Redis
        if self.redis_client:
            cached_config = self.redis_cache.get_domain_config(domain_name)
            if cached_config:
                logger.debug(f"Carregando configuração de Redis para domínio '{domain_name}'")
                self._configs[domain_name] = cached_config
                return cached_config
        
        # Carregar do sistema de arquivos e persistir
        return self._load_and_cache_domain(domain_name)
    
    def _load_and_cache_domain(self, domain_name: str) -> Dict[str, Any]:
        """
        Carrega uma configuração de domínio e a persiste em cache.
        
        Args:
            domain_name: Nome do domínio a ser carregado
            
        Returns:
            Configuração do domínio
        """
        logger.info(f"Carregando configuração para domínio '{domain_name}' do sistema de arquivos")
        
        # Carregar do sistema de arquivos via DomainLoader
        config = self.loader.load_domain(domain_name)
        
        # Persistir em Redis
        if self.redis_client and config:
            self.redis_cache.store_domain_config(domain_name, config)
            logger.debug(f"Configuração para domínio '{domain_name}' persistida em Redis")
        
        # Atualizar cache em memória
        self._configs[domain_name] = config
        
        return config
        
    def get_account_domain_mapping(self) -> Dict[str, Any]:
        """
        Obtém o mapeamento de account_id para domínio a partir do arquivo de configuração.
        
        Returns:
            Dict[str, Any]: Mapeamento de account_id para informações de domínio
        """
        # Carregar o arquivo de mapeamento
        import os
        import yaml
        
        mapping_file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 
                                        'config', 'chatwoot_mapping.yaml')
        
        account_domain_mapping = {}
        
        if os.path.exists(mapping_file_path):
            try:
                with open(mapping_file_path, 'r') as file:
                    mapping_config = yaml.safe_load(file) or {}
                    
                # Extrair o mapeamento de account_id para domínio
                accounts = mapping_config.get('accounts', {})
                account_domain_mapping = accounts
                
                logger.info(f"Mapeamento de account_id para domínio carregado: {len(accounts)} contas")
            except Exception as e:
                logger.error(f"Erro ao carregar mapeamento de account_id para domínio: {e}")
        else:
            logger.warning(f"Arquivo de mapeamento não encontrado: {mapping_file_path}")
            
        return account_domain_mapping
    
    def update_domain_config(self, domain_name: str, new_config: Dict[str, Any]):
        """
        Atualiza a configuração de um domínio em cache e persistência.
        
        Args:
            domain_name: Nome do domínio a ser atualizado
            new_config: Nova configuração
        """
        # Atualizar cache em memória
        self._configs[domain_name] = new_config
        
        # Persistir em Redis
        if self.redis_client:
            self.redis_cache.store_domain_config(domain_name, new_config)
            
        logger.info(f"Configuração para domínio '{domain_name}' atualizada")
        
    def invalidate_domain(self, domain_name: str):
        """
        Remove um domínio do cache, forçando recarregamento na próxima consulta.
        
        Args:
            domain_name: Nome do domínio a ser invalidado
        """
        # Remover do cache em memória
        if domain_name in self._configs:
            del self._configs[domain_name]
        
        # Remover do Redis
        if self.redis_client:
            self.redis_cache.invalidate_domain_config(domain_name)
            
        logger.info(f"Cache para domínio '{domain_name}' invalidado")
        
    def list_cached_domains(self):
        """Lista os domínios atualmente em cache."""
        return list(self._configs.keys())
    
    def domain_exists(self, domain_name: str) -> bool:
        """
        Verifica se um domínio existe.
        
        Args:
            domain_name: Nome do domínio a verificar
            
        Returns:
            True se o domínio existir, False caso contrário
        """
        return self.loader.domain_exists(domain_name)


# Singleton para o registro de domínios
_domain_registry = None

def get_domain_registry(force_new=False, redis_client=None, domains_dir=None) -> DomainRegistry:
    """
    Obtém a instância singleton do registro de domínios.
    
    Args:
        force_new: Se True, força a criação de uma nova instância
        redis_client: Cliente Redis opcional
        domains_dir: Diretório de domínios opcional
        
    Returns:
        Instância do DomainRegistry
    """
    global _domain_registry
    
    if _domain_registry is None or force_new:
        _domain_registry = DomainRegistry(redis_client, domains_dir)
        
    return _domain_registry
