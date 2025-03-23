"""
ConversationContextService - Serviço para gerenciamento de contexto de conversas.

Este serviço implementa funcionalidades para armazenar, recuperar e gerenciar
o contexto das conversas entre agentes e clientes, incluindo histórico de mensagens,
intenções detectadas e variáveis de contexto.
"""

import logging
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Union, Optional, Tuple

from .base_data_service import BaseDataService

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConversationContextService(BaseDataService):
    """
    Serviço de dados especializado em contexto de conversas.
    
    Implementa operações específicas para gerenciamento de contexto, incluindo:
    - Armazenamento e recuperação de mensagens
    - Rastreamento de intenções e entidades detectadas
    - Gerenciamento de variáveis de contexto
    - Persistência de estado da conversa
    """
    
    def __init__(self, data_service_hub):
        """
        Inicializa o serviço de contexto de conversas.
        
        Args:
            data_service_hub: Instância do DataServiceHub.
        """
        super().__init__(data_service_hub)
        
        # Prefixos para chaves de cache
        self.context_prefix = "context"
        self.messages_prefix = "messages"
        self.variables_prefix = "variables"
        
        # TTL padrão (30 minutos para contexto de conversa)
        self.context_ttl = 1800
        
        logger.info("ConversationContextService inicializado")
    
    def get_entity_type(self) -> str:
        """
        Retorna o tipo de entidade gerenciada por este serviço.
        
        Returns:
            String representando o tipo de entidade.
        """
        return "conversation_contexts"
    
    def _get_context_key(self, conversation_id: str) -> str:
        """
        Gera a chave de cache para o contexto completo.
        
        Args:
            conversation_id: ID da conversa.
            
        Returns:
            Chave formatada.
        """
        return f"{self.context_prefix}:{conversation_id}"
    
    def _get_messages_key(self, conversation_id: str) -> str:
        """
        Gera a chave de cache para as mensagens da conversa.
        
        Args:
            conversation_id: ID da conversa.
            
        Returns:
            Chave formatada.
        """
        return f"{self.messages_prefix}:{conversation_id}"
    
    def _get_variables_key(self, conversation_id: str) -> str:
        """
        Gera a chave de cache para as variáveis de contexto.
        
        Args:
            conversation_id: ID da conversa.
            
        Returns:
            Chave formatada.
        """
        return f"{self.variables_prefix}:{conversation_id}"
    
    def get_context(self, conversation_id: str) -> Dict[str, Any]:
        """
        Obtém o contexto completo da conversa.
        
        Args:
            conversation_id: ID da conversa.
            
        Returns:
            Contexto completo da conversa ou dicionário vazio se não encontrado.
        """
        # Tentar obter do cache
        context_key = self._get_context_key(conversation_id)
        cached_context = self.hub.cache_get(context_key)
        
        if cached_context:
            logger.debug(f"Contexto da conversa {conversation_id} recuperado do cache")
            return cached_context
        
        # Se não estiver no cache, tentar obter do banco de dados
        query = """
            SELECT 
                id,
                conversation_id,
                customer_id,
                agent_id,
                status,
                metadata,
                created_at,
                updated_at
            FROM conversation_contexts
            WHERE conversation_id = %(conversation_id)s
        """
        
        params = {"conversation_id": conversation_id}
        
        result = self.hub.execute_query(query, params, fetch_all=False)
        
        if not result:
            # Criar um novo contexto vazio
            now = datetime.now()
            empty_context = {
                "conversation_id": conversation_id,
                "customer_id": None,
                "agent_id": None,
                "status": "new",
                "metadata": {},
                "created_at": now.isoformat(),  # serializar datetime para string
                "updated_at": now.isoformat(),  # serializar datetime para string
                "messages": [],
                "variables": {}
            }
            
            # Armazenar no cache
            self.hub.cache_set(context_key, empty_context, ttl=self.context_ttl)
            
            return empty_context
        
        # Serializar campos de data para string ISO
        if isinstance(result.get("created_at"), datetime):
            result["created_at"] = result["created_at"].isoformat()
        
        if isinstance(result.get("updated_at"), datetime):
            result["updated_at"] = result["updated_at"].isoformat()
            
        # Converter campos JSON
        if isinstance(result.get("metadata"), str):
            try:
                result["metadata"] = json.loads(result["metadata"])
            except json.JSONDecodeError:
                result["metadata"] = {}
        
        # Obter mensagens da conversa
        result["messages"] = self.get_messages(conversation_id)
        
        # Obter variáveis de contexto
        result["variables"] = self.get_variables(conversation_id)
        
        # Serializar completamente o resultado para garantir que todos os objetos são serializáveis
        serialized_result = json.dumps(result, default=self.hub._json_encoder)
        
        # Armazenar no cache
        self.hub.cache_set(context_key, serialized_result, ttl=self.context_ttl)
        
        # Retornar objeto deserializado
        return json.loads(serialized_result)
    
    def update_context(self, conversation_id: str, context_data: Dict[str, Any]) -> bool:
        """
        Atualiza o contexto de uma conversa.
        
        Args:
            conversation_id: ID da conversa.
            context_data: Dados do contexto para atualizar.
            
        Returns:
            True se atualizado com sucesso, False caso contrário.
        """
        # Obter o contexto atual
        current_context = self.get_context(conversation_id)
        
        # Atualizar campos do contexto
        context_id = current_context.get("id")
        customer_id = context_data.get("customer_id") or current_context.get("customer_id")
        agent_id = context_data.get("agent_id") or current_context.get("agent_id")
        status = context_data.get("status") or current_context.get("status")
        
        # Merge de metadata (preservando campos existentes)
        metadata = current_context.get("metadata", {})
        if context_data.get("metadata"):
            metadata.update(context_data.get("metadata", {}))
        
        # Timestamp atualizado
        updated_at = datetime.now()
        
        # Atualizar mensagens se fornecidas
        if "messages" in context_data:
            self.set_messages(conversation_id, context_data["messages"])
        
        # Atualizar variáveis se fornecidas
        if "variables" in context_data:
            self.set_variables(conversation_id, context_data["variables"])
        
        # Remover campos que são tratados separadamente
        update_data = {k: v for k, v in context_data.items() 
                    if k not in ["messages", "variables", "metadata"]}
        
        # Adicionar metadata serializada
        update_data["metadata"] = json.dumps(metadata)
        update_data["updated_at"] = updated_at
        
        if context_id:
            # Contexto já existe, atualizar
            update_data["id"] = context_id
            
            # Construir SET clause
            set_clauses = [f"{key} = %({key})s" for key in update_data.keys()]
            set_clause = ", ".join(set_clauses)
            
            query = f"""
                UPDATE conversation_contexts
                SET {set_clause}
                WHERE id = %(id)s
                RETURNING id
            """
        else:
            # Criar novo contexto
            update_data["conversation_id"] = conversation_id
            update_data["customer_id"] = customer_id
            update_data["agent_id"] = agent_id
            update_data["status"] = status
            update_data["created_at"] = updated_at
            
            columns = ", ".join(update_data.keys())
            placeholders = ", ".join([f"%({key})s" for key in update_data.keys()])
            
            query = f"""
                INSERT INTO conversation_contexts ({columns})
                VALUES ({placeholders})
                RETURNING id
            """
        
        result = self.hub.execute_query(query, update_data, fetch_all=False)
        
        if not result:
            logger.error(f"Falha ao atualizar contexto da conversa: {conversation_id}")
            return False
        
        # Invalidar cache
        context_key = self._get_context_key(conversation_id)
        self.hub.cache_invalidate(context_key)
        
        return True
    
    def get_messages(self, conversation_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Obtém as mensagens de uma conversa.
        
        Args:
            conversation_id: ID da conversa.
            limit: Número máximo de mensagens.
            
        Returns:
            Lista de mensagens da conversa.
        """
        # Tentar obter do cache
        messages_key = self._get_messages_key(conversation_id)
        cached_messages = self.hub.cache_get(messages_key)
        
        if cached_messages:
            try:
                return json.loads(cached_messages)
            except json.JSONDecodeError:
                logger.error(f"Erro ao decodificar mensagens da conversa: {conversation_id}")
        
        # Se não estiver no cache, obter do banco de dados
        query = """
            SELECT 
                id,
                conversation_id,
                sender_id,
                sender_type,
                content,
                metadata,
                created_at
            FROM conversation_messages
            WHERE conversation_id = %(conversation_id)s
            ORDER BY created_at DESC
            LIMIT %(limit)s
        """
        
        params = {
            "conversation_id": conversation_id,
            "limit": limit
        }
        
        messages = self.hub.execute_query(query, params) or []
        
        # Converter campos JSON e serializar campos de data
        for msg in messages:
            # Serializar campos de data
            if isinstance(msg.get("created_at"), datetime):
                msg["created_at"] = msg["created_at"].isoformat()
                
            # Converter campos JSON
            if isinstance(msg.get("metadata"), str):
                try:
                    msg["metadata"] = json.loads(msg["metadata"])
                except json.JSONDecodeError:
                    msg["metadata"] = {}
        
        # Inverter para ordem cronológica
        messages.reverse()
        
        # Serializar para JSON e armazenar no cache
        # Usamos dumps e loads para garantir que temos um objeto completamente serializável
        serialized_messages = json.dumps(messages, default=self.hub._json_encoder)
        self.hub.cache_set(messages_key, serialized_messages, ttl=self.context_ttl)
        
        # Retornar objeto deserializado para garantir que tudo está no formato correto
        return json.loads(serialized_messages)
    
    def add_message(self, conversation_id: str, message_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Adiciona uma nova mensagem à conversa.
        
        Args:
            conversation_id: ID da conversa.
            message_data: Dados da mensagem.
            
        Returns:
            Mensagem adicionada ou None em caso de erro.
        """
        # Garantir que temos conversation_id
        data = dict(message_data)
        data["conversation_id"] = conversation_id
        
        # Garantir que temos timestamp
        if "created_at" not in data:
            data["created_at"] = datetime.now()
        
        # Serializar metadata se necessário
        if "metadata" in data and not isinstance(data["metadata"], str):
            data["metadata"] = json.dumps(data["metadata"])
        
        # Inserir mensagem
        columns = ", ".join(data.keys())
        placeholders = ", ".join([f"%({key})s" for key in data.keys()])
        
        query = f"""
            INSERT INTO conversation_messages ({columns})
            VALUES ({placeholders})
            RETURNING *
        """
        
        result = self.hub.execute_query(query, data, fetch_all=False)
        
        if not result:
            logger.error(f"Falha ao adicionar mensagem à conversa: {conversation_id}")
            return None
        
        # Invalidar caches
        messages_key = self._get_messages_key(conversation_id)
        context_key = self._get_context_key(conversation_id)
        self.hub.cache_invalidate(messages_key)
        self.hub.cache_invalidate(context_key)
        
        # Converter metadata de volta para objeto
        if isinstance(result.get("metadata"), str):
            try:
                result["metadata"] = json.loads(result["metadata"])
            except json.JSONDecodeError:
                result["metadata"] = {}
        
        return result
    
    def set_messages(self, conversation_id: str, messages: List[Dict[str, Any]]) -> bool:
        """
        Define as mensagens de uma conversa (substitui as existentes).
        
        Args:
            conversation_id: ID da conversa.
            messages: Lista de mensagens.
            
        Returns:
            True se definido com sucesso, False caso contrário.
        """
        # Serializar mensagens para JSON usando o codificador personalizado
        messages_key = self._get_messages_key(conversation_id)
        serialized_messages = json.dumps(messages, default=self.hub._json_encoder)
        self.hub.cache_set(messages_key, serialized_messages, ttl=self.context_ttl)
        
        # Invalidar cache do contexto
        context_key = self._get_context_key(conversation_id)
        self.hub.cache_invalidate(context_key)
        
        return True
    
    def get_variables(self, conversation_id: str) -> Dict[str, Any]:
        """
        Obtém as variáveis de contexto de uma conversa.
        
        Args:
            conversation_id: ID da conversa.
            
        Returns:
            Dicionário de variáveis de contexto.
        """
        # Tentar obter do cache
        variables_key = self._get_variables_key(conversation_id)
        cached_variables = self.hub.cache_get(variables_key)
        
        if cached_variables:
            try:
                return json.loads(cached_variables)
            except json.JSONDecodeError:
                logger.error(f"Erro ao decodificar variáveis da conversa: {conversation_id}")
        
        # Se não estiver no cache, obter do banco de dados
        query = """
            SELECT variable_key, variable_value
            FROM conversation_variables
            WHERE conversation_id = %(conversation_id)s
        """
        
        params = {"conversation_id": conversation_id}
        
        results = self.hub.execute_query(query, params) or []
        
        # Converter para dicionário
        variables = {}
        for var in results:
            # Tentar converter valores JSON
            try:
                value = json.loads(var['variable_value'])
            except (json.JSONDecodeError, TypeError):
                value = var['variable_value']
                
            variables[var['variable_key']] = value
        
        # Serializar para JSON usando o codificador personalizado e armazenar no cache
        serialized_variables = json.dumps(variables, default=self.hub._json_encoder)
        self.hub.cache_set(variables_key, serialized_variables, ttl=self.context_ttl)
        
        # Retornar objeto deserializado para garantir que tudo está no formato correto
        return json.loads(serialized_variables)
    
    def set_variable(self, conversation_id: str, key: str, value: Any) -> bool:
        """
        Define ou atualiza uma variável de contexto.
        
        Args:
            conversation_id: ID da conversa.
            key: Chave da variável.
            value: Valor da variável.
            
        Returns:
            True se definido com sucesso, False caso contrário.
        """
        # Obter variáveis atuais
        variables = self.get_variables(conversation_id)
        
        # Atualizar variável
        variables[key] = value
        
        # Armazenar no cache
        variables_key = self._get_variables_key(conversation_id)
        self.hub.cache_set(variables_key, json.dumps(variables, default=self.hub._json_encoder), ttl=self.context_ttl)
        
        # Invalidar cache do contexto
        context_key = self._get_context_key(conversation_id)
        self.hub.cache_invalidate(context_key)
        
        # Serializar valor se necessário
        if not isinstance(value, str):
            value = json.dumps(value)
        
        # Verificar se a variável já existe
        check_query = """
            SELECT id FROM conversation_variables
            WHERE conversation_id = %(conversation_id)s AND variable_key = %(key)s
        """
        
        check_params = {
            "conversation_id": conversation_id,
            "key": key
        }
        
        existing = self.hub.execute_query(check_query, check_params, fetch_all=False)
        
        if existing:
            # Atualizar variável existente
            update_query = """
                UPDATE conversation_variables
                SET variable_value = %(value)s, updated_at = NOW()
                WHERE conversation_id = %(conversation_id)s AND variable_key = %(key)s
                RETURNING id
            """
            
            update_params = {
                "conversation_id": conversation_id,
                "key": key,
                "value": value
            }
            
            result = self.hub.execute_query(update_query, update_params, fetch_all=False)
        else:
            # Inserir nova variável
            insert_query = """
                INSERT INTO conversation_variables
                (conversation_id, variable_key, variable_value, created_at, updated_at)
                VALUES (%(conversation_id)s, %(key)s, %(value)s, NOW(), NOW())
                RETURNING id
            """
            
            insert_params = {
                "conversation_id": conversation_id,
                "key": key,
                "value": value
            }
            
            result = self.hub.execute_query(insert_query, insert_params, fetch_all=False)
        
        return result is not None
    
    def set_variables(self, conversation_id: str, variables: Dict[str, Any]) -> bool:
        """
        Define as variáveis de contexto de uma conversa (substitui as existentes).
        
        Args:
            conversation_id: ID da conversa.
            variables: Dicionário de variáveis.
            
        Returns:
            True se definido com sucesso, False caso contrário.
        """
        # Armazenar no cache
        variables_key = self._get_variables_key(conversation_id)
        self.hub.cache_set(variables_key, json.dumps(variables, default=self.hub._json_encoder), ttl=self.context_ttl)
        
        # Invalidar cache do contexto
        context_key = self._get_context_key(conversation_id)
        self.hub.cache_invalidate(context_key)
        
        # Opcionalmente, podemos sincronizar com o banco de dados
        # Para manter simples, apenas armazenamos no cache por enquanto
        
        return True
    
    def clear_context(self, conversation_id: str) -> bool:
        """
        Limpa o contexto de uma conversa.
        
        Args:
            conversation_id: ID da conversa.
            
        Returns:
            True se limpo com sucesso, False caso contrário.
        """
        # Invalidar todos os caches
        context_key = self._get_context_key(conversation_id)
        messages_key = self._get_messages_key(conversation_id)
        variables_key = self._get_variables_key(conversation_id)
        
        self.hub.cache_invalidate(context_key)
        self.hub.cache_invalidate(messages_key)
        self.hub.cache_invalidate(variables_key)
        
        # Atualizar status no banco de dados
        query = """
            UPDATE conversation_contexts
            SET status = 'closed', updated_at = NOW()
            WHERE conversation_id = %(conversation_id)s
            RETURNING id
        """
        
        params = {"conversation_id": conversation_id}
        
        result = self.hub.execute_query(query, params, fetch_all=False)
        
        return True  # Mesmo se não houver um registro para atualizar
    
    def get_active_conversations(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Obtém uma lista de conversas ativas.
        
        Args:
            limit: Número máximo de conversas.
            
        Returns:
            Lista de contextos de conversas ativas.
        """
        query = """
            SELECT 
                id,
                conversation_id,
                customer_id,
                agent_id,
                status,
                metadata,
                created_at,
                updated_at
            FROM conversation_contexts
            WHERE status NOT IN ('closed', 'archived')
            ORDER BY updated_at DESC
            LIMIT %(limit)s
        """
        
        params = {"limit": limit}
        
        results = self.hub.execute_query(query, params) or []
        
        # Converter campos JSON
        for context in results:
            if isinstance(context.get("metadata"), str):
                try:
                    context["metadata"] = json.loads(context["metadata"])
                except json.JSONDecodeError:
                    context["metadata"] = {}
        
        return results
    
    def get_recent_conversations_by_customer(self, customer_id: int, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Obtém as conversas recentes de um cliente.
        
        Args:
            customer_id: ID do cliente.
            limit: Número máximo de conversas.
            
        Returns:
            Lista de contextos de conversas recentes.
        """
        query = """
            SELECT 
                id,
                conversation_id,
                customer_id,
                agent_id,
                status,
                metadata,
                created_at,
                updated_at
            FROM conversation_contexts
            WHERE customer_id = %(customer_id)s
            ORDER BY updated_at DESC
            LIMIT %(limit)s
        """
        
        params = {
            "customer_id": customer_id,
            "limit": limit
        }
        
        results = self.hub.execute_query(query, params) or []
        
        # Converter campos JSON
        for context in results:
            if isinstance(context.get("metadata"), str):
                try:
                    context["metadata"] = json.loads(context["metadata"])
                except json.JSONDecodeError:
                    context["metadata"] = {}
            
            # Adicionar resumo de mensagens
            context["message_summary"] = self._get_conversation_summary(context["conversation_id"])
        
        return results
    
    def _get_conversation_summary(self, conversation_id: str) -> Dict[str, Any]:
        """
        Gera um resumo da conversa.
        
        Args:
            conversation_id: ID da conversa.
            
        Returns:
            Resumo da conversa.
        """
        # Obter primeiras e últimas mensagens
        messages = self.get_messages(conversation_id, limit=10)
        
        if not messages:
            return {
                "message_count": 0,
                "first_message": None,
                "last_message": None,
                "duration": None
            }
        
        first_message = messages[0] if messages else None
        last_message = messages[-1] if messages else None
        
        # Calcular duração
        duration = None
        if first_message and last_message:
            try:
                first_time = datetime.fromisoformat(first_message.get("created_at").replace("Z", "+00:00"))
                last_time = datetime.fromisoformat(last_message.get("created_at").replace("Z", "+00:00"))
                duration = (last_time - first_time).total_seconds()
            except (ValueError, AttributeError):
                duration = None
        
        return {
            "message_count": len(messages),
            "first_message": first_message,
            "last_message": last_message,
            "duration": duration
        }
