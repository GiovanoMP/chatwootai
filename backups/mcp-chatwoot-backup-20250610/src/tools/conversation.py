"""
Ferramentas MCP para gerenciamento de conversas no Chatwoot.
"""
import httpx
from typing import Dict, Any, List, Optional
from fastmcp.tools import FunctionTool
from ..common.config import CHATWOOT_BASE_URL, CHATWOOT_ACCESS_TOKEN

async def get_conversation(account_id: int, conversation_id: int) -> Dict[str, Any]:
    """
    Obtém detalhes de uma conversa específica no Chatwoot.

    Args:
        account_id: ID da conta (tenant) no Chatwoot
        conversation_id: ID da conversa no Chatwoot

    Returns:
        Detalhes da conversa incluindo mensagens
    """
    url = f"{CHATWOOT_BASE_URL}/api/v1/accounts/{account_id}/conversations/{conversation_id}/messages"
    headers = {
        "api_access_token": CHATWOOT_ACCESS_TOKEN,
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            return {
                "error": f"Erro ao obter conversa: {response.status_code}",
                "details": response.text
            }

# Criando a ferramenta MCP usando FunctionTool
get_conversation_tool = FunctionTool.from_function(
    fn=get_conversation,
    name="chatwoot-get-conversation",
    description="Obtém detalhes de uma conversa específica no Chatwoot"
)

async def reply_to_conversation(account_id: int, conversation_id: int, content: str, message_type: str = "outgoing") -> Dict[str, Any]:
    """
    Envia uma resposta para uma conversa no Chatwoot.

    Args:
        account_id: ID da conta (tenant) no Chatwoot
        conversation_id: ID da conversa no Chatwoot
        content: Conteúdo da mensagem a ser enviada
        message_type: Tipo de mensagem (outgoing ou template)

    Returns:
        Resultado da operação de envio
    """
    url = f"{CHATWOOT_BASE_URL}/api/v1/accounts/{account_id}/conversations/{conversation_id}/messages"
    headers = {
        "api_access_token": CHATWOOT_ACCESS_TOKEN,
        "Content-Type": "application/json"
    }
    data = {
        "content": content,
        "message_type": message_type
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=data)
        if response.status_code in [200, 201]:
            return response.json()
        else:
            return {
                "error": f"Erro ao enviar resposta: {response.status_code}",
                "details": response.text
            }

# Criando a ferramenta MCP usando FunctionTool
reply_to_conversation_tool = FunctionTool.from_function(
    fn=reply_to_conversation,
    name="chatwoot-reply",
    description="Envia uma resposta para uma conversa no Chatwoot"
)

async def list_conversations(account_id: int, inbox_id: int, status: str = "open") -> Dict[str, Any]:
    """
    Lista conversas de uma caixa de entrada específica no Chatwoot.
    
    Args:
        account_id: ID da conta (tenant) no Chatwoot
        inbox_id: ID da caixa de entrada no Chatwoot
        status: Status das conversas (open, resolved, pending)
        
    Returns:
        Lista de conversas
    """
    url = f"{CHATWOOT_BASE_URL}/api/v1/accounts/{account_id}/conversations"
    headers = {
        "api_access_token": CHATWOOT_ACCESS_TOKEN,
        "Content-Type": "application/json"
    }
    params = {
        "inbox_id": inbox_id,
        "status": status
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            return {
                "error": f"Erro ao listar conversas: {response.status_code}",
                "details": response.text
            }

# Criando a ferramenta MCP usando FunctionTool
list_conversations_tool = FunctionTool.from_function(
    fn=list_conversations,
    name="chatwoot-list-conversations",
    description="Lista conversas de uma caixa de entrada específica no Chatwoot"
)
