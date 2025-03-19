"""
Chatwoot API client for the hub-and-spoke architecture.

This module implements a client for interacting with the Chatwoot API,
allowing the system to fetch conversations and send messages.
"""

import logging
import requests
from typing import Dict, List, Any, Optional, Union

logger = logging.getLogger(__name__)


class ChatwootClient:
    """Client for interacting with the Chatwoot API."""
    
    def __init__(self, base_url: str, api_key: str):
        """
        Initialize the Chatwoot API client.
        
        Args:
            base_url: Base URL of the Chatwoot API
            api_key: API key for authentication
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.headers = {
            'Content-Type': 'application/json',
            'api_access_token': api_key
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
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self.headers,
                params=params,
                json=data
            )
            
            response.raise_for_status()
            
            if response.content:
                return response.json()
            return {}
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Error making request to Chatwoot API: {e}")
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
    
    def send_message(self, account_id: int, conversation_id: int, 
                     content: str, message_type: str = 'outgoing',
                     private: bool = False) -> Dict[str, Any]:
        """
        Send a message to a conversation.
        
        Args:
            account_id: ID of the account
            conversation_id: ID of the conversation
            content: Message content
            message_type: Type of message ('outgoing' or 'template')
            private: Whether the message is private
            
        Returns:
            Response data
        """
        endpoint = f"accounts/{account_id}/conversations/{conversation_id}/messages"
        
        data = {
            'content': content,
            'message_type': message_type,
            'private': private
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
        try:
            event_type = data.get('event')
            
            if event_type == 'message_created':
                return self._handle_message_created(data)
            
            elif event_type == 'conversation_created':
                return self._handle_conversation_created(data)
            
            elif event_type == 'conversation_status_changed':
                return self._handle_conversation_status_changed(data)
            
            else:
                logger.info(f"Unhandled webhook event: {event_type}")
                return {"status": "ignored", "event": event_type}
        
        except Exception as e:
            logger.error(f"Error handling webhook: {e}")
            return {"error": str(e)}
    
    def _handle_message_created(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a message_created webhook.
        
        Args:
            data: Webhook data
            
        Returns:
            Response data
        """
        try:
            message = data.get('message', {})
            conversation = data.get('conversation', {})
            
            # Only process incoming messages from contacts
            if message.get('message_type') != 'incoming':
                return {"status": "ignored", "reason": "not an incoming message"}
            
            # Extract relevant data
            account_id = data.get('account', {}).get('id')
            conversation_id = str(conversation.get('id', ''))
            contact = data.get('contact', {})
            inbox = data.get('inbox', {})
            
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
