"""
Hub Agents for the hub-and-spoke architecture.

This module implements specialized agents for the central orchestration layer (HubCrew),
which is responsible for routing messages between communication channels and functional crews.

The hub-and-spoke architecture follows these principles:
1. Direct routing: Messages are routed directly to specialized crews without unnecessary intermediaries
2. Centralized coordination: The orchestrator maintains global state and coordinates between crews
3. Decoupled components: Each crew operates independently, communicating via well-defined interfaces
4. Scalable design: Components can scale independently based on load requirements
5. Resilient operation: Failures in one component don't compromise the entire system
"""

import logging
from typing import Dict, List, Any, Optional, Union
import json
import datetime

from crewai import Agent, Task, Crew
# Importamos nossa própria implementação de RedisAgentCache
from src.core.cache.agent_cache import RedisAgentCache

from crewai.tools.base_tool import BaseTool

from src.core.memory import MemorySystem
# Nova estrutura com componentes centralizados em src/core
from src.core.data_proxy_agent import DataProxyAgent
from src.core.data_service_hub import DataServiceHub
from src.core.domain.domain_manager import DomainManager
from src.core.crews.crew_factory import CrewFactory, get_crew_factory
from src.plugins.core.plugin_manager import PluginManager

logger = logging.getLogger(__name__)


def normalize_message(message: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normaliza uma mensagem para um formato padrão.
    
    Args:
        message: A mensagem a ser normalizada
    
    Returns:
        A mensagem normalizada
    """
    # Implementação da normalização de mensagens
    # Por exemplo, converter todos os campos para minúsculas
    normalized_message = {key.lower(): value for key, value in message.items()}
    return normalized_message


def validate_message(message: Dict[str, Any]) -> bool:
    """
    Valida se uma mensagem está no formato correto.
    
    Args:
        message: A mensagem a ser validada
    
    Returns:
        True se a mensagem for válida, False caso contrário
    """
    # Implementação da validação de mensagens
    # Por exemplo, verificar se a mensagem tem os campos obrigatórios
    required_fields = ["id", "content", "sender_id"]
    for field in required_fields:
        if field not in message:
            return False
    return True


class OrchestratorAgent(Agent):
    """
    Agent responsible for orchestrating the flow of information between crews.
    
    This agent is the central component of the hub-and-spoke architecture, analyzing
    incoming messages and routing them to the appropriate functional crew based on:
    1. Message content and intent analysis
    2. Conversation context and history
    3. Customer profile and preferences
    4. Current system load and availability
    
    The orchestrator maintains a high-level view of all active conversations and
    ensures efficient distribution of work across the system.
    """
    
    def __init__(self, 
                 memory_system: Optional[MemorySystem] = None,
                 data_proxy_agent: Optional[DataProxyAgent] = None,
                 additional_tools: Optional[List[BaseTool]] = None,
                 crew_registry: Optional[Dict[str, Any]] = None,
                 **kwargs):
        """
        Initialize the orchestrator agent.
        
        Args:
            memory_system: Shared memory system (optional)
            data_proxy_agent: Agent for data access (optional)
            additional_tools: Additional tools for the agent (optional)
            crew_registry: Dictionary mapping crew names to crew instances (optional)
            **kwargs: Additional arguments for the Agent class
        """
        tools = []
        
        # Adicionar data_proxy_agent como ferramenta se fornecido
        if data_proxy_agent:
            # Não adicionamos o data_proxy_agent diretamente às ferramentas,
            # mas o mantemos como um atributo para chamadas de método
            pass
        
        if additional_tools:
            tools.extend(additional_tools)
        
        # Default configuration for the orchestrator agent
        default_config = {
            "role": "Chief Orchestrator",
            "goal": "Efficiently route messages to the appropriate functional crews based on content analysis",
            "backstory": """You are the central orchestrator of the hub-and-spoke architecture.
            Your job is to analyze incoming messages, understand their intent and context,
            and route them to the appropriate functional crew for processing.
            You have a deep understanding of each functional crew's capabilities and responsibilities.""",
            "verbose": True,
            "allow_delegation": True,
            "tools": tools
        }
        
        # Override defaults with any provided kwargs
        config = {**default_config, **kwargs}
        
        super().__init__(**config)
        
        # Armazenar atributos necessários para os testes
        # Estes não são usados pelo Pydantic, então não causarão problemas
        self.__dict__["_memory_system"] = memory_system
        self.__dict__["_data_proxy_agent"] = data_proxy_agent
        self.__dict__["_crew_registry"] = crew_registry or {}
        self.__dict__["agent_cache"] = None  # Inicializado como None, será definido nos testes
    
    @property
    def memory_system(self):
        return self.__dict__["_memory_system"]
    
    @property
    def data_proxy_agent(self):
        return self.__dict__["_data_proxy_agent"]
    
    @property
    def crew_registry(self):
        return self.__dict__["_crew_registry"]
    
    def route_message(self, message: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Route a message to the appropriate functional crew.
        
        This is the core routing function that determines which specialized crew
        should handle a specific message based on content analysis and context.
        
        Args:
            message: The message to route (contains content, sender info, etc.)
            context: Additional context for routing (conversation history, channel type, etc.)
            
        Returns:
            Routing decision with crew, reasoning, and confidence level
        """
        logger.debug(f"Roteando mensagem: {message}")
        # Normaliza a mensagem
        normalized_message = normalize_message(message)
        
        # Valida a mensagem
        if not validate_message(normalized_message):
            raise ValueError('Mensagem inválida')
        
        # Check cache first for performance optimization if agent_cache is available
        message_id = normalized_message.get('id', '')
        agent_id = f"orchestrator:{self.role}"
        input_data = json.dumps({"message": normalized_message, "context": context})
        cached_route = None
        
        if "agent_cache" in self.__dict__ and self.__dict__["agent_cache"]:
            cached_route = self.__dict__["agent_cache"].get(agent_id, input_data)
            # Não precisamos fazer json.loads aqui, pois o método get já retorna um dicionário
            if cached_route:
                logger.info(f"Cache hit para {agent_id}")
        
        if cached_route:
            logger.info(f"Usando rota em cache para a mensagem {normalized_message.get('id', '')}")
            return cached_route
        
        # Se não há cache, use o método de roteamento com LLM
        logger.debug(f"Iniciando roteamento com LLM para a mensagem: {message}")
        result = self._route_with_llm(normalized_message, context)
        logger.info(f"Roteamento concluído para a mensagem {message.get('id', '')}")
        
        # Cache the result for future use if agent_cache is available
        if "agent_cache" in self.__dict__ and self.__dict__["agent_cache"]:
            try:
                self.__dict__["agent_cache"].set(agent_id, input_data, result)
            except Exception as e:
                logger.error(f"Error caching route: {e}")
        
        return result
    
    def _route_with_llm(self, message: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Roteamento usando LLM quando não há cache disponível.
        
        Args:
            message: A mensagem a ser roteada
            context: Contexto adicional para roteamento
            
        Returns:
            Decisão de roteamento com crew, raciocínio e nível de confiança
        """
        # Analyze message content and context to determine intent
        # This is a simplified implementation - in a real system, this would use
        # more sophisticated NLP techniques and potentially call an LLM
        
        # Extract key information from message and context
        message_content = message.get("content", "").lower()
        channel_type = context.get("channel_type", "unknown")
        customer_id = context.get("customer_id")
        
        # Load customer history if available
        customer_history = {}
        if customer_id and self.memory_system:
            customer_history = self.memory_system.retrieve_customer_data(customer_id)
        
        # Use DataProxyAgent para encontrar interações similares, se disponível
        similar_interactions = []
        if self.data_proxy_agent and message_content:
            # Usar o data_proxy_agent para buscar interações similares
            query_params = {
                "query": message_content,
                "limit": 3
            }
            result = self.data_proxy_agent.fetch_data("similar_interactions", query_params)
            if result and not isinstance(result, dict) and not result.get("error", False):
                similar_interactions = result
        
        # Determine which crew should handle this message
        # This is a simplified routing logic - in a real system, this would be more complex
        
        # Default values
        selected_crew = "sales"
        confidence = 0.5
        reasoning = "Default routing to sales crew"
        
        # Check for sales-related keywords
        sales_keywords = ["buy", "price", "cost", "purchase", "order", "discount"]
        if any(keyword in message_content for keyword in sales_keywords):
            selected_crew = "sales"
            confidence = 0.8
            reasoning = "Message contains sales-related keywords"
        
        # Check for support-related keywords
        support_keywords = ["help", "issue", "problem", "broken", "not working", "error"]
        if any(keyword in message_content for keyword in support_keywords):
            selected_crew = "support"
            confidence = 0.8
            reasoning = "Message contains support-related keywords"
        
        # Check for product-related keywords
        product_keywords = ["product", "feature", "specification", "specs", "details"]
        if any(keyword in message_content for keyword in product_keywords):
            selected_crew = "product"
            confidence = 0.7
            reasoning = "Message contains product-related keywords"
        
        # Adjust based on customer history if available
        if customer_history:
            # If customer has recent support interactions, route to support
            if customer_history.get("recent_support_tickets", 0) > 0:
                if confidence < 0.9:  # Only override if not very confident
                    selected_crew = "support"
                    confidence = 0.6
                    reasoning = "Customer has recent support tickets"
            
            # If customer has recent purchases, route to sales
            if customer_history.get("recent_purchases", 0) > 0:
                if confidence < 0.7:  # Only override if not confident
                    selected_crew = "sales"
                    confidence = 0.6
                    reasoning = "Customer has recent purchases"
        
        # Create routing result
        routing_result = {
            "crew": selected_crew,
            "confidence": confidence,
            "reasoning": reasoning
        }
        
        logger.info(f"Roteamento da mensagem {message.get('id', '')} para a crew funcional")
        return routing_result


class ContextManagerAgent(Agent):
    """
    Agent responsible for managing context across conversations.
    
    This agent maintains and updates the context of conversations,
    ensuring that all agents have access to relevant information.
    """
    
    def __init__(self, 
                 memory_system: Optional[MemorySystem] = None,
                 data_proxy_agent: Optional[DataProxyAgent] = None,
                 additional_tools: Optional[List[BaseTool]] = None,
                 **kwargs):
        """
        Initialize the context manager agent.
        
        Args:
            memory_system: Shared memory system (optional)
            data_proxy_agent: Agent for data access (optional)
            additional_tools: Additional tools for the agent (optional)
            **kwargs: Additional arguments for the Agent class
        """
        tools = []
        
        # Adicionar data_proxy_agent como ferramenta se fornecido
        if data_proxy_agent:
            # Não adicionamos o data_proxy_agent diretamente às ferramentas,
            # mas o mantemos como um atributo para chamadas de método
            pass
        
        if additional_tools:
            tools.extend(additional_tools)
        
        # Default configuration for the context manager agent
        default_config = {
            "role": "Context Manager",
            "goal": "Maintain and update conversation context to ensure coherent and relevant interactions",
            "backstory": """You are the context manager of the hub-and-spoke architecture.
            Your job is to maintain and update the context of conversations,
            ensuring that all agents have access to relevant information.
            You have a deep understanding of conversation flow and context management.""",
            "verbose": True,
            "allow_delegation": True,
            "tools": tools
        }
        
        # Override defaults with any provided kwargs
        config = {**default_config, **kwargs}
        
        super().__init__(**config)
        
        # Armazenar atributos necessários
        self.__dict__["_memory_system"] = memory_system
        self.__dict__["_data_proxy_agent"] = data_proxy_agent
    
    @property
    def memory_system(self):
        return self.__dict__["_memory_system"]
    
    @property
    def data_proxy_agent(self):
        return self.__dict__["_data_proxy_agent"]
    
    def update_context(self, 
                      conversation_id: str, 
                      message: Dict[str, Any],
                      current_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update the context of a conversation.
        
        Args:
            conversation_id: ID of the conversation
            message: New message in the conversation
            current_context: Current context of the conversation
            
        Returns:
            Updated context
        """
        # Extract key information from the message
        message_content = message.get("content", "")
        sender_id = message.get("sender_id", "")
        timestamp = message.get("timestamp", "")
        
        # Update the context with the new message
        updated_context = current_context.copy()
        
        # Add the new message to the message history
        if "message_history" not in updated_context:
            updated_context["message_history"] = []
        
        updated_context["message_history"].append({
            "content": message_content,
            "sender_id": sender_id,
            "timestamp": timestamp
        })
        
        # Limit the message history to the last 10 messages
        updated_context["message_history"] = updated_context["message_history"][-10:]
        
        # Update the last message information
        updated_context["last_message"] = {
            "content": message_content,
            "sender_id": sender_id,
            "timestamp": timestamp
        }
        
        # Extract entities and intents from the message
        # This is a simplified implementation - in a real system, this would use
        # more sophisticated NLP techniques
        
        # Extract entities (simplified)
        entities = []
        
        # Check for product mentions
        product_keywords = ["product", "item", "goods"]
        if any(keyword in message_content.lower() for keyword in product_keywords):
            entities.append({"type": "product", "value": "unknown"})
        
        # Check for location mentions
        location_keywords = ["location", "address", "city", "country"]
        if any(keyword in message_content.lower() for keyword in location_keywords):
            entities.append({"type": "location", "value": "unknown"})
        
        # Update entities in the context
        if entities:
            if "entities" not in updated_context:
                updated_context["entities"] = []
            
            updated_context["entities"].extend(entities)
        
        # Store the updated context in the memory system
        if self.memory_system:
            self.memory_system.store_conversation_context(conversation_id, updated_context)
        
        return updated_context


class IntegrationAgent(Agent):
    """
    Agent responsible for integrating with external systems.
    
    This agent handles the integration with external systems like Odoo,
    retrieving and updating information as needed.
    """
    
    def __init__(self, 
                 memory_system: Optional[MemorySystem] = None,
                 data_proxy_agent: Optional[DataProxyAgent] = None,
                 additional_tools: Optional[List[BaseTool]] = None,
                 **kwargs):
        """
        Initialize the integration agent.
        
        Args:
            memory_system: Shared memory system (optional)
            data_proxy_agent: Agent for data access across different services (optional)
            additional_tools: Additional tools for the agent (optional)
            **kwargs: Additional arguments for the Agent class
        """
        tools = []
        
        if additional_tools:
            tools.extend(additional_tools)
        
        # Default configuration for the integration agent
        default_config = {
            "role": "System Integrator",
            "goal": "Seamlessly integrate with external systems to retrieve and update information",
            "backstory": """You are the system integrator of the hub-and-spoke architecture.
            Your job is to handle the integration with external systems like Odoo,
            retrieving and updating information as needed.
            You have a deep understanding of APIs and data integration.""",
            "verbose": True,
            "allow_delegation": True,
            "tools": tools
        }
        
        # Override defaults with any provided kwargs
        config = {**default_config, **kwargs}
        
        super().__init__(**config)
        
        # Armazenar atributos necessários
        self.__dict__["_memory_system"] = memory_system
        self.__dict__["_data_proxy_agent"] = data_proxy_agent
    
    @property
    def memory_system(self):
        return self.__dict__["_memory_system"]
    
    @property
    def data_proxy_agent(self):
        return self.__dict__["_data_proxy_agent"]
    
    def fetch_customer_data(self, customer_id: str) -> Dict[str, Any]:
        """
        Fetch customer data from the external system.
        
        Args:
            customer_id: ID of the customer
            
        Returns:
            Customer data
        """
        # Usar o DataProxyAgent para buscar dados do cliente
        if self.data_proxy_agent:
            # Preparar os parâmetros da consulta
            query_params = {
                "customer_id": customer_id
            }
            
            # Buscar os dados usando o DataProxyAgent
            result = self.data_proxy_agent.fetch_data("customer", query_params)
            
            # Verificar se o resultado é válido
            if result and not isinstance(result, dict) or not result.get("error", False):
                logger.info(f"Retrieved customer data for {customer_id} via DataProxyAgent")
                return result
        
        # Caso o DataProxyAgent não esteja disponível ou falhe, usar implementação de fallback
        logger.warning(f"Using fallback method to fetch customer data for {customer_id}")
        
        # Simulate fetching customer data (implementação simplificada como fallback)
        customer_data = {
            "id": customer_id,
            "name": f"Customer {customer_id}",
            "email": f"customer{customer_id}@example.com",
            "phone": f"+1-555-{customer_id}-0000",
            "address": "123 Main St, Anytown, USA",
            "created_at": "2023-01-01T00:00:00Z",
            "last_purchase": "2023-06-15T00:00:00Z",
            "total_purchases": 5,
            "loyalty_tier": "silver",
            "preferences": {
                "communication_channel": "email",
                "product_categories": ["electronics", "home appliances"]
            }
        }
        
        return customer_data
    
    def fetch_product_data(self, product_id: str) -> Dict[str, Any]:
        """
        Fetch product data from the external system.
        
        Args:
            product_id: ID of the product
            
        Returns:
            Product data
        """
        # Usar o DataProxyAgent para buscar dados do produto
        if self.data_proxy_agent:
            # Preparar os parâmetros da consulta
            query_params = {
                "product_id": product_id
            }
            
            # Buscar os dados usando o DataProxyAgent
            result = self.data_proxy_agent.fetch_data("product", query_params)
            
            # Verificar se o resultado é válido
            if result and not isinstance(result, dict) or not result.get("error", False):
                logger.info(f"Retrieved product data for {product_id} via DataProxyAgent")
                return result
        
        # Caso o DataProxyAgent não esteja disponível ou falhe, usar implementação de fallback
        logger.warning(f"Using fallback method to fetch product data for {product_id}")
        
        # Simulate fetching product data (implementação simplificada como fallback)
        product_data = {
            "id": product_id,
            "name": f"Product {product_id}",
            "description": f"This is product {product_id}",
            "price": 99.99,
            "category": "electronics",
            "in_stock": True,
            "stock_level": 42,
            "features": [
                "Feature 1",
                "Feature 2",
                "Feature 3"
            ],
            "specifications": {
                "weight": "1.5 kg",
                "dimensions": "10 x 20 x 5 cm",
                "color": "black"
            }
        }
        
        return product_data
    
    def fetch_business_rules(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Fetch business rules from the external system.
        
        Args:
            category: Optional category filter
            
        Returns:
            List of business rules
        """
        # Usar o DataProxyAgent para buscar regras de negócio
        if self.data_proxy_agent:
            # Preparar os parâmetros da consulta
            query_params = {}
            if category:
                query_params["category"] = category
            
            # Buscar os dados usando o DataProxyAgent
            result = self.data_proxy_agent.fetch_data("business_rule", query_params)
            
            # Verificar se o resultado é válido
            if result and not isinstance(result, dict) or not result.get("error", False):
                logger.info(f"Retrieved business rules for {category or 'all'} via DataProxyAgent")
                return result
        
        # Caso o DataProxyAgent não esteja disponível ou falhe, usar implementação de fallback
        logger.warning(f"Using fallback method to fetch business rules for {category or 'all'}")
        
        # Simulate fetching business rules (implementação simplificada como fallback)
        all_rules = [
            {
                "id": "rule1",
                "category": "pricing",
                "name": "Bulk Discount",
                "description": "Apply 10% discount for orders over $1000",
                "condition": "order_total > 1000",
                "action": "apply_discount(0.1)",
                "priority": 1
            },
            {
                "id": "rule2",
                "category": "shipping",
                "name": "Free Shipping",
                "description": "Free shipping for orders over $50",
                "condition": "order_total > 50",
                "action": "set_shipping_cost(0)",
                "priority": 2
            },
            {
                "id": "rule3",
                "category": "loyalty",
                "name": "Loyalty Points",
                "description": "Award 1 loyalty point per $10 spent",
                "condition": "customer.is_registered",
                "action": "award_points(order_total / 10)",
                "priority": 3
            }
        ]
        
        # Filter by category if provided
        if category:
            filtered_rules = [rule for rule in all_rules if rule["category"] == category]
        else:
            filtered_rules = all_rules
            
        return filtered_rules


class HubCrew(Crew):
    """
    Crew responsible for orchestrating interactions between channel crews and functional crews.
    
    This crew is the central orchestration layer of the hub-and-spoke architecture,
    providing the following key functions:
    
    1. Message Routing: Analyzes incoming messages and routes them to appropriate functional crews
    2. Context Management: Maintains conversation context and history across interactions
    3. System Integration: Handles communication with external systems like Odoo
    4. State Coordination: Ensures consistent state across all components
    5. Performance Optimization: Implements caching and load balancing strategies
    
    The HubCrew follows a direct routing approach, where messages are sent directly to
    specialized crews without unnecessary intermediaries, while maintaining centralized
    coordination and visibility.
    """
    
    def __init__(self, 
                 memory_system: MemorySystem,
                 data_service_hub: Optional['DataServiceHub'] = None,
                 domain_manager: Optional[DomainManager] = None,
                 crew_factory: Optional[CrewFactory] = None,
                 plugin_manager: Optional[PluginManager] = None,
                 additional_tools: Optional[Dict[str, List[BaseTool]]] = None,
                 agent_cache: Optional[RedisAgentCache] = None,
                 **kwargs):
        """
        Initialize the hub crew.
        
        Args:
            memory_system: Shared memory system
            data_service_hub: Central hub for all data services
            additional_tools: Additional tools for the agents (optional)
            agent_cache: Cache for agent responses (optional)
            **kwargs: Additional arguments for the Crew class
        """
        # Create agents
        orchestrator_tools = additional_tools.get("orchestrator", []) if additional_tools else []
        context_manager_tools = additional_tools.get("context_manager", []) if additional_tools else []
        integration_tools = additional_tools.get("integration", []) if additional_tools else []
        data_proxy_tools = additional_tools.get("data_proxy", []) if additional_tools else []
        
        # Se não for fornecido um DataServiceHub, criar um novo
        if not data_service_hub:
            # Em um cenário real, seria melhor exigir este parâmetro
            logger.warning("DataServiceHub não fornecido à HubCrew. Criando um novo.")
            # Usando a importação do novo local
            data_service_hub = DataServiceHub()
        
        # Primeiro criamos o DataProxyAgent que será usado pelos outros agentes
        data_proxy = DataProxyAgent(
            data_service_hub=data_service_hub,
            memory_system=memory_system,
            additional_tools=data_proxy_tools
        )
        
        # Agora criamos os outros agentes, passando o DataProxyAgent
        orchestrator = OrchestratorAgent(
            memory_system=memory_system,
            data_proxy_agent=data_proxy,
            additional_tools=orchestrator_tools
        )
        
        context_manager = ContextManagerAgent(
            memory_system=memory_system,
            data_proxy_agent=data_proxy,
            additional_tools=context_manager_tools
        )
        
        integration_agent = IntegrationAgent(
            memory_system=memory_system,
            data_proxy_agent=data_proxy,
            additional_tools=integration_tools
        )
        
        # Usar o agente interno do DataProxyAgent (agent ou _crew_agent) em vez do próprio DataProxyAgent
        data_proxy_crew_agent = getattr(data_proxy, 'agent', None) or getattr(data_proxy, '_crew_agent', None)
        if not data_proxy_crew_agent:
            raise ValueError("DataProxyAgent deve ter um agente interno (agent ou _crew_agent)")
            
        agents = [orchestrator, context_manager, integration_agent, data_proxy_crew_agent]
        
        # Default configuration for the hub crew
        default_config = {
            "agents": agents,
            "tasks": [],  # Tasks will be created dynamically
            "verbose": True,
            "process": "sequential",  # Process tasks sequentially
            "cache": True,  # Habilitar cache (booleano)
            "name": "HubCrew"  # Nome da crew para identificação
        }
        
        # Override defaults with any provided kwargs
        config = {**default_config, **kwargs}
        
        super().__init__(**config)
        
        # Armazenar atributos necessários
        self.__dict__["_memory_system"] = memory_system
        # Corrigido: data_proxy_agent deve ser a variável data_proxy que criamos acima
        self.__dict__["_data_proxy_agent"] = data_proxy  # A variável correta é data_proxy
        self.__dict__["_agent_cache"] = agent_cache
        # Adicionar o atributo role para identificação da crew
        self.__dict__["_role"] = "HubCrew"
        self.__dict__["_integration_agent"] = integration_agent
        self.__dict__["_context_manager"] = context_manager
        self.__dict__["_data_proxy"] = data_proxy
        self.__dict__["_data_service_hub"] = data_service_hub
        
        # Armazenar componentes de multi-tenancy
        self.__dict__["_domain_manager"] = domain_manager
        
        # Inicializar ou armazenar o crew_factory
        if crew_factory:
            self.__dict__["_crew_factory"] = crew_factory
        else:
            # Criar uma nova instância do CrewFactory se não for fornecida
            self.__dict__["_crew_factory"] = get_crew_factory(
                data_proxy_agent=data_proxy,
                memory_system=memory_system,
                domain_manager=domain_manager
            )
            
        # Armazenar o plugin_manager
        self.__dict__["_plugin_manager"] = plugin_manager
        
        # Cache para crews funcionais por domínio
        self.__dict__["_functional_crews_cache"] = {}
    
    @property
    def memory_system(self):
        return self.__dict__["_memory_system"]
    
    @property
    def data_proxy_agent(self):
        return self.__dict__["_data_proxy_agent"]
    
    @property
    def context_manager(self):
        return self.__dict__["_context_manager"]
    
    @property
    def integration_agent(self):
        return self.__dict__["_integration_agent"]
    
    @property
    def data_proxy(self):
        return self.__dict__["_data_proxy"]
    
    @property
    def data_service_hub(self):
        return self.__dict__["_data_service_hub"]
        
    @property
    def domain_manager(self):
        return self.__dict__["_domain_manager"]
        
    @property
    def crew_factory(self):
        return self.__dict__["_crew_factory"]
        
    @property
    def plugin_manager(self):
        return self.__dict__["_plugin_manager"]
    
    def _route_message(self, message: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Route a message to the appropriate functional crew.
        
        This is the core routing function that determines which specialized crew
        should handle a specific message based on content analysis and context.
        
        Args:
            message: The message to route (contains content, sender info, etc.)
            context: Additional context for routing (conversation history, channel type, etc.)
            
        Returns:
            Routing decision with crew, reasoning, and confidence level
        """
        logger.debug(f"Roteando mensagem: {message}")
        # Normaliza a mensagem
        normalized_message = normalize_message(message)
        
        # Valida a mensagem
        if not validate_message(normalized_message):
            raise ValueError('Mensagem inválida')
        
        # Check cache first for performance optimization if agent_cache is available
        message_id = normalized_message.get('id', '')
        # Usar o atributo _role em vez de acessar self.role diretamente
        agent_id = f"hubcrew:{self.__dict__.get('_role', 'HubCrew')}"
        input_data = json.dumps({"message": normalized_message, "context": context})
        cached_route = None
        
        if self.__dict__["_agent_cache"]:
            cached_route = self.__dict__["_agent_cache"].get(agent_id, input_data)
            # Não precisamos fazer json.loads aqui, pois o método get já retorna um dicionário
            if cached_route:
                logger.info(f"Cache hit para {agent_id}")
        
        if cached_route:
            logger.info(f"Usando rota em cache para a mensagem {normalized_message.get('id', '')}")
            return cached_route
        
        # Se não há cache, use o método de roteamento com LLM
        logger.debug(f"Iniciando roteamento com LLM para a mensagem: {message}")
        result = self._route_with_llm(normalized_message, context)
        logger.info(f"Roteamento concluído para a mensagem {message.get('id', '')}")
        
        # Cache the result for future use if agent_cache is available
        if self.__dict__["_agent_cache"]:
            try:
                self.__dict__["_agent_cache"].set(agent_id, input_data, result)
            except Exception as e:
                logger.error(f"Error caching route: {e}")
        
        return result
    
    def _route_with_llm(self, message: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Roteamento usando LLM quando não há cache disponível.
        
        Args:
            message: A mensagem a ser roteada
            context: Contexto adicional para roteamento
            
        Returns:
            Decisão de roteamento com crew, raciocínio e nível de confiança
        """
        # Analyze message content and context to determine intent
        # This is a simplified implementation - in a real system, this would use
        # more sophisticated NLP techniques and potentially call an LLM
        
        # Extract key information from message and context
        message_content = message.get("content", "").lower()
        channel_type = context.get("channel_type", "unknown")
        customer_id = context.get("customer_id")
        
        # Load customer history if available
        customer_history = {}
        if customer_id and self.memory_system:
            customer_history = self.memory_system.retrieve_customer_data(customer_id)
        
        # Use DataProxyAgent para encontrar interações similares, se disponível
        similar_interactions = []
        if self.data_proxy_agent and message_content:
            # Usar o data_proxy_agent para buscar interações similares
            query_params = {
                "query": message_content,
                "limit": 3
            }
            result = self.data_proxy_agent.fetch_data("similar_interactions", query_params)
            if result and not isinstance(result, dict) and not result.get("error", False):
                similar_interactions = result
        
        # Determine which crew should handle this message
        # This is a simplified routing logic - in a real system, this would be more complex
        
        # Default values
        selected_crew = "sales"
        confidence = 0.5
        reasoning = "Default routing to sales crew"
        
        # Check for sales-related keywords
        sales_keywords = ["buy", "price", "cost", "purchase", "order", "discount"]
        if any(keyword in message_content for keyword in sales_keywords):
            selected_crew = "sales"
            confidence = 0.8
            reasoning = "Message contains sales-related keywords"
        
        # Check for support-related keywords
        support_keywords = ["help", "issue", "problem", "broken", "not working", "error"]
        if any(keyword in message_content for keyword in support_keywords):
            selected_crew = "support"
            confidence = 0.8
            reasoning = "Message contains support-related keywords"
        
        # Check for product-related keywords
        product_keywords = ["product", "feature", "specification", "specs", "details"]
        if any(keyword in message_content for keyword in product_keywords):
            selected_crew = "product"
            confidence = 0.7
            reasoning = "Message contains product-related keywords"
        
        # Adjust based on customer history if available
        if customer_history:
            # If customer has recent support interactions, route to support
            if customer_history.get("recent_support_tickets", 0) > 0:
                if confidence < 0.9:  # Only override if not very confident
                    selected_crew = "support"
                    confidence = 0.6
                    reasoning = "Customer has recent support tickets"
            
            # If customer has recent purchases, route to sales
            if customer_history.get("recent_purchases", 0) > 0:
                if confidence < 0.7:  # Only override if not confident
                    selected_crew = "sales"
                    confidence = 0.6
                    reasoning = "Customer has recent purchases"
        
        # Create routing result
        routing_result = {
            "crew": selected_crew,
            "confidence": confidence,
            "reasoning": reasoning
        }
        
        logger.info(f"Roteamento da mensagem {message.get('id', '')} para a crew funcional")
        return routing_result
    
    def register_conversation(self, conversation_id: str, customer_id: str, domain_name: str = None) -> Dict[str, Any]:
        """
        Registra uma nova conversa no sistema de memória.
        
        Este método é chamado pelo webhook_handler quando uma nova conversa é criada,
        permitindo que o HubCrew inicialize o contexto da conversa e prepare
        os sistemas de memória e gerenciamento de contexto.
        
        Args:
            conversation_id: ID único da conversa
            customer_id: ID do cliente/contato
            domain_name: Nome do domínio para a conversa (opcional)
            
        Returns:
            Dict[str, Any]: Informações sobre a conversa registrada, incluindo domínio
        """
        domain_specific_plugins = None
        domain_config = None
        
        try:
            # Determinar o domínio para a conversa
            if domain_name is None and self.domain_manager:
                # Tentar determinar o domínio com base no cliente
                try:
                    customer_data = self.get_customer_data(customer_id)
                    domain_name = customer_data.get("domain") if customer_data else None
                    logger.info(f"Domínio determinado a partir dos dados do cliente: {domain_name}")
                except Exception as e:
                    logger.warning(f"Erro ao obter dados do cliente para determinar domínio: {e}")
                    
                # Se ainda não tiver um domínio, usar o domínio ativo
                if not domain_name and self.domain_manager:
                    domain_name = self.domain_manager.get_active_domain()
                    logger.info(f"Domínio padrão ativo utilizado: {domain_name}")
            
            # Obter configurações do domínio se disponível
            if domain_name and self.domain_manager:
                try:
                    domain_config = self.domain_manager.get_domain_config(domain_name)
                    logger.info(f"Configurações do domínio {domain_name} carregadas")
                except Exception as e:
                    logger.warning(f"Erro ao carregar configurações do domínio {domain_name}: {e}")
            
            # Inicializa a conversa no sistema de memória
            self.memory_system.initialize_conversation(
                conversation_id=conversation_id,
                customer_id=customer_id
            )
            
            # Prepara o contexto inicial da conversa com informações de domínio
            initial_context = {
                "customer_id": customer_id,
                "domain_name": domain_name,
                "start_time": self._get_current_timestamp(),
                "interaction_count": 0,
                "status": "active"
            }
            
            # Adicionar informações adicionais do domínio ao contexto
            if domain_config:
                initial_context["domain_config"] = {
                    "name": domain_name,
                    "display_name": domain_config.get("display_name", domain_name),
                    "description": domain_config.get("description", ""),
                    "version": domain_config.get("version", "1.0")
                }
            
            # Armazena o contexto inicial
            self.memory_system.store_conversation_context(
                conversation_id=conversation_id,
                context=initial_context
            )
            
            # Inicializar plugins para o domínio se necessário
            if self.plugin_manager and domain_name:
                try:
                    domain_specific_plugins = self.plugin_manager.initialize_plugins_for_domain(domain_name)
                    plugin_names = list(domain_specific_plugins.keys()) if domain_specific_plugins else []
                    logger.info(f"Plugins inicializados para o domínio {domain_name}: {plugin_names}")
                    
                    # Adicionar informações de plugins ao contexto
                    if plugin_names:
                        updated_context = self.memory_system.retrieve_conversation_context(conversation_id) or {}
                        updated_context["active_plugins"] = plugin_names
                        self.memory_system.store_conversation_context(
                            conversation_id=conversation_id,
                            context=updated_context
                        )
                except Exception as plugin_error:
                    logger.warning(f"Erro ao inicializar plugins para o domínio {domain_name}: {plugin_error}")
                
            logger.info(f"Conversa {conversation_id} inicializada no HubCrew para o domínio {domain_name}")
            
            # Retornar informações sobre a conversa registrada
            return {
                "conversation_id": conversation_id,
                "customer_id": customer_id,
                "domain_name": domain_name,
                "plugins": list(domain_specific_plugins.keys()) if domain_specific_plugins else [],
                "status": "active",
                "start_time": initial_context["start_time"]
            }
        except Exception as e:
            logger.error(f"Erro ao inicializar conversa no HubCrew: {str(e)}")
            # Retornar informações básicas mesmo em caso de erro
            return {
                "conversation_id": conversation_id,
                "customer_id": customer_id,
                "domain_name": domain_name,
                "status": "error",
                "error": str(e)
            }
    
    def finalize_conversation(self, conversation_id: str) -> Dict[str, Any]:
        """
        Finaliza uma conversa no sistema de memória.
        
        Este método é chamado pelo webhook_handler quando uma conversa é encerrada,
        permitindo que o HubCrew finalize o contexto da conversa e libere recursos.
        
        Args:
            conversation_id: ID único da conversa
            
        Returns:
            Contexto final da conversa com informações de domínio
        """
        try:
            # Recupera o contexto atual para obter o domínio
            context = self.memory_system.retrieve_conversation_context(conversation_id) or {}
            domain_name = context.get("domain_name", "default")
            
            # Finaliza a conversa no sistema de memória
            self.memory_system.finalize_conversation(conversation_id)
            
            # Atualiza o contexto com a finalização
            context["end_time"] = self._get_current_timestamp()
            context["status"] = "resolved"
            
            # Armazena o contexto final
            self.memory_system.store_conversation_context(
                conversation_id=conversation_id,
                context=context
            )
            
            # Desativar plugins específicos do domínio se necessário
            if self.plugin_manager and domain_name:
                try:
                    self.plugin_manager.deactivate_plugins_for_domain(domain_name)
                    logger.info(f"Plugins para o domínio {domain_name} desativados")
                except Exception as plugin_error:
                    logger.warning(f"Erro ao desativar plugins para o domínio {domain_name}: {str(plugin_error)}")
            
            logger.info(f"Conversa {conversation_id} finalizada no HubCrew para o domínio {domain_name}")
            
            # Retorna o contexto final com informações de domínio
            return {
                "conversation_id": conversation_id,
                "domain_name": domain_name,
                "status": "resolved",
                "end_time": context["end_time"]
            }
        except Exception as e:
            logger.error(f"Erro ao finalizar conversa no HubCrew: {str(e)}")
            # Retorna informações básicas mesmo em caso de erro
            return {
                "conversation_id": conversation_id,
                "status": "error",
                "error": str(e)
            }
    
    def _get_current_timestamp(self) -> str:
        """
        Retorna o timestamp atual no formato ISO.
        
        Returns:
            Timestamp atual no formato ISO
        """
        from datetime import datetime
        return datetime.now().isoformat()
    
    async def process_message(self, 
                       message: Dict[str, Any],
                       conversation_id: str,
                       channel_type: str,
                       functional_crews: Dict[str, Any] = None,
                       domain_name: str = None) -> Dict[str, Any]:
        """
        Processa uma mensagem e a encaminha para a crew funcional apropriada.
        
        Este é o ponto de entrada principal para o processamento de mensagens na arquitetura hub-and-spoke.
        Ele gerencia o fluxo completo desde o recebimento de uma mensagem até o encaminhamento
        para a crew especializada adequada, agora com suporte assíncrono.
        
        Args:
            message: A mensagem a ser processada (conteúdo, informações do remetente, etc.)
            conversation_id: Identificador único da conversa
            channel_type: Canal de origem (WhatsApp, Instagram, etc.)
            functional_crews: Dicionário de crews funcionais disponíveis (opcional)
            domain_name: Nome do domínio para a conversa (opcional)
            
        Returns:
            Resultado do processamento com mensagem, contexto, roteamento e resposta
        """
        # Carrega ou cria o contexto da conversa
        context = self.memory_system.retrieve_conversation_context(conversation_id) or {}
        
        # Adiciona informações do canal ao contexto
        context["channel_type"] = channel_type
        context["conversation_id"] = conversation_id
        
        # Incrementa o contador de interações
        context["interaction_count"] = context.get("interaction_count", 0) + 1
        
        # Determinar o domínio para esta conversa
        # Prioridade: 1) domínio fornecido como parâmetro, 2) domínio no contexto, 3) domínio do cliente, 4) domínio ativo no DomainManager
        active_domain = None
        
        # 1. Verificar se o domínio foi fornecido como parâmetro
        if domain_name:
            active_domain = domain_name
            logger.info(f"Usando domínio fornecido como parâmetro: {domain_name}")
            
        # 2. Verificar se o domínio já está no contexto
        elif "domain_name" in context:
            active_domain = context["domain_name"]
            logger.info(f"Usando domínio do contexto: {active_domain}")
            
        # 3. Tentar determinar o domínio com base no cliente
        elif not active_domain:
            try:
                customer_id = context.get("customer_id", None)
                if customer_id:
                    customer_data = self.get_customer_data(customer_id)
                    if customer_data and "domain" in customer_data:
                        active_domain = customer_data["domain"]
                        logger.info(f"Domínio determinado a partir dos dados do cliente: {active_domain}")
            except Exception as e:
                logger.warning(f"Erro ao obter domínio do cliente: {str(e)}")
                
        # 4. Usar o domínio ativo no DomainManager
        if not active_domain and self.domain_manager:
            try:
                active_domain = self.domain_manager.get_active_domain()
                logger.info(f"Usando domínio ativo do DomainManager: {active_domain}")
            except Exception as e:
                logger.warning(f"Erro ao obter domínio ativo do DomainManager: {str(e)}")
                
        # Se ainda não tiver um domínio, usar o padrão
        if not active_domain:
            active_domain = "default"
            logger.warning(f"Nenhum domínio determinado, usando domínio padrão: {active_domain}")
            
        # Adicionar o domínio ao contexto
        context["domain_name"] = active_domain
        
        # Inicializar plugins para o domínio se necessário
        if self.plugin_manager:
            try:
                self.plugin_manager.initialize_plugins_for_domain(active_domain)
                logger.info(f"Plugins inicializados para o domínio: {active_domain}")
            except Exception as e:
                logger.error(f"Erro ao inicializar plugins para o domínio {active_domain}: {str(e)}")
        
        # Atualiza o contexto com a nova mensagem
        updated_context = self.context_manager.update_context(
            conversation_id=conversation_id,
            message=message,
            current_context=context
        )
        
        # Garante que o domínio esteja no contexto atualizado
        if "domain_name" not in updated_context and "domain_name" in context:
            updated_context["domain_name"] = context["domain_name"]
        
        # Roteia a mensagem para a crew funcional apropriada
        routing = self._route_message(
            message=message,
            context=updated_context
        )
        
        # Obter o domínio da conversa
        domain_name = updated_context.get("domain_name")
        
        # Se não há crews funcionais disponíveis, tentar criar usando o CrewFactory
        if not functional_crews:
            functional_crews = {}
            
            # Se temos um CrewFactory e um domínio, tentar criar as crews necessárias
            if self.crew_factory and domain_name and routing.get("crew"):
                try:
                    crew_id = routing.get("crew")
                    # Criar a crew usando o CrewFactory
                    crew = self.crew_factory.get_crew_for_domain(crew_id, domain_name)
                    if crew:
                        functional_crews[crew_id] = crew
                        logger.info(f"Crew {crew_id} criada dinamicamente para o domínio {domain_name}")
                except Exception as e:
                    logger.error(f"Erro ao criar crew dinamicamente: {str(e)}")
            
            # Se ainda não temos crews funcionais, retornar apenas o roteamento
            if not functional_crews:
                logger.warning("Nenhuma crew funcional disponível para processar a mensagem")
                result = {
                    "message": message,
                    "context": updated_context,
                    "routing": routing,
                    "response": None,
                    "domain_name": domain_name,
                    "domain_specific_crew": False,
                    "error": "Nenhuma crew funcional disponível para processar a mensagem"
                }
                return result
        
        # Processa a mensagem com a crew funcional apropriada
        selected_crew_name = routing.get("crew")
        
        # Verificar se a crew já está no dicionário fornecido
        if selected_crew_name in functional_crews:
            selected_crew = functional_crews.get(selected_crew_name)
        else:
            # Tentar criar a crew usando o CrewFactory
            try:
                # Chave para o cache de crews
                cache_key = f"{domain_name or 'default'}:{selected_crew_name}"
                
                # Verificar se já existe no cache
                if cache_key in self.__dict__["_functional_crews_cache"]:
                    selected_crew = self.__dict__["_functional_crews_cache"][cache_key]
                    logger.info(f"Usando crew {selected_crew_name} do cache para o domínio {domain_name}")
                else:
                    # Criar a crew usando o CrewFactory
                    selected_crew = self.crew_factory.get_crew_for_domain(selected_crew_name, domain_name)
                    
                    # Armazenar no cache
                    self.__dict__["_functional_crews_cache"][cache_key] = selected_crew
                    logger.info(f"Crew {selected_crew_name} criada para o domínio {domain_name}")
                    
                # Adicionar ao dicionário de crews funcionais
                functional_crews[selected_crew_name] = selected_crew
            except Exception as e:
                logger.error(f"Erro ao criar crew {selected_crew_name}: {e}")
                selected_crew = None
        
        if not selected_crew:
            logger.warning(f"Crew '{selected_crew_name}' não encontrada")
            result = {
                "message": message,
                "context": updated_context,
                "routing": routing,
                "response": None,
                "domain_name": domain_name,
                "domain_specific_crew": False,
                "error": f"Crew '{selected_crew_name}' não encontrada"
            }
            return result
        
        # Chama o método process da crew funcional
        try:
            # Adiciona informações adicionais ao contexto
            processing_context = {
                **updated_context,
                "routing": routing
            }
            
            # Chama o método process da crew funcional
            response = await selected_crew.process(message, processing_context)
            
            # Retorna o resultado completo do processamento
            result = {
                "message": message,
                "context": updated_context,
                "routing": routing,
                "response": response,
                "domain_name": domain_name,
                "domain_specific_crew": True
            }
            
            return result
        except Exception as e:
            logger.error(f"Erro ao processar mensagem com a crew {selected_crew_name}: {str(e)}")
            # Em caso de erro, retorna o resultado sem resposta
            result = {
                "message": message,
                "context": updated_context,
                "routing": routing,
                "response": None,
                "domain_name": domain_name,
                "error": str(e)
            }
            return result
    
    def get_customer_data(self, customer_id: str) -> Dict[str, Any]:
        """
        Get customer data from the external system.
        
        Args:
            customer_id: ID of the customer
            
        Returns:
            Customer data
        """
        return self.integration_agent.fetch_customer_data(customer_id)
    
    def get_product_data(self, product_id: str) -> Dict[str, Any]:
        """
        Get product data from the external system.
        
        Args:
            product_id: ID of the product
            
        Returns:
            Product data
        """
        return self.integration_agent.fetch_product_data(product_id)
    
    def get_business_rules(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get business rules from the external system.
        
        Args:
            category: Optional category filter
            
        Returns:
            List of business rules
        """
        return self.integration_agent.fetch_business_rules(category)
    
    def route_to_functional_crew(self, message: Dict[str, Any], context: Dict[str, Any], functional_crews: Dict[str, Any]) -> Dict[str, Any]:
        """
        Roteia uma mensagem para a crew funcional apropriada com base na intenção detectada.
        
        Args:
            message: A mensagem normalizada
            context: Contexto da conversa, incluindo intenção preliminar
            functional_crews: Dicionário de crews funcionais disponíveis
            
        Returns:
            Resultado do processamento pela crew funcional
        """
        # Obtém a intenção da mensagem do contexto ou usa o _route_message para detectá-la
        intent = context.get("preliminary_intent", None)
        if not intent:
            # Se não houver intenção preliminar, usa o _route_message para analisá-la
            routing = self._route_message(message=message, context=context)
            intent = routing.get("crew")
        
        # Mapeia intenções para tipos de crews funcionais
        intent_to_crew_map = {
            "purchase": "sales",
            "buy": "sales",
            "order": "sales",
            "price": "sales",
            "help": "support",
            "issue": "support",
            "problem": "support",
            "complaint": "support",
            "info": "info",
            "information": "info",
            "details": "info",
            "schedule": "scheduling",
            "appointment": "scheduling",
            "book": "scheduling",
            "meet": "scheduling"
        }
        
        # Obtém o tipo de crew com base na intenção ou usa um default
        crew_type = intent_to_crew_map.get(intent.lower() if intent else "", "info")
        
        # Obtém o domínio para determinar o nome específico da crew
        domain_name = context.get("domain_name", "default")
        
        # Com a abordagem GenericCrew, usamos diretamente o tipo da crew (sales, support, etc.)
        # como identificador, independente do domínio
        crew_name = crew_type
        
        logger.info(f"Usando crew genérica do tipo '{crew_name}' para o domínio '{domain_name}'")
        
        # Tenta obter a crew pelo nome específico do domínio
        target_crew = functional_crews.get(crew_name)
        
        # Se não encontrar, tenta pelo tipo genérico como fallback
        if not target_crew:
            target_crew = functional_crews.get(crew_type)
            
        # Se ainda não encontrou e temos um CrewFactory, tenta criar dinamicamente
        if not target_crew and self.crew_factory:
            try:
                # Chave para o cache de crews
                cache_key = f"{domain_name}:{crew_name}"
                
                # Verificar se já existe no cache
                if cache_key in self.__dict__["_functional_crews_cache"]:
                    target_crew = self.__dict__["_functional_crews_cache"][cache_key]
                    logger.info(f"Usando crew {crew_name} do cache para o domínio {domain_name}")
                else:
                    # Criar a crew usando o CrewFactory
                    # Agora usamos o tipo genérico (sales, support, etc.) diretamente
                    target_crew = self.crew_factory.get_crew_for_domain(crew_name, domain_name)
                    
                    # Armazenar no cache
                    if target_crew:
                        self.__dict__["_functional_crews_cache"][cache_key] = target_crew
                        logger.info(f"GenericCrew do tipo '{crew_name}' criada para o domínio '{domain_name}'")
                        
                        # Adicionar ao dicionário de crews funcionais
                        functional_crews[crew_name] = target_crew
            except Exception as e:
                logger.error(f"Erro ao criar crew {crew_name} para o domínio {domain_name}: {e}")
        
        # Registra a decisão de roteamento para debug
        logger.info(f"Roteando mensagem para crew funcional: {crew_name} (tipo: {crew_type}, domínio: {domain_name})")
        
        # Se não encontrar a crew apropriada, usa uma resposta padrão
        if not target_crew:
            logger.warning(f"Crew funcional '{crew_name}' não encontrada! Tentou também '{crew_type}'")
            return {
                "functional_result": "Desculpe, não consegui processar sua solicitação adequadamente.",
                "hub_metadata": {
                    "original_intent": intent,
                    "mapped_crew_type": crew_type,
                    "domain_specific_crew": crew_name,
                    "domain_name": domain_name,
                    "routing_error": "crew not found"
                }
            }
        
        # Processa a mensagem na crew funcional
        try:
            # Adicionar informações de domínio ao contexto se ainda não estiver presente
            if "domain_name" not in context:
                context["domain_name"] = domain_name
                
            # Inicializar plugins para o domínio se necessário
            if self.plugin_manager:
                try:
                    self.plugin_manager.initialize_plugins_for_domain(domain_name)
                except Exception as e:
                    logger.warning(f"Erro ao inicializar plugins para o domínio {domain_name}: {e}")
            
            # As crews funcionais esperam um método process(message, context)
            result = target_crew.process(message, context)
            
            # Adiciona metadata sobre o roteamento
            if isinstance(result, dict):
                result["hub_metadata"] = {
                    "original_intent": intent,
                    "original_target_crew": crew_type,
                    "domain_specific_crew": crew_name,
                    "domain_name": domain_name,
                    "routing_successful": True
                }
            else:
                # Se o resultado não for um dicionário, encapsula-o
                result = {
                    "functional_result": result,
                    "hub_metadata": {
                        "original_intent": intent,
                        "original_target_crew": crew_type,
                        "domain_specific_crew": crew_name,
                        "domain_name": domain_name,
                        "routing_successful": True
                    }
                }
            
            return result
            
        except Exception as e:
            logger.error(f"Erro ao processar mensagem na crew funcional {crew_type}: {e}")
            return {
                "functional_result": "Ocorreu um erro ao processar sua solicitação.",
                "hub_metadata": {
                    "original_intent": intent,
                    "original_target_crew": crew_type,
                    "domain_specific_crew": crew_name,
                    "domain_name": domain_name,
                    "routing_error": str(e)
                }
            }
