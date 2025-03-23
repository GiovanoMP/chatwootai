"""
Clientes para API do Chatwoot.

Este pacote contém os clientes para interagir com a API do Chatwoot,
permitindo enviar mensagens e gerenciar conversas.
"""

from .client import ChatwootClient
from .client import ChatwootWebhookHandler

__all__ = ["ChatwootClient", "ChatwootWebhookHandler"]
