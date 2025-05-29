"""
Gerenciador de contexto para conversas.
Mantém o histórico e estado das conversas.
"""

import json
import logging
import time
from flask import current_app
from app.utils.logger import get_logger

# Configuração do logger
logger = get_logger(__name__)

class ContextManager:
    """
    Gerenciador de contexto para conversas.
    """
    
    def __init__(self):
        """
        Inicializa o gerenciador de contexto.
        Em uma implementação real, isso usaria um banco de dados ou Redis.
        """
        # Armazenamento em memória para contextos (apenas para demonstração)
        # Em produção, isso seria um banco de dados ou Redis
        self.contexts = {}
    
    def get_context(self, conversation_id):
        """
        Obtém o contexto de uma conversa.
        
        Args:
            conversation_id: ID da conversa
            
        Returns:
            Dicionário com o contexto da conversa
        """
        # Se o contexto não existir, cria um novo
        if conversation_id not in self.contexts:
            self.contexts[conversation_id] = {
                'created_at': time.time(),
                'updated_at': time.time(),
                'messages': [],
                'metadata': {},
                'channel': 'unknown',
                'last_crew': None
            }
            logger.info(f"Novo contexto criado para conversa {conversation_id}")
        
        return self.contexts[conversation_id]
    
    def update_context(self, conversation_id, data):
        """
        Atualiza o contexto de uma conversa.
        
        Args:
            conversation_id: ID da conversa
            data: Dados a serem atualizados no contexto
            
        Returns:
            Contexto atualizado
        """
        # Obtém o contexto existente
        context = self.get_context(conversation_id)
        
        # Atualiza os dados
        for key, value in data.items():
            if key == 'messages' and isinstance(value, dict):
                # Adiciona uma nova mensagem ao histórico
                context['messages'].append(value)
                # Limita o tamanho do histórico
                max_messages = current_app.config.get('MAX_CONTEXT_MESSAGES', 10)
                if len(context['messages']) > max_messages:
                    context['messages'] = context['messages'][-max_messages:]
            else:
                # Atualiza outros campos diretamente
                context[key] = value
        
        # Atualiza o timestamp
        context['updated_at'] = time.time()
        
        # Salva o contexto atualizado
        self.contexts[conversation_id] = context
        
        logger.debug(f"Contexto atualizado para conversa {conversation_id}")
        
        return context
    
    def clear_context(self, conversation_id):
        """
        Limpa o contexto de uma conversa.
        
        Args:
            conversation_id: ID da conversa
            
        Returns:
            Boolean indicando sucesso ou falha
        """
        if conversation_id in self.contexts:
            del self.contexts[conversation_id]
            logger.info(f"Contexto limpo para conversa {conversation_id}")
            return True
        
        return False
    
    def add_message_to_context(self, conversation_id, message_data):
        """
        Adiciona uma mensagem ao contexto de uma conversa.
        
        Args:
            conversation_id: ID da conversa
            message_data: Dados da mensagem
            
        Returns:
            Contexto atualizado
        """
        # Cria um objeto de mensagem para o contexto
        message = {
            'id': message_data.get('message_id'),
            'content': message_data.get('content'),
            'timestamp': message_data.get('created_at'),
            'sender_type': message_data.get('sender', {}).get('type'),
            'sender_name': message_data.get('sender', {}).get('name')
        }
        
        # Atualiza o contexto
        return self.update_context(conversation_id, {
            'messages': message,
            'last_message': message_data.get('content'),
            'last_message_time': message_data.get('created_at'),
            'channel': message_data.get('channel')
        })
    
    def get_conversation_history(self, conversation_id, limit=None):
        """
        Obtém o histórico de mensagens de uma conversa.
        
        Args:
            conversation_id: ID da conversa
            limit: Número máximo de mensagens a retornar
            
        Returns:
            Lista de mensagens
        """
        context = self.get_context(conversation_id)
        messages = context.get('messages', [])
        
        if limit and len(messages) > limit:
            return messages[-limit:]
        
        return messages
