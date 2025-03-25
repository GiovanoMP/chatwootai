#!/usr/bin/env python3
"""
Módulo de cliente Redis para o ChatwootAI

Este módulo fornece uma interface unificada para conexão com o Redis,
garantindo que apenas uma conexão seja estabelecida e reutilizada em todo o sistema.
"""

import os
import logging
import redis
from typing import Optional, Dict, Any

# Configurar logging
logger = logging.getLogger(__name__)

# Singleton para a conexão Redis
_redis_client = None

def get_redis_client(force_new=False) -> Optional[redis.Redis]:
    """
    Obtém uma conexão com o Redis, criando-a se necessário.
    
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
        
        logger.info(f"Conexão com Redis estabelecida: {redis_config['host']}:{redis_config['port']}")
        
        # Armazenar o cliente no singleton
        _redis_client = client
        return client
        
    except ImportError:
        logger.error("Módulo redis não está instalado. Execute: pip install redis")
        return None
    except Exception as e:
        logger.error(f"Erro ao conectar ao Redis: {str(e)}")
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
    
    def store_domain_config(self, domain_name: str, config: Dict[str, Any], ttl: int = 3600) -> bool:
        """
        Armazena a configuração de um domínio no cache.
        
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
    
    def get_domain_config(self, domain_name: str) -> Optional[Dict[str, Any]]:
        """
        Recupera a configuração de um domínio do cache.
        
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
