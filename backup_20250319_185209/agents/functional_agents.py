"""
Functional Agents for the hub-and-spoke architecture.

This module implements specialized agents for the FunctionalCrew,
which is responsible for handling specific business functions like sales, support, etc.
"""

import logging
from typing import Dict, List, Any, Optional, Union
import json

from crewai import Agent, Task, Crew
from src.core.cache.agent_cache import RedisAgentCache
from langchain.tools import BaseTool

from src.core.memory import MemorySystem
from src.agents.data_proxy_agent import DataProxyAgent

logger = logging.getLogger(__name__)


class FunctionalAgent(Agent):
    """
    Base class for all functional agents.
    
    This agent is specialized in a specific business function,
    like sales, support, scheduling, etc.
    """
    # Configuração do modelo Pydantic para permitir tipos arbitrários
    model_config = {"arbitrary_types_allowed": True}
    
    # Definindo os campos do modelo Pydantic
    function_type: str
    memory_system: MemorySystem
    data_proxy_agent: DataProxyAgent
    
    def __init__(self, 
                 function_type: str,
                 memory_system: MemorySystem,
                 data_proxy_agent: DataProxyAgent,
                 additional_tools: Optional[List[BaseTool]] = None,
                 **kwargs):
        """
        Initialize the functional agent.
        
        Args:
            function_type: Type of business function
            memory_system: Shared memory system
            data_proxy_agent: Agent that provides access to data services
            additional_tools: Additional tools for the agent
            **kwargs: Additional arguments for the Agent class
        """
        tools = [data_proxy_agent]
        
        if additional_tools:
            tools.extend(additional_tools)
        
        # Default configuration for the functional agent
        default_config = {
            "role": f"{function_type.capitalize()} Specialist",
            "goal": f"Handle {function_type} tasks with expertise and efficiency",
            "backstory": f"""You are a specialist in {function_type}.
            Your job is to handle tasks related to {function_type},
            providing expert knowledge and solutions in this area.
            You have deep understanding of {function_type} processes and best practices.""",
            "verbose": True,
            "allow_delegation": True,
            "tools": tools
        }
        
        # Override defaults with any provided kwargs
        config = {**default_config, **kwargs}
        
        # Inicializa os campos do modelo Pydantic
        model_data = {
            "function_type": function_type,
            "memory_system": memory_system,
            "data_proxy_agent": data_proxy_agent,
            **config
        }
        
        # Chama o construtor da classe pai com todos os dados
        super().__init__(**model_data)
    
    def generate_response(self, 
                         message: Dict[str, Any],
                         context: Dict[str, Any],
                         conversation_id: str) -> str:
        """
        Generate a response to a message.
        
        Args:
            message: The message to respond to
            context: Context of the conversation
            conversation_id: ID of the conversation
            
        Returns:
            Generated response
        """
        # Check cache first
        cache_key = f"response:{self.function_type}:{message.get('id', '')}"
        cached_response = self.cache_tool.get(cache_key)
        
        if cached_response:
            logger.info(f"Using cached response for message {message.get('id', '')}")
            return cached_response
        
        # Prepare the task for the agent
        task_description = f"""
        Generate a response to the following message as a {self.function_type} specialist:
        
        Message: {message.get('content', '')}
        Sender: {message.get('sender', {}).get('name', 'Unknown')}
        Conversation ID: {conversation_id}
        
        Context:
        {json.dumps(context)}
        
        Generate a helpful, informative, and professional response that addresses the message.
        Focus on your expertise in {self.function_type}.
        """
        
        # Execute the task
        result = self.execute_task(Task(
            description=task_description,
            expected_output="Text response to the message"
        ))
        
        # Ensure the result is a string
        if not isinstance(result, str):
            result = str(result)
        
        # Cache the result
        self.cache_tool.set(cache_key, result, ttl=3600)  # Cache for 1 hour
        
        return result
