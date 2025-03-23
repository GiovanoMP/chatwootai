"""
Data Proxy Agent refatorado para o ChatwootAI.

Este módulo implementa o agente especializado que atua como intermediário entre
outros agentes e serviços de dados, fornecendo uma interface unificada para acesso
a dados em diferentes domínios de negócio.

Principais responsabilidades:
1. Ser o ÚNICO ponto de acesso para consultas de dados no sistema
2. Traduzir consultas em linguagem natural para operações específicas
3. Implementar otimizações como caching, batching e indexação
4. Garantir consistência na formatação dos dados retornados
5. Centralizar a gestão de ferramentas via ToolRegistry
"""

import logging
import time
from typing import Dict, List, Any, Optional, Union, ClassVar, Type, Set
from pydantic import Field, BaseModel
import json

from crewai import Agent
from crewai.tools.base_tool import BaseTool
from crewai.tools.structured_tool import CrewStructuredTool as StructuredTool

# Importando serviços e ferramentas de suporte
from src.core.data_service_hub import DataServiceHub
from src.core.memory import MemorySystem
from src.core.tools.tool_registry import ToolRegistry
from src.core.domain.domain_manager import DomainManager

logger = logging.getLogger(__name__)


class DataAccessError(Exception):
    """Exceção lançada quando há erros de acesso a dados."""
    pass


class ConfigurationError(Exception):
    """Exceção lançada quando há erros de configuração."""
    pass


class DataProxyAgent:
    """
    Agente responsável por intermediar o acesso a dados para outros agentes.
    
    Este agente serve como proxy entre agentes funcionais e serviços de dados,
    traduzindo requisições de alto nível em consultas otimizadas e fornecendo
    uma camada de acesso a dados adaptada ao domínio de negócio atual.
    
    Responsabilidades principais:
    1. Entendimento de requisições de dados em linguagem natural
    2. Otimização de consultas e estratégias de cache
    3. Transformações de dados específicas por domínio
    4. Formatação consistente de dados para consumo pelos agentes
    5. Gerenciamento centralizado de ferramentas
    """
    
    # Atributos de classe
    _data_service_hub: ClassVar[DataServiceHub]
    _memory_system: ClassVar[Optional[MemorySystem]]
    _tool_registry: ClassVar[ToolRegistry]
    _domain_manager: ClassVar[Optional[DomainManager]]
    _access_stats: ClassVar[Dict[str, Any]]
    _crew_agent: ClassVar[Agent]
    
    def __init__(self, 
                 data_service_hub: DataServiceHub,
                 memory_system: Optional[MemorySystem] = None,
                 tool_registry: Optional[ToolRegistry] = None,
                 domain_manager: Optional[DomainManager] = None,
                 additional_tools: Optional[List[BaseTool]] = None,
                 **kwargs):
        """
        Inicializa o agente de proxy de dados.
        
        Args:
            data_service_hub: Hub central para serviços de dados
            memory_system: Sistema de memória compartilhada (opcional)
            tool_registry: Registro centralizado de ferramentas (opcional)
            domain_manager: Gerenciador de domínios de negócio (opcional)
            additional_tools: Ferramentas adicionais para o agente (opcional)
            **kwargs: Argumentos adicionais para a classe Agent
        """
        # Validar e armazenar atributos essenciais
        if not data_service_hub:
            raise ConfigurationError("DataServiceHub é obrigatório para o DataProxyAgent")
            
        self._data_service_hub = data_service_hub
        self._memory_system = memory_system or MemorySystem()
        self._tool_registry = tool_registry or ToolRegistry()
        self._domain_manager = domain_manager
        
        # Configurar ferramentas padrão
        tools = []
        
        # Adicionar ferramentas adicionais se fornecidas
        if additional_tools:
            tools.extend(additional_tools)
            
        # Configuração padrão para o agente de proxy de dados
        default_config = {
            "role": "Data Proxy",
            "goal": "Fornecer acesso eficiente e adaptado ao domínio de negócio para todos os agentes",
            "backstory": """Você é o proxy de dados da arquitetura centralizada.
            Seu trabalho é facilitar o acesso a dados para outros agentes, traduzindo suas
            requisições em consultas otimizadas e garantindo que recebam dados em um 
            formato consistente, independentemente da fonte de dados subjacente ou domínio de negócio.
            Você tem conhecimento profundo de estruturas de dados, otimização de consultas e 
            esquemas específicos de domínio.""",
            "verbose": True,
            "allow_delegation": True,
            "tools": tools
        }
        
        # Sobrescrever padrões com kwargs fornecidos
        config = {**default_config, **kwargs}
        
        # Criar o agente CrewAI
        self._crew_agent = Agent(**config)
        
        # Estatísticas de acesso para otimização
        self._access_stats = {
            "products": {"count": 0, "avg_time": 0},
            "customers": {"count": 0, "avg_time": 0},
            "orders": {"count": 0, "avg_time": 0},
            "business_rules": {"count": 0, "avg_time": 0},
            "vector_search": {"count": 0, "avg_time": 0},
            "memory": {"count": 0, "avg_time": 0},
        }
        
        # Inicializar o registro de ferramentas se houver domínio ativo
        self._initialize_tools()
        
        logger.info("DataProxyAgent inicializado com sucesso")
    
    def _initialize_tools(self) -> None:
        """
        Inicializa o registro de ferramentas com base nas configurações do domínio ativo.
        
        Esta função é responsável por registrar todas as ferramentas disponíveis
        no sistema a partir da configuração do domínio ativo.
        """
        # Se não houver gerenciador de domínio, não há ferramentas para inicializar
        if not self._domain_manager:
            logger.warning("DomainManager não disponível, ferramentas não serão inicializadas")
            return
        
        try:
            # Obter as configurações de ferramentas do domínio ativo
            tools_config = self._domain_manager.get_tools_config()
            
            if not tools_config:
                logger.warning("Nenhuma configuração de ferramentas encontrada no domínio ativo")
                return
            
            # Registrar as ferramentas no registro centralizado
            self._tool_registry.register_tools_from_config(tools_config)
            logger.info(f"Ferramentas registradas: {self._tool_registry.get_tool_ids()}")
            
        except Exception as e:
            logger.error(f"Erro ao inicializar ferramentas: {str(e)}")
            import traceback
            logger.debug(f"Traceback: {traceback.format_exc()}")
    
    @property
    def data_service_hub(self) -> DataServiceHub:
        """Obtém o hub de serviços de dados."""
        return self._data_service_hub
    
    @property
    def memory_system(self) -> MemorySystem:
        """Obtém o sistema de memória."""
        return self._memory_system
    
    @property
    def tool_registry(self) -> ToolRegistry:
        """Obtém o registro de ferramentas."""
        return self._tool_registry
    
    @property
    def domain_manager(self) -> Optional[DomainManager]:
        """Obtém o gerenciador de domínios."""
        return self._domain_manager
    
    def is_ready(self) -> bool:
        """
        Verifica se o agente está pronto para uso.
        
        Returns:
            bool: True se o agente está pronto, False caso contrário
        """
        # Verificar componentes essenciais
        if not self._data_service_hub:
            logger.error("DataServiceHub não disponível")
            return False
        
        if not self._tool_registry:
            logger.warning("ToolRegistry não disponível, funcionalidades limitadas")
        
        if not self._domain_manager:
            logger.warning("DomainManager não disponível, funcionalidades limitadas")
        
        return True
        
    def get_tools(self) -> List[BaseTool]:
        """
        Retorna as ferramentas disponibilizadas pelo DataProxyAgent para outros agentes.
        
        Estas ferramentas são wrappers em formato compatível com o BaseTool do CrewAI,
        possuindo os atributos 'name', 'func' e 'description'.
        
        Returns:
            List[BaseTool]: Lista de ferramentas para consulta de dados
        """
        # Definir schemas para as ferramentas usando Pydantic
        class ProductQueryInput(BaseModel):
            query_text: str = Field(..., description="Texto da consulta sobre produtos")
            filters: Optional[Dict[str, Any]] = Field(None, description="Filtros opcionais para refinar a busca")
            domain: Optional[str] = Field(None, description="Domínio específico para a consulta (opcional)")
            
        class CustomerQueryInput(BaseModel):
            query_text: str = Field(..., description="Texto da consulta sobre clientes")
            filters: Optional[Dict[str, Any]] = Field(None, description="Filtros opcionais para refinar a busca")
            domain: Optional[str] = Field(None, description="Domínio específico para a consulta (opcional)")
            
        class BusinessRulesQueryInput(BaseModel):
            query_text: str = Field(..., description="Texto da consulta sobre regras de negócio")
            category: Optional[str] = Field(None, description="Categoria específica de regras de negócio")
            domain: Optional[str] = Field(None, description="Domínio específico para a consulta (opcional)")
            
        class VectorSearchInput(BaseModel):
            query_text: str = Field(..., description="Texto da consulta para busca semântica")
            collection: Optional[str] = Field(None, description="Coleção específica para busca")
            limit: Optional[int] = Field(5, description="Número máximo de resultados")
            domain: Optional[str] = Field(None, description="Domínio específico para a consulta (opcional)")
            
        class MemoryQueryInput(BaseModel):
            query_text: str = Field(..., description="Texto da consulta para busca na memória")
            limit: Optional[int] = Field(5, description="Número máximo de resultados")
            agent_id: Optional[str] = Field(None, description="ID do agente para filtrar memórias")
            
        # Criando classes de ferramentas que herdam de BaseTool
        
        # Ferramenta de busca de produtos
        class ProductQueryTool(BaseTool):
            name: str = "query_product_data"
            description: str = "Busca informações sobre produtos no catálogo"
            args_schema: type = ProductQueryInput
            
            def _run(self, query_text: str, filters: Optional[Dict[str, Any]] = None, domain: Optional[str] = None) -> str:
                result = self.data_proxy_agent.query_product_data(query_text, filters, domain)
                return json.dumps(result, ensure_ascii=False, indent=2)
                
            data_proxy_agent = self
        
        # Ferramenta de busca de clientes
        class CustomerQueryTool(BaseTool):
            name: str = "query_customer_data"
            description: str = "Busca informações sobre clientes no banco de dados"
            args_schema: type = CustomerQueryInput
            
            def _run(self, query_text: str, filters: Optional[Dict[str, Any]] = None, domain: Optional[str] = None) -> str:
                result = self.data_proxy_agent.query_customer_data(query_text, filters, domain)
                return json.dumps(result, ensure_ascii=False, indent=2)
                
            data_proxy_agent = self
            
        # Ferramenta de busca de regras de negócio
        class BusinessRulesQueryTool(BaseTool):
            name: str = "query_business_rules"
            description: str = "Busca regras de negócio para o domínio atual"
            args_schema: type = BusinessRulesQueryInput
            
            def _run(self, query_text: str, category: Optional[str] = None, domain: Optional[str] = None) -> str:
                result = self.data_proxy_agent.query_business_rules(query_text, category, domain)
                return json.dumps(result, ensure_ascii=False, indent=2)
                
            data_proxy_agent = self
        
        # Ferramenta de busca semântica
        class VectorSearchTool(BaseTool):
            name: str = "vector_search"
            description: str = "Realiza busca semântica em documentos e bases de conhecimento"
            args_schema: type = VectorSearchInput
            
            def _run(self, query_text: str, collection: Optional[str] = None, limit: Optional[int] = 5, domain: Optional[str] = None) -> str:
                result = self.data_proxy_agent.vector_search(query_text, collection, limit, domain)
                return json.dumps(result, ensure_ascii=False, indent=2)
                
            data_proxy_agent = self
            
        # Ferramenta de busca na memória
        class MemoryQueryTool(BaseTool):
            name: str = "memory_query"
            description: str = "Busca informações na memória do sistema"
            args_schema: type = MemoryQueryInput
            
            def _run(self, query_text: str, limit: Optional[int] = 5, agent_id: Optional[str] = None) -> str:
                result = self.data_proxy_agent.memory_query(query_text, limit, agent_id)
                return json.dumps(result, ensure_ascii=False, indent=2)
                
            data_proxy_agent = self
        
        # Instanciar as ferramentas passando self como data_proxy_agent
        product_tool = ProductQueryTool()
        product_tool.data_proxy_agent = self
        
        customer_tool = CustomerQueryTool()
        customer_tool.data_proxy_agent = self
        
        business_rules_tool = BusinessRulesQueryTool()
        business_rules_tool.data_proxy_agent = self
        
        vector_search_tool = VectorSearchTool()
        vector_search_tool.data_proxy_agent = self
        
        memory_tool = MemoryQueryTool()
        memory_tool.data_proxy_agent = self
        
        # Lista de ferramentas que serão disponibilizadas
        tools = [
            product_tool,
            customer_tool,
            business_rules_tool,
            vector_search_tool,
            memory_tool
        ]
        
        return tools
        
    def get_domain_tools(self, domain_name: Optional[str] = None) -> List[Any]:
        """
        Obtém as ferramentas específicas para um domínio.
        
        Args:
            domain_name: Nome do domínio (se None, usa o domínio ativo)
            
        Returns:
            List[Any]: Lista de instâncias de ferramentas para o domínio
        """
        if not self._domain_manager:
            logger.warning("DomainManager não disponível, não é possível obter ferramentas do domínio")
            return []
            
        # Obter o domínio ativo se nenhum for especificado
        domain = domain_name or self._domain_manager.get_active_domain_name()
        
        # Obter as configurações de ferramentas para o domínio
        tools_config = self._domain_manager.get_tools_config(domain)
        
        # Obter instâncias das ferramentas
        tools = []
        for tool_id in tools_config.keys():
            try:
                tool = self._tool_registry.get_tool_instance(tool_id)
                tools.append(tool)
            except Exception as e:
                logger.warning(f"Não foi possível carregar a ferramenta {tool_id}: {str(e)}")
                
        return tools
    
    def get_agent_tools(self, agent_name: str, domain_name: Optional[str] = None) -> List[Any]:
        """
        Obtém as ferramentas específicas para um agente em um domínio.
        
        Args:
            agent_name: Nome do agente
            domain_name: Nome do domínio (se None, usa o domínio ativo)
            
        Returns:
            List[Any]: Lista de instâncias de ferramentas para o agente
        """
        if not self._domain_manager:
            logger.warning("DomainManager não disponível, não é possível obter ferramentas do agente")
            return []
            
        # Obter a lista de ferramentas do agente
        tool_ids = self._domain_manager.get_agent_tools(agent_name, domain_name)
        
        if not tool_ids:
            logger.warning(f"Nenhuma ferramenta configurada para o agente {agent_name}")
            return []
            
        # Obter instâncias das ferramentas
        return self._tool_registry.get_tools_for_agent(tool_ids)
    
    def query_product_data(self, query_text: str, filters: dict = None, domain: str = None):
        """
        Consulta informações sobre produtos no catálogo.
        
        Args:
            query_text: O texto da consulta sobre produtos
            filters: Filtros opcionais para refinar a busca
            domain: Domínio específico para a consulta
            
        Returns:
            dict: Resultados da consulta de produtos
        """
        start_time = time.time()
        try:
            # Usar o serviço de dados de produtos para realizar a consulta
            if self.data_service_hub:
                service = self.data_service_hub.get_service('ProductDataService')
                if service:
                    # Incluir o contexto de domínio na consulta se fornecido
                    context = {"domain": domain} if domain else None
                    results = service.search_products(query_text, filters, context=context)
                    # Atualizar estatísticas de acesso
                    self._update_access_stats('products', time.time() - start_time)
                    return results
            return {"error": "Serviço de dados de produtos não disponível"}
        except Exception as e:
            logger.error(f"Erro ao consultar dados de produtos: {str(e)}")
            return {"error": f"Falha na consulta de produtos: {str(e)}"}
    
    def query_customer_data(self, query_text: str, filters: dict = None, domain: str = None):
        """
        Consulta informações sobre clientes no banco de dados.
        
        Args:
            query_text: O texto da consulta sobre clientes
            filters: Filtros opcionais para refinar a busca
            domain: Domínio específico para a consulta
            
        Returns:
            dict: Resultados da consulta de clientes
        """
        start_time = time.time()
        try:
            # Usar o serviço de dados de clientes para realizar a consulta
            if self.data_service_hub:
                service = self.data_service_hub.get_service('CustomerDataService')
                if service:
                    # Incluir o contexto de domínio na consulta se fornecido
                    context = {"domain": domain} if domain else None
                    results = service.search_customers(query_text, filters, context=context)
                    # Atualizar estatísticas de acesso
                    self._update_access_stats('customers', time.time() - start_time)
                    return results
            return {"error": "Serviço de dados de clientes não disponível"}
        except Exception as e:
            logger.error(f"Erro ao consultar dados de clientes: {str(e)}")
            return {"error": f"Falha na consulta de clientes: {str(e)}"}
    
    def query_business_rules(self, query_text: str, category: str = None, domain: str = None):
        """
        Consulta regras de negócio para o domínio atual ou especificado.
        
        Args:
            query_text: O texto da consulta sobre regras de negócio
            category: Categoria específica de regras de negócio
            domain: Domínio específico para a consulta
            
        Returns:
            dict: Regras de negócio correspondentes à consulta
        """
        start_time = time.time()
        try:
            # Usar o serviço de regras de domínio para realizar a consulta
            if self.data_service_hub:
                service = self.data_service_hub.get_service('DomainRulesService')
                if service:
                    # Se nenhum domínio for especificado, usar o domínio ativo
                    if domain is None and self._domain_manager:
                        domain = self._domain_manager.get_active_domain_name()
                    
                    rules = service.get_domain_rules(query_text, domain, category)
                    # Atualizar estatísticas de acesso
                    self._update_access_stats('business_rules', time.time() - start_time)
                    return rules
            return {"error": "Serviço de regras de domínio não disponível"}
        except Exception as e:
            logger.error(f"Erro ao consultar regras de negócio: {str(e)}")
            return {"error": f"Falha na consulta de regras de negócio: {str(e)}"}
    
    def vector_search(self, query_text: str, collection_name: str = None, limit: int = 5, domain: str = None):
        """
        Realiza busca semântica em documentos e bases de conhecimento.
        
        Args:
            query_text: O texto da consulta para busca semântica
            collection_name: Nome da coleção específica para buscar
            limit: Número máximo de resultados a retornar
            domain: Domínio específico para a consulta
            
        Returns:
            dict: Resultados da busca semântica
        """
        start_time = time.time()
        try:
            # Se domínio for especificado, ajustar a coleção
            if domain and not collection_name:
                collection_name = f"{domain}_documents"
                
            # Usar o DataServiceHub para realizar a consulta
            if self.data_service_hub:
                vector_service = self.data_service_hub.get_service('VectorSearchService')
                if vector_service:
                    results = vector_service.search(
                        query_text,
                        collection_name=collection_name,
                        limit=limit
                    )
                    # Atualizar estatísticas de acesso
                    self._update_access_stats('vector_search', time.time() - start_time)
                    return {"results": results}
            return {"error": "Serviço de busca vetorial não disponível"}
        except Exception as e:
            logger.error(f"Erro ao realizar busca semântica: {str(e)}")
            return {"error": f"Falha na busca semântica: {str(e)}"}
    
    def memory_query(self, query_text: str, limit: int = 5, agent_id: str = None):
        """
        Realiza busca na memória do sistema.
        
        Args:
            query_text: O texto da consulta para busca na memória
            limit: Número máximo de resultados a retornar
            agent_id: ID do agente para filtrar memórias
            
        Returns:
            dict: Resultados da busca na memória
        """
        start_time = time.time()
        try:
            if self._memory_system:
                results = self._memory_system.search(
                    query_text,
                    limit=limit,
                    filter_by={"agent_id": agent_id} if agent_id else None
                )
                # Atualizar estatísticas de acesso
                self._update_access_stats('memory', time.time() - start_time)
                return {"results": results}
            return {"error": "Sistema de memória não disponível"}
        except Exception as e:
            logger.error(f"Erro ao realizar busca na memória: {str(e)}")
            return {"error": f"Falha na busca de memória: {str(e)}"}
    
    def _update_access_stats(self, data_type, time_elapsed):
        """
        Atualiza as estatísticas de acesso para um tipo de dados.
        
        Args:
            data_type: O tipo de dados acessado
            time_elapsed: O tempo gasto na operação
        """
        if data_type in self._access_stats:
            stats = self._access_stats[data_type]
            count = stats["count"] + 1
            avg_time = ((stats["avg_time"] * stats["count"]) + time_elapsed) / count
            self._access_stats[data_type] = {"count": count, "avg_time": avg_time}
    
    def execute_task(self, task):
        """
        Processa uma tarefa relacionada a dados de outro agente.
        
        Este método serve como o ponto de entrada principal para o DataProxyAgent,
        lidando com vários tipos de requisições de dados e encaminhando-as para
        os manipuladores especializados apropriados.
        
        Args:
            task: A tarefa a ser executada, contendo uma descrição da requisição de dados
            
        Returns:
            Resultados da operação de dados
        """
        instruction = task.description
        
        # Registrar a requisição recebida
        logger.info(f"DataProxyAgent recebeu tarefa: {instruction[:100]}...")
        
        # Analisar a requisição para determinar o tipo de operação de dados
        if any(keyword in instruction.lower() for keyword in ["produto", "item", "catálogo"]):
            return self._handle_product_request(instruction)
        
        elif any(keyword in instruction.lower() for keyword in ["cliente", "usuário", "perfil"]):
            return self._handle_customer_request(instruction)
        
        elif any(keyword in instruction.lower() for keyword in ["pedido", "compra", "venda"]):
            return self._handle_order_request(instruction)
        
        elif any(keyword in instruction.lower() for keyword in ["regra", "política", "procedimento"]):
            return self._handle_business_rule_request(instruction)
            
        elif any(keyword in instruction.lower() for keyword in ["memória", "lembrar", "histórico"]):
            return self._handle_memory_request(instruction)
        
        else:
            # Tratamento genérico para outros tipos de requisições de dados
            return self._handle_generic_request(instruction)
    
    # Métodos para compatibilidade com CrewAI
    
    @property
    def role(self):
        """Retorna o papel do agente."""
        return self._crew_agent.role
    
    @property
    def goal(self):
        """Retorna o objetivo do agente."""
        return self._crew_agent.goal
    
    @property
    def backstory(self):
        """Retorna a história de fundo do agente."""
        return self._crew_agent.backstory
    
    @property
    def allow_delegation(self):
        """Retorna se o agente permite delegação."""
        return self._crew_agent.allow_delegation
    
    def get(self, attr, default=None):
        """Método para compatibilidade com dicionários e CrewAI."""
        return getattr(self._crew_agent, attr, default)
    
    def __getitem__(self, key):
        """Implementa acesso como dicionário para compatibilidade com CrewAI."""
        return getattr(self._crew_agent, key)
    
    def keys(self):
        """Retorna as chaves disponíveis, para compatibilidade com dict."""
        return self._crew_agent.__dict__.keys()
    
    @property
    def agent(self):
        """
        Retorna o agente CrewAI interno.
        
        Este é um getter explícito para expor o agente CrewAI interno,
        facilitando o uso em contextos que esperam um Agent do CrewAI.
        """
        return self._crew_agent
