#!/usr/bin/env python3
"""
MongoDBAdapter - Adaptador personalizado para integração entre CrewAI e MCP-MongoDB

Este adaptador permite que agentes CrewAI utilizem ferramentas expostas por um servidor MCP-MongoDB
através de chamadas REST, contornando a limitação do MCPServerAdapter que requer transporte SSE
ou streamable-http.

Características:
- Descoberta dinâmica de ferramentas via endpoint REST /tools
- Suporte a multi-tenant via parâmetro tenant_id
- Criação automática de objetos Tool compatíveis com CrewAI
- Tratamento robusto de erros e timeouts
- Interface de context manager para facilidade de uso
- Caching opcional de ferramentas para melhor performance
- Logging detalhado para diagnóstico
"""

import json
import logging
import time
import requests
from typing import Dict, List, Any, Optional, Union, Callable
from crewai.tools import tool

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("MongoDBAdapter")

# Não precisamos mais da classe MongoDBTool, vamos usar funções com o decorador @tool


class MongoDBAdapter:
    """
    Adaptador personalizado para conectar o MCP-MongoDB ao CrewAI.
    
    Este adaptador descobre automaticamente as ferramentas disponíveis no MCP-MongoDB
    e as converte em objetos compatíveis com o CrewAI.
    
    Exemplo de uso:
    ```python
    from mongodb_adapter_enhanced import MongoDBAdapter
    from crewai import Agent, Task, Crew
    
    # Usando context manager (recomendado)
    with MongoDBAdapter(base_url="http://localhost:8001", tenant_id="account_1") as tools:
        agent = Agent(
            role="Analista de MongoDB",
            goal="Consultar dados no MongoDB",
    """
    
    def __init__(
        self, 
        base_url: str = "http://localhost:8001", 
        tenant_id: Optional[str] = None,
        cache_ttl: int = 300,
        retry_attempts: int = 3,
        retry_backoff: float = 1.5,
        timeout: int = 10
    ):
        """
        Inicializa o adaptador MongoDB.
        
        Args:
            base_url: URL base do servidor MCP-MongoDB
            tenant_id: ID do tenant para multi-tenant
            cache_ttl: Tempo de vida do cache em segundos
            retry_attempts: Número de tentativas de retry
            retry_backoff: Fator de backoff para retry
            timeout: Timeout para requisições em segundos
        """
        self.base_url = base_url.rstrip("/")
        self.tenant_id = tenant_id
        self.cache_ttl = cache_ttl
        self.retry_attempts = retry_attempts
        self.retry_backoff = retry_backoff
        self.timeout = timeout
        
        self._raw_tools_data = None
        self._last_cache_time = 0
        self._tools = None
        
        logger.info(f"Inicializando MongoDBAdapter com URL: {base_url}, Tenant: {tenant_id}")
    
    def _make_request(self, method: str, url: str, **kwargs) -> requests.Response:
        """
        Faz uma requisição HTTP com retry e timeout.
        
        Args:
            method: Método HTTP (get, post, etc.)
            url: URL da requisição
            **kwargs: Argumentos adicionais para requests
            
        Returns:
            Resposta da requisição
            
        Raises:
            ConnectionError: Se não for possível conectar após todas as tentativas
            TimeoutError: Se a requisição expirar
            HTTPError: Se o servidor retornar erro
        """
        # Garantir que headers estejam presentes
        if "headers" not in kwargs:
            kwargs["headers"] = {"Content-Type": "application/json"}
            
        # Adicionar timeout se não especificado
        if "timeout" not in kwargs:
            kwargs["timeout"] = self.timeout
            
        # Tentar fazer a requisição com retry
        for attempt in range(1, self.retry_attempts + 1):
            try:
                response = requests.request(method, url, **kwargs)
                response.raise_for_status()
                return response
            except requests.exceptions.Timeout:
                if attempt == self.retry_attempts:
                    logger.error(f"Timeout após {self.retry_attempts} tentativas: {url}")
                    raise TimeoutError(f"Timeout ao conectar a {url} após {self.retry_attempts} tentativas")
                wait_time = self.retry_backoff ** attempt
                logger.warning(f"Timeout na tentativa {attempt}/{self.retry_attempts}, tentando novamente em {wait_time:.2f}s")
            except requests.exceptions.HTTPError as e:
                logger.error(f"Erro HTTP {e.response.status_code}: {url}")
                raise
            except requests.exceptions.ConnectionError:
                if attempt == self.retry_attempts:
                    logger.error(f"Falha de conexão após {self.retry_attempts} tentativas: {url}")
                    raise ConnectionError(f"Não foi possível conectar a {url} após {self.retry_attempts} tentativas")
                wait_time = self.retry_backoff ** attempt
                logger.warning(f"Falha de conexão na tentativa {attempt}/{self.retry_attempts}, tentando novamente em {wait_time:.2f}s")
            except Exception as e:
                logger.error(f"Erro inesperado: {e}")
                raise
                
            # Esperar antes de tentar novamente com backoff exponencial
            time.sleep(self.retry_backoff ** attempt)
    
    def _fetch_tools(self) -> List[Dict[str, Any]]:
        """
        Busca as ferramentas disponíveis no MCP-MongoDB.
        
        Returns:
            Lista de ferramentas disponíveis
        """
        # Verificar se podemos usar o cache
        current_time = time.time()
        if (
            self._raw_tools_data is not None and 
            current_time - self._last_cache_time < self.cache_ttl
        ):
            logger.debug("Usando ferramentas em cache")
            return self._raw_tools_data
            
        # Buscar ferramentas via API REST
        logger.info(f"Buscando ferramentas em {self.base_url}/tools")
        
        # Preparar parâmetros de query
        params = {}
        if self.tenant_id:
            params["tenant_id"] = self.tenant_id
            
        response = self._make_request("get", f"{self.base_url}/tools", params=params)
        tools_data = response.json()
        
        # Atualizar cache
        self._raw_tools_data = tools_data
        self._last_cache_time = current_time
        
        logger.info(f"Encontradas {len(tools_data)} ferramentas")
        return tools_data
            else:
                logger.warning(f"Formato de resposta inesperado: {tools_data}")
                self._raw_tools_data = []
                
            # Atualizar timestamp do cache
            self._last_cache_time = current_time
            
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
            start_time = time.time()
            
            # Adicionar tenant_id se não especificado e disponível no adaptador
            if "tenant_id" not in kwargs and self.tenant_id:
                kwargs["tenant_id"] = self.tenant_id
                
            try:
                logger.info(f"Executando ferramenta {tool_name} com parâmetros: {kwargs}")
                
                # Preparar parâmetros de query
                params = {}
                if self.tenant_id:
                    params["tenant_id"] = self.tenant_id
                
                # Executar a ferramenta via API REST
                response = self._make_request(
                    "post",
                    f"{self.base_url}/tools/{tool_name}",
                    json=kwargs,
                    params=params
                )
                
                # Processar resultado
                try:
                    result = response.json()
                    execution_time = time.time() - start_time
                    logger.info(f"Ferramenta {tool_name} executada com sucesso em {execution_time:.2f}s")
                    
                    # Formatar o resultado para melhor legibilidade
                    if isinstance(result, dict):
                        return json.dumps(result, indent=2, ensure_ascii=False)
                    return str(result)
                except json.JSONDecodeError:
                    # Se não for JSON, retornar o texto da resposta
                    logger.warning(f"Resposta da ferramenta {tool_name} não é JSON válido")
                    return response.text
                    
            except Exception as e:
                logger.error(f"Erro ao executar ferramenta {tool_name}: {e}")
                return f"Erro ao executar ferramenta {tool_name}: {e}"
        
        return execute_tool
    
    def _build_tools(self) -> List[Callable]:
        """
        Constrói funções de ferramentas compatíveis com CrewAI a partir das ferramentas do MCP-MongoDB.
        
        Returns:
            Lista de funções decoradas com @tool
        """
        raw_tools = self._fetch_tools()
        tools = []
        
        for tool_data in raw_tools:
            try:
                # Extrair informações da ferramenta
                name = tool_data["name"]
                description = tool_data.get("description", "Sem descrição disponível")
                parameters = tool_data.get("parameters", {})
                
                # Criar descrição detalhada incluindo parâmetros
                detailed_description = f"{description}\n\nParâmetros:"
                
                # Processar parâmetros
                if isinstance(parameters, dict):
                    # Verificar se há propriedades aninhadas
                    properties = parameters.get("properties", {})
                    required = parameters.get("required", [])
                    
                    if properties:
                        # Formato: {"properties": {...}, "required": [...]}
                        for param_name, param_info in properties.items():
                            param_type = param_info.get("type", "any")
                            param_desc = param_info.get("description", "")
                            is_required = "Obrigatório" if param_name in required else "Opcional"
                            detailed_description += f"\n- {param_name} ({param_type}, {is_required}): {param_desc}"
                    else:
                        # Formato simples
                        for param_name, param_info in parameters.items():
                            if param_name != "required":
                                param_type = "any"
                                param_desc = ""
                                if isinstance(param_info, dict):
                                    param_type = param_info.get("type", "any")
                                    param_desc = param_info.get("description", "")
                                is_required = "Obrigatório" if param_name in required else "Opcional"
                                detailed_description += f"\n- {param_name} ({param_type}, {is_required}): {param_desc}"
                
                # Criar a função de execução da ferramenta
                exec_func = self._create_tool_function(name)
                
                # Criar uma função decorada com @tool
                @tool(name=name, description=detailed_description)
                def dynamic_tool(**kwargs):
                    return exec_func(**kwargs)
                
                # Renomear a função para evitar sobrescrita
                dynamic_tool.__name__ = f"mongodb_{name}"
                
                tools.append(dynamic_tool)
                logger.debug(f"Ferramenta criada: {name}")
                
            except KeyError as e:
                logger.warning(f"Ferramenta inválida, faltando campo obrigatório: {e}")
            except Exception as e:
                logger.warning(f"Erro ao processar ferramenta: {e}")
        
        return tools
    
    @property
    def tools(self) -> List[Callable]:
        """
        Obtém as ferramentas do MCP-MongoDB como funções decoradas com @tool compatíveis com CrewAI.
        
        Returns:
            Lista de funções decoradas com @tool
        """
        if self._tools is None:
            self._tools = self._build_tools()
        return self._tools
    
    def refresh_tools(self) -> List[Callable]:
        """
        Atualiza a lista de ferramentas do MCP-MongoDB.
        
        Returns:
            Lista atualizada de funções decoradas com @tool
        """
        self._tools = None
        self._raw_tools_data = None
        self._last_cache_time = 0
        return self.tools
    
    def check_health(self) -> Dict[str, Any]:
        """
        Verifica a saúde do servidor MCP-MongoDB.
        
        Returns:
            Informações de saúde do servidor
            
        Raises:
            ConnectionError: Se não for possível verificar a saúde
        """
        try:
            logger.info(f"Verificando saúde em {self.base_url}/health")
            response = self._make_request("get", f"{self.base_url}/health")
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
            # Extrair nome e descrição da função decorada
            tool_name = tool.__name__
            tool_desc = tool.__doc__ or "Sem descrição"
            if "\n\nParâmetros:" in tool_desc:
                tool_desc = tool_desc.split("\n\nParâmetros:")[0].strip()
            print(f"{i+1}. {tool_name}: {tool_desc}")
        
        # Exemplo de integração com CrewAI
        print("\nExemplo de como usar com CrewAI:")
        print("""
        from crewai import Agent, Task, Crew
        
        # Obter ferramentas do adaptador MongoDB
        mongodb_adapter = MongoDBAdapter(tenant_id="account_1")
        mongodb_tools = mongodb_adapter.tools
        
        # Criar agente com as ferramentas
        agent = Agent(
            role="Analista de MongoDB",
            goal="Consultar dados no MongoDB",
            backstory="Especialista em análise de dados com MongoDB",
            tools=mongodb_tools,
            verbose=True
        )
        
        # Criar tarefa
        task = Task(
            description="Consultar configurações da empresa na coleção 'company_services'",
            agent=agent
        )
        
        # Criar crew e executar
        crew = Crew(
            agents=[agent],
            tasks=[task]
        )
        
        result = crew.kickoff()
        """)
            
    except Exception as e:
        print(f"Erro: {e}")
        import traceback
        traceback.print_exc()
