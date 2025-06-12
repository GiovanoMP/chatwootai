#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ChatwootDynamicAdapter - Um adaptador aprimorado para integrar o MCP-Chatwoot com o CrewAI
que descobre ferramentas dinamicamente, similar ao adaptador MongoDB.

Este adaptador se conecta ao servidor MCP-Chatwoot (FastAPI) e descobre
suas ferramentas dinamicamente para o CrewAI.
"""

import json
import logging
import requests
from typing import List, Dict, Any, Optional, Callable
from crewai.tools.base_tool import Tool

# Configurar logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("chatwoot_dynamic_adapter")

class ChatwootDynamicAdapter:
    """
    Adaptador dinâmico para o servidor MCP-Chatwoot que descobre e expõe ferramentas compatíveis com CrewAI.
    Este adaptador se conecta diretamente ao servidor MCP-Chatwoot via HTTP,
    descobre suas ferramentas dinamicamente e as converte em objetos Tool do CrewAI.
    """
    
    def __init__(self, base_url: str = "http://localhost:8004"):
        """
        Inicializa o adaptador com a URL base do servidor MCP-Chatwoot.
        
        Args:
            base_url: URL base do servidor MCP-Chatwoot (padrão: http://localhost:8004)
        """
        # Remover /sse do final da URL se estiver presente
        if base_url.endswith("/sse"):
            base_url = base_url[:-4]
        
        self.base_url = base_url.rstrip("/")
        self.message_url = f"{self.base_url}/messages/"
        self.sse_url = f"{self.base_url}/sse"
        
        self.session = requests.Session()
        self._tools = None
        self._raw_tools_data = None
        self._verify_server_health()
        
    def _verify_server_health(self) -> None:
        """Verifica se o servidor MCP-Chatwoot está acessível."""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=5)
            response.raise_for_status()
            health_data = response.json()
            logger.info(f"Status do servidor MCP-Chatwoot: {health_data}")
        except Exception as e:
            logger.error(f"Erro ao verificar saúde do servidor: {e}")
            raise ConnectionError(f"Não foi possível conectar ao servidor MCP-Chatwoot em {self.base_url}: {e}")
    
    def _discover_tools(self) -> List[Dict[str, Any]]:
        """
        Descobre as ferramentas disponíveis no servidor MCP-Chatwoot.
        
        Returns:
            Lista de ferramentas disponíveis
        """
        try:
            # Primeiro, tentamos usar o endpoint /tools se ele existir
            try:
                response = self.session.get(f"{self.base_url}/tools", timeout=5)
                if response.status_code == 200:
                    tools_data = response.json()
                    if "tools" in tools_data and isinstance(tools_data["tools"], list):
                        self._raw_tools_data = tools_data["tools"]
                        logger.info(f"Ferramentas descobertas via endpoint /tools: {len(self._raw_tools_data)}")
                        return self._raw_tools_data
            except Exception as e:
                logger.warning(f"Endpoint /tools não disponível: {e}")
            
            # Se não conseguirmos via /tools, tentamos via mensagem initialize JSON-RPC
            jsonrpc_request = {
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {},
                "id": 1
            }
            
            response = self.session.post(self.message_url, json=jsonrpc_request, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            if "result" in result and "capabilities" in result["result"]:
                # Se o servidor suporta ferramentas, tentamos obter a lista
                if result["result"]["capabilities"].get("tools", False):
                    # Agora tentamos obter a lista de ferramentas
                    jsonrpc_request = {
                        "jsonrpc": "2.0",
                        "method": "getTools",
                        "params": {},
                        "id": 2
                    }
                    
                    try:
                        response = self.session.post(self.message_url, json=jsonrpc_request, timeout=10)
                        response.raise_for_status()
                        result = response.json()
                        
                        if "result" in result and "tools" in result["result"]:
                            self._raw_tools_data = result["result"]["tools"]
                            logger.info(f"Ferramentas descobertas via JSON-RPC getTools: {len(self._raw_tools_data)}")
                            return self._raw_tools_data
                    except Exception as e:
                        logger.warning(f"Não foi possível obter lista de ferramentas via getTools: {e}")
            
            # Se não conseguirmos descobrir dinamicamente, usamos a lista padrão
            logger.warning("Usando lista de ferramentas padrão")
            self._raw_tools_data = self._get_default_tools()
            return self._raw_tools_data
            
        except Exception as e:
            logger.error(f"Erro ao descobrir ferramentas: {e}")
            # Fallback para ferramentas padrão
            self._raw_tools_data = self._get_default_tools()
            return self._raw_tools_data
    
    def _call_chatwoot_api(self, tool_name: str, params: Optional[Dict] = None) -> Dict:
        """
        Faz uma chamada à API do MCP-Chatwoot usando o endpoint /messages/ com JSON-RPC.
        
        Args:
            tool_name: Nome da ferramenta/método a ser chamado
            params: Parâmetros para a chamada da ferramenta
            
        Returns:
            Resposta da API como um dicionário
        """
        url = self.message_url
        
        # Criar mensagem JSON-RPC
        jsonrpc_request = {
            "jsonrpc": "2.0",
            "method": tool_name,
            "params": params or {},
            "id": 1
        }
        
        try:
            logger.info(f"Enviando requisição JSON-RPC para {tool_name}: {jsonrpc_request}")
            response = self.session.post(url, json=jsonrpc_request, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Resposta recebida: {result}")
            
            # Verificar se há erro na resposta JSON-RPC
            if "error" in result:
                error = result["error"]
                logger.error(f"Erro JSON-RPC: {error}")
                raise Exception(f"Erro na API: {error.get('message', 'Erro desconhecido')}")
                
            return result.get("result", {})
        except Exception as e:
            logger.error(f"Erro na chamada à API ({url}): {e}")
            raise
    
    def _create_tool_function(self, tool_name: str, parameters: Dict[str, Any]) -> Callable:
        """
        Cria uma função que executa a ferramenta especificada via API REST.
        
        Args:
            tool_name: Nome da ferramenta no MCP-Chatwoot
            parameters: Parâmetros da ferramenta
            
        Returns:
            Função que executa a ferramenta
        """
        def execute_tool(**kwargs):
            try:
                # Executar a ferramenta via API JSON-RPC
                result = self._call_chatwoot_api(tool_name, params=kwargs)
                
                # Formatar o resultado para melhor legibilidade
                if isinstance(result, dict) or isinstance(result, list):
                    return json.dumps(result, indent=2, ensure_ascii=False)
                return str(result)
            except Exception as e:
                return f"Erro ao executar ferramenta {tool_name}: {e}"
        
        return execute_tool
    
    def _build_tools(self) -> List[Tool]:
        """
        Constrói objetos Tool do CrewAI a partir das ferramentas do MCP-Chatwoot.
        
        Returns:
            Lista de objetos Tool do CrewAI
        """
        raw_tools = self._discover_tools()
        tools = []
        
        for tool_data in raw_tools:
            name = tool_data["name"]
            description = tool_data.get("description", "")
            parameters = tool_data.get("parameters", {})
            
            # Criar descrição detalhada incluindo parâmetros
            detailed_description = f"{description}\n\nParâmetros:"
            for param_name, param_info in parameters.items():
                param_type = param_info.get("type", "any")
                param_desc = param_info.get("description", "")
                param_default = param_info.get("default", "não especificado")
                detailed_description += f"\n- {param_name} ({param_type}): {param_desc}"
                if param_default != "não especificado":
                    detailed_description += f" (padrão: {param_default})"
            
            # Criar a ferramenta
            tool = Tool(
                name=name,
                description=detailed_description,
                func=self._create_tool_function(name, parameters)
            )
            tools.append(tool)
        
        return tools
    
    @property
    def tools(self) -> List[Tool]:
        """
        Obtém as ferramentas do MCP-Chatwoot como objetos Tool do CrewAI.
        
        Returns:
            Lista de objetos Tool do CrewAI
        """
        if self._tools is None:
            self._tools = self._build_tools()
        return self._tools
    
    def refresh_tools(self) -> List[Tool]:
        """
        Atualiza a lista de ferramentas do MCP-Chatwoot.
        
        Returns:
            Lista atualizada de objetos Tool do CrewAI
        """
        self._tools = None
        self._raw_tools_data = None
        return self.tools
    
    def _get_default_tools(self) -> List[Dict]:
        """
        Retorna uma lista de ferramentas padrão do MCP-Chatwoot.
        Usado como fallback quando não é possível obter a lista do servidor.
        
        Returns:
            Lista de informações sobre ferramentas do MCP-Chatwoot
        """
        return [
            {
                "name": "get_conversation",
                "description": "Obtém detalhes de uma conversa do Chatwoot pelo ID",
                "parameters": {
                    "conversation_id": {
                        "type": "integer",
                        "description": "ID da conversa"
                    }
                }
            },
            {
                "name": "send_message",
                "description": "Envia uma mensagem para uma conversa do Chatwoot",
                "parameters": {
                    "conversation_id": {
                        "type": "integer",
                        "description": "ID da conversa"
                    },
                    "message": {
                        "type": "string",
                        "description": "Conteúdo da mensagem"
                    },
                    "message_type": {
                        "type": "string",
                        "description": "Tipo da mensagem (outgoing, template, etc.)",
                        "default": "outgoing"
                    }
                }
            },
            {
                "name": "list_conversations",
                "description": "Lista conversas do Chatwoot",
                "parameters": {
                    "status": {
                        "type": "string",
                        "description": "Status das conversas (open, resolved, etc.)",
                        "default": "open"
                    },
                    "page": {
                        "type": "integer",
                        "description": "Número da página",
                        "default": 1
                    }
                }
            }
        ]
    
    def __enter__(self):
        """
        Suporte para uso com context manager.
        
        Returns:
            Lista de ferramentas
        """
        return self.tools
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Limpeza ao sair do context manager.
        """
        pass


# Exemplo de uso
if __name__ == "__main__":
    # Testar o adaptador
    try:
        chatwoot = ChatwootDynamicAdapter()
        tools = chatwoot.tools
        print(f"Ferramentas disponíveis: {len(tools)}")
        for tool in tools:
            print(f"- {tool.name}: {tool.description}")
    except Exception as e:
        print(f"Erro ao inicializar o adaptador: {e}")
