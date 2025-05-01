"""
Chatwoot API client for the hub-and-spoke architecture.

This module implements a client for interacting with the Chatwoot API,
allowing the system to fetch conversations and send messages.
"""

import logging
import json
import requests
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Union

# Verifica se o módulo debug_logger está disponível
try:
    from src.utils.debug_logger import get_logger, log_function_call, TRACE
    logger = get_logger('chatwoot_client', level=logging.DEBUG)
except ImportError:
    # Fallback para logging padrão
    logger = logging.getLogger(__name__)


class ChatwootClient:
    """Client for interacting with the Chatwoot API."""

    def __init__(self, base_url: str, api_token: str):
        """
        Initialize the Chatwoot API client.

        Args:
            base_url: Base URL of the Chatwoot API
            api_token: API token for authentication
        """
        self.base_url = base_url.rstrip('/')
        self.headers = {
            'api_access_token': api_token,
            'Content-Type': 'application/json'
        }

    def _make_request(self, method: str, endpoint: str,
                      params: Optional[Dict[str, Any]] = None,
                      data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make a request to the Chatwoot API.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint
            params: Query parameters
            data: Request body

        Returns:
            Response data
        """
        # Remover qualquer prefixo 'api/v1' ou '/api/v1' para evitar duplicação
        if endpoint.startswith('api/v1/'):
            endpoint = endpoint[7:]  # Remove 'api/v1/'
        elif endpoint.startswith('/api/v1/'):
            endpoint = endpoint[8:]  # Remove '/api/v1/'

        # Construir a URL completa com o prefixo api/v1
        url = f"{self.base_url}/api/v1/{endpoint.lstrip('/')}"

        # Verificar se não há duplicação de api/v1 na URL
        if '/api/v1/api/v1/' in url:
            url = url.replace('/api/v1/api/v1/', '/api/v1/')
            logger.warning(f"Detectada duplicação de api/v1 na URL. URL corrigida: {url}")

        logger.info(f"Making {method} request to: {url}")
        if data:
            logger.info(f"Request data: {data}")

        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self.headers,
                params=params,
                json=data
            )

            logger.info(f"Response status: {response.status_code}")

            # Se receber erro 401, pode ser problema com o token
            if response.status_code == 401:
                logger.error("Erro de autenticação. Verifique se o token de API está correto e não expirou.")

            response.raise_for_status()

            if response.content:
                return response.json()
            return {}

        except requests.exceptions.RequestException as e:
            logger.error(f"Error making request to Chatwoot API: {e}")
            logger.error(f"URL: {url}")
            logger.error(f"Headers: {self.headers}")
            logger.error(f"Data: {data}")
            return {"error": str(e)}

    def get_account_details(self, account_id: int) -> Dict[str, Any]:
        """
        Get details of a Chatwoot account.

        Args:
            account_id: ID of the account

        Returns:
            Account details
        """
        endpoint = f"accounts/{account_id}"
        return self._make_request("GET", endpoint)

    def get_conversations(self, account_id: int, inbox_id: Optional[int] = None,
                          status: Optional[str] = None, assignee_type: Optional[str] = None,
                          page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """
        Get conversations from a Chatwoot account.

        Args:
            account_id: ID of the account
            inbox_id: ID of the inbox to filter by
            status: Status to filter by ('open', 'resolved', 'pending')
            assignee_type: Assignee type to filter by ('me', 'unassigned', 'all')
            page: Page number
            page_size: Number of conversations per page

        Returns:
            List of conversations
        """
        endpoint = f"accounts/{account_id}/conversations"

        params = {
            'page': page,
            'page_size': page_size
        }

        if inbox_id:
            params['inbox_id'] = inbox_id

        if status:
            params['status'] = status

        if assignee_type:
            params['assignee_type'] = assignee_type

        return self._make_request("GET", endpoint, params=params)

    def get_conversation(self, account_id: int, conversation_id: int) -> Dict[str, Any]:
        """
        Get details of a specific conversation.

        Args:
            account_id: ID of the account
            conversation_id: ID of the conversation

        Returns:
            Conversation details
        """
        endpoint = f"accounts/{account_id}/conversations/{conversation_id}"
        return self._make_request("GET", endpoint)

    def get_messages(self, account_id: int, conversation_id: int) -> List[Dict[str, Any]]:
        """
        Get messages from a conversation.

        Args:
            account_id: ID of the account
            conversation_id: ID of the conversation

        Returns:
            List of messages
        """
        endpoint = f"accounts/{account_id}/conversations/{conversation_id}/messages"
        response = self._make_request("GET", endpoint)
        return response.get('payload', [])

    def send_message(self, conversation_id: int, message: str, account_id: int = 1):
        """
        Send a message to a conversation.

        Args:
            conversation_id: ID of the conversation
            message: Message content
            account_id: ID of the account (default: 1)

        Returns:
            Response data
        """
        # Usar o formato correto da URL com account_id
        endpoint = f"accounts/{account_id}/conversations/{conversation_id}/messages"

        data = {
            'content': message,
            'message_type': 'outgoing'
        }

        return self._make_request("POST", endpoint, data=data)

    def update_conversation(self, account_id: int, conversation_id: int,
                           status: Optional[str] = None,
                           assignee_id: Optional[int] = None,
                           team_id: Optional[int] = None,
                           labels: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Update a conversation.

        Args:
            account_id: ID of the account
            conversation_id: ID of the conversation
            status: New status ('open', 'resolved', 'pending')
            assignee_id: ID of the assignee
            team_id: ID of the team
            labels: List of labels

        Returns:
            Response data
        """
        endpoint = f"accounts/{account_id}/conversations/{conversation_id}"

        data = {}

        if status:
            data['status'] = status

        if assignee_id is not None:
            data['assignee_id'] = assignee_id

        if team_id is not None:
            data['team_id'] = team_id

        if labels:
            data['labels'] = labels

        return self._make_request("PATCH", endpoint, data=data)

    def get_contact(self, account_id: int, contact_id: int) -> Dict[str, Any]:
        """
        Get details of a contact.

        Args:
            account_id: ID of the account
            contact_id: ID of the contact

        Returns:
            Contact details
        """
        endpoint = f"accounts/{account_id}/contacts/{contact_id}"
        return self._make_request("GET", endpoint)

    def create_contact(self, account_id: int, name: str, email: Optional[str] = None,
                      phone_number: Optional[str] = None,
                      custom_attributes: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a new contact.

        Args:
            account_id: ID of the account
            name: Name of the contact
            email: Email of the contact
            phone_number: Phone number of the contact
            custom_attributes: Custom attributes for the contact

        Returns:
            Response data
        """
        endpoint = f"accounts/{account_id}/contacts"

        data = {
            'name': name
        }

        if email:
            data['email'] = email

        if phone_number:
            data['phone_number'] = phone_number

        if custom_attributes:
            data['custom_attributes'] = custom_attributes

        return self._make_request("POST", endpoint, data=data)

    def update_contact(self, account_id: int, contact_id: int,
                      name: Optional[str] = None,
                      email: Optional[str] = None,
                      phone_number: Optional[str] = None,
                      custom_attributes: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Update a contact.

        Args:
            account_id: ID of the account
            contact_id: ID of the contact
            name: New name of the contact
            email: New email of the contact
            phone_number: New phone number of the contact
            custom_attributes: New custom attributes for the contact

        Returns:
            Response data
        """
        endpoint = f"accounts/{account_id}/contacts/{contact_id}"

        data = {}

        if name:
            data['name'] = name

        if email:
            data['email'] = email

        if phone_number:
            data['phone_number'] = phone_number

        if custom_attributes:
            data['custom_attributes'] = custom_attributes

        return self._make_request("PATCH", endpoint, data=data)

    def get_inboxes(self, account_id: int) -> List[Dict[str, Any]]:
        """
        Get inboxes from a Chatwoot account.

        Args:
            account_id: ID of the account

        Returns:
            List of inboxes
        """
        endpoint = f"accounts/{account_id}/inboxes"
        response = self._make_request("GET", endpoint)
        return response.get('payload', [])

    def get_inbox(self, account_id: int, inbox_id: int) -> Dict[str, Any]:
        """
        Get details of a specific inbox.

        Args:
            account_id: ID of the account
            inbox_id: ID of the inbox

        Returns:
            Inbox details
        """
        endpoint = f"accounts/{account_id}/inboxes/{inbox_id}"
        return self._make_request("GET", endpoint)

    def get_agents(self, account_id: int) -> List[Dict[str, Any]]:
        """
        Get agents from a Chatwoot account.

        Args:
            account_id: ID of the account

        Returns:
            List of agents
        """
        endpoint = f"accounts/{account_id}/agents"
        response = self._make_request("GET", endpoint)
        return response.get('payload', [])

    def get_teams(self, account_id: int) -> List[Dict[str, Any]]:
        """
        Get teams from a Chatwoot account.

        Args:
            account_id: ID of the account

        Returns:
            List of teams
        """
        endpoint = f"accounts/{account_id}/teams"
        response = self._make_request("GET", endpoint)
        return response.get('payload', [])

    def get_canned_responses(self, account_id: int) -> List[Dict[str, Any]]:
        """
        Get canned responses from a Chatwoot account.

        Args:
            account_id: ID of the account

        Returns:
            List of canned responses
        """
        endpoint = f"accounts/{account_id}/canned_responses"
        response = self._make_request("GET", endpoint)
        return response.get('payload', [])

    def check_connection(self, account_id: int = 1) -> bool:
        """
        Check if the connection to Chatwoot API is working.

        Args:
            account_id: ID of the account to check

        Returns:
            bool: True if connection is successful, False otherwise
        """
        try:
            # Tentar obter detalhes da conta para verificar a conexão
            endpoint = f"accounts/{account_id}/inboxes"
            response = self._make_request("GET", endpoint)

            # Se não houver erro, a conexão está funcionando
            if "error" not in response:
                logger.info("✅ Conexão com Chatwoot API verificada com sucesso")
                return True

            logger.error(f"❌ Erro ao verificar conexão com Chatwoot API: {response.get('error')}")
            return False
        except Exception as e:
            logger.error(f"❌ Erro ao verificar conexão com Chatwoot API: {str(e)}")
            return False


class ChatwootWebhookHandler:
    """Handler for Chatwoot webhooks."""

    def __init__(self, hub_crew, crew_registry=None):
        """
        Initialize the webhook handler.

        Args:
            hub_crew: The hub crew for processing messages
            crew_registry: Registry of crews for different channels
        """
        self.hub_crew = hub_crew
        self.crew_registry = crew_registry

    def handle_webhook(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a webhook from Chatwoot.

        Args:
            data: Webhook data

        Returns:
            Response data
        """
        start_time = time.time()
        try:
            event_type = data.get('event')
            logger.info(f"Processando webhook do tipo: {event_type}")

            # Registra timestamp para análise de latência
            processing_timestamp = datetime.now().isoformat()

            result = None
            if event_type == 'message_created':
                logger.debug(f"Encaminhando para handler de message_created")
                result = self._handle_message_created(data)

            elif event_type == 'conversation_created':
                logger.debug(f"Encaminhando para handler de conversation_created")
                result = self._handle_conversation_created(data)

            elif event_type == 'conversation_status_changed':
                logger.debug(f"Encaminhando para handler de conversation_status_changed")
                result = self._handle_conversation_status_changed(data)

            else:
                logger.info(f"Tipo de evento não tratado: {event_type}")
                result = {"status": "ignored", "event": event_type}

            # Calcula e registra o tempo de processamento
            processing_time = time.time() - start_time
            logger.info(f"Webhook {event_type} processado em {processing_time:.3f}s")

            # Adiciona informações de performance à resposta
            if isinstance(result, dict):
                result["processing_time"] = f"{processing_time:.3f}s"
                result["timestamp"] = processing_timestamp

            return result

        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Erro ao processar webhook: {str(e)}")

            # Log mais detalhado do erro
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")

            return {
                "error": str(e),
                "error_type": type(e).__name__,
                "processing_time": f"{processing_time:.3f}s"
            }

    def _handle_message_created(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a message_created webhook.

        Args:
            data: Webhook data

        Returns:
            Response data
        """
        start_time = time.time()
        try:
            # Log detalhado dos dados da mensagem
            logger.debug(f"Dados completos do webhook message_created: {json.dumps(data, indent=2, ensure_ascii=False)}")

            message = data.get('message', {})
            conversation = data.get('conversation', {})

            # Verifica o tipo de mensagem
            message_type = message.get('message_type')
            logger.debug(f"Tipo de mensagem recebida: {message_type}")

            # Only process incoming messages from contacts
            if message_type != 'incoming':
                logger.info(f"Ignorando mensagem do tipo {message_type} (apenas mensagens 'incoming' são processadas)")
                return {"status": "ignored", "reason": f"not an incoming message (type: {message_type})"}

            # Extract relevant data
            account_id = data.get('account', {}).get('id')
            conversation_id = str(conversation.get('id', ''))
            contact = data.get('contact', {})
            inbox = data.get('inbox', {})

            logger.debug(f"Processando mensagem da conta {account_id}, conversa {conversation_id}")

            # Determine the channel type
            channel_type = inbox.get('channel_type', 'api')

            # Enrich the message with additional metadata for better processing
            enriched_message = {
                "content": message.get('content', ''),
                "created_at": message.get('created_at'),
                "id": message.get('id'),
                "conversation_id": conversation_id,
                "customer_id": contact.get('id'),
                "channel_type": channel_type,
                "account_id": account_id,
                "inbox_id": inbox.get('id'),
                "contact": {
                    "id": contact.get('id'),
                    "name": contact.get('name', ''),
                    "email": contact.get('email', ''),
                    "phone": contact.get('phone_number', '')
                },
                # Incluir o objeto original para processamento avançado se necessário
                "raw_message": message
            }

            # Process the message through the appropriate channel crew
            # Este é um passo importante - recuperamos a crew específica do canal
            channel_crew = self._get_channel_crew(channel_type)

            if not channel_crew:
                logger.error(f"No crew found for channel type: {channel_type}")
                return {
                    "status": "error",
                    "reason": f"no crew registered for channel type {channel_type}",
                    "channel_type": channel_type
                }

            # Processa a mensagem usando o método process_message do ChannelCrew
            # Isso delegará a chamada ao HubCrew internamente na implementação do canal
            response = channel_crew.process_message(enriched_message, conversation_id)

            logger.info(f"Message processed successfully for conversation {conversation_id}")

            return {
                "status": "processed",
                "channel_type": channel_type,
                "conversation_id": conversation_id,
                "response": response
            }

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    def _handle_conversation_created(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a conversation_created webhook.

        Args:
            data: Webhook data

        Returns:
            Response data
        """
        # This is a placeholder - in the actual implementation, we might
        # want to do something when a new conversation is created
        return {"status": "acknowledged", "event": "conversation_created"}

    def _handle_conversation_status_changed(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a conversation_status_changed webhook.

        Args:
            data: Webhook data

        Returns:
            Response data
        """
        # This is a placeholder - in the actual implementation, we might
        # want to do something when a conversation's status changes
        return {"status": "acknowledged", "event": "conversation_status_changed"}

    def _get_channel_crew(self, channel_type: str):
        """
        Get the appropriate channel crew for a channel type.

        Args:
            channel_type: Type of channel

        Returns:
            Channel crew or None if not found
        """
        # Se crew_registry não foi fornecido, importa o módulo
        if self.crew_registry is None:
            from src.core.crew_registry import CrewRegistry
            self.crew_registry = CrewRegistry()

        # Map of channel types to their normalized names
        channel_map = {
            'api': 'api',
            'web_widget': 'web',
            'whatsapp': 'whatsapp',
            'facebook': 'facebook',
            'twitter': 'twitter',
            'telegram': 'telegram',
            'line': 'line',
            'sms': 'sms',
            'email': 'email',
            'instagram': 'instagram'
        }

        normalized_type = channel_map.get(channel_type, channel_type)

        # Obter a crew do registro fornecido
        crew = self.crew_registry.get_crew(normalized_type)

        if crew is None:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Nenhuma crew registrada para o canal '{normalized_type}'. Verifique se a crew foi registrada durante a inicialização.")

        return crew
