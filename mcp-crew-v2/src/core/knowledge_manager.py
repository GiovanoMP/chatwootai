"""
Knowledge Sharing System - Sistema de Compartilhamento de Conhecimento
Gerencia compartilhamento de conhecimento entre agentes e crews
"""

import logging
import time
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

from src.config.config import (
    redis_manager, 
    serialize_json, 
    deserialize_json, 
    get_knowledge_cache_key,
    get_stream_name,
    Config
)
from src.redis_manager.redis_manager import DataType

logger = logging.getLogger(__name__)

class KnowledgeType(Enum):
    """Tipos de conhecimento compartilhado"""
    PRODUCT_INFO = "product_info"
    CUSTOMER_INSIGHT = "customer_insight"
    CONVERSATION_SUMMARY = "conversation_summary"
    ANALYSIS_RESULT = "analysis_result"
    RECOMMENDATION = "recommendation"
    MARKET_DATA = "market_data"
    TECHNICAL_SPEC = "technical_spec"
    GENERAL_FACT = "general_fact"
    GENERAL = "general"

@dataclass
class KnowledgeItem:
    """Item de conhecimento compartilhado"""
    id: str
    type: KnowledgeType
    topic: str
    title: str
    content: Dict[str, Any]
    metadata: Dict[str, Any]
    source_agent: str
    source_crew: str
    account_id: str
    created_at: float
    expires_at: Optional[float] = None
    tags: List[str] = None
    confidence_score: float = 1.0
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if not self.id:
            self.id = str(uuid.uuid4())
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['type'] = self.type.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'KnowledgeItem':
        data['type'] = KnowledgeType(data['type'])
        return cls(**data)
    
    def is_expired(self) -> bool:
        """Verifica se o conhecimento expirou"""
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at

@dataclass
class KnowledgeEvent:
    """Evento de conhecimento para notificação"""
    event_id: str
    event_type: str  # 'created', 'updated', 'deleted'
    knowledge_id: str
    topic: str
    summary: str
    source_agent: str
    source_crew: str
    account_id: str
    timestamp: float
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if not self.event_id:
            self.event_id = str(uuid.uuid4())
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'KnowledgeEvent':
        return cls(**data)

class KnowledgeManager:
    """Gerenciador de conhecimento compartilhado"""
    
    def __init__(self):
        self.local_cache: Dict[str, KnowledgeItem] = {}
        self.subscribers: Dict[str, Set[str]] = {}  # topic -> set of subscriber_ids
    
    def store_knowledge(
        self, 
        knowledge_item: KnowledgeItem,
        notify_subscribers: bool = True
    ) -> bool:
        """Armazena item de conhecimento"""
        try:
            # Validar item
            if not self._validate_knowledge_item(knowledge_item):
                logger.error(f"Item de conhecimento inválido: {knowledge_item.id}")
                return False
            
            # Chave para armazenamento
            cache_key = get_knowledge_cache_key(
                knowledge_item.account_id, 
                knowledge_item.topic, 
                knowledge_item.id
            )
            
            # Armazenar no Redis com TTL otimizado por tipo de conhecimento
            # Definir TTLs específicos por tipo de conhecimento
            knowledge_ttls = {
                KnowledgeType.PRODUCT_INFO: 2592000,        # 30 dias (informações de produto mudam pouco)
                KnowledgeType.CUSTOMER_INSIGHT: 1209600,    # 14 dias (insights de clientes)
                KnowledgeType.CONVERSATION_SUMMARY: 604800, # 7 dias (resumos de conversas)
                KnowledgeType.ANALYSIS_RESULT: 1209600,    # 14 dias (resultados de análise)
                KnowledgeType.RECOMMENDATION: 604800,      # 7 dias (recomendações)
                KnowledgeType.MARKET_DATA: 259200,         # 3 dias (dados de mercado mudam rápido)
                KnowledgeType.TECHNICAL_SPEC: 2592000,     # 30 dias (especificações técnicas)
                KnowledgeType.GENERAL_FACT: 2592000,       # 30 dias (fatos gerais)
                KnowledgeType.GENERAL: 604800              # 7 dias (conhecimento geral)
            }
            
            # Obter TTL específico para o tipo de conhecimento ou usar o padrão
            ttl = knowledge_ttls.get(knowledge_item.type, Config.KNOWLEDGE_CACHE_TTL)
            
            # Se tem expiração específica, usar o menor TTL
            if knowledge_item.expires_at:
                custom_ttl = int(knowledge_item.expires_at - time.time())
                if custom_ttl > 0:
                    ttl = min(ttl, custom_ttl)
                    
            logger.debug(f"Usando TTL de {ttl} segundos para conhecimento do tipo {knowledge_item.type.value}")
            
            # Usar o RedisManager robusto com tenant_id (account_id)
            success = redis_manager.set(
                tenant_id=knowledge_item.account_id,
                data_type=DataType.KNOWLEDGE,
                identifier=f"{knowledge_item.topic}:{knowledge_item.id}",
                value=knowledge_item.to_dict(),
                ttl=ttl
            )
            
            if success:
                # Armazenar no cache local
                self.local_cache[knowledge_item.id] = knowledge_item
                
                # Indexar por tópico para busca rápida
                topic_index_key = get_knowledge_cache_key(
                    knowledge_item.account_id, 
                    f"index:{knowledge_item.topic}", 
                    "items"
                )
                
                # Adicionar ID à lista de itens do tópico
                # Usar o RedisManager robusto com tenant_id (account_id)
                existing_ids = redis_manager.get(
                    tenant_id=knowledge_item.account_id,
                    data_type=DataType.KNOWLEDGE,
                    identifier=f"index:{knowledge_item.topic}"
                )
                
                if existing_ids:
                    ids_list = existing_ids
                else:
                    ids_list = []
                
                if knowledge_item.id not in ids_list:
                    ids_list.append(knowledge_item.id)
                    redis_manager.set(
                        tenant_id=knowledge_item.account_id,
                        data_type=DataType.KNOWLEDGE,
                        identifier=f"index:{knowledge_item.topic}",
                        value=ids_list,
                        ttl=ttl
                    )
                
                # Notificar subscribers se solicitado
                if notify_subscribers:
                    self._notify_knowledge_event(knowledge_item, 'created')
                
                logger.info(f"✅ Conhecimento armazenado: {knowledge_item.id} ({knowledge_item.topic})")
                return True
            
        except Exception as e:
            logger.error(f"Erro ao armazenar conhecimento: {e}")
        
        return False
    
    def retrieve_knowledge(
        self, 
        account_id: str, 
        knowledge_id: str, 
        topic: Optional[str] = None
    ) -> Optional[KnowledgeItem]:
        """Recupera item de conhecimento específico"""
        try:
            # Verificar cache local primeiro
            if knowledge_id in self.local_cache:
                item = self.local_cache[knowledge_id]
                if not item.is_expired():
                    return item
                else:
                    # Remover item expirado do cache local
                    del self.local_cache[knowledge_id]
            
            # Se tópico não fornecido, tentar buscar em todos os tópicos
            if not topic:
                # Buscar em tópicos conhecidos (implementação simplificada)
                for knowledge_type in KnowledgeType:
                    item = self._retrieve_from_redis(account_id, knowledge_type.value, knowledge_id)
                    if item:
                        return item
                return None
            
            return self._retrieve_from_redis(account_id, topic, knowledge_id)
            
        except Exception as e:
            logger.error(f"Erro ao recuperar conhecimento {knowledge_id}: {e}")
            return None
    
    def _retrieve_from_redis(self, account_id: str, topic: str, knowledge_id: str) -> Optional[KnowledgeItem]:
        """Recupera conhecimento do Redis usando o RedisManager robusto"""
        try:
            # Usar o RedisManager robusto com tenant_id (account_id)
            knowledge_dict = redis_manager.get(
                tenant_id=account_id,
                data_type=DataType.KNOWLEDGE,
                identifier=f"{topic}:{knowledge_id}"
            )
            
            if knowledge_dict:
                knowledge_item = KnowledgeItem.from_dict(knowledge_dict)
                
                # Verificar se não expirou
                if not knowledge_item.is_expired():
                    # Adicionar ao cache local
                    self.local_cache[knowledge_id] = knowledge_item
                    return knowledge_item
                else:
                    # Remover item expirado
                    redis_manager.delete(
                        tenant_id=account_id,
                        data_type=DataType.KNOWLEDGE,
                        identifier=f"{topic}:{knowledge_id}"
                    )
            
        except Exception as e:
            logger.error(f"Erro ao recuperar do Redis: {e}")
        
        return None
    
    def search_knowledge_by_topic(
        self, 
        account_id: str, 
        topic: str, 
        limit: int = 10,
        tags: Optional[List[str]] = None
    ) -> List[KnowledgeItem]:
        """Busca conhecimento por tópico"""
        try:
            # Obter lista de IDs do tópico
            topic_index_key = get_knowledge_cache_key(account_id, f"index:{topic}", "items")
            cached_ids = redis_manager.get(topic_index_key)
            
            if not cached_ids:
                return []
            
            ids_list = deserialize_json(cached_ids)
            results = []
            
            for knowledge_id in ids_list[:limit * 2]:  # Buscar mais para filtrar
                knowledge_item = self.retrieve_knowledge(account_id, knowledge_id, topic)
                if knowledge_item:
                    # Filtrar por tags se especificado
                    if tags:
                        if any(tag in knowledge_item.tags for tag in tags):
                            results.append(knowledge_item)
                    else:
                        results.append(knowledge_item)
                
                if len(results) >= limit:
                    break
            
            # Ordenar por timestamp (mais recente primeiro)
            results.sort(key=lambda x: x.created_at, reverse=True)
            return results[:limit]
            
        except Exception as e:
            logger.error(f"Erro ao buscar conhecimento por tópico {topic}: {e}")
            return []
    
    def search_knowledge_by_content(
        self, 
        account_id: str, 
        query: str, 
        limit: int = 10
    ) -> List[KnowledgeItem]:
        """Busca conhecimento por conteúdo (busca textual simples)"""
        try:
            results = []
            query_lower = query.lower()
            
            # Buscar em todos os tópicos conhecidos
            for knowledge_type in KnowledgeType:
                topic_results = self.search_knowledge_by_topic(account_id, knowledge_type.value, limit)
                
                for item in topic_results:
                    # Busca simples no título e conteúdo
                    if (query_lower in item.title.lower() or 
                        query_lower in str(item.content).lower() or
                        any(query_lower in tag.lower() for tag in item.tags)):
                        results.append(item)
                
                if len(results) >= limit:
                    break
            
            # Ordenar por relevância (score de confiança + recência)
            results.sort(key=lambda x: (x.confidence_score, x.created_at), reverse=True)
            return results[:limit]
            
        except Exception as e:
            logger.error(f"Erro ao buscar conhecimento por conteúdo: {e}")
            return []
    
    def subscribe_to_topic(self, account_id: str, topic: str, subscriber_id: str):
        """Inscreve um agente/crew para receber notificações de um tópico"""
        try:
            topic_key = f"{account_id}:{topic}"
            if topic_key not in self.subscribers:
                self.subscribers[topic_key] = set()
            
            self.subscribers[topic_key].add(subscriber_id)
            logger.info(f"📢 {subscriber_id} inscrito no tópico {topic}")
            
        except Exception as e:
            logger.error(f"Erro ao inscrever no tópico: {e}")
    
    def unsubscribe_from_topic(self, account_id: str, topic: str, subscriber_id: str):
        """Remove inscrição de um tópico"""
        try:
            topic_key = f"{account_id}:{topic}"
            if topic_key in self.subscribers:
                self.subscribers[topic_key].discard(subscriber_id)
                logger.info(f"🔇 {subscriber_id} desinscrito do tópico {topic}")
                
        except Exception as e:
            logger.error(f"Erro ao desinscrever do tópico: {e}")
    
    def _notify_knowledge_event(self, knowledge_item: KnowledgeItem, event_type: str):
        """Notifica subscribers sobre evento de conhecimento"""
        try:
            # Criar evento
            event = KnowledgeEvent(
                event_id=str(uuid.uuid4()),
                event_type=event_type,
                knowledge_id=knowledge_item.id,
                topic=knowledge_item.topic,
                summary=knowledge_item.title,
                source_agent=knowledge_item.source_agent,
                source_crew=knowledge_item.source_crew,
                account_id=knowledge_item.account_id,
                timestamp=time.time(),
                metadata={
                    'type': knowledge_item.type.value,
                    'tags': knowledge_item.tags,
                    'confidence_score': knowledge_item.confidence_score
                }
            )
            
            # Publicar no Redis Stream
            stream_name = get_stream_name(knowledge_item.account_id, "knowledge_events")
            event_data = event.to_dict()
            
            # Converter valores para string (Redis Streams requirement)
            stream_fields = {k: str(v) for k, v in event_data.items()}
            
            message_id = redis_manager.xadd(stream_name, stream_fields, maxlen=1000)
            
            if message_id:
                logger.info(f"📡 Evento de conhecimento publicado: {event.event_id}")
            
        except Exception as e:
            logger.error(f"Erro ao notificar evento de conhecimento: {e}")
    
    def get_knowledge_events(
        self, 
        account_id: str, 
        last_id: str = "0", 
        count: int = 10
    ) -> List[KnowledgeEvent]:
        """Obtém eventos de conhecimento do stream"""
        try:
            stream_name = get_stream_name(account_id, "knowledge_events")
            streams = {stream_name: last_id}
            
            messages = redis_manager.xread(streams, count=count, block=1000)  # 1 segundo de timeout
            
            events = []
            for stream, msgs in messages:
                for msg_id, fields in msgs:
                    try:
                        # Converter campos de volta para tipos apropriados
                        event_data = {}
                        for key, value in fields.items():
                            if key in ['timestamp', 'confidence_score']:
                                event_data[key] = float(value)
                            elif key == 'metadata':
                                event_data[key] = deserialize_json(value)
                            else:
                                event_data[key] = value
                        
                        event = KnowledgeEvent.from_dict(event_data)
                        events.append(event)
                        
                    except Exception as e:
                        logger.error(f"Erro ao parsear evento: {e}")
            
            return events
            
        except Exception as e:
            logger.error(f"Erro ao obter eventos de conhecimento: {e}")
            return []
    
    def _validate_knowledge_item(self, item: KnowledgeItem) -> bool:
        """Valida item de conhecimento"""
        if not item.id or not item.topic or not item.title:
            return False
        if not item.source_agent or not item.account_id:
            return False
        if not isinstance(item.content, dict):
            return False
        return True
    
    def get_knowledge_stats(self, account_id: str) -> Dict[str, Any]:
        """Obtém estatísticas de conhecimento"""
        try:
            stats = {
                'total_items': 0,
                'by_topic': {},
                'by_type': {},
                'recent_activity': 0
            }
            
            # Contar itens por tópico
            for knowledge_type in KnowledgeType:
                topic = knowledge_type.value
                items = self.search_knowledge_by_topic(account_id, topic, limit=1000)
                count = len(items)
                
                stats['by_topic'][topic] = count
                stats['total_items'] += count
                
                # Contar por tipo
                stats['by_type'][knowledge_type.value] = count
                
                # Atividade recente (últimas 24h)
                recent_items = [item for item in items if time.time() - item.created_at < 86400]
                stats['recent_activity'] += len(recent_items)
            
            return stats
            
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas: {e}")
            return {}
    
    def cleanup_expired_knowledge(self, account_id: str) -> int:
        """Remove conhecimento expirado"""
        try:
            removed_count = 0
            
            for knowledge_type in KnowledgeType:
                topic = knowledge_type.value
                items = self.search_knowledge_by_topic(account_id, topic, limit=1000)
                
                for item in items:
                    if item.is_expired():
                        cache_key = get_knowledge_cache_key(account_id, topic, item.id)
                        if redis_manager.delete(cache_key):
                            removed_count += 1
                            
                            # Remover do cache local
                            if item.id in self.local_cache:
                                del self.local_cache[item.id]
            
            if removed_count > 0:
                logger.info(f"🧹 Removidos {removed_count} itens de conhecimento expirados")
            
            return removed_count
            
        except Exception as e:
            logger.error(f"Erro ao limpar conhecimento expirado: {e}")
            return 0

# Instância global do gerenciador de conhecimento
knowledge_manager = KnowledgeManager()

