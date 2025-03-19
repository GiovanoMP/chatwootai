"""
Channel Agents for the hub-and-spoke architecture.

This module implements specialized agents for the ChannelCrew,
which is responsible for handling messages from specific communication channels.
"""

import logging
from typing import Dict, List, Any, Optional, Union
import json

from crewai import Agent, Task, Crew
from src.core.cache.agent_cache import RedisAgentCache
from langchain.tools import BaseTool

from src.core.memory import MemorySystem
from src.tools.vector_tools import QdrantVectorSearchTool
from src.tools.database_tools import PGSearchTool
from src.tools.cache_tools import CacheTool
from src.api.chatwoot_client import ChatwootClient

logger = logging.getLogger(__name__)


class MessageProcessorAgent(Agent):
    """
    Agent responsible for processing messages from a specific channel.
    
    This agent understands the nuances of a specific channel and
    formats messages appropriately for that channel.
    """
    
    def __init__(self, 
                 channel_type: str,
                 memory_system: MemorySystem,
                 vector_tool: QdrantVectorSearchTool,
                 db_tool: PGSearchTool,
                 cache_tool: CacheTool,
                 chatwoot_client: ChatwootClient,
                 additional_tools: Optional[List[BaseTool]] = None,
                 **kwargs):
        """
        Initialize the message processor agent.
        
        Args:
            channel_type: Type of channel
            memory_system: Shared memory system
            vector_tool: Tool for vector search
            db_tool: Tool for database search
            cache_tool: Tool for caching
            chatwoot_client: Client for Chatwoot API
            additional_tools: Additional tools for the agent
            **kwargs: Additional arguments for the Agent class
        """
        tools = [vector_tool, db_tool, cache_tool]
        
        if additional_tools:
            tools.extend(additional_tools)
        
        # Default configuration for the message processor agent
        default_config = {
            "role": f"{channel_type.capitalize()} Channel Specialist",
            "goal": f"Process messages from {channel_type} channel with expertise in its specific nuances",
            "backstory": f"""You are a specialist in the {channel_type} communication channel.
            Your job is to process messages from this channel, understanding its specific nuances,
            and format responses appropriately for this channel.
            You have deep knowledge of {channel_type}'s features, limitations, and best practices.""",
            "verbose": True,
            "allow_delegation": True,
            "tools": tools
        }
        
        # Override defaults with any provided kwargs
        config = {**default_config, **kwargs}
        
        super().__init__(**config)
        
        # Armazenar os atributos como dicionário privado para evitar conflitos com Pydantic
        self.__dict__["_channel_type"] = channel_type
        self.__dict__["_memory_system"] = memory_system
        self.__dict__["_vector_tool"] = vector_tool
        self.__dict__["_db_tool"] = db_tool
        self.__dict__["_cache_tool"] = cache_tool
        self.__dict__["_chatwoot_client"] = chatwoot_client
    
    @property
    def channel_type(self):
        return self.__dict__["_channel_type"]
    
    @property
    def memory_system(self):
        return self.__dict__["_memory_system"]
    
    @property
    def vector_tool(self):
        return self.__dict__["_vector_tool"]
    
    @property
    def db_tool(self):
        return self.__dict__["_db_tool"]
    
    @property
    def cache_tool(self):
        return self.__dict__["_cache_tool"]
    
    @property
    def chatwoot_client(self):
        return self.__dict__["_chatwoot_client"]
    
    def process_incoming_message(self, 
                                message: Dict[str, Any],
                                conversation_id: str) -> Dict[str, Any]:
        """
        Process an incoming message from the channel.
        
        Args:
            message: The message to process
            conversation_id: ID of the conversation
            
        Returns:
            Processed message
        """
        # Check cache first
        cache_key = f"processed:{self.channel_type}:{message.get('id', '')}"
        cached_result = self.cache_tool.get(cache_key)
        
        if cached_result:
            logger.info(f"Using cached processing for message {message.get('id', '')}")
            return json.loads(cached_result)
        
        # Prepare the task for the agent
        task_description = f"""
        Process the following message from the {self.channel_type} channel:
        
        Message: {message.get('content', '')}
        Sender: {message.get('sender', {}).get('name', 'Unknown')}
        Conversation ID: {conversation_id}
        
        Extract the following information:
        1. Intent of the message
        2. Key entities mentioned (products, services, etc.)
        3. Sentiment (positive, negative, neutral)
        4. Any specific requests or questions
        5. Priority level (low, medium, high)
        
        Format the information in a structured way for further processing.
        """
        
        # Execute the task
        result = self.execute_task(Task(
            description=task_description,
            expected_output="JSON object with processed message information"
        ))
        
        # Parse the result
        try:
            if isinstance(result, str):
                # Try to extract JSON from the string
                import re
                json_match = re.search(r'```json\n(.*?)\n```', result, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group(1))
                else:
                    # Try to parse the entire string as JSON
                    result = json.loads(result)
            
            # Ensure the result has the required fields
            if not isinstance(result, dict):
                result = {
                    "intent": "unknown",
                    "entities": [],
                    "sentiment": "neutral",
                    "requests": [],
                    "priority": "medium",
                    "channel_specific": {}
                }
            
            # Add channel-specific information
            result["channel_type"] = self.channel_type
            result["original_message"] = message
            result["conversation_id"] = conversation_id
        
        except Exception as e:
            logger.error(f"Error parsing message processing result: {e}")
            result = {
                "intent": "unknown",
                "entities": [],
                "sentiment": "neutral",
                "requests": [],
                "priority": "medium",
                "channel_type": self.channel_type,
                "original_message": message,
                "conversation_id": conversation_id,
                "error": str(e)
            }
        
        # Cache the result
        self.cache_tool.set(cache_key, json.dumps(result), ttl=3600)  # Cache for 1 hour
        
        return result
    
    def format_outgoing_message(self, 
                               content: str,
                               context: Dict[str, Any],
                               conversation_id: str) -> Dict[str, Any]:
        """
        Format an outgoing message for the channel.
        
        Args:
            content: Content of the message
            context: Context of the conversation
            conversation_id: ID of the conversation
            
        Returns:
            Formatted message
        """
        # Check cache first
        cache_key = f"formatted:{self.channel_type}:{conversation_id}:{hash(content)}"
        cached_result = self.cache_tool.get(cache_key)
        
        if cached_result:
            logger.info(f"Using cached formatting for message in conversation {conversation_id}")
            return json.loads(cached_result)
        
        # Prepare the task for the agent
        task_description = f"""
        Format the following message for the {self.channel_type} channel:
        
        Content: {content}
        Conversation ID: {conversation_id}
        Context: {json.dumps(context)}
        
        Format the message according to the best practices for {self.channel_type}:
        1. Adjust length and formatting for the channel
        2. Add appropriate greetings and sign-offs
        3. Format any rich content (if supported)
        4. Ensure compliance with channel limitations
        
        Return the formatted message ready to be sent.
        """
        
        # Execute the task
        result = self.execute_task(Task(
            description=task_description,
            expected_output="JSON object with formatted message"
        ))
        
        # Parse the result
        try:
            if isinstance(result, str):
                # Try to extract JSON from the string
                import re
                json_match = re.search(r'```json\n(.*?)\n```', result, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group(1))
                else:
                    # Try to parse the entire string as JSON
                    result = json.loads(result)
            
            # Ensure the result has the required fields
            if not isinstance(result, dict):
                result = {
                    "content": content,
                    "channel_type": self.channel_type,
                    "conversation_id": conversation_id
                }
            
            # Add channel-specific information
            if "channel_type" not in result:
                result["channel_type"] = self.channel_type
            
            if "conversation_id" not in result:
                result["conversation_id"] = conversation_id
            
            if "content" not in result:
                result["content"] = content
        
        except Exception as e:
            logger.error(f"Error parsing message formatting result: {e}")
            result = {
                "content": content,
                "channel_type": self.channel_type,
                "conversation_id": conversation_id,
                "error": str(e)
            }
        
        # Cache the result
        self.cache_tool.set(cache_key, json.dumps(result), ttl=3600)  # Cache for 1 hour
        
        return result


class ChannelMonitorAgent(Agent):
    """
    Agent responsible for monitoring a specific channel.
    
    This agent monitors the channel for new messages and events,
    and triggers the appropriate actions.
    """
    
    def __init__(self, 
                 channel_type: str,
                 memory_system: MemorySystem,
                 vector_tool: QdrantVectorSearchTool,
                 db_tool: PGSearchTool,
                 cache_tool: CacheTool,
                 chatwoot_client: ChatwootClient,
                 additional_tools: Optional[List[BaseTool]] = None,
                 **kwargs):
        """
        Initialize the channel monitor agent.
        
        Args:
            channel_type: Type of channel
            memory_system: Shared memory system
            vector_tool: Tool for vector search
            db_tool: Tool for database search
            cache_tool: Tool for caching
            chatwoot_client: Client for Chatwoot API
            additional_tools: Additional tools for the agent
            **kwargs: Additional arguments for the Agent class
        """
        tools = [vector_tool, db_tool, cache_tool]
        
        if additional_tools:
            tools.extend(additional_tools)
        
        # Default configuration for the channel monitor agent
        default_config = {
            "role": f"{channel_type.capitalize()} Channel Monitor",
            "goal": f"Monitor the {channel_type} channel for new messages and events",
            "backstory": f"""You are a monitor for the {channel_type} communication channel.
            Your job is to continuously monitor this channel for new messages and events,
            and trigger the appropriate actions when something happens.
            You have deep knowledge of {channel_type}'s API and event system.""",
            "verbose": True,
            "allow_delegation": True,
            "tools": tools
        }
        
        # Override defaults with any provided kwargs
        config = {**default_config, **kwargs}
        
        super().__init__(**config)
        
        # Armazenar os atributos como dicionário privado para evitar conflitos com Pydantic
        self.__dict__["_channel_type"] = channel_type
        self.__dict__["_memory_system"] = memory_system
        self.__dict__["_vector_tool"] = vector_tool
        self.__dict__["_db_tool"] = db_tool
        self.__dict__["_cache_tool"] = cache_tool
        self.__dict__["_chatwoot_client"] = chatwoot_client
    
    @property
    def channel_type(self):
        return self.__dict__["_channel_type"]
    
    @property
    def memory_system(self):
        return self.__dict__["_memory_system"]
    
    @property
    def vector_tool(self):
        return self.__dict__["_vector_tool"]
    
    @property
    def db_tool(self):
        return self.__dict__["_db_tool"]
    
    @property
    def cache_tool(self):
        return self.__dict__["_cache_tool"]
    
    @property
    def chatwoot_client(self):
        return self.__dict__["_chatwoot_client"]
    
    def check_new_messages(self, 
                          last_check_time: Optional[float] = None) -> List[Dict[str, Any]]:
        """
        Check for new messages in the channel.
        
        Args:
            last_check_time: Time of the last check
            
        Returns:
            List of new messages
        """
        # This is a placeholder - in the actual implementation, we would
        # use the Chatwoot client to check for new messages
        
        try:
            # Get new conversations
            new_conversations = self.chatwoot_client.get_new_conversations(
                channel_type=self.channel_type,
                since=last_check_time
            )
            
            # Get new messages from each conversation
            new_messages = []
            
            for conversation in new_conversations:
                conversation_id = conversation.get("id")
                messages = self.chatwoot_client.get_conversation_messages(
                    conversation_id=conversation_id,
                    since=last_check_time
                )
                
                # Filter out messages from the bot
                messages = [
                    msg for msg in messages
                    if not msg.get("sender", {}).get("type") == "bot"
                ]
                
                new_messages.extend(messages)
            
            return new_messages
        
        except Exception as e:
            logger.error(f"Error checking new messages: {e}")
            return []
    
    def handle_channel_event(self, 
                            event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a channel event.
        
        Args:
            event: The event to handle
            
        Returns:
            Result of handling the event
        """
        # Prepare the task for the agent
        task_description = f"""
        Handle the following event from the {self.channel_type} channel:
        
        Event Type: {event.get('type', 'Unknown')}
        Event Data: {json.dumps(event.get('data', {}))}
        
        Determine the appropriate action to take based on the event type and data.
        """
        
        # Execute the task
        result = self.execute_task(Task(
            description=task_description,
            expected_output="JSON object with action to take"
        ))
        
        # Parse the result
        try:
            if isinstance(result, str):
                # Try to extract JSON from the string
                import re
                json_match = re.search(r'```json\n(.*?)\n```', result, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group(1))
                else:
                    # Try to parse the entire string as JSON
                    result = json.loads(result)
            
            # Ensure the result has the required fields
            if not isinstance(result, dict):
                result = {
                    "action": "none",
                    "reason": "Failed to parse agent result"
                }
            
            if "action" not in result:
                result["action"] = "none"
            
            if "reason" not in result:
                result["reason"] = "No reason provided"
        
        except Exception as e:
            logger.error(f"Error parsing event handling result: {e}")
            result = {
                "action": "none",
                "reason": f"Error in handling: {str(e)}",
                "error": str(e)
            }
        
        return result


class ChannelCrew(Crew):
    """
    Crew responsible for handling messages from a specific communication channel.
    
    This crew specializes in the nuances of a specific channel,
    processing messages and formatting responses appropriately.
    """
    # Configuração Pydantic para permitir tipos arbitrários
    model_config = {"arbitrary_types_allowed": True, "validate_assignment": False}
    
    def __init__(self, 
                 channel_type: str,
                 memory_system: MemorySystem,
                 vector_tool: QdrantVectorSearchTool,
                 db_tool: PGSearchTool,
                 cache_tool: CacheTool,
                 chatwoot_client: ChatwootClient,
                 additional_tools: Optional[Dict[str, List[BaseTool]]] = None,
                 agent_cache: Optional[RedisAgentCache] = None,
                 **kwargs):
        """
        Initialize the channel crew.
        
        Args:
            channel_type: Type of channel
            memory_system: Shared memory system
            vector_tool: Tool for vector search
            db_tool: Tool for database search
            cache_tool: Tool for caching
            chatwoot_client: Client for Chatwoot API
            additional_tools: Additional tools for the agents
            agent_cache: Cache for agent responses
            **kwargs: Additional arguments for the Crew class
        """
        # Create agents
        processor_tools = additional_tools.get("processor", []) if additional_tools else []
        monitor_tools = additional_tools.get("monitor", []) if additional_tools else []
        
        processor = MessageProcessorAgent(
            channel_type=channel_type,
            memory_system=memory_system,
            vector_tool=vector_tool,
            db_tool=db_tool,
            cache_tool=cache_tool,
            chatwoot_client=chatwoot_client,
            additional_tools=processor_tools
        )
        
        monitor = ChannelMonitorAgent(
            channel_type=channel_type,
            memory_system=memory_system,
            vector_tool=vector_tool,
            db_tool=db_tool,
            cache_tool=cache_tool,
            chatwoot_client=chatwoot_client,
            additional_tools=monitor_tools
        )
        
        agents = [processor, monitor]
        
        # Para evitar problemas com o modelo Pydantic do Crew, precisamos definir 
        # corretamente os parâmetros de inicialização
        # Garantir que os agents sempre sejam uma lista, mesmo que seja vazia
        if agents is None:
            agents = []

        # Default configuration for the channel crew
        default_config = {
            "agents": agents,
            "tasks": [],  # Tasks will be created dynamically
            "verbose": True,
            "process": "sequential",  # Process tasks sequentially
            # O parâmetro cache na classe Crew é um booleano, não um objeto
            # Se o agent_cache foi fornecido, vamos definir cache como True
            "cache": agent_cache is not None
        }
        
        # Override defaults with any provided kwargs
        config = {**default_config, **kwargs}
        
        # Criamos um dict limpo para evitar erros de validação
        # Removendo qualquer parâmetro que não seja válido para o modelo Pydantic
        clean_config = {}
        for key in ['agents', 'tasks', 'verbose', 'process', 'cache']:
            if key in config:
                clean_config[key] = config[key]
        
        # Garantir que agents é uma lista, mesmo que vazia
        if "agents" not in clean_config or clean_config["agents"] is None:
            clean_config["agents"] = []
            
        # Garantir que tasks é uma lista, mesmo que vazia
        if "tasks" not in clean_config or clean_config["tasks"] is None:
            clean_config["tasks"] = []
            
        # Garantir que cache é um booleano
        if "cache" not in clean_config:
            clean_config["cache"] = True
        
        super().__init__(**clean_config)
        
        # Armazenar os atributos como dicionário privado para evitar conflitos com Pydantic
        self.__dict__["_channel_type"] = channel_type
        self.__dict__["_memory_system"] = memory_system
        self.__dict__["_vector_tool"] = vector_tool
        self.__dict__["_db_tool"] = db_tool
        self.__dict__["_cache_tool"] = cache_tool
        self.__dict__["_chatwoot_client"] = chatwoot_client
        self.__dict__["_processor"] = processor
        self.__dict__["_monitor"] = monitor
        self.__dict__["_agent_cache"] = agent_cache
    
    @property
    def channel_type(self):
        return self.__dict__["_channel_type"]
    
    @property
    def memory_system(self):
        return self.__dict__["_memory_system"]
    
    @property
    def vector_tool(self):
        return self.__dict__["_vector_tool"]
    
    @property
    def db_tool(self):
        return self.__dict__["_db_tool"]
    
    @property
    def cache_tool(self):
        return self.__dict__["_cache_tool"]
    
    @property
    def chatwoot_client(self):
        return self.__dict__["_chatwoot_client"]
    
    @property
    def processor(self):
        return self.__dict__["_processor"]
    
    @property
    def monitor(self):
        return self.__dict__["_monitor"]
        
    @property
    def agent_cache(self):
        return self.__dict__["_agent_cache"]
    
    def create_tasks(self):
        """Método necessário para a classe Crew, mas não usado nesta implementação.
        
        As tasks são criadas nos métodos específicos de cada ChannelCrew.
        """
        return []
    
    def process_message(self, 
                       message: Dict[str, Any],
                       conversation_id: str) -> Dict[str, Any]:
        """
        Process a message from the channel.
        
        Args:
            message: The message to process
            conversation_id: ID of the conversation
            
        Returns:
            Processed message
        """
        return self.processor.process_incoming_message(
            message=message,
            conversation_id=conversation_id
        )
    
    def format_message(self, 
                      content: str,
                      context: Dict[str, Any],
                      conversation_id: str) -> Dict[str, Any]:
        """
        Format a message for the channel.
        
        Args:
            content: Content of the message
            context: Context of the conversation
            conversation_id: ID of the conversation
            
        Returns:
            Formatted message
        """
        return self.processor.format_outgoing_message(
            content=content,
            context=context,
            conversation_id=conversation_id
        )
    
    def check_new_messages(self, 
                          last_check_time: Optional[float] = None) -> List[Dict[str, Any]]:
        """
        Check for new messages in the channel.
        
        Args:
            last_check_time: Time of the last check
            
        Returns:
            List of new messages
        """
        return self.monitor.check_new_messages(last_check_time)
    
    def handle_event(self, 
                    event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a channel event.
        
        Args:
            event: The event to handle
            
        Returns:
            Result of handling the event
        """
        return self.monitor.handle_channel_event(event)
    
    def send_message(self, 
                    content: str,
                    conversation_id: str,
                    context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Send a message to the channel.
        
        Args:
            content: Content of the message
            conversation_id: ID of the conversation
            context: Context of the conversation
            
        Returns:
            Result of sending the message
        """
        # Get context if not provided
        if context is None:
            context = self.memory_system.get_conversation_context(conversation_id) or {}
        
        # Format the message
        formatted = self.format_message(
            content=content,
            context=context,
            conversation_id=conversation_id
        )
        
        # Send the message
        try:
            result = self.chatwoot_client.send_message(
                conversation_id=conversation_id,
                content=formatted.get("content", content),
                message_type="outgoing"
            )
            
            # Store the message in memory
            self.memory_system.add_message_to_conversation(
                conversation_id=conversation_id,
                message={
                    "id": result.get("id"),
                    "content": formatted.get("content", content),
                    "sender": {
                        "type": "bot",
                        "name": "ChatwootAI"
                    },
                    "created_at": result.get("created_at")
                }
            )
            
            return {
                "status": "success",
                "message_id": result.get("id"),
                "conversation_id": conversation_id
            }
        
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return {
                "status": "error",
                "error": str(e),
                "conversation_id": conversation_id
            }
