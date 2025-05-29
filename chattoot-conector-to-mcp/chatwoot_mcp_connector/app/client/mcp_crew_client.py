"""
Cliente para comunicação com o MCP-Crew.
Envia mensagens para análise e roteamento.
"""

import json
import requests
import logging
from flask import current_app
from app.utils.logger import get_logger

# Configuração do logger
logger = get_logger(__name__)

class MCPCrewClient:
    """
    Cliente para comunicação com o MCP-Crew.
    """
    
    def __init__(self, api_url=None, api_key=None, decision_engine_url=None):
        """
        Inicializa o cliente MCP-Crew.
        
        Args:
            api_url: URL base da API do MCP-Crew
            api_key: Chave de API para autenticação
            decision_engine_url: URL do motor de decisão
        """
        self.api_url = api_url or current_app.config.get('MCP_CREW_API_URL')
        self.api_key = api_key or current_app.config.get('MCP_CREW_API_KEY')
        self.decision_engine_url = decision_engine_url or current_app.config.get('MCP_CREW_DECISION_ENGINE_URL')
        
        if not self.api_url:
            logger.warning("URL da API do MCP-Crew não configurada")
        
        if not self.api_key:
            logger.warning("Chave de API do MCP-Crew não configurada")
    
    def send_message(self, payload):
        """
        Envia uma mensagem para o MCP-Crew.
        
        Args:
            payload: Dados da mensagem a ser enviada
            
        Returns:
            Resposta do MCP-Crew ou None em caso de erro
        """
        if not self.api_url or not self.api_key:
            logger.error("Cliente MCP-Crew não configurado corretamente")
            return None
        
        try:
            # Prepara os headers
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            # Prepara o endpoint
            endpoint = f"{self.api_url}/api"
            
            # Prepara o payload
            data = {
                'action': 'process_message',
                'data': payload
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
                return response.json()
            else:
                logger.error(f"Erro ao enviar mensagem para MCP-Crew: {response.status_code} - {response.text}")
                return None
        
        except Exception as e:
            logger.error(f"Erro ao comunicar com MCP-Crew: {str(e)}")
            return None
    
    def get_decision(self, message, context):
        """
        Obtém uma decisão do motor de decisão do MCP-Crew.
        
        Args:
            message: Texto da mensagem
            context: Contexto da conversa
            
        Returns:
            Decisão do motor ou None em caso de erro
        """
        if not self.decision_engine_url or not self.api_key:
            logger.error("Motor de decisão do MCP-Crew não configurado corretamente")
            return None
        
        try:
            # Prepara os headers
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            # Prepara o endpoint
            endpoint = f"{self.decision_engine_url}/api"
            
            # Prepara o payload
            data = {
                'action': 'decision_route_message',
                'message': message,
                'context': context
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
                return response.json()
            else:
                logger.error(f"Erro ao obter decisão do MCP-Crew: {response.status_code} - {response.text}")
                return None
        
        except Exception as e:
            logger.error(f"Erro ao comunicar com motor de decisão do MCP-Crew: {str(e)}")
            return None
