"""
Módulo de integração com o Odoo.
"""

from .client import OdooClient
from .conversation_context import OdooConversationContextClient

__all__ = ["OdooClient", "OdooConversationContextClient"]
