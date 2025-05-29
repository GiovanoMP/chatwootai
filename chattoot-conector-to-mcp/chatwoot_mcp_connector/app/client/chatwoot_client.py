"""
Cliente para comunicação com o Chatwoot.
Envia mensagens e atualiza conversas.
"""

import json
import requests
import logging
from flask import current_app
from app.utils.logger import get_logger

# Configuração do logger
logger = get_logger(__name__)

class ChatwootClient:
    """
    Cliente para comunicação com o Chatwoot.
    """
    
    def __init__(self, api_url=None, api_access_token=None):
        """
        Inicializa o cliente Chatwoot.
        
        Args:
            api_url: URL base da API do Chatwoot
            api_access_token: Token de acesso para autenticação
        """
        self.api_url = api_url or current_app.config.get('CHATWOOT_API_URL')
        self.api_access_token = api_access_token or current_app.config.get('CHATWOOT_API_ACCESS_TOKEN')
        
        if not self.api_url:
            logger.warning("URL da API do Chatwoot não configurada")
        
        if not self.api_access_token:
            logger.warning("Token de acesso do Chatwoot não configurado")
    
    def send_message(self, conversation_id, content, message_type='outgoing', content_type='text', content_attributes=None):
        """
        Envia uma mensagem para uma conversa no Chatwoot.
        
        Args:
            conversation_id: ID da conversa
            content: Conteúdo da mensagem
            message_type: Tipo da mensagem (outgoing, template)
            content_type: Tipo do conteúdo (text, input_select, cards, form)
            content_attributes: Atributos adicionais do conteúdo
            
        Returns:
            Boolean indicando sucesso ou falha
        """
        if not self.api_url or not self.api_access_token:
            logger.error("Cliente Chatwoot não configurado corretamente")
            return False
        
        try:
            # Prepara os headers
            headers = {
                'api_access_token': self.api_access_token,
                'Content-Type': 'application/json'
            }
            
            # Prepara o endpoint
            endpoint = f"{self.api_url}/api/v1/accounts/1/conversations/{conversation_id}/messages"
            
            # Prepara o payload
            data = {
                'content': content,
                'message_type': message_type,
                'content_type': content_type
            }
            
            # Adiciona atributos de conteúdo se fornecidos
            if content_attributes:
                data['content_attributes'] = content_attributes
            
            # Envia a requisição
            response = requests.post(
                endpoint,
                headers=headers,
                json=data,
                timeout=10
            )
            
            # Verifica o status da resposta
            if response.status_code in [200, 201]:
                logger.info(f"Mensagem enviada com sucesso para conversa {conversation_id}")
                return True
            else:
                logger.error(f"Erro ao enviar mensagem para Chatwoot: {response.status_code} - {response.text}")
                return False
        
        except Exception as e:
            logger.error(f"Erro ao comunicar com Chatwoot: {str(e)}")
            return False
    
    def update_conversation_status(self, conversation_id, status):
        """
        Atualiza o status de uma conversa no Chatwoot.
        
        Args:
            conversation_id: ID da conversa
            status: Novo status (open, resolved, pending)
            
        Returns:
            Boolean indicando sucesso ou falha
        """
        if not self.api_url or not self.api_access_token:
            logger.error("Cliente Chatwoot não configurado corretamente")
            return False
        
        try:
            # Prepara os headers
            headers = {
                'api_access_token': self.api_access_token,
                'Content-Type': 'application/json'
            }
            
            # Prepara o endpoint
            endpoint = f"{self.api_url}/api/v1/accounts/1/conversations/{conversation_id}/status"
            
            # Prepara o payload
            data = {
                'status': status
            }
            
            # Envia a requisição
            response = requests.post(
                endpoint,
                headers=headers,
                json=data,
                timeout=10
            )
            
            # Verifica o status da resposta
            if response.status_code == 200:
                logger.info(f"Status da conversa {conversation_id} atualizado para {status}")
                return True
            else:
                logger.error(f"Erro ao atualizar status da conversa: {response.status_code} - {response.text}")
                return False
        
        except Exception as e:
            logger.error(f"Erro ao comunicar com Chatwoot: {str(e)}")
            return False
    
    def get_conversation(self, conversation_id):
        """
        Obtém detalhes de uma conversa no Chatwoot.
        
        Args:
            conversation_id: ID da conversa
            
        Returns:
            Dados da conversa ou None em caso de erro
        """
        if not self.api_url or not self.api_access_token:
            logger.error("Cliente Chatwoot não configurado corretamente")
            return None
        
        try:
            # Prepara os headers
            headers = {
                'api_access_token': self.api_access_token
            }
            
            # Prepara o endpoint
            endpoint = f"{self.api_url}/api/v1/accounts/1/conversations/{conversation_id}"
            
            # Envia a requisição
            response = requests.get(
                endpoint,
                headers=headers,
                timeout=10
            )
            
            # Verifica o status da resposta
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Erro ao obter conversa: {response.status_code} - {response.text}")
                return None
        
        except Exception as e:
            logger.error(f"Erro ao comunicar com Chatwoot: {str(e)}")
            return None
