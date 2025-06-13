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
                        "method": "get_tools",
                        "params": {},
                        "id": 2
                    }
                    
                    response = self.session.post(self.message_url, json=jsonrpc_request, timeout=10)
                    response.raise_for_status()
                    
                    result = response.json()
                    if "result" in result and "tools" in result["result"]:
                        self._raw_tools_data = result["result"]["tools"]
                        logger.info(f"Ferramentas descobertas via JSON-RPC: {len(self._raw_tools_data)}")
                        return self._raw_tools_data
            
            # Se não conseguirmos descobrir as ferramentas, usamos uma lista padrão
            logger.warning("Não foi possível descobrir ferramentas, usando lista padrão")
            self._raw_tools_data = self._get_default_tools()
            return self._raw_tools_data
            
        except Exception as e:
            logger.error(f"Erro ao descobrir ferramentas: {e}")
            # Em caso de erro, usamos uma lista padrão de ferramentas
            self._raw_tools_data = self._get_default_tools()
            return self._raw_tools_data
    
    def _call_chatwoot_api(self, tool_name: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Faz uma chamada à API do MCP-Chatwoot usando o endpoint /messages/ com JSON-RPC.
        
        Args:
            tool_name: Nome da ferramenta/método a ser chamado
            params: Parâmetros para a chamada da ferramenta
            
        Returns:
            Resposta da API como um dicionário
        """
        if params is None:
            params = {}
            
        jsonrpc_request = {
            "jsonrpc": "2.0",
            "method": tool_name,
            "params": params,
            "id": hash(f"{tool_name}_{json.dumps(params)}") % 10000  # ID único baseado na chamada
        }
        
        try:
            response = self.session.post(self.message_url, json=jsonrpc_request, timeout=30)
            response.raise_for_status()
            result = response.json()
            
            if "error" in result:
                error_msg = f"Erro na chamada da API: {result['error'].get('message', 'Erro desconhecido')}"
                logger.error(error_msg)
                return {"error": error_msg}
                
            return result.get("result", {})
        except Exception as e:
            error_msg = f"Falha ao chamar {tool_name}: {str(e)}"
            logger.error(error_msg)
            return {"error": error_msg}
    
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
                # Executar a ferramenta via API REST
                result = self._call_chatwoot_api(tool_name, kwargs)
                
                # Formatar o resultado para melhor legibilidade
                return json.dumps(result, indent=2, ensure_ascii=False)
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
            description = tool_data.get("description", f"Ferramenta {name} do MCP-Chatwoot")
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
