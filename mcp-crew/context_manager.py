"""
Gerenciador de Contexto para o MCP-Crew.

Este módulo é responsável pelo gerenciamento de contexto e estado, incluindo:
- Armazenamento de histórico de interações
- Persistência de estado entre sessões
- Gerenciamento de memória de curto e longo prazo
- Integração com Redis para caching e armazenamento distribuído
"""

import json
import time
import uuid
from enum import Enum
from typing import Dict, List, Optional, Any, Union

from ..utils.logging import get_logger

logger = get_logger(__name__)

class ContextType(Enum):
    """Tipos de contexto no sistema."""
    CONVERSATION = "conversation"  # Histórico de conversas
    AGENT_STATE = "agent_state"    # Estado de um agente
    SESSION = "session"            # Dados de sessão
    TASK = "task"                  # Contexto de uma tarefa
    GLOBAL = "global"              # Contexto global


class Context:
    """
    Representa um contexto no sistema MCP-Crew.
    
    Atributos:
        id (str): Identificador único do contexto
        type (ContextType): Tipo do contexto
        owner_id (str): ID do proprietário do contexto (agente, sessão, etc.)
        data (Dict): Dados do contexto
        created_at (float): Timestamp de criação
        updated_at (float): Timestamp da última atualização
        ttl (Optional[int]): Tempo de vida em segundos (None para sem expiração)
        metadata (Dict): Metadados adicionais
    """
    
    def __init__(
        self,
        context_type: ContextType,
        owner_id: str,
        data: Dict[str, Any],
        ttl: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Inicializa um novo contexto.
        
        Args:
            context_type: Tipo do contexto
            owner_id: ID do proprietário do contexto
            data: Dados do contexto
            ttl: Tempo de vida em segundos (None para sem expiração)
            metadata: Metadados adicionais
        """
        self.id = str(uuid.uuid4())
        self.type = context_type
        self.owner_id = owner_id
        self.data = data
        self.created_at = time.time()
        self.updated_at = self.created_at
        self.ttl = ttl
        self.metadata = metadata or {}
        
        logger.debug(f"Contexto criado: {self.id} ({self.type.value}) para {owner_id}")
    
    def update(self, data: Dict[str, Any], merge: bool = True) -> None:
        """
        Atualiza os dados do contexto.
        
        Args:
            data: Novos dados
            merge: Se True, mescla com dados existentes; se False, substitui
        """
        if merge:
            self._deep_update(self.data, data)
        else:
            self.data = data
        
        self.updated_at = time.time()
        logger.debug(f"Contexto atualizado: {self.id}")
    
    def _deep_update(self, original: Dict, update: Dict) -> None:
        """
        Atualiza recursivamente um dicionário.
        
        Args:
            original: Dicionário original
            update: Dicionário com atualizações
        """
        for key, value in update.items():
            if key in original and isinstance(original[key], dict) and isinstance(value, dict):
                self._deep_update(original[key], value)
            else:
                original[key] = value
    
    def is_expired(self) -> bool:
        """
        Verifica se o contexto está expirado.
        
        Returns:
            True se expirado, False caso contrário
        """
        if self.ttl is None:
            return False
        
        return time.time() > (self.updated_at + self.ttl)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Converte o contexto para um dicionário.
        
        Returns:
            Dicionário representando o contexto
        """
        return {
            "id": self.id,
            "type": self.type.value,
            "owner_id": self.owner_id,
            "data": self.data,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "ttl": self.ttl,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Context':
        """
        Cria um contexto a partir de um dicionário.
        
        Args:
            data: Dicionário contendo os dados do contexto
            
        Returns:
            Instância de Context
        """
        context = cls(
            context_type=ContextType(data["type"]),
            owner_id=data["owner_id"],
            data=data["data"],
            ttl=data.get("ttl"),
            metadata=data.get("metadata", {})
        )
        context.id = data["id"]
        context.created_at = data["created_at"]
        context.updated_at = data["updated_at"]
        return context


class ContextManager:
    """
    Gerenciador de contexto para o MCP-Crew.
    
    Responsável por gerenciar o ciclo de vida dos contextos, incluindo
    criação, atualização, recuperação e expiração.
    """
    
    def __init__(self, redis_client=None):
        """
        Inicializa o gerenciador de contexto.
        
        Args:
            redis_client: Cliente Redis para armazenamento distribuído (opcional)
        """
        self.contexts: Dict[str, Context] = {}
        self.redis_client = redis_client
        
        logger.info("ContextManager inicializado")
        if redis_client:
            logger.info("Integração com Redis ativada para ContextManager")
    
    def create_context(
        self,
        context_type: ContextType,
        owner_id: str,
        data: Dict[str, Any],
        ttl: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Context:
        """
        Cria um novo contexto.
        
        Args:
            context_type: Tipo do contexto
            owner_id: ID do proprietário do contexto
            data: Dados do contexto
            ttl: Tempo de vida em segundos (None para sem expiração)
            metadata: Metadados adicionais
            
        Returns:
            Contexto criado
        """
        context = Context(
            context_type=context_type,
            owner_id=owner_id,
            data=data,
            ttl=ttl,
            metadata=metadata
        )
        
        self.contexts[context.id] = context
        
        # Se Redis está disponível, armazena também lá
        if self.redis_client:
            self._store_in_redis(context)
        
        logger.info(f"Contexto criado: {context.id} ({context_type.value}) para {owner_id}")
        return context
    
    def get_context(self, context_id: str) -> Optional[Context]:
        """
        Obtém um contexto pelo ID.
        
        Args:
            context_id: ID do contexto
            
        Returns:
            Contexto correspondente ou None se não encontrado ou expirado
        """
        # Tenta obter do cache local
        context = self.contexts.get(context_id)
        
        # Se não encontrou localmente e Redis está disponível, tenta lá
        if context is None and self.redis_client:
            context = self._load_from_redis(context_id)
            if context:
                # Atualiza o cache local
                self.contexts[context_id] = context
        
        # Verifica se o contexto está expirado
        if context and context.is_expired():
            self.delete_context(context_id)
            logger.debug(f"Contexto expirado: {context_id}")
            return None
        
        return context
    
    def update_context(
        self,
        context_id: str,
        data: Dict[str, Any],
        merge: bool = True
    ) -> Optional[Context]:
        """
        Atualiza um contexto existente.
        
        Args:
            context_id: ID do contexto
            data: Novos dados
            merge: Se True, mescla com dados existentes; se False, substitui
            
        Returns:
            Contexto atualizado ou None se não encontrado
        """
        context = self.get_context(context_id)
        if not context:
            logger.warning(f"Tentativa de atualizar contexto inexistente: {context_id}")
            return None
        
        context.update(data, merge)
        
        # Se Redis está disponível, atualiza também lá
        if self.redis_client:
            self._store_in_redis(context)
        
        logger.debug(f"Contexto atualizado: {context_id}")
        return context
    
    def delete_context(self, context_id: str) -> bool:
        """
        Remove um contexto.
        
        Args:
            context_id: ID do contexto
            
        Returns:
            True se o contexto foi removido, False caso contrário
        """
        if context_id in self.contexts:
            context = self.contexts.pop(context_id)
            
            # Se Redis está disponível, remove também de lá
            if self.redis_client:
                self._delete_from_redis(context_id)
            
            logger.debug(f"Contexto removido: {context_id} ({context.type.value})")
            return True
        
        # Tenta remover do Redis mesmo se não estiver no cache local
        if self.redis_client:
            result = self._delete_from_redis(context_id)
            if result:
                logger.debug(f"Contexto removido apenas do Redis: {context_id}")
                return True
        
        return False
    
    def get_contexts_by_owner(self, owner_id: str, context_type: Optional[ContextType] = None) -> List[Context]:
        """
        Obtém todos os contextos de um proprietário.
        
        Args:
            owner_id: ID do proprietário
            context_type: Tipo de contexto para filtrar (opcional)
            
        Returns:
            Lista de contextos do proprietário
        """
        result = []
        
        # Busca no cache local
        for context in self.contexts.values():
            if context.owner_id == owner_id and (context_type is None or context.type == context_type):
                if not context.is_expired():
                    result.append(context)
        
        # Se Redis está disponível, busca também lá
        if self.redis_client:
            redis_contexts = self._load_owner_contexts_from_redis(owner_id, context_type)
            
            # Mescla resultados, evitando duplicatas
            existing_ids = {context.id for context in result}
            for context in redis_contexts:
                if context.id not in existing_ids and not context.is_expired():
                    result.append(context)
                    # Atualiza o cache local
                    self.contexts[context.id] = context
        
        return result
    
    def cleanup_expired(self) -> int:
        """
        Remove todos os contextos expirados.
        
        Returns:
            Número de contextos removidos
        """
        expired_ids = []
        
        # Identifica contextos expirados
        for context_id, context in list(self.contexts.items()):
            if context.is_expired():
                expired_ids.append(context_id)
        
        # Remove os contextos expirados
        for context_id in expired_ids:
            self.delete_context(context_id)
        
        count = len(expired_ids)
        if count > 0:
            logger.info(f"Removidos {count} contextos expirados")
        
        return count
    
    def _store_in_redis(self, context: Context) -> bool:
        """
        Armazena um contexto no Redis.
        
        Args:
            context: Contexto a ser armazenado
            
        Returns:
            True se armazenado com sucesso, False caso contrário
        """
        if not self.redis_client:
            return False
        
        try:
            # Chave no formato mcp:crew:context:{context_id}
            key = f"mcp:crew:context:{context.id}"
            
            # Chave secundária para busca por proprietário
            owner_key = f"mcp:crew:owner:{context.owner_id}:contexts"
            
            # Serializa o contexto
            context_data = json.dumps(context.to_dict())
            
            # Armazena o contexto
            if context.ttl:
                self.redis_client.setex(key, context.ttl, context_data)
            else:
                self.redis_client.set(key, context_data)
            
            # Adiciona à lista de contextos do proprietário
            self.redis_client.sadd(owner_key, context.id)
            
            return True
        except Exception as e:
            logger.error(f"Erro ao armazenar contexto no Redis: {e}")
            return False
    
    def _load_from_redis(self, context_id: str) -> Optional[Context]:
        """
        Carrega um contexto do Redis.
        
        Args:
            context_id: ID do contexto
            
        Returns:
            Contexto carregado ou None se não encontrado
        """
        if not self.redis_client:
            return None
        
        try:
            # Chave no formato mcp:crew:context:{context_id}
            key = f"mcp:crew:context:{context_id}"
            
            # Obtém o contexto serializado
            context_data = self.redis_client.get(key)
            if not context_data:
                return None
            
            # Deserializa o contexto
            context_dict = json.loads(context_data)
            return Context.from_dict(context_dict)
        except Exception as e:
            logger.error(f"Erro ao carregar contexto do Redis: {e}")
            return None
    
    def _delete_from_redis(self, context_id: str) -> bool:
        """
        Remove um contexto do Redis.
        
        Args:
            context_id: ID do contexto
            
        Returns:
            True se removido com sucesso, False caso contrário
        """
        if not self.redis_client:
            return False
        
        try:
            # Chave no formato mcp:crew:context:{context_id}
            key = f"mcp:crew:context:{context_id}"
            
            # Obtém o contexto para saber o proprietário
            context_data = self.redis_client.get(key)
            if context_data:
                try:
                    context_dict = json.loads(context_data)
                    owner_id = context_dict.get("owner_id")
                    
                    # Remove da lista de contextos do proprietário
                    if owner_id:
                        owner_key = f"mcp:crew:owner:{owner_id}:contexts"
                        self.redis_client.srem(owner_key, context_id)
                except:
                    pass
            
            # Remove o contexto
            self.redis_client.delete(key)
            
            return True
        except Exception as e:
            logger.error(f"Erro ao remover contexto do Redis: {e}")
            return False
    
    def _load_owner_contexts_from_redis(self, owner_id: str, context_type: Optional[ContextType] = None) -> List[Context]:
        """
        Carrega todos os contextos de um proprietário do Redis.
        
        Args:
            owner_id: ID do proprietário
            context_type: Tipo de contexto para filtrar (opcional)
            
        Returns:
            Lista de contextos do proprietário
        """
        if not self.redis_client:
            return []
        
        try:
            # Chave no formato mcp:crew:owner:{owner_id}:contexts
            owner_key = f"mcp:crew:owner:{owner_id}:contexts"
            
            # Obtém os IDs dos contextos do proprietário
            context_ids = self.redis_client.smembers(owner_key)
            if not context_ids:
                return []
            
            result = []
            for context_id in context_ids:
                context = self._load_from_redis(context_id)
                if context and (context_type is None or context.type == context_type):
       
(Content truncated due to size limit. Use line ranges to read in chunks)