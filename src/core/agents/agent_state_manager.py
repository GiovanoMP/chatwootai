#!/usr/bin/env python3
"""
Gerenciador de Estado de Agentes para o ChatwootAI

Este módulo implementa o AgentStateManager, responsável por persistir e recuperar
o estado dos agentes entre diferentes interações, garantindo continuidade nas conversas.
"""

import json
import logging
from typing import Dict, Any, Optional

from src.utils.redis_client import get_redis_client, RedisCache

# Configurar logging
logger = logging.getLogger(__name__)

class AgentStateManager:
    """
    Gerenciador de estado persistente dos agentes.
    
    Responsável por salvar e recuperar o estado dos agentes entre diferentes
    interações, garantindo que o contexto seja mantido ao longo de uma conversa.
    """
    
    def __init__(self, redis_client=None):
        """
        Inicializa o gerenciador de estado.
        
        Args:
            redis_client: Cliente Redis para persistência (opcional)
        """
        self.redis_client = redis_client or get_redis_client()
        self.redis_cache = RedisCache(self.redis_client)
        
        logger.info("AgentStateManager inicializado")
    
    def save_agent_state(self, agent_id: str, domain_name: str, conversation_id: str, state: Dict[str, Any]) -> bool:
        """
        Salva o estado do agente para uma conversa específica.
        
        Args:
            agent_id: Identificador do agente
            domain_name: Nome do domínio
            conversation_id: ID da conversa
            state: Estado a ser persistido (dict)
            
        Returns:
            True se salvo com sucesso, False caso contrário
        """
        if not self.redis_client:
            logger.warning("Redis não disponível para persistência de estado")
            return False
        
        # Validar estado
        if not isinstance(state, dict):
            logger.error(f"Estado inválido para agente {agent_id}: deve ser um dicionário")
            return False
            
        # Limitar tamanho do estado para evitar problemas de memória
        state_size = len(json.dumps(state))
        if state_size > 1024 * 100:  # 100KB
            logger.warning(f"Estado do agente {agent_id} muito grande ({state_size} bytes), truncando")
            # Implementar lógica de truncamento se necessário
            
        # Salvar estado
        result = self.redis_cache.store_agent_state(agent_id, domain_name, conversation_id, state)
        
        if result:
            logger.debug(f"Estado do agente {agent_id} salvo para conversa {conversation_id}")
        else:
            logger.error(f"Falha ao salvar estado do agente {agent_id}")
            
        return result
    
    def load_agent_state(self, agent_id: str, domain_name: str, conversation_id: str) -> Dict[str, Any]:
        """
        Carrega o estado persistido de um agente.
        
        Args:
            agent_id: Identificador do agente
            domain_name: Nome do domínio
            conversation_id: ID da conversa
            
        Returns:
            dict: Estado do agente ou {} se não encontrado
        """
        if not self.redis_client:
            logger.warning("Redis não disponível para carregar estado")
            return {}
            
        # Carregar estado
        state = self.redis_cache.get_agent_state(agent_id, domain_name, conversation_id)
        
        if state:
            logger.debug(f"Estado do agente {agent_id} carregado para conversa {conversation_id}")
        else:
            logger.debug(f"Nenhum estado encontrado para agente {agent_id} na conversa {conversation_id}")
            state = {}
            
        return state
    
    def clear_agent_state(self, agent_id: str, domain_name: str, conversation_id: str) -> bool:
        """
        Remove o estado persistido de um agente.
        
        Args:
            agent_id: Identificador do agente
            domain_name: Nome do domínio
            conversation_id: ID da conversa
            
        Returns:
            True se removido com sucesso, False caso contrário
        """
        if not self.redis_client:
            return False
            
        try:
            key = f"agent:state:{domain_name}:{agent_id}:{conversation_id}"
            self.redis_client.delete(key)
            logger.debug(f"Estado do agente {agent_id} removido para conversa {conversation_id}")
            return True
        except Exception as e:
            logger.error(f"Erro ao remover estado do agente: {str(e)}")
            return False
    
    def clear_conversation_states(self, conversation_id: str) -> bool:
        """
        Remove todos os estados de agentes para uma conversa específica.
        
        Args:
            conversation_id: ID da conversa
            
        Returns:
            True se removido com sucesso, False caso contrário
        """
        if not self.redis_client:
            return False
            
        try:
            pattern = f"agent:state:*:*:{conversation_id}"
            keys = self.redis_client.keys(pattern)
            
            if keys:
                self.redis_client.delete(*keys)
                logger.debug(f"Removidos {len(keys)} estados de agentes para conversa {conversation_id}")
                
            return True
        except Exception as e:
            logger.error(f"Erro ao remover estados da conversa: {str(e)}")
            return False


# Singleton para o gerenciador de estado
_agent_state_manager = None

def get_agent_state_manager(force_new=False, redis_client=None) -> AgentStateManager:
    """
    Obtém a instância singleton do gerenciador de estado.
    
    Args:
        force_new: Se True, força a criação de uma nova instância
        redis_client: Cliente Redis opcional
        
    Returns:
        Instância do AgentStateManager
    """
    global _agent_state_manager
    
    if _agent_state_manager is None or force_new:
        _agent_state_manager = AgentStateManager(redis_client)
        
    return _agent_state_manager
