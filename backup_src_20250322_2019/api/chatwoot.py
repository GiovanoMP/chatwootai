"""
Cliente para API do Chatwoot.

Este módulo implementa um cliente para interagir com a API do Chatwoot,
permitindo enviar e receber mensagens, gerenciar conversas e contatos.
"""

import logging
import json
import asyncio
import aiohttp
from typing import Dict, Any, List, Optional, Union
import traceback

logger = logging.getLogger(__name__)

class ChatwootClient:
    """
    Cliente para API do Chatwoot.
    
    Esta classe implementa as operações necessárias para interagir com a
    API do Chatwoot, como enviar mensagens, obter conversas, etc.
    """
    
    def __init__(self, api_key: str, base_url: str, account_id: int):
        """
        Inicializa o cliente do Chatwoot.
        
        Args:
            api_key: Chave da API do Chatwoot
            base_url: URL base da API do Chatwoot (ex: https://chatwoot.seu-dominio.com/api/v1)
            account_id: ID da conta do Chatwoot
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.account_id = account_id
        self.default_headers = {
            'api_access_token': api_key,
            'Content-Type': 'application/json'
        }
        
        # Sessão HTTP (será inicializada sob demanda)
        self._session = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """
        Retorna a sessão HTTP ou cria uma nova se não existir.
        
        Returns:
            aiohttp.ClientSession: Sessão HTTP
        """
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(headers=self.default_headers)
        return self._session
    
    async def close(self):
        """Fecha a sessão HTTP."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None
    
    async def _make_request(self, method: str, endpoint: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Faz uma requisição para a API do Chatwoot.
        
        Args:
            method: Método HTTP (GET, POST, etc.)
            endpoint: Endpoint da API (sem a URL base)
            data: Dados a serem enviados na requisição
            
        Returns:
            Dict[str, Any]: Resposta da API
        """
        # Garante que temos uma sessão válida
        session = await self._get_session()
        
        # Monta a URL completa
        url = f"{self.base_url}{endpoint}"
        
        # Adiciona account_id à URL se não estiver presente
        if 'accounts/' not in endpoint:
            url = f"{self.base_url}/accounts/{self.account_id}{endpoint}"
        
        try:
            # Log da requisição
            logger.debug(f"Requisição para API do Chatwoot: {method} {url}")
            if data:
                logger.debug(f"Dados: {json.dumps(data, ensure_ascii=False)}")
            
            # Faz a requisição
            async with session.request(method, url, json=data) as response:
                # Verifica se a resposta é JSON
                content_type = response.headers.get('Content-Type', '')
                if 'application/json' in content_type:
                    result = await response.json()
                else:
                    text = await response.text()
                    logger.warning(f"Resposta não é JSON: {text}")
                    result = {'text': text}
                
                # Loga o status HTTP
                logger.debug(f"Status HTTP: {response.status}")
                
                # Se a resposta não for bem-sucedida, loga o erro
                if not response.ok:
                    logger.error(f"Erro na API do Chatwoot: {response.status} - {result}")
                    # Adiciona informações de status ao resultado
                    result['status_code'] = response.status
                
                # Retorna o resultado
                return result
        except aiohttp.ClientError as e:
            # Erro de rede
            logger.error(f"Erro de rede ao chamar API do Chatwoot: {str(e)}")
            logger.error(traceback.format_exc())
            raise
        except json.JSONDecodeError as e:
            # Erro de parsing JSON
            logger.error(f"Erro ao fazer parsing da resposta da API do Chatwoot: {str(e)}")
            logger.error(traceback.format_exc())
            raise
        except Exception as e:
            # Erro genérico
            logger.error(f"Erro ao chamar API do Chatwoot: {str(e)}")
            logger.error(traceback.format_exc())
            raise
    
    async def send_message(self, conversation_id: str, content: str, private: bool = False, 
                          message_type: str = "outgoing", content_type: str = "text") -> Dict[str, Any]:
        """
        Envia uma mensagem para uma conversa.
        
        Args:
            conversation_id: ID da conversa
            content: Conteúdo da mensagem
            private: Se a mensagem é privada (apenas para agentes)
            message_type: Tipo da mensagem (outgoing, template, etc.)
            content_type: Tipo do conteúdo (text, input_select, etc.)
            
        Returns:
            Dict[str, Any]: Resultado da operação
        """
        endpoint = f"/conversations/{conversation_id}/messages"
        data = {
            "content": content,
            "private": private,
            "message_type": message_type,
            "content_type": content_type
        }
        
        return await self._make_request('POST', endpoint, data)
    
    async def get_conversation(self, conversation_id: str) -> Dict[str, Any]:
        """
        Obtém detalhes de uma conversa.
        
        Args:
            conversation_id: ID da conversa
            
        Returns:
            Dict[str, Any]: Detalhes da conversa
        """
        endpoint = f"/conversations/{conversation_id}"
        return await self._make_request('GET', endpoint)
    
    async def get_messages(self, conversation_id: str, before: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Obtém mensagens de uma conversa.
        
        Args:
            conversation_id: ID da conversa
            before: ID da mensagem para paginação (opcional)
            
        Returns:
            List[Dict[str, Any]]: Lista de mensagens
        """
        endpoint = f"/conversations/{conversation_id}/messages"
        
        # Se temos um ID para paginação
        if before:
            endpoint += f"?before={before}"
        
        return await self._make_request('GET', endpoint)
    
    async def get_contact(self, contact_id: str) -> Dict[str, Any]:
        """
        Obtém detalhes de um contato.
        
        Args:
            contact_id: ID do contato
            
        Returns:
            Dict[str, Any]: Detalhes do contato
        """
        endpoint = f"/contacts/{contact_id}"
        return await self._make_request('GET', endpoint)
    
    async def get_all_conversations(self, status_filter: str = "open") -> List[Dict[str, Any]]:
        """
        Obtém todas as conversas.
        
        Args:
            status_filter: Filtro de status (open, resolved, etc.)
            
        Returns:
            List[Dict[str, Any]]: Lista de conversas
        """
        endpoint = f"/conversations?status={status_filter}"
        return await self._make_request('GET', endpoint)
    
    async def update_conversation_status(self, conversation_id: str, status: str) -> Dict[str, Any]:
        """
        Atualiza o status de uma conversa.
        
        Args:
            conversation_id: ID da conversa
            status: Novo status (open, resolved, etc.)
            
        Returns:
            Dict[str, Any]: Resultado da operação
        """
        endpoint = f"/conversations/{conversation_id}/toggle_status"
        data = {"status": status}
        return await self._make_request('POST', endpoint, data)
    
    async def assign_conversation(self, conversation_id: str, assignee_id: int) -> Dict[str, Any]:
        """
        Atribui uma conversa a um agente.
        
        Args:
            conversation_id: ID da conversa
            assignee_id: ID do agente
            
        Returns:
            Dict[str, Any]: Resultado da operação
        """
        endpoint = f"/conversations/{conversation_id}/assignments"
        data = {"assignee_id": assignee_id}
        return await self._make_request('POST', endpoint, data)
    
    async def get_labels(self, conversation_id: str) -> List[str]:
        """
        Obtém as etiquetas de uma conversa.
        
        Args:
            conversation_id: ID da conversa
            
        Returns:
            List[str]: Lista de etiquetas
        """
        endpoint = f"/conversations/{conversation_id}/labels"
        result = await self._make_request('GET', endpoint)
        # Processa o resultado para extrair as etiquetas
        if isinstance(result, dict) and 'payload' in result:
            return result['payload']
        return result
    
    async def add_label(self, conversation_id: str, labels: List[str]) -> Dict[str, Any]:
        """
        Adiciona etiquetas a uma conversa.
        
        Args:
            conversation_id: ID da conversa
            labels: Lista de etiquetas
            
        Returns:
            Dict[str, Any]: Resultado da operação
        """
        endpoint = f"/conversations/{conversation_id}/labels"
        data = {"labels": labels}
        return await self._make_request('POST', endpoint, data)
