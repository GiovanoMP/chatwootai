import hmac
import hashlib
import requests
import aiohttp
from typing import Dict, Any, Optional, Union, Tuple, List, Bool
from common.config import (
    CHATWOOT_BASE_URL, 
    CHATWOOT_ACCESS_TOKEN,
    CHATWOOT_HMAC_KEY,
    CHATWOOT_INBOX_IDENTIFIER
)

class ChatwootClient:
    def __init__(self, 
                 base_url: str = CHATWOOT_BASE_URL, 
                 access_token: str = CHATWOOT_ACCESS_TOKEN,
                 hmac_key: str = CHATWOOT_HMAC_KEY,
                 inbox_identifier: str = CHATWOOT_INBOX_IDENTIFIER):
        self.base_url = base_url.rstrip('/')
        self.access_token = access_token
        self.hmac_key = hmac_key
        self.inbox_identifier = inbox_identifier
        self.headers = {
            'api_access_token': access_token,
            'Content-Type': 'application/json'
        }

    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """Verifica a assinatura HMAC do webhook."""
        if not self.hmac_key or not signature:
            return False

        expected = hmac.new(
            self.hmac_key.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(expected, signature)
        
    async def check_connection(self) -> bool:
        """Verifica a conexão com o Chatwoot."""
        try:
            # Verifica se consegue acessar a API do Chatwoot
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/api/v1/platform/status"
                async with session.get(url) as response:
                    return response.status == 200
        except Exception:
            return False

    def create_contact(self, account_id: int, name: str, identifier: str) -> Optional[Dict[str, Any]]:
        """Cria ou obtém um contato existente."""
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/accounts/{account_id}/contacts",
                headers=self.headers,
                json={
                    'name': name,
                    'identifier': identifier,
                }
            )
            if response.status_code in (200, 201):
                return response.json()
            return None
        except Exception:
            return None

    def create_conversation(self, account_id: int, contact_id: int, source_id: str) -> Optional[Dict[str, Any]]:
        """Cria uma nova conversa para um contato."""
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/accounts/{account_id}/conversations",
                headers=self.headers,
                json={
                    'contact_id': contact_id,
                    'inbox_id': self.inbox_identifier,
                    'source_id': source_id,
                }
            )
            if response.status_code in (200, 201):
                return response.json()
            return None
        except Exception:
            return None

    def send_message(self, account_id: int, conversation_id: int, message: str, message_type: str = 'outgoing') -> bool:
        """Envia uma mensagem para uma conversa."""
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/accounts/{account_id}/conversations/{conversation_id}/messages",
                headers=self.headers,
                json={
                    'content': message,
                    'message_type': message_type,
                }
            )
            return response.status_code in (200, 201)
        except Exception:
            return False
