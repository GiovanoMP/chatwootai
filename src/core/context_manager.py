#!/usr/bin/env python3
"""
Gerenciador de Contexto para o ChatwootAI

Este módulo implementa o ContextManagerAgent, responsável por gerenciar o contexto
das conversas no sistema ChatwootAI. Ele mantém o histórico de mensagens, informações
do cliente, e outros dados relevantes para o processamento de mensagens.
"""

import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

# Configuração de logging
logger = logging.getLogger(__name__)

class ContextManagerAgent:
    """
    Agente responsável por gerenciar o contexto das conversas.
    
    O ContextManagerAgent mantém um registro do histórico de conversas,
    informações do cliente, e outros dados relevantes para o processamento
    de mensagens. Ele fornece métodos para atualizar e consultar o contexto.
    """
    
    def __init__(self, max_history: int = 10):
        """
        Inicializa o ContextManagerAgent.
        
        Args:
            max_history: Número máximo de mensagens a manter no histórico
        """
        self.max_history = max_history
        self.contexts = {}  # Dicionário de contextos por conversation_id
        logger.info("ContextManagerAgent inicializado")
    
    def get_context(self, conversation_id: str) -> Dict[str, Any]:
        """
        Obtém o contexto de uma conversa.
        
        Args:
            conversation_id: ID da conversa
            
        Returns:
            Dict[str, Any]: Contexto da conversa
        """
        if conversation_id not in self.contexts:
            # Criar novo contexto se não existir
            self.contexts[conversation_id] = {
                "conversation_id": conversation_id,
                "history": [],
                "client_info": {},
                "metadata": {
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                }
            }
            logger.info(f"Novo contexto criado para conversa {conversation_id}")
        
        return self.contexts[conversation_id]
    
    def update_context(self, conversation_id: str, message: Dict[str, Any], 
                       client_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Atualiza o contexto de uma conversa com uma nova mensagem.
        
        Args:
            conversation_id: ID da conversa
            message: Mensagem a ser adicionada ao contexto
            client_info: Informações do cliente (opcional)
            
        Returns:
            Dict[str, Any]: Contexto atualizado
        """
        context = self.get_context(conversation_id)
        
        # Adicionar mensagem ao histórico
        context["history"].append({
            "timestamp": datetime.now().isoformat(),
            "message": message
        })
        
        # Limitar tamanho do histórico
        if len(context["history"]) > self.max_history:
            context["history"] = context["history"][-self.max_history:]
        
        # Atualizar informações do cliente, se fornecidas
        if client_info:
            context["client_info"].update(client_info)
            logger.debug(f"Informações do cliente atualizadas para conversa {conversation_id}")
        
        # Atualizar timestamp
        context["metadata"]["updated_at"] = datetime.now().isoformat()
        
        logger.debug(f"Contexto atualizado para conversa {conversation_id}")
        return context
    
    def clear_context(self, conversation_id: str) -> None:
        """
        Limpa o contexto de uma conversa.
        
        Args:
            conversation_id: ID da conversa
        """
        if conversation_id in self.contexts:
            del self.contexts[conversation_id]
            logger.info(f"Contexto limpo para conversa {conversation_id}")
    
    def get_conversation_history(self, conversation_id: str) -> List[Dict[str, Any]]:
        """
        Obtém o histórico de mensagens de uma conversa.
        
        Args:
            conversation_id: ID da conversa
            
        Returns:
            List[Dict[str, Any]]: Histórico de mensagens
        """
        context = self.get_context(conversation_id)
        return context["history"]
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Converte o estado do ContextManagerAgent para um dicionário.
        
        Returns:
            Dict[str, Any]: Estado do ContextManagerAgent
        """
        return {
            "contexts": self.contexts,
            "max_history": self.max_history
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ContextManagerAgent':
        """
        Cria um ContextManagerAgent a partir de um dicionário.
        
        Args:
            data: Dicionário com o estado do ContextManagerAgent
            
        Returns:
            ContextManagerAgent: Nova instância do ContextManagerAgent
        """
        instance = cls(max_history=data.get("max_history", 10))
        instance.contexts = data.get("contexts", {})
        return instance
    
    def __str__(self) -> str:
        """
        Representação em string do ContextManagerAgent.
        
        Returns:
            str: Representação em string
        """
        return f"ContextManagerAgent(contexts={len(self.contexts)}, max_history={self.max_history})"
