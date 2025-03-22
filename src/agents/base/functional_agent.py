#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
FunctionalAgent: Agente Funcional

Base class for all functional agents.

This agent is specialized in a specific business function,
like sales, support, scheduling, etc.
"""

import logging
from typing import Dict, List, Any, Optional, Union
import json
from pydantic import ConfigDict
from crewai import Agent, Task, Crew
from src.core.cache.agent_cache import RedisAgentCache
from langchain.tools import BaseTool
from src.core.memory import MemorySystem
from src.core.data_proxy_agent import DataProxyAgent

class FunctionalAgent(Agent):
    """
    Base class for all functional agents.
    
    This agent is specialized in a specific business function,
    like sales, support, scheduling, etc.
    """
    # Configuração do modelo Pydantic para permitir tipos arbitrários
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    def __init__(self, 
                 function_type: str,
                 memory_system=None,
                 data_proxy_agent=None,
                 additional_tools=None,
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
        # Armazenar atributos no dicionário privado para evitar problemas com Pydantic
        self.__dict__["_function_type"] = function_type
        self.__dict__["_memory_system"] = memory_system
        self.__dict__["_data_proxy_agent"] = data_proxy_agent
        self.__dict__["_config"] = {}
        
        # Preparar as ferramentas para o agente
        tools = []
        
        # Adicionar as ferramentas do DataProxyAgent (se existirem)
        if data_proxy_agent and hasattr(data_proxy_agent, 'get_tools') and callable(getattr(data_proxy_agent, 'get_tools')):
            tools.extend(data_proxy_agent.get_tools())
        
        # Adicionar ferramentas adicionais
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
        
        # Armazenar a configuração no dicionário privado
        self.__dict__["_config"] = config
        
        # Chama o construtor da classe pai com todos os dados
        super().__init__(**config)
    
    # Propriedades para acessar os atributos privados
    @property
    def function_type(self):
        """Retorna o tipo de função do agente."""
        return self.__dict__.get("_function_type", "unknown")
    
    @property
    def memory_system(self):
        """Retorna o sistema de memória compartilhada."""
        return self.__dict__.get("_memory_system")
    
    @property
    def data_proxy_agent(self):
        """Retorna o agente proxy para acesso a dados."""
        return self.__dict__.get("_data_proxy_agent")
    
    @property
    def config(self):
        """Retorna a configuração do agente."""
        return self.__dict__.get("_config", {})
    
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
            str: The response
        """
        # Implementação básica que pode ser sobrescrita por subclasses
        return f"Resposta padrão do agente {self.function_type}"
    
    def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a message and generate a response.
        
        Args:
            message: The message to process
            
        Returns:
            Dict[str, Any]: The processed response
        """
        # Implementação básica que pode ser sobrescrita por subclasses
        return {
            "status": "success",
            "response": f"Mensagem processada pelo agente {self.function_type}",
            "context": {}
        }
    
    def get_agent_type(self) -> str:
        """
        Get the type of the agent.
        
        Returns:
            str: The type of the agent
        """
        return self.function_type
    
    def get_memory(self, key: str) -> Any:
        """
        Get a value from the memory system.
        
        Args:
            key: The key to get
            
        Returns:
            Any: The value
        """
        if self.memory_system:
            return self.memory_system.get(key)
        return None
    
    def set_memory(self, key: str, value: Any) -> bool:
        """
        Set a value in the memory system.
        
        Args:
            key: The key to set
            value: The value to set
            
        Returns:
            bool: True if successful, False otherwise
        """
        if self.memory_system:
            return self.memory_system.set(key, value)
        return False
