"""
Sistema de Eventos usando Redis Streams para o MCP-Crew v2.
"""

import json
import logging
import threading
import time
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from src.redis_manager.redis_manager import redis_manager, DataType

logger = logging.getLogger(__name__)

class EventPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class EventType(Enum):
    TOOL_DISCOVERY = "tool_discovery"
    CONVERSATION = "conversation"
    KNOWLEDGE_UPDATE = "knowledge_update"
    SYSTEM = "system"

class Event:
    def __init__(
        self, 
        event_type: EventType, 
        data: Dict[str, Any], 
        priority: EventPriority = EventPriority.MEDIUM
    ):
        self.event_type = event_type
        self.data = data
        self.priority = priority
        self.timestamp = time.time()
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type.value,
            "data": self.data,
            "priority": self.priority.value,
            "timestamp": self.timestamp
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Event':
        return cls(
            event_type=EventType(data["event_type"]),
            data=data["data"],
            priority=EventPriority(data["priority"])
        )

class EventManager:
    def __init__(self, tenant_id: str = "system"):
        self.tenant_id = tenant_id
        self.consumers = {}
        self.running = False
        
    def publish(self, event: Event, stream_name: str = "default") -> bool:
        try:
            key = f"{stream_name}"
            event_dict = event.to_dict()
            
            # Serializar o dicionário de dados para JSON
            if "data" in event_dict and isinstance(event_dict["data"], dict):
                event_dict["data"] = json.dumps(event_dict["data"])
            
            # Converter todos os valores para strings para garantir compatibilidade com Redis
            event_data = {k: str(v) for k, v in event_dict.items()}
            
            result = redis_manager.client.xadd(
                f"{redis_manager.prefix}:{self.tenant_id}:{DataType.EVENT}:{key}",
                event_data,
                maxlen=1000
            )
            
            return result is not None
            
        except Exception as e:
            logger.error(f"Erro ao publicar evento: {e}")
            return False
            
    def subscribe(self, stream_name: str, callback: Callable[[Event], None]) -> bool:
        if stream_name not in self.consumers:
            self.consumers[stream_name] = []
            
        self.consumers[stream_name].append(callback)
        
        if not self.running:
            self._start_consumer()
            
        return True
        
    def _start_consumer(self):
        self.running = True
        thread = threading.Thread(target=self._consumer_loop, daemon=True)
        thread.start()
        
    def _consumer_loop(self):
        last_ids = {stream: "0-0" for stream in self.consumers.keys()}
        
        while self.running:
            try:
                streams = [f"{redis_manager.prefix}:{self.tenant_id}:{DataType.EVENT}:{stream}" 
                          for stream in self.consumers.keys()]
                
                stream_data = redis_manager.client.xread(
                    streams={stream: last_id for stream, last_id in zip(streams, last_ids.values())},
                    count=10,
                    block=1000
                )
                
                if not stream_data:
                    continue
                    
                for stream_name, messages in stream_data:
                    short_name = stream_name.split(":")[-1]
                    
                    for message_id, data in messages:
                        last_ids[short_name] = message_id
                        
                        # Converter dados de volta para o formato original
                        parsed_data = {}
                        for k, v in data.items():
                            if k == "data" and isinstance(v, str):
                                try:
                                    parsed_data[k] = json.loads(v)
                                except json.JSONDecodeError:
                                    parsed_data[k] = v
                            else:
                                parsed_data[k] = v
                        
                        event = Event.from_dict(parsed_data)
                        
                        for callback in self.consumers.get(short_name, []):
                            try:
                                callback(event)
                            except Exception as e:
                                logger.error(f"Erro no callback: {e}")
                
            except Exception as e:
                logger.error(f"Erro no loop do consumidor: {e}")
                time.sleep(1)
                
    def stop(self):
        self.running = False
