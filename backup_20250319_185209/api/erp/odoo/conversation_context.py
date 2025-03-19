"""
Extensão do cliente Odoo para gerenciar o contexto das conversas.
"""
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime
import json

from .client import OdooClient

logger = logging.getLogger(__name__)

class OdooConversationContextClient(OdooClient):
    """
    Extensão do cliente Odoo para gerenciar o contexto das conversas.
    
    Esta classe estende o OdooClient para adicionar métodos específicos
    para gerenciar o contexto das conversas no CRM do Odoo.
    """
    
    def search_customer(self, email: str = None, phone: str = None) -> Dict[str, Any]:
        """
        Busca um cliente pelo email ou telefone.
        
        Args:
            email: Email do cliente (opcional)
            phone: Telefone do cliente (opcional)
            
        Returns:
            Dict[str, Any]: Cliente encontrado ou None
        """
        logger.info(f"Buscando cliente por email: {email} ou telefone: {phone}")
        
        # Constrói os parâmetros de busca
        params = {}
        if email:
            params["email"] = email
        if phone:
            params["phone"] = phone
            
        if not params:
            logger.warning("Nenhum critério de busca fornecido (email ou telefone)")
            return None
            
        # Realiza a busca
        result = self._make_request("GET", "/customers/search", params)
        
        # Verifica se encontrou algum cliente
        if "error" in result or not result.get("data"):
            logger.info("Nenhum cliente encontrado")
            return None
            
        return result.get("data")[0]  # Retorna o primeiro cliente encontrado
    
    def create_lead(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Cria um novo lead no CRM.
        
        Args:
            lead_data: Dados do lead
            
        Returns:
            Dict[str, Any]: Lead criado
        """
        logger.info(f"Criando novo lead: {lead_data}")
        
        # Adiciona a data de criação
        lead_data["create_date"] = datetime.now().isoformat()
        
        # Cria o lead
        result = self._make_request("POST", "/crm/leads", lead_data)
        
        if "error" in result:
            logger.error(f"Erro ao criar lead: {result['error']}")
            return None
            
        return result.get("data")
    
    def create_conversation_thread(self, thread_data: Dict[str, Any]) -> bool:
        """
        Cria uma nova thread de conversa vinculada a um cliente.
        
        Args:
            thread_data: Dados da thread
            
        Returns:
            bool: True se a operação foi bem-sucedida
        """
        logger.info(f"Criando thread de conversa para cliente: {thread_data.get('customer_id')}")
        
        # Adiciona a data de criação
        if "timestamp" not in thread_data:
            thread_data["timestamp"] = datetime.now().isoformat()
        
        # Cria a thread
        result = self._make_request("POST", "/crm/conversation-threads", thread_data)
        
        if "error" in result:
            logger.error(f"Erro ao criar thread de conversa: {result['error']}")
            return False
            
        return True
    
    def get_conversation_threads(self, customer_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Obtém as threads de conversa de um cliente.
        
        Args:
            customer_id: ID do cliente
            limit: Limite de resultados
            
        Returns:
            List[Dict[str, Any]]: Lista de threads de conversa
        """
        logger.info(f"Obtendo threads de conversa para cliente: {customer_id}")
        
        # Obtém as threads
        result = self._make_request("GET", f"/crm/customers/{customer_id}/conversation-threads", {"limit": limit})
        
        if "error" in result:
            logger.error(f"Erro ao obter threads de conversa: {result['error']}")
            return []
            
        return result.get("data", [])
    
    def get_conversation_context(self, conversation_id: str) -> Dict[str, Any]:
        """
        Obtém o contexto de uma conversa.
        
        Args:
            conversation_id: ID da conversa
            
        Returns:
            Dict[str, Any]: Contexto da conversa
        """
        logger.info(f"Obtendo contexto da conversa: {conversation_id}")
        
        # Obtém o contexto
        result = self._make_request("GET", f"/crm/conversations/{conversation_id}/context")
        
        if "error" in result:
            logger.error(f"Erro ao obter contexto da conversa: {result['error']}")
            return {}
            
        return result.get("data", {})
    
    def update_conversation_context(self, conversation_id: str, customer_id: int, context_data: Dict[str, Any]) -> bool:
        """
        Atualiza o contexto de uma conversa.
        
        Args:
            conversation_id: ID da conversa
            customer_id: ID do cliente
            context_data: Dados de contexto a serem atualizados
            
        Returns:
            bool: True se a operação foi bem-sucedida
        """
        logger.info(f"Atualizando contexto da conversa: {conversation_id}")
        
        # Prepara os dados
        data = {
            "conversation_id": conversation_id,
            "customer_id": customer_id,
            "context_data": context_data,
            "updated_at": datetime.now().isoformat()
        }
        
        # Atualiza o contexto
        result = self._make_request("PUT", f"/crm/conversations/{conversation_id}/context", data)
        
        if "error" in result:
            logger.error(f"Erro ao atualizar contexto da conversa: {result['error']}")
            return False
            
        return True
    
    def get_conversation_messages(self, conversation_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Obtém as mensagens de uma conversa.
        
        Args:
            conversation_id: ID da conversa
            limit: Limite de resultados
            
        Returns:
            List[Dict[str, Any]]: Lista de mensagens
        """
        logger.info(f"Obtendo mensagens da conversa: {conversation_id}")
        
        # Obtém as mensagens
        result = self._make_request("GET", f"/crm/conversations/{conversation_id}/messages", {"limit": limit})
        
        if "error" in result:
            logger.error(f"Erro ao obter mensagens da conversa: {result['error']}")
            return []
            
        return result.get("data", [])
