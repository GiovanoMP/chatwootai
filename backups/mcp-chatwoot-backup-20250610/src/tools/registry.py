"""
Registro e utilitários para ferramentas MCP.
Este módulo fornece funções para registrar, listar e formatar ferramentas MCP.
"""
import inspect
from typing import Dict, List, Any, Callable, Optional
import logging

logger = logging.getLogger("mcp-chatwoot.tools")

def get_tool_parameters(tool_func: Callable) -> Dict[str, Dict[str, Any]]:
    """
    Extrai os parâmetros de uma função de ferramenta.
    
    Args:
        tool_func: Função da ferramenta
        
    Returns:
        Dicionário com informações sobre os parâmetros
    """
    parameters = {}
    sig = inspect.signature(tool_func)
    
    for param_name, param in sig.parameters.items():
        if param_name == 'self':
            continue
            
        param_info = {
            "type": "string",  # Tipo padrão
            "description": "",  # Descrição padrão
        }
        
        # Tentar extrair tipo da anotação
        if param.annotation != inspect.Parameter.empty:
            if param.annotation == int:
                param_info["type"] = "integer"
            elif param.annotation == bool:
                param_info["type"] = "boolean"
            elif param.annotation == float:
                param_info["type"] = "number"
            elif param.annotation == list or param.annotation == List:
                param_info["type"] = "array"
            elif param.annotation == dict or param.annotation == Dict:
                param_info["type"] = "object"
                
        # Valor padrão se disponível
        if param.default != inspect.Parameter.empty:
            param_info["default"] = param.default
            
        parameters[param_name] = param_info
    
    return parameters

def format_tool_info(tool) -> Dict[str, Any]:
    """
    Formata informações de uma ferramenta para o formato MCP.
    
    Args:
        tool: Objeto de ferramenta MCP
        
    Returns:
        Dicionário com informações formatadas da ferramenta
    """
    # Verificar se é uma FunctionTool do fastmcp
    if hasattr(tool, "fn") and callable(tool.fn):
        # É uma FunctionTool
        name = getattr(tool, "name", tool.fn.__name__)
        description = getattr(tool, "description", getattr(tool.fn, "__doc__", ""))
        parameters = get_tool_parameters(tool.fn)
    else:
        # Extrair nome e descrição para outros tipos
        name = getattr(tool, "name", tool.__name__ if callable(tool) else str(tool))
        description = getattr(tool, "description", getattr(tool, "__doc__", ""))
        
        # Extrair parâmetros
        if callable(tool):
            parameters = get_tool_parameters(tool)
        else:
            parameters = getattr(tool, "parameters", {})
    
    # Garantir que o nome não tenha prefixos específicos de implementação
    if name.startswith("chatwoot-"):
        name = name[9:]  # Remover prefixo "chatwoot-"
    
    return {
        "name": name,
        "description": description.strip() if description else "",
        "parameters": parameters
    }

def format_tools_for_api(tools: List[Any]) -> List[Dict[str, Any]]:
    """
    Formata uma lista de ferramentas para o formato da API MCP.
    
    Args:
        tools: Lista de ferramentas MCP
        
    Returns:
        Lista de dicionários com informações formatadas das ferramentas
    """
    return [format_tool_info(tool) for tool in tools]
