#!/usr/bin/env python3
"""
Adaptador personalizado para integrar MCP-MongoDB com CrewAI
"""

import requests
import json
from typing import List, Dict, Any, Callable
from crewai.tools.base_tool import Tool

class MongoDBAdapter:
    """
    Adaptador personalizado para conectar o MCP-MongoDB ao CrewAI.
    
    Este adaptador descobre automaticamente as ferramentas disponíveis no MCP-MongoDB
    e as converte em objetos Tool compatíveis com o CrewAI.
    """
    
    def __init__(self, base_url: str = "http://localhost:8001", tenant_id: str = "account_1"):
        """
        Inicializa o adaptador para o MCP-MongoDB.
        
        Args:
            base_url: URL base do servidor MCP-MongoDB
            tenant_id: ID do tenant para operações multi-tenant
        """
        self.base_url = base_url
        self.tenant_id = tenant_id
        self._tools = None
        self._raw_tools_data = None
    
    def _fetch_tools(self) -> List[Dict[str, Any]]:
        """
        Busca a lista de ferramentas disponíveis no MCP-MongoDB.
        
        Returns:
            Lista de ferramentas no formato original do MCP-MongoDB
        """
        try:
            response = requests.get(f"{self.base_url}/tools")
            response.raise_for_status()
            tools_data = response.json()
            self._raw_tools_data = tools_data["tools"]
            return self._raw_tools_data
        except Exception as e:
            raise ConnectionError(f"Erro ao buscar ferramentas do MCP-MongoDB: {e}")
    
    def _create_tool_function(self, tool_name: str) -> Callable:
        """
        Cria uma função que executa a ferramenta especificada via API REST.
        
        Args:
            tool_name: Nome da ferramenta no MCP-MongoDB
            
        Returns:
            Função que executa a ferramenta
        """
        def execute_tool(**kwargs):
            # Adicionar tenant_id se não especificado
            if "tenant_id" not in kwargs:
                kwargs["tenant_id"] = self.tenant_id
                
            try:
                # Executar a ferramenta via API REST
                response = requests.post(
                    f"{self.base_url}/tools/{tool_name}", 
                    json=kwargs
                )
                response.raise_for_status()
                result = response.json()
                
                # Formatar o resultado para melhor legibilidade
                return json.dumps(result, indent=2)
            except Exception as e:
                return f"Erro ao executar ferramenta {tool_name}: {e}"
        
        return execute_tool
    
    def _build_tools(self) -> List[Tool]:
        """
        Constrói objetos Tool do CrewAI a partir das ferramentas do MCP-MongoDB.
        
        Returns:
            Lista de objetos Tool do CrewAI
        """
        raw_tools = self._fetch_tools()
        tools = []
        
        for tool_data in raw_tools:
            name = tool_data["name"]
            description = tool_data["description"]
            parameters = tool_data.get("parameters", {})
            
            # Criar descrição detalhada incluindo parâmetros
            detailed_description = f"{description}\n\nParâmetros:"
            for param_name, param_info in parameters.items():
                param_type = param_info.get("type", "any")
                param_desc = param_info.get("description", "")
                detailed_description += f"\n- {param_name} ({param_type}): {param_desc}"
            
            # Criar a ferramenta
            tool = Tool(
                name=name,
                description=detailed_description,
                func=self._create_tool_function(name)
            )
            tools.append(tool)
        
        return tools
    
    @property
    def tools(self) -> List[Tool]:
        """
        Obtém as ferramentas do MCP-MongoDB como objetos Tool do CrewAI.
        
        Returns:
            Lista de objetos Tool do CrewAI
        """
        if self._tools is None:
            self._tools = self._build_tools()
        return self._tools
    
    def refresh_tools(self) -> List[Tool]:
        """
        Atualiza a lista de ferramentas do MCP-MongoDB.
        
        Returns:
            Lista atualizada de objetos Tool do CrewAI
        """
        self._tools = None
        return self.tools
    
    def check_health(self) -> Dict[str, Any]:
        """
        Verifica a saúde do servidor MCP-MongoDB.
        
        Returns:
            Informações de saúde do servidor
        """
        try:
            response = requests.get(f"{self.base_url}/health")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise ConnectionError(f"Erro ao verificar saúde do MCP-MongoDB: {e}")
    
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
