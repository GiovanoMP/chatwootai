#!/usr/bin/env python3
"""
Adaptador personalizado para integrar MCP-MongoDB com CrewAI
"""

import requests
import json
import logging
from typing import List, Dict, Any, Callable, Optional
from crewai.tools.base_tool import BaseTool

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("MongoDBAdapter")

class MongoDBTool(BaseTool):
    """
    Implementação personalizada de ferramenta para o MCP-MongoDB
    """
    
    def __init__(
        self, 
        name: str, 
        description: str, 
        func: Callable, 
        parameters: Dict[str, Any] = None
    ):
        """
        Inicializa uma ferramenta do MCP-MongoDB.
        
        Args:
            name: Nome da ferramenta
            description: Descrição da ferramenta
            func: Função que executa a ferramenta
            parameters: Parâmetros da ferramenta
        """
        self._name = name
        self._description = description
        self._func = func
        self._parameters = parameters or {}
        
    @property
    def name(self) -> str:
        """Nome da ferramenta"""
        return self._name
    
    @property
    def description(self) -> str:
        """Descrição da ferramenta"""
        return self._description
    
    def __call__(self, *args, **kwargs):
        """Executa a ferramenta"""
        return self._func(*args, **kwargs)


class MongoDBAdapter:
    """
    Adaptador personalizado para conectar o MCP-MongoDB ao CrewAI.
    
    Este adaptador descobre automaticamente as ferramentas disponíveis no MCP-MongoDB
    e as converte em objetos compatíveis com o CrewAI.
    """
    
    def __init__(
        self, 
        base_url: str = "http://localhost:8001", 
        tenant_id: str = "account_1",
        timeout: int = 10
    ):
        """
        Inicializa o adaptador para o MCP-MongoDB.
        
        Args:
            base_url: URL base do servidor MCP-MongoDB
            tenant_id: ID do tenant para operações multi-tenant
            timeout: Timeout para requisições HTTP em segundos
        """
        self.base_url = base_url
        self.tenant_id = tenant_id
        self.timeout = timeout
        self._tools = None
        self._raw_tools_data = None
        logger.info(f"Inicializando MongoDBAdapter com URL: {base_url}")
    
    def _fetch_tools(self) -> List[Dict[str, Any]]:
        """
        Busca a lista de ferramentas disponíveis no MCP-MongoDB.
        
        Returns:
            Lista de ferramentas no formato original do MCP-MongoDB
        """
        try:
            logger.info(f"Buscando ferramentas em {self.base_url}/tools")
            response = requests.get(f"{self.base_url}/tools", timeout=self.timeout)
            response.raise_for_status()
            tools_data = response.json()
            self._raw_tools_data = tools_data.get("tools", [])
            logger.info(f"Encontradas {len(self._raw_tools_data)} ferramentas")
            return self._raw_tools_data
        except Exception as e:
            logger.error(f"Erro ao buscar ferramentas: {e}")
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
                logger.info(f"Executando ferramenta {tool_name} com parâmetros: {kwargs}")
                # Executar a ferramenta via API REST
                response = requests.post(
                    f"{self.base_url}/tools/{tool_name}", 
                    json=kwargs,
                    timeout=self.timeout
                )
                response.raise_for_status()
                result = response.json()
                logger.info(f"Ferramenta {tool_name} executada com sucesso")
                
                # Formatar o resultado para melhor legibilidade
                return json.dumps(result, indent=2)
            except Exception as e:
                logger.error(f"Erro ao executar ferramenta {tool_name}: {e}")
                return f"Erro ao executar ferramenta {tool_name}: {e}"
        
        return execute_tool
    
    def _build_tools(self) -> List[BaseTool]:
        """
        Constrói objetos de ferramentas compatíveis com CrewAI a partir das ferramentas do MCP-MongoDB.
        
        Returns:
            Lista de objetos de ferramentas compatíveis com CrewAI
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
                required = "Obrigatório" if param_name in parameters.get("required", []) else "Opcional"
                detailed_description += f"\n- {param_name} ({param_type}, {required}): {param_desc}"
            
            # Criar a ferramenta
            tool = MongoDBTool(
                name=name,
                description=detailed_description,
                func=self._create_tool_function(name),
                parameters=parameters
            )
            tools.append(tool)
        
        return tools
    
    @property
    def tools(self) -> List[BaseTool]:
        """
        Obtém as ferramentas do MCP-MongoDB como objetos compatíveis com CrewAI.
        
        Returns:
            Lista de objetos de ferramentas compatíveis com CrewAI
        """
        if self._tools is None:
            self._tools = self._build_tools()
        return self._tools
    
    def refresh_tools(self) -> List[BaseTool]:
        """
        Atualiza a lista de ferramentas do MCP-MongoDB.
        
        Returns:
            Lista atualizada de objetos de ferramentas compatíveis com CrewAI
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
            logger.info(f"Verificando saúde em {self.base_url}/health")
            response = requests.get(f"{self.base_url}/health", timeout=self.timeout)
            response.raise_for_status()
            health_data = response.json()
            logger.info(f"Status de saúde: {health_data}")
            return health_data
        except Exception as e:
            logger.error(f"Erro ao verificar saúde: {e}")
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


if __name__ == "__main__":
    # Exemplo de uso
    try:
        print("Testando adaptador para MCP-MongoDB...")
        adapter = MongoDBAdapter()
        
        # Verificar saúde
        health = adapter.check_health()
        print(f"Saúde do servidor: {health}")
        
        # Obter ferramentas
        tools = adapter.tools
        print(f"Ferramentas encontradas: {len(tools)}")
        
        # Listar ferramentas
        for i, tool in enumerate(tools):
            print(f"{i+1}. {tool.name}: {tool.description.split('Parâmetros:')[0].strip()}")
            
    except Exception as e:
        print(f"Erro: {e}")
