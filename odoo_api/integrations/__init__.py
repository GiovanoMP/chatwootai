"""
Integrações com sistemas externos.

Este pacote contém módulos para integração com sistemas externos,
como Chatwoot, WhatsApp, etc.
"""

from .chatwoot import ChatwootClient, ChatwootWebhookHandler

__all__ = ["ChatwootClient", "ChatwootWebhookHandler"]
