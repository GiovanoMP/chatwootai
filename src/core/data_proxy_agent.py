"""
Data Proxy Agent for the hub-and-spoke architecture.

This module implements a specialized agent that acts as an intermediary between
other agents and data services, providing a unified interface for data access
across different business domains.

The DataProxyAgent is responsible for:
1. Translating natural language requests into structured data queries
2. Applying domain-specific rules and configurations to queries
3. Optimizing data access patterns with caching and batching
4. Providing consistent data formats across different sources
"""

import logging
import time
from typing import Dict, List, Any, Optional, Union, ClassVar, Type
from pydantic import Field

from crewai import Agent
from crewai.tools.base_tool import BaseTool
from crewai.tools.structured_tool import CrewStructuredTool as StructuredTool

# Importando do novo local
from src.core.data_service_hub import DataServiceHub

from src.core.memory import MemorySystem
from src.tools.vector_tools import QdrantVectorSearchTool
from src.tools.database_tools import PGSearchTool
from src.tools.cache_tools import TwoLevelCache

logger = logging.getLogger(__name__)


class DataProxyAgent:
    """
    Agent responsible for intermediating data access for other agents.
    
    This agent serves as a proxy between functional agents and the data services,
    translating high-level data requests into optimized database queries and providing
    a domain-aware data access layer that adapts to the current business domain.
    
    Key responsibilities:
    1. Natural language understanding of data requests
    2. Query optimization and caching strategies
    3. Domain-specific data transformations
    4. Consistent data formatting for agent consumption
    """
    
    # Atributos de classe que não são tratados como campos Pydantic
    _data_service_hub: ClassVar[DataServiceHub]
    _memory_system: ClassVar[Optional[MemorySystem]]
    _access_stats: ClassVar[Dict[str, Any]]
    _crew_agent: ClassVar[Agent]
    
    def __init__(self, 
                 data_service_hub: DataServiceHub,
                 memory_system: Optional[MemorySystem] = None,
                 additional_tools: Optional[List[BaseTool]] = None,
                 **kwargs):
        """
        Initialize the data proxy agent.
        
        Args:
            data_service_hub: Central hub for data services
            memory_system: Shared memory system (optional)
            additional_tools: Additional tools for the agent (optional)
            **kwargs: Additional arguments for the Agent class
        """
        # Armazenar atributos necessários
        self._data_service_hub = data_service_hub
        self._memory_system = memory_system
        
        # Garantir que o memory_system existe e inicializá-lo se não existir
        if self._memory_system is None:
            self._memory_system = MemorySystem()
        
        # Configurar ferramentas
        tools = []
        
        # Adicionar ferramentas adicionais se fornecidas
        if additional_tools:
            tools.extend(additional_tools)
            
        # Default configuration for the data proxy agent
        default_config = {
            "role": "Data Proxy",
            "goal": "Provide efficient and domain-aware data access to all agents",
            "backstory": """You are the data proxy of the hub-and-spoke architecture.
            Your job is to facilitate data access for other agents, translating their
            requests into optimized queries and ensuring they receive data in a 
            consistent format regardless of the underlying data source or business domain.
            You have deep knowledge of data structures, query optimization, and 
            domain-specific schemas.""",
            "verbose": True,
            "allow_delegation": True,
            "tools": tools
        }
        
        # Override defaults with any provided kwargs
        config = {**default_config, **kwargs}
        
        # Criar o agente CrewAI em vez de herdar
        self._crew_agent = Agent(**config)
                
        # Não armazenamos mais referências diretas às ferramentas de dados
        # Agora todo acesso a dados é feito através do DataServiceHub
        
        # Estatísticas de acesso para otimização
        self._access_stats = {
            "products": {"count": 0, "avg_time": 0},
            "customers": {"count": 0, "avg_time": 0},
            "orders": {"count": 0, "avg_time": 0},
            "business_rules": {"count": 0, "avg_time": 0},
        }
    
    @property
    def data_service_hub(self):
        return self.__dict__.get("_data_service_hub")
    
    @property
    def memory_system(self):
        return self.__dict__.get("_memory_system")
    
    # Removemos as propriedades vector_tool, db_tool e cache_tool
    # pois agora todos os acessos a dados são feitos através do DataServiceHub
    
    def get_tools(self) -> List[BaseTool]:
        """
        Retorna as ferramentas disponibilizadas pelo DataProxyAgent para outros agentes.
        
        Estas ferramentas são wrappers em formato compatível com o BaseTool do CrewAI,
        possuindo os atributos 'name', 'func' e 'description'.
        
        Returns:
            List[BaseTool]: Lista de ferramentas para consulta de dados
        """
        # Importamos BaseTool e tool do CrewAI
        from crewai.tools import BaseTool
        from crewai.tools import tool
        from typing import Dict, List, Any, Optional
        from pydantic import BaseModel, Field
        
        # Definir schemas para as ferramentas
        class ProductQueryInput(BaseModel):
            query_text: str = Field(..., description="Texto da consulta sobre produtos")
            filters: Optional[Dict[str, Any]] = Field(None, description="Filtros opcionais para refinar a busca")
            
        class CustomerQueryInput(BaseModel):
            query_text: str = Field(..., description="Texto da consulta sobre clientes")
            filters: Optional[Dict[str, Any]] = Field(None, description="Filtros opcionais para refinar a busca")
            
        class BusinessRulesQueryInput(BaseModel):
            query_text: str = Field(..., description="Texto da consulta sobre regras de negócio")
            category: Optional[str] = Field(None, description="Categoria específica de regras de negócio")
            
        class VectorSearchInput(BaseModel):
            query_text: str = Field(..., description="Texto da consulta para busca semântica")
            collection: Optional[str] = Field(None, description="Coleção específica para busca")
            limit: Optional[int] = Field(5, description="Número máximo de resultados")
        
        # Criando classes de ferramentas que herdam de BaseTool
        
        # Ferramenta de busca de produtos
        class ProductQueryTool(BaseTool):
            name: str = "query_product_data"
            description: str = "Busca informações sobre produtos no catálogo"
            args_schema: type = ProductQueryInput
            
            def _run(self, query_text: str, filters: Optional[Dict[str, Any]] = None) -> str:
                result = self.data_proxy_agent.query_product_data(query_text, filters)
                return str(result)
                
            # Referência para o data_proxy_agent
            data_proxy_agent = self
        
        # Ferramenta de busca de clientes
        class CustomerQueryTool(BaseTool):
            name: str = "query_customer_data"
            description: str = "Busca informações sobre clientes no banco de dados"
            args_schema: type = CustomerQueryInput
            
            def _run(self, query_text: str, filters: Optional[Dict[str, Any]] = None) -> str:
                result = self.data_proxy_agent.query_customer_data(query_text, filters)
                return str(result)
                
            # Referência para o data_proxy_agent
            data_proxy_agent = self
            
        # Ferramenta de busca de regras de negócio
        class BusinessRulesQueryTool(BaseTool):
            name: str = "query_business_rules"
            description: str = "Busca regras de negócio para o domínio atual"
            args_schema: type = BusinessRulesQueryInput
            
            def _run(self, query_text: str, category: Optional[str] = None) -> str:
                result = self.data_proxy_agent.query_business_rules(query_text, category)
                return str(result)
                
            # Referência para o data_proxy_agent
            data_proxy_agent = self
        
        # Ferramenta de busca semântica
        class VectorSearchTool(BaseTool):
            name: str = "vector_search"
            description: str = "Realiza busca semântica em documentos e bases de conhecimento"
            args_schema: type = VectorSearchInput
            
            def _run(self, query_text: str, collection: Optional[str] = None, limit: Optional[int] = 5) -> str:
                result = self.data_proxy_agent.vector_search(query_text, collection, limit)
                return str(result)
                
            # Referência para o data_proxy_agent
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
        
        # Lista de ferramentas que serão disponibilizadas
        tools = [
            product_tool,
            customer_tool,
            business_rules_tool,
            vector_search_tool
        ]
        
        return tools
    
    def query_product_data(self, query_text: str, filters: dict = None):
        """
        Consulta informações sobre produtos no catálogo.
        
        Args:
            query_text (str): O texto da consulta sobre produtos
            filters (dict, optional): Filtros opcionais para refinar a busca
            
        Returns:
            dict: Resultados da consulta de produtos
        """
        start_time = time.time()
        try:
            # Usar o serviço de dados de produtos para realizar a consulta
            if self.data_service_hub:
                service = self.data_service_hub.get_service('ProductDataService')
                if service:
                    results = service.search_products(query_text, filters)
                    # Atualizar estatísticas de acesso
                    self._update_access_stats('products', time.time() - start_time)
                    return results
            return {"error": "Serviço de dados de produtos não disponível"}
        except Exception as e:
            logger.error(f"Erro ao consultar dados de produtos: {str(e)}")
            return {"error": f"Falha na consulta de produtos: {str(e)}"}
    
    def query_customer_data(self, query_text: str, filters: dict = None):
        """
        Consulta informações sobre clientes no banco de dados.
        
        Args:
            query_text (str): O texto da consulta sobre clientes
            filters (dict, optional): Filtros opcionais para refinar a busca
            
        Returns:
            dict: Resultados da consulta de clientes
        """
        start_time = time.time()
        try:
            # Usar o serviço de dados de clientes para realizar a consulta
            if self.data_service_hub:
                service = self.data_service_hub.get_service('CustomerDataService')
                if service:
                    results = service.search_customers(query_text, filters)
                    # Atualizar estatísticas de acesso
                    self._update_access_stats('customers', time.time() - start_time)
                    return results
            return {"error": "Serviço de dados de clientes não disponível"}
        except Exception as e:
            logger.error(f"Erro ao consultar dados de clientes: {str(e)}")
            return {"error": f"Falha na consulta de clientes: {str(e)}"}
    
    def query_business_rules(self, domain: str = None, rule_type: str = None):
        """
        Consulta regras de negócio para o domínio atual ou especificado.
        
        Args:
            domain (str, optional): O domínio específico para consultar regras
            rule_type (str, optional): O tipo específico de regra a ser consultado
            
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
                    domain = domain or service.get_active_domain()
                    rules = service.get_domain_rules(domain, rule_type)
                    # Atualizar estatísticas de acesso
                    self._update_access_stats('business_rules', time.time() - start_time)
                    return rules
            return {"error": "Serviço de regras de domínio não disponível"}
        except Exception as e:
            logger.error(f"Erro ao consultar regras de negócio: {str(e)}")
            return {"error": f"Falha na consulta de regras de negócio: {str(e)}"}
    
    def vector_search(self, query_text: str, collection_name: str = None, limit: int = 5):
        """
        Realiza busca semântica em documentos e bases de conhecimento.
        
        Args:
            query_text (str): O texto da consulta para busca semântica
            collection_name (str, optional): Nome da coleção específica para buscar
            limit (int, optional): Número máximo de resultados a retornar
            
        Returns:
            dict: Resultados da busca semântica
        """
        try:
            # Usar o cliente Qdrant do DataServiceHub para realizar a consulta
            if self.data_service_hub and hasattr(self.data_service_hub, 'vector_tool'):
                results = self.data_service_hub.vector_tool.search(
                    query_text,
                    collection_name=collection_name,
                    limit=limit
                )
                return {"results": results}
            return {"error": "Ferramenta de busca vetorial não disponível"}
        except Exception as e:
            logger.error(f"Erro ao realizar busca semântica: {str(e)}")
            return {"error": f"Falha na busca semântica: {str(e)}"}
    
    def _update_access_stats(self, data_type, time_elapsed):
        """
        Atualiza as estatísticas de acesso para um tipo de dados.
        
        Args:
            data_type (str): O tipo de dados acessado
            time_elapsed (float): O tempo gasto na operação
        """
        if data_type in self._access_stats:
            stats = self._access_stats[data_type]
            count = stats["count"] + 1
            avg_time = ((stats["avg_time"] * stats["count"]) + time_elapsed) / count
            self._access_stats[data_type] = {"count": count, "avg_time": avg_time}
    
    def execute_task(self, task):
        """
        Process a data-related task from another agent.
        
        This method serves as the main entry point for the DataProxyAgent,
        handling various types of data requests and routing them to the
        appropriate specialized handlers.
        
        Args:
            task: The task to execute, containing a description of the data request
            
        Returns:
            Results of the data operation
        """
        instruction = task.description
        
        # Log the incoming request
        logger.info(f"DataProxyAgent received task: {instruction[:100]}...")
        
        # Parse the request to determine the type of data operation
        if any(keyword in instruction.lower() for keyword in ["produto", "item", "catálogo"]):
            return self._handle_product_request(instruction)
        
        elif any(keyword in instruction.lower() for keyword in ["cliente", "usuário", "perfil"]):
            return self._handle_customer_request(instruction)
        
        elif any(keyword in instruction.lower() for keyword in ["pedido", "compra", "venda"]):
            return self._handle_order_request(instruction)
        
        elif any(keyword in instruction.lower() for keyword in ["regra", "política", "procedimento"]):
            return self._handle_business_rule_request(instruction)
        
        else:
            # Generic handling for other types of data requests
            return self._handle_generic_request(instruction)
    
    def fetch_data(self, data_type: str, query_params: Dict[str, Any], context: Optional[Dict[str, Any]] = None):
        """
        Fetch data from the appropriate data service based on type.
        
        This method provides a unified interface for data retrieval across different
        data types, handling the routing to specific services, monitoring performance,
        and applying caching strategies.
        
        Args:
            data_type: Type of data to fetch (product, customer, order, business_rule)
            query_params: Parameters for the query
            context: Additional context for the query (optional)
            
        Returns:
            The requested data
        """
        # Record starting time for performance monitoring
        start_time = time.time()
        
        # Verificar cache usando o DataServiceHub
        cache_key = f"{data_type}:{hash(str(query_params))}"
        # Usar os métodos de cache do DataServiceHub
        cached_data = self.data_service_hub.cache_get(cache_key, data_type)
        if cached_data:
            logger.info(f"Cache hit for {data_type} query")
            return cached_data
        
        try:
            # Route to the appropriate service
            if data_type == "product":
                result = self.data_service_hub.product_data_service.search_products(**query_params)
            
            elif data_type == "customer":
                result = self.data_service_hub.customer_data_service.search_customers(**query_params)
            
            elif data_type == "order":
                result = self.data_service_hub.order_data_service.search_orders(**query_params)
            
            elif data_type == "business_rule":
                result = self.data_service_hub.business_rule_service.get_rules(**query_params)
            
            else:
                # Generic query through the hub
                result = self.data_service_hub.query(data_type, query_params, context)
            
            # Armazenar o resultado no cache através do DataServiceHub
            if result:
                # Definir tempo de expiração com base no tipo de dados
                expiration = {
                    "product": 3600,  # 1 hora para produtos
                    "customer": 300,  # 5 minutos para clientes
                    "order": 600,     # 10 minutos para pedidos
                    "business_rule": 1800  # 30 minutos para regras de negócio
                }.get(data_type, 600)  # 10 minutos por padrão
                
                # Usar o método de cache do DataServiceHub
                self.data_service_hub.cache_set(cache_key, result, data_type, expiration)
            
            # Update access statistics
            elapsed = time.time() - start_time
            stats = self._access_stats.get(f"{data_type}s", {"count": 0, "avg_time": 0})
            stats["count"] += 1
            stats["avg_time"] = ((stats["avg_time"] * (stats["count"] - 1)) + elapsed) / stats["count"]
            
            logger.info(f"Data fetch for {data_type} completed in {elapsed:.3f}s")
            
            return result
            
        except Exception as e:
            logger.error(f"Error fetching {data_type} data: {str(e)}")
            # Return structured error response
            return {
                "error": True,
                "message": str(e),
                "data_type": data_type,
                "query_params": query_params
            }
    
    def _handle_product_request(self, instruction: str):
        """
        Handle requests related to products.
        
        Args:
            instruction: Natural language instruction describing the product request
            
        Returns:
            Product data matching the request
        """
        # Extract query parameters from the instruction
        query_params = self._extract_product_params(instruction)
        
        # Log for debugging
        logger.debug(f"Extracted product query params: {query_params}")
        
        # Fetch product data
        return self.fetch_data("product", query_params)
    
    def _handle_customer_request(self, instruction: str):
        """
        Handle requests related to customers.
        
        Args:
            instruction: Natural language instruction describing the customer request
            
        Returns:
            Customer data matching the request
        """
        # Extract query parameters from the instruction
        query_params = self._extract_customer_params(instruction)
        
        # Log for debugging
        logger.debug(f"Extracted customer query params: {query_params}")
        
        # Fetch customer data
        return self.fetch_data("customer", query_params)
    
    def _handle_order_request(self, instruction: str):
        """
        Handle requests related to orders.
        
        Args:
            instruction: Natural language instruction describing the order request
            
        Returns:
            Order data matching the request
        """
        # Extract query parameters from the instruction
        query_params = self._extract_order_params(instruction)
        
        # Log for debugging
        logger.debug(f"Extracted order query params: {query_params}")
        
        # Fetch order data
        return self.fetch_data("order", query_params)
    
    def _handle_business_rule_request(self, instruction: str):
        """
        Handle requests related to business rules.
        
        Args:
            instruction: Natural language instruction describing the rule request
            
        Returns:
            Business rule data matching the request
        """
        # Extract query parameters from the instruction
        query_params = self._extract_rule_params(instruction)
        
        # Log for debugging
        logger.debug(f"Extracted business rule query params: {query_params}")
        
        # Fetch business rule data
        return self.fetch_data("business_rule", query_params)
    
    def _handle_generic_request(self, instruction: str):
        """
        Handle generic data requests that don't fit into specific categories.
        
        Args:
            instruction: Natural language instruction describing the data request
            
        Returns:
            Data matching the request
        """
        # This would typically use more advanced NLP to determine intent
        # For now, we provide a simplified implementation
        
        # Extract basic parameters
        words = instruction.lower().split()
        data_type = None
        
        # Attempt to identify the data type from the instruction
        for word in words:
            if word in self.data_service_hub.available_services:
                data_type = word
                break
        
        if not data_type:
            return {
                "error": True,
                "message": "Could not determine data type from instruction",
                "instruction": instruction
            }
        
        # For generic requests, we use a simple keyword-based approach
        query_params = {
            "query": instruction,
            "limit": 10  # Default limit
        }
        
        return self.fetch_data(data_type, query_params)
    
    def _extract_product_params(self, instruction: str) -> Dict[str, Any]:
        """
        Extract product search parameters from a natural language instruction.
        
        In a full implementation, this would use NLP capabilities to parse
        parameters from the instruction. For this example, we use a simplified
        keyword-based approach.
        
        Args:
            instruction: Natural language instruction
            
        Returns:
            Dictionary of query parameters
        """
        params = {"query": instruction, "limit": 10}
        
        # Extract common product parameters
        instruction_lower = instruction.lower()
        
        # Name matching
        if "nome" in instruction_lower or "chamado" in instruction_lower:
            # Extract name after relevant keywords
            name_patterns = ["nome", "chamado", "produto"]
            for pattern in name_patterns:
                if pattern in instruction_lower:
                    pos = instruction_lower.find(pattern) + len(pattern)
                    name_part = instruction[pos:pos+50].strip()
                    if name_part:
                        params["name"] = name_part.split()[0] if name_part.split() else ""
        
        # Price range
        if "preço" in instruction_lower or "valor" in instruction_lower:
            if "menor que" in instruction_lower or "abaixo de" in instruction_lower:
                # Extract number after these patterns
                for pattern in ["menor que", "abaixo de"]:
                    if pattern in instruction_lower:
                        pos = instruction_lower.find(pattern) + len(pattern)
                        price_text = instruction[pos:pos+20].strip()
                        try:
                            # Extract numeric part
                            price = ''.join(filter(lambda x: x.isdigit() or x == '.', price_text))
                            params["max_price"] = float(price) if price else None
                        except ValueError:
                            pass
            
            if "maior que" in instruction_lower or "acima de" in instruction_lower:
                # Extract number after these patterns
                for pattern in ["maior que", "acima de"]:
                    if pattern in instruction_lower:
                        pos = instruction_lower.find(pattern) + len(pattern)
                        price_text = instruction[pos:pos+20].strip()
                        try:
                            # Extract numeric part
                            price = ''.join(filter(lambda x: x.isdigit() or x == '.', price_text))
                            params["min_price"] = float(price) if price else None
                        except ValueError:
                            pass
        
        # Categories
        categories = []
        category_indicators = ["categoria", "tipo", "departamento"]
        for indicator in category_indicators:
            if indicator in instruction_lower:
                pos = instruction_lower.find(indicator) + len(indicator)
                category_text = instruction[pos:pos+30].strip()
                if category_text:
                    categories.append(category_text.split()[0] if category_text.split() else "")
        
        if categories:
            params["categories"] = categories
        
        return params
    
    def _extract_customer_params(self, instruction: str) -> Dict[str, Any]:
        """
        Extract customer search parameters from a natural language instruction.
        
        Args:
            instruction: Natural language instruction
            
        Returns:
            Dictionary of query parameters
        """
        params = {"query": instruction, "limit": 10}
        
        # Extract common customer parameters
        instruction_lower = instruction.lower()
        
        # Name matching
        if "nome" in instruction_lower:
            pos = instruction_lower.find("nome") + 4
            name_part = instruction[pos:pos+50].strip()
            if name_part:
                params["name"] = name_part.split()[0] if name_part.split() else ""
        
        # Email matching
        if "email" in instruction_lower:
            pos = instruction_lower.find("email") + 5
            email_part = instruction[pos:pos+50].strip()
            if email_part:
                params["email"] = email_part.split()[0] if email_part.split() else ""
        
        # Phone matching
        if "telefone" in instruction_lower or "celular" in instruction_lower:
            for pattern in ["telefone", "celular"]:
                if pattern in instruction_lower:
                    pos = instruction_lower.find(pattern) + len(pattern)
                    phone_part = instruction[pos:pos+20].strip()
                    if phone_part:
                        # Extract only digits
                        phone = ''.join(filter(lambda x: x.isdigit(), phone_part))
                        if phone:
                            params["phone"] = phone
                            break
        
        return params
    
    def _extract_order_params(self, instruction: str) -> Dict[str, Any]:
        """
        Extract order search parameters from a natural language instruction.
        
        Args:
            instruction: Natural language instruction
            
        Returns:
            Dictionary of query parameters
        """
        params = {"query": instruction, "limit": 10}
        
        # Extract common order parameters
        instruction_lower = instruction.lower()
        
        # Order ID
        id_indicators = ["pedido", "número", "código"]
        for indicator in id_indicators:
            if indicator in instruction_lower:
                pos = instruction_lower.find(indicator) + len(indicator)
                id_part = instruction[pos:pos+20].strip()
                if id_part:
                    # Extract only digits
                    order_id = ''.join(filter(lambda x: x.isdigit(), id_part))
                    if order_id:
                        params["order_id"] = order_id
                        break
        
        # Status
        status_mapping = {
            "pendente": "pending",
            "em processamento": "processing",
            "enviado": "shipped",
            "entregue": "delivered",
            "cancelado": "cancelled"
        }
        
        for pt_status, en_status in status_mapping.items():
            if pt_status in instruction_lower:
                params["status"] = en_status
                break
        
        # Date range
        date_indicators = {
            "depois de": "min_date",
            "após": "min_date",
            "antes de": "max_date",
            "até": "max_date"
        }
        
        for indicator, param_name in date_indicators.items():
            if indicator in instruction_lower:
                pos = instruction_lower.find(indicator) + len(indicator)
                date_part = instruction[pos:pos+20].strip()
                if date_part:
                    # In a real implementation, we would use more sophisticated
                    # date parsing here. For simplicity, we're just capturing
                    # the raw text.
                    params[param_name] = date_part
        
        return params
    
    def _extract_rule_params(self, instruction: str) -> Dict[str, Any]:
        """
        Extract business rule search parameters from a natural language instruction.
        
        Args:
            instruction: Natural language instruction
            
        Returns:
            Dictionary of query parameters
        """
        params = {"query": instruction, "limit": 10}
        
        # Extract common business rule parameters
        instruction_lower = instruction.lower()
        
        # Category
        category_indicators = ["categoria", "tipo", "classe"]
        for indicator in category_indicators:
            if indicator in instruction_lower:
                pos = instruction_lower.find(indicator) + len(indicator)
                category_part = instruction[pos:pos+30].strip()
                if category_part:
                    params["category"] = category_part.split()[0] if category_part.split() else ""
                    break
        
        # Active rules only
        if "ativo" in instruction_lower or "vigente" in instruction_lower:
            params["active_only"] = True
        
        return params
        
    # Métodos que delegam para o CrewAI Agent interno
    def execute_task(self, task):
        """Delega a execução de uma tarefa para o agente CrewAI interno"""
        return self._crew_agent.execute_task(task)
    
    @property
    def role(self):
        """Retorna o papel do agente"""
        return self._crew_agent.role
    
    @property
    def goal(self):
        """Retorna o objetivo do agente"""
        return self._crew_agent.goal
    
    @property
    def backstory(self):
        """Retorna a história de fundo do agente"""
        return self._crew_agent.backstory
    
    @property
    def allow_delegation(self):
        """Retorna se o agente permite delegação"""
        return self._crew_agent.allow_delegation
        
    def get(self, attr, default=None):
        """Método para compatibilidade com dicionários e CrewAI"""
        # Primeiro tenta acessar o atributo no próprio objeto
        if hasattr(self, attr):
            return getattr(self, attr)
        # Depois tenta acessar no _crew_agent
        elif hasattr(self._crew_agent, attr):
            return getattr(self._crew_agent, attr)
        # Finalmente retorna o valor padrão
        return default
    
    def __getitem__(self, key):
        """Implementa acesso como dicionário para compatibilidade com CrewAI"""
        return self.get(key)
        
    def keys(self):
        """Retorna as chaves disponíveis, para compatibilidade com dict"""
        # Combina atributos do objeto e do _crew_agent
        keys = set(dir(self))
        if hasattr(self, '_crew_agent'):
            keys.update(dir(self._crew_agent))
        return [k for k in keys if not k.startswith('_')]
        
    @property
    def agent(self):
        """Retorna o agente CrewAI interno
        
        Este é um getter explícito para expor o agente CrewAI interno,
        facilitando o uso em contextos que esperam um Agent do CrewAI.
        """
        return self._crew_agent
