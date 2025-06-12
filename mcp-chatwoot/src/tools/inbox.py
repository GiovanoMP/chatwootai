"""
Ferramentas MCP para gerenciamento de inboxes no Chatwoot.
"""
import httpx
from typing import Dict, Any, List, Optional
from fastmcp.tools import FunctionTool
from ..common.config import CHATWOOT_BASE_URL, CHATWOOT_ACCESS_TOKEN

async def list_inboxes(account_id: int) -> Dict[str, Any]:
    """
    Lista todas as caixas de entrada disponíveis para uma conta no Chatwoot.
    
    Args:
        account_id: ID da conta (tenant) no Chatwoot
        
    Returns:
        Lista de caixas de entrada
    """
    url = f"{CHATWOOT_BASE_URL}/api/v1/accounts/{account_id}/inboxes"
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
                "error": f"Erro ao listar inboxes: {response.status_code}",
                "details": response.text
            }

# Criando a ferramenta MCP usando FunctionTool
list_inboxes_tool = FunctionTool.from_function(
    fn=list_inboxes,
    name="chatwoot-list-inboxes",
    description="Lista todas as caixas de entrada disponíveis para uma conta no Chatwoot"
)

async def get_inbox(account_id: int, inbox_id: int) -> Dict[str, Any]:
    """
    Obtém detalhes de uma caixa de entrada específica no Chatwoot.
    
    Args:
        account_id: ID da conta (tenant) no Chatwoot
        inbox_id: ID da caixa de entrada no Chatwoot
        
    Returns:
        Detalhes da caixa de entrada
    """
    url = f"{CHATWOOT_BASE_URL}/api/v1/accounts/{account_id}/inboxes/{inbox_id}"
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
                "error": f"Erro ao obter inbox: {response.status_code}",
                "details": response.text
            }

# Criando a ferramenta MCP usando FunctionTool
get_inbox_tool = FunctionTool.from_function(
    fn=get_inbox,
    name="chatwoot-get-inbox",
    description="Obtém detalhes de uma caixa de entrada específica no Chatwoot"
)

async def create_conversation(
    account_id: int, 
    inbox_id: int, 
    contact_id: int, 
    message: str
) -> Dict[str, Any]:
    """
    Cria uma nova conversa em uma caixa de entrada específica no Chatwoot.
    
    Args:
        account_id: ID da conta (tenant) no Chatwoot
        inbox_id: ID da caixa de entrada no Chatwoot
        contact_id: ID do contato no Chatwoot
        message: Mensagem inicial da conversa
        
    Returns:
        Detalhes da conversa criada
    """
    url = f"{CHATWOOT_BASE_URL}/api/v1/accounts/{account_id}/conversations"
    headers = {
        "api_access_token": CHATWOOT_ACCESS_TOKEN,
        "Content-Type": "application/json"
    }
    payload = {
        "inbox_id": inbox_id,
        "contact_id": contact_id,
        "message": {
            "content": message
        }
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload)
        if response.status_code in [200, 201]:
            return response.json()
        else:
            return {
                "error": f"Erro ao criar conversa: {response.status_code}",
                "details": response.text
            }

# Criando a ferramenta MCP usando FunctionTool
create_conversation_tool = FunctionTool.from_function(
    fn=create_conversation,
    name="chatwoot-create-conversation",
    description="Cria uma nova conversa em uma caixa de entrada específica no Chatwoot"
)
