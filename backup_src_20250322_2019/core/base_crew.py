"""
Base classes for the hub-and-spoke architecture crews.

This module defines the base classes for the three layers of the hub-and-spoke architecture:
1. Channel Crews (Input Layer)
2. Hub Crew (Orchestration Layer)
3. Functional Crews (Specialized Layer)
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from crewai import Agent, Task, Crew, Process


class BaseCrew(ABC):
    """Base class for all crews in the hub-and-spoke architecture."""
    
    def __init__(self, name: str, agents: Optional[List[Agent]] = None):
        """
        Initialize a base crew.
        
        Args:
            name: The name of the crew
            agents: List of CrewAI agents for this crew
        """
        self.name = name
        self.agents = agents or []
        self.tools = self.initialize_tools()
        
    @abstractmethod
    def initialize_tools(self) -> Dict[str, Any]:
        """Initialize tools specific to this crew."""
        pass
    
    @abstractmethod
    def process(self, data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process data using this crew's agents and tools.
        
        Args:
            data: The data to process
            context: Additional context for processing
            
        Returns:
            The processed result
        """
        pass


class ChannelCrew(BaseCrew):
    """Crew specialized in a specific communication channel."""
    
    def __init__(self, channel_type: str, agents: Optional[List[Agent]] = None):
        """
        Initialize a channel crew.
        
        Args:
            channel_type: The type of channel (e.g., WhatsApp, Instagram)
            agents: List of CrewAI agents for this crew
        """
        super().__init__(f"{channel_type}Channel", agents)
        self.channel_type = channel_type
    
    def initialize_tools(self) -> Dict[str, Any]:
        """Initialize tools specific to this channel."""
        # These will be implemented with actual tools
        return {
            "message_formatter": None,  # Will be MessageFormatterTool
            "channel_api": None,        # Will be ChannelAPITool
        }
    
    def normalize_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize a message from this channel to a standard format.
        
        Args:
            message: The raw message from the channel
            
        Returns:
            The normalized message
        """
        # This will be implemented with channel-specific normalization
        return message
    
    def detect_preliminary_intent(self, message: Dict[str, Any]) -> str:
        """
        Detect the preliminary intent of a message.
        
        Args:
            message: The normalized message
            
        Returns:
            The detected intent
        """
        # This will be implemented with intent detection logic
        return "general_inquiry"
    
    def extract_metadata(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract metadata from a message.
        
        Args:
            message: The raw message from the channel
            
        Returns:
            The extracted metadata
        """
        # This will be implemented with channel-specific metadata extraction
        return {}
    
    def process(self, message: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an incoming message from this channel.
        
        Args:
            message: The raw message from the channel
            context: Additional context for processing
            
        Returns:
            The processed result with normalized message, intent, and metadata
        """
        normalized_message = self.normalize_message(message)
        intent = self.detect_preliminary_intent(normalized_message)
        
        return {
            "normalized_message": normalized_message,
            "preliminary_intent": intent,
            "channel_metadata": self.extract_metadata(message),
            "channel_type": self.channel_type
        }


class HubCrew(BaseCrew):
    """Central hub for orchestrating message flow between crews."""
    
    def __init__(self, functional_crews: Dict[str, 'FunctionalCrew'] = None, agents: Optional[List[Agent]] = None):
        """
        Initialize the hub crew.
        
        Args:
            functional_crews: Dictionary of functional crews by type
            agents: List of CrewAI agents for this crew
        """
        super().__init__("Hub", agents)
        self.functional_crews = functional_crews or {}
        
    def initialize_tools(self) -> Dict[str, Any]:
        """Initialize tools specific to the hub."""
        # These will be implemented with actual tools
        return {
            "intent_analyzer": None,  # Will be IntentAnalyzerTool
            "context_manager": None,  # Will be ContextManagerTool
            "sla_monitor": None,      # Will be SLAMonitorTool
        }
    
    def analyze_intent(self, message: Dict[str, Any], channel_data: Dict[str, Any]) -> str:
        """
        Analyze the intent of a message in detail.
        
        Args:
            message: The normalized message
            channel_data: Data from the channel crew
            
        Returns:
            The detailed intent
        """
        # This will be implemented with advanced intent analysis
        return channel_data.get("preliminary_intent", "general_inquiry")
    
    def select_crew(self, intent: str) -> 'FunctionalCrew':
        """
        Select the appropriate functional crew based on intent.
        
        Args:
            intent: The detected intent
            
        Returns:
            The selected functional crew
        """
        # Map intents to crew types
        intent_to_crew = {
            "sales_inquiry": "sales",
            "support_request": "support",
            "scheduling_request": "scheduling",
            "feedback": "analytics",
            "marketing_inquiry": "marketing",
            "general_inquiry": "support"  # Default to support
        }
        
        crew_type = intent_to_crew.get(intent, "support")
        return self.functional_crews.get(crew_type)
    
    def process(self, data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process data by routing it to the appropriate functional crew.
        
        Args:
            data: The data from a channel crew
            context: Additional context for processing
            
        Returns:
            The processed result from the functional crew
        """
        # Extract the normalized message
        message = data.get("normalized_message", {})
        
        # Analyze intent in detail
        intent = self.analyze_intent(message, data)
        
        # Update context with new information
        context.update({
            "intent": intent,
            "channel_data": data
        })
        
        # Select the appropriate crew
        crew = self.select_crew(intent)
        if not crew:
            return {
                "error": "No suitable crew found for intent: " + intent,
                "fallback_response": "I'm not sure how to help with that specific request."
            }
        
        # Process with the selected crew
        return crew.process(message, context)


class FunctionalCrew(BaseCrew):
    """Crew specialized in a specific business function."""
    
    def __init__(self, function_type: str, agents: Optional[List[Agent]] = None):
        """
        Initialize a functional crew.
        
        Args:
            function_type: The type of function (e.g., sales, support)
            agents: List of CrewAI agents for this crew
        """
        super().__init__(f"{function_type.capitalize()}Crew", agents)
        self.function_type = function_type
    
    def initialize_tools(self) -> Dict[str, Any]:
        """Initialize tools specific to this function."""
        # These will be implemented with actual tools
        return {
            "qdrant": None,       # Will be QdrantVectorSearchTool
            "postgres": None,     # Will be PGSearchTool
            "redis_cache": None,  # Will be RedisCacheTool
        }
    
    def get_relevant_tables(self) -> List[str]:
        """
        Get the relevant database tables for this function.
        
        Returns:
            List of relevant table names
        """
        # Map function types to relevant tables
        function_to_tables = {
            "sales": ["products", "pricing", "inventory", "customers"],
            "support": ["faq", "tickets", "product_issues"],
            "scheduling": ["appointments", "availability", "staff"],
            "analytics": ["feedback", "interactions", "metrics"],
            "marketing": ["campaigns", "promotions", "content"]
        }
        
        return function_to_tables.get(self.function_type, [])
    
    def process(self, message: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a message using this function's specialized agents and tools.
        
        Args:
            message: The normalized message
            context: Additional context for processing
            
        Returns:
            The processed result
        """
        # Create a task for the agents
        task = Task(
            description=f"Process {self.function_type} request: {message.get('content', '')}",
            expected_output="Detailed response addressing the user's needs"
        )
        
        # Execute the task with the available agents
        crew = Crew(
            agents=self.agents,
            tasks=[task],
            verbose=True,
            process=Process.sequential
        )
        
        # This is a placeholder for the actual execution
        # In a real implementation, we would return crew.kickoff()
        return {
            "response": f"Processed by {self.name}",
            "function_type": self.function_type,
            "status": "success"
        }
