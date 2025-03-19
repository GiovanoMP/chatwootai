"""
Shared memory system for the hub-and-spoke architecture.

This module implements a multi-level memory system using Redis:
1. Short-term memory: For conversation context (1 hour TTL)
2. Medium-term memory: For recent customer interactions (7 days TTL)
3. Long-term memory: For persistent customer preferences and patterns
"""

import json
import logging
from typing import Dict, Any, Optional, Union
from redis import Redis

logger = logging.getLogger(__name__)


class SharedMemory:
    """Shared memory system for crews using Redis."""
    
    def __init__(self, redis_client: Redis):
        """
        Initialize the shared memory system.
        
        Args:
            redis_client: Redis client instance
        """
        self.redis = redis_client
    
    def store_short_term(self, conversation_id: str, data: Dict[str, Any], ttl: int = 3600) -> bool:
        """
        Store data in short-term memory (1 hour by default).
        
        Args:
            conversation_id: Unique identifier for the conversation
            data: Data to store
            ttl: Time-to-live in seconds (default: 3600 seconds = 1 hour)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            key = f"short_term:{conversation_id}"
            self.redis.setex(key, ttl, json.dumps(data))
            return True
        except Exception as e:
            logger.error(f"Error storing short-term memory: {e}")
            return False
    
    def store_medium_term(self, customer_id: str, data: Dict[str, Any], ttl: int = 86400*7) -> bool:
        """
        Store data in medium-term memory (7 days by default).
        
        Args:
            customer_id: Unique identifier for the customer
            data: Data to store
            ttl: Time-to-live in seconds (default: 604800 seconds = 7 days)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            key = f"medium_term:{customer_id}"
            self.redis.setex(key, ttl, json.dumps(data))
            return True
        except Exception as e:
            logger.error(f"Error storing medium-term memory: {e}")
            return False
    
    def store_long_term(self, customer_id: str, data: Dict[str, Any]) -> bool:
        """
        Store data in long-term memory (permanent).
        
        Args:
            customer_id: Unique identifier for the customer
            data: Data to store
            
        Returns:
            True if successful, False otherwise
        """
        try:
            key = f"long_term:{customer_id}"
            self.redis.set(key, json.dumps(data))
            return True
        except Exception as e:
            logger.error(f"Error storing long-term memory: {e}")
            return False
    
    def get_memory(self, memory_type: str, id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve data from memory.
        
        Args:
            memory_type: Type of memory ('short_term', 'medium_term', or 'long_term')
            id: Unique identifier (conversation_id for short_term, customer_id for others)
            
        Returns:
            The stored data or None if not found
        """
        try:
            key = f"{memory_type}:{id}"
            data = self.redis.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Error retrieving memory: {e}")
            return None
    
    def update_memory(self, memory_type: str, id: str, 
                      update_data: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """
        Update existing memory with new data.
        
        Args:
            memory_type: Type of memory ('short_term', 'medium_term', or 'long_term')
            id: Unique identifier (conversation_id for short_term, customer_id for others)
            update_data: New data to merge with existing data
            ttl: Time-to-live in seconds (only for short_term and medium_term)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get existing data
            existing_data = self.get_memory(memory_type, id) or {}
            
            # Merge with new data
            existing_data.update(update_data)
            
            # Store updated data
            key = f"{memory_type}:{id}"
            if ttl is not None:
                self.redis.setex(key, ttl, json.dumps(existing_data))
            else:
                self.redis.set(key, json.dumps(existing_data))
            
            return True
        except Exception as e:
            logger.error(f"Error updating memory: {e}")
            return False
    
    def delete_memory(self, memory_type: str, id: str) -> bool:
        """
        Delete memory.
        
        Args:
            memory_type: Type of memory ('short_term', 'medium_term', or 'long_term')
            id: Unique identifier (conversation_id for short_term, customer_id for others)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            key = f"{memory_type}:{id}"
            self.redis.delete(key)
            return True
        except Exception as e:
            logger.error(f"Error deleting memory: {e}")
            return False


class ContextManager:
    """Manages conversation context using the shared memory system."""
    
    def __init__(self, shared_memory: Optional[SharedMemory] = None):
        """
        Initialize the context manager.
        
        Args:
            shared_memory: SharedMemory instance
        """
        self.shared_memory = shared_memory
        self.active_context = {}  # In-memory context for current conversation
    
    def update_context(self, message: Dict[str, Any], intent: str, 
                       channel_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update the conversation context with new information.
        
        Args:
            message: The normalized message
            intent: The detected intent
            channel_data: Data from the channel
            
        Returns:
            The updated context
        """
        # Extract conversation and customer IDs
        conversation_id = channel_data.get("conversation_id")
        customer_id = channel_data.get("customer_id")
        
        # Update in-memory context
        self.active_context.update({
            "last_message": message,
            "last_intent": intent,
            "last_channel_data": channel_data,
            "timestamp": channel_data.get("timestamp")
        })
        
        # If shared memory is available, store context
        if self.shared_memory and conversation_id:
            self.shared_memory.store_short_term(conversation_id, self.active_context)
            
            # If customer ID is available, update medium-term memory
            if customer_id:
                customer_context = {
                    "last_conversation_id": conversation_id,
                    "last_interaction_time": channel_data.get("timestamp"),
                    "last_intent": intent,
                    "channel_type": channel_data.get("channel_type")
                }
                self.shared_memory.update_memory("medium_term", customer_id, customer_context)
        
        return self.active_context
    
    def get_context(self) -> Dict[str, Any]:
        """
        Get the current context.
        
        Returns:
            The current context
        """
        return self.active_context
    
    def load_context(self, conversation_id: str) -> Dict[str, Any]:
        """
        Load context from shared memory.
        
        Args:
            conversation_id: Unique identifier for the conversation
            
        Returns:
            The loaded context
        """
        if self.shared_memory:
            loaded_context = self.shared_memory.get_memory("short_term", conversation_id) or {}
            self.active_context.update(loaded_context)
        
        return self.active_context
    
    def load_customer_history(self, customer_id: str) -> Dict[str, Any]:
        """
        Load customer history from medium and long-term memory.
        
        Args:
            customer_id: Unique identifier for the customer
            
        Returns:
            Combined customer history
        """
        if not self.shared_memory:
            return {}
        
        # Load from medium-term memory
        medium_term = self.shared_memory.get_memory("medium_term", customer_id) or {}
        
        # Load from long-term memory
        long_term = self.shared_memory.get_memory("long_term", customer_id) or {}
        
        # Combine and return
        history = {**long_term, **medium_term}  # Medium-term overrides long-term if keys overlap
        
        return history


class MemorySystem:
    """Unified memory system for the ChatwootAI architecture.
    
    This class provides a unified interface to the different memory components,
    including shared memory and context management.
    """
    
    def __init__(self, shared_memory: Optional[SharedMemory] = None):
        """Initialize the memory system.
        
        Args:
            shared_memory: SharedMemory instance for persistent storage
        """
        self.shared_memory = shared_memory or SharedMemory(Redis())
        self.context_manager = ContextManager(shared_memory=self.shared_memory)
    
    def store_conversation_context(self, conversation_id: str, context: Dict[str, Any], ttl: int = 3600) -> bool:
        """Store conversation context in short-term memory.
        
        Args:
            conversation_id: Unique identifier for the conversation
            context: Context data to store
            ttl: Time-to-live in seconds (default: 1 hour)
            
        Returns:
            True if successful, False otherwise
        """
        return self.shared_memory.store_short_term(conversation_id, context, ttl)
    
    def retrieve_conversation_context(self, conversation_id: str) -> Dict[str, Any]:
        """Retrieve conversation context from short-term memory.
        
        Args:
            conversation_id: Unique identifier for the conversation
            
        Returns:
            The conversation context or an empty dict if not found
        """
        return self.shared_memory.get_memory("short_term", conversation_id) or {}
    
    def store_customer_data(self, customer_id: str, data: Dict[str, Any], persistent: bool = False) -> bool:
        """Store customer data in medium or long-term memory.
        
        Args:
            customer_id: Unique identifier for the customer
            data: Customer data to store
            persistent: If True, store in long-term memory, otherwise in medium-term
            
        Returns:
            True if successful, False otherwise
        """
        if persistent:
            return self.shared_memory.store_long_term(customer_id, data)
        else:
            return self.shared_memory.store_medium_term(customer_id, data)
    
    def retrieve_customer_data(self, customer_id: str, persistent: bool = False) -> Dict[str, Any]:
        """Retrieve customer data from medium or long-term memory.
        
        Args:
            customer_id: Unique identifier for the customer
            persistent: If True, retrieve from long-term memory, otherwise from medium-term
            
        Returns:
            The customer data or an empty dict if not found
        """
        memory_type = "long_term" if persistent else "medium_term"
        return self.shared_memory.get_memory(memory_type, customer_id) or {}
    
    def update_context(self, message: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Update the conversation context with new information.
        
        Args:
            message: The incoming message
            context: The current context
            
        Returns:
            The updated context
        """
        # Extract conversation_id and channel_data from context
        conversation_id = context.get('conversation_id', '')
        channel_data = context.get('channel_data', {})
        intent = context.get('intent', '')
        
        # Update context using context manager
        updated_context = self.context_manager.update_context(
            message=message,
            intent=intent,
            channel_data=channel_data
        )
        
        return updated_context
