"""
Ferramentas MCP para gerenciamento de contatos no Chatwoot.
"""
import httpx
from typing import Dict, Any, List, Optional
from fastmcp.tools import FunctionTool
from ..common.config import CHATWOOT_BASE_URL, CHATWOOT_ACCESS_TOKEN

async def create_contact(
    account_id: int, 
    inbox_id: int, 
    name: str,
    email: Optional[str] = None,
    phone_number: Optional[str] = None
) -> Dict[str, Any]:
    """
    Cria um novo contato no Chatwoot.
    
    Args:
        account_id: ID da conta (tenant) no Chatwoot
        inbox_id: ID da caixa de entrada no Chatwoot
        name: Nome do contato
        email: Email do contato
        phone_number: Número de telefone do contato
        
    Returns:
        Detalhes do contato criado
    """
    url = f"{CHATWOOT_BASE_URL}/api/v1/accounts/{account_id}/contacts"
    headers = {
        "api_access_token": CHATWOOT_ACCESS_TOKEN,
        "Content-Type": "application/json"
    }
    payload = {
        "inbox_id": inbox_id,
        "name": name
    }
    
    if email:
        payload["email"] = email
    if phone_number:
        payload["phone_number"] = phone_number
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload)
        if response.status_code in [200, 201]:
            return response.json()
        else:
            return {
                "error": f"Erro ao criar contato: {response.status_code}",
                "details": response.text
            }

# Criando a ferramenta MCP usando FunctionTool
create_contact_tool = FunctionTool.from_function(
    fn=create_contact,
    name="chatwoot-create-contact",
    description="Cria um novo contato no Chatwoot"
)

async def get_contact(account_id: int, contact_id: int) -> Dict[str, Any]:
    """
    Obtém detalhes de um contato específico no Chatwoot.
    
    Args:
        account_id: ID da conta (tenant) no Chatwoot
        contact_id: ID do contato no Chatwoot
        
    Returns:
        Detalhes do contato
    """
    url = f"{CHATWOOT_BASE_URL}/api/v1/accounts/{account_id}/contacts/{contact_id}"
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
                "error": f"Erro ao obter contato: {response.status_code}",
                "details": response.text
            }

# Criando a ferramenta MCP usando FunctionTool
get_contact_tool = FunctionTool.from_function(
    fn=get_contact,
    name="chatwoot-get-contact",
    description="Obtém detalhes de um contato específico no Chatwoot"
)

async def search_contacts(account_id: int, query: str) -> Dict[str, Any]:
    """
    Pesquisa contatos no Chatwoot.
    
    Args:
        account_id: ID da conta (tenant) no Chatwoot
        query: Termo de pesquisa (nome, email ou telefone)
        
    Returns:
        Lista de contatos encontrados
    """
    url = f"{CHATWOOT_BASE_URL}/api/v1/accounts/{account_id}/contacts/search"
    headers = {
        "api_access_token": CHATWOOT_ACCESS_TOKEN,
        "Content-Type": "application/json"
    }
    params = {
        "q": query
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            return {
                "error": f"Erro ao pesquisar contatos: {response.status_code}",
                "details": response.text
            }

# Criando a ferramenta MCP usando FunctionTool
search_contacts_tool = FunctionTool.from_function(
    fn=search_contacts,
    name="chatwoot-search-contacts",
    description="Pesquisa contatos no Chatwoot"
)
