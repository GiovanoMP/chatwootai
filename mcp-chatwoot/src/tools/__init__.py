"""
Inicialização das ferramentas MCP para o MCP-Chatwoot.
"""
from .conversation import get_conversation_tool, reply_to_conversation_tool, list_conversations_tool
from .contact import create_contact_tool, get_contact_tool, search_contacts_tool
from .inbox import list_inboxes_tool, get_inbox_tool, create_conversation_tool

# Lista de todas as ferramentas disponíveis
tools = [
    get_conversation_tool,
    reply_to_conversation_tool,
    list_conversations_tool,
    create_contact_tool,
    get_contact_tool,
    search_contacts_tool,
    list_inboxes_tool,
    get_inbox_tool,
    create_conversation_tool
]

__all__ = [
    'get_conversation_tool',
    'reply_to_conversation_tool',
    'list_conversations_tool',
    'create_contact_tool',
    'get_contact_tool',
    'search_contacts_tool',
    'list_inboxes_tool',
    'get_inbox_tool',
    'create_conversation_tool',
    'tools'
]
