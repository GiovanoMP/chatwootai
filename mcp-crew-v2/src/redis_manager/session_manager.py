"""
Gerenciamento de Sessão usando Redis para o MCP-Crew v2.

Implementa métodos para armazenar e recuperar dados de sessão do usuário.
"""

import json
import logging
import time
import uuid
from typing import Any, Dict, List, Optional

from src.redis_manager.redis_manager import redis_manager, DataType

logger = logging.getLogger(__name__)

# TTL padrão para sessões (em segundos)
DEFAULT_SESSION_TTL = 1800  # 30 minutos

class SessionManager:
    """Gerencia sessões de usuário no Redis."""
    
    def __init__(self, tenant_id: str):
        """
        Inicializa o gerenciador de sessões.
        
        Args:
            tenant_id: ID do tenant (account_id)
        """
        self.tenant_id = tenant_id
    
    def create_session(self, user_id: str, data: Dict[str, Any] = None, ttl: int = DEFAULT_SESSION_TTL) -> str:
        """
        Cria uma nova sessão.
        
        Args:
            user_id: ID do usuário
            data: Dados iniciais da sessão
            ttl: Tempo de vida da sessão em segundos
            
        Returns:
            str: ID da sessão criada
        """
        session_id = str(uuid.uuid4())
        
        session_data = {
            "user_id": user_id,
            "created_at": time.time(),
            "last_accessed": time.time(),
            "data": data or {}
        }
        
        success = redis_manager.set(
            tenant_id=self.tenant_id,
            data_type=DataType.CONVERSATION_CONTEXT,
            identifier=f"session:{session_id}",
            value=session_data,
            ttl=ttl
        )
        
        if success:
            return session_id
        return None
    
    def get_session(self, session_id: str, update_access: bool = True) -> Optional[Dict[str, Any]]:
        """
        Recupera dados de uma sessão.
        
        Args:
            session_id: ID da sessão
            update_access: Se True, atualiza o timestamp de último acesso
            
        Returns:
            Dict: Dados da sessão ou None se não encontrada
        """
        session_data = redis_manager.get(
            tenant_id=self.tenant_id,
            data_type=DataType.CONVERSATION_CONTEXT,
            identifier=f"session:{session_id}"
        )
        
        if not session_data:
            return None
            
        if update_access:
            # Atualizar timestamp de último acesso
            session_data["last_accessed"] = time.time()
            
            # Salvar sessão atualizada
            redis_manager.set(
                tenant_id=self.tenant_id,
                data_type=DataType.CONVERSATION_CONTEXT,
                identifier=f"session:{session_id}",
                value=session_data
            )
            
        return session_data
    
    def update_session(self, session_id: str, data: Dict[str, Any], ttl: int = DEFAULT_SESSION_TTL) -> bool:
        """
        Atualiza dados de uma sessão.
        
        Args:
            session_id: ID da sessão
            data: Novos dados para a sessão
            ttl: Novo tempo de vida da sessão em segundos
            
        Returns:
            bool: True se atualizado com sucesso
        """
        session_data = self.get_session(session_id, update_access=False)
        
        if not session_data:
            return False
            
        # Atualizar dados
        session_data["data"].update(data)
        session_data["last_accessed"] = time.time()
        
        # Salvar sessão atualizada
        return redis_manager.set(
            tenant_id=self.tenant_id,
            data_type=DataType.CONVERSATION_CONTEXT,
            identifier=f"session:{session_id}",
            value=session_data,
            ttl=ttl
        )
    
    def delete_session(self, session_id: str) -> bool:
        """
        Remove uma sessão.
        
        Args:
            session_id: ID da sessão
            
        Returns:
            bool: True se removida com sucesso
        """
        return redis_manager.delete(
            tenant_id=self.tenant_id,
            data_type=DataType.CONVERSATION_CONTEXT,
            identifier=f"session:{session_id}"
        )
    
    def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Recupera todas as sessões de um usuário.
        
        Args:
            user_id: ID do usuário
            
        Returns:
            List[Dict]: Lista de sessões do usuário
        """
        # Obter todas as chaves de sessão
        keys = redis_manager.get_keys_by_pattern(
            tenant_id=self.tenant_id,
            data_type=DataType.CONVERSATION_CONTEXT,
            pattern="session:*"
        )
        
        sessions = []
        
        # Filtrar sessões do usuário
        for key in keys:
            # Extrair session_id da chave
            session_id = key.split(":")[-1]
            
            # Obter dados da sessão
            session_data = self.get_session(session_id, update_access=False)
            
            if session_data and session_data.get("user_id") == user_id:
                sessions.append({
                    "session_id": session_id,
                    **session_data
                })
        
        return sessions
    
    def cleanup_expired_sessions(self, max_idle_time: int = DEFAULT_SESSION_TTL) -> int:
        """
        Remove sessões expiradas manualmente.
        
        Args:
            max_idle_time: Tempo máximo de inatividade em segundos
            
        Returns:
            int: Número de sessões removidas
        """
        # Obter todas as chaves de sessão
        keys = redis_manager.get_keys_by_pattern(
            tenant_id=self.tenant_id,
            data_type=DataType.CONVERSATION_CONTEXT,
            pattern="session:*"
        )
        
        current_time = time.time()
        removed_count = 0
        
        # Verificar e remover sessões expiradas
        for key in keys:
            # Extrair session_id da chave
            session_id = key.split(":")[-1]
            
            # Obter dados da sessão
            session_data = self.get_session(session_id, update_access=False)
            
            if session_data:
                last_accessed = session_data.get("last_accessed", 0)
                
                # Verificar se a sessão está expirada
                if current_time - last_accessed > max_idle_time:
                    # Remover sessão
                    if self.delete_session(session_id):
                        removed_count += 1
        
        return removed_count
