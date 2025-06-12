from typing import Optional, Dict, Any
from pydantic import BaseModel

class WebhookPayload(BaseModel):
    """Modelo para payload de webhook do Chatwoot."""
    account_id: int
    inbox_id: int
    event: str
    data: Dict[str, Any]

class TenantConfig(BaseModel):
    """Configurações específicas por tenant."""
    account_id: int
    is_active: bool = True
    allowed_inboxes: list[int] = []
    meta: Dict[str, Any] = {}

class MessageResponse(BaseModel):
    """Resposta para mensagens processadas."""
    success: bool
    message: str
    error: Optional[str] = None
