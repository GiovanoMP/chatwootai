from typing import Dict, Any
from src.core.security import verify_webhook_signature
from src.core.data_proxy_agent import DataProxyAgent
from src.core.exceptions import SecurityViolationError

class WhatsAppHandler:
    def __init__(self, data_proxy: DataProxyAgent):
        self.data_proxy = data_proxy
        self.supported_events = ['message', 'status', 'error']

    async def process_event(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        # Validação de segurança
        if not verify_webhook_signature(payload):
            raise SecurityViolationError("Invalid webhook signature")
        
        event_type = payload.get('event')
        
        if event_type == 'message':
            return await self._process_message(payload)
        elif event_type == 'status':
            return await self._process_status(payload)
        else:
            return {'status': 'ignored', 'event_type': event_type}

    async def _process_message(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        # TODO: Implementar lógica de roteamento para os agentes
        return {'status': 'received', 'message_id': payload.get('id')}
