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
from typing import Dict, List, Any, Optional, Union

from crewai import Agent
from crewai.tools.base_tool import BaseTool

from src.core.memory import MemorySystem
from src.services.data.data_service_hub import DataServiceHub
from src.tools.vector_tools import QdrantVectorSearchTool
from src.tools.database_tools import PGSearchTool
from src.tools.cache_tools import TwoLevelCache

logger = logging.getLogger(__name__)


class DataProxyAgent(Agent):
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
        
        super().__init__(**config)
        
        # Armazenar atributos necessários
        self.__dict__["_data_service_hub"] = data_service_hub
        self.__dict__["_memory_system"] = memory_system
        
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
