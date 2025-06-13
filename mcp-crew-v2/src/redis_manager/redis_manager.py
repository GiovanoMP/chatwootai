"""
RedisManager para o MCP-Crew v2.

Este módulo implementa uma classe para gerenciar conexões e operações Redis
específicas para o MCP-Crew, incluindo particionamento por tenant,
circuit breakers e TTLs configuráveis por tipo de dado.
"""

import json
import logging
import os
import time
from typing import Any, Dict, List, Optional, Union

import redis
from redis.exceptions import RedisError

# Configuração de logging
logger = logging.getLogger(__name__)

# Constantes para tipos de dados
class DataType:
    """Constantes para os diferentes tipos de dados armazenados no Redis."""
    TOOL_DISCOVERY = "tool_discovery"
    CONVERSATION_CONTEXT = "conversation_context"
    QUERY_RESULT = "query_result"
    EMBEDDING = "embedding"
    KNOWLEDGE = "knowledge"
    EVENT = "event"

# TTLs padrão por tipo de dado (em segundos)
DEFAULT_TTL = {
    DataType.TOOL_DISCOVERY: 14400,       # 4 horas (ferramentas padrão)
    DataType.CONVERSATION_CONTEXT: 172800, # 48 horas (contexto padrão)
    DataType.QUERY_RESULT: 3600,          # 1 hora
    DataType.EMBEDDING: 86400,            # 24 horas
    DataType.KNOWLEDGE: 604800,           # 7 dias
    DataType.EVENT: 3600,                 # 1 hora
}

# TTLs específicos para ferramentas por MCP (em segundos)
# Algumas ferramentas são atualizadas com mais frequência que outras
TOOL_DISCOVERY_TTL = {
    'mcp-mongodb': 28800,      # 8 horas (atualização menos frequente)
    'mcp-redis': 14400,        # 4 horas (atualização moderada)
    'mcp-chatwoot': 7200,      # 2 horas (atualização mais frequente)
    'mcp-qdrant': 14400,       # 4 horas (atualização moderada)
    'default': 14400           # 4 horas (valor padrão)
}

# TTLs específicos para contextos de conversação por importância (em segundos)
CONVERSATION_CONTEXT_TTL = {
    'high': 604800,            # 7 dias (conversas importantes)
    'medium': 259200,          # 3 dias (conversas regulares)
    'low': 86400,              # 1 dia (conversas de baixa importância)
    'default': 172800          # 2 dias (valor padrão)
}

class CircuitBreaker:
    """Implementa um circuit breaker para proteger contra falhas em cascata."""
    
    def __init__(self, failure_threshold: int = 5, reset_timeout: int = 30):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.last_failure_time = 0
        self.is_open = False
        
    def record_failure(self):
        """Registra uma falha e potencialmente abre o circuit breaker."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.is_open = True
            logger.warning("Circuit breaker aberto após %s falhas", self.failure_count)
    
    def record_success(self):
        """Registra um sucesso e reseta o contador de falhas."""
        self.failure_count = 0
        self.is_open = False
    
    def allow_request(self) -> bool:
        """Verifica se uma requisição deve ser permitida."""
        if not self.is_open:
            return True
            
        # Verifica se o tempo de reset passou
        if time.time() - self.last_failure_time >= self.reset_timeout:
            logger.info("Tentando fechar circuit breaker após timeout de %s segundos", self.reset_timeout)
            self.is_open = False
            return True
            
        return False


class RedisManager:
    """
    Gerencia conexões e operações Redis para o MCP-Crew.
    
    Esta classe implementa:
    - Conexão com Redis
    - Particionamento por tenant
    - Cache com TTL configurável por tipo de dado
    - Circuit breakers para proteção contra falhas
    """
    
    def __init__(
        self,
        host: str = None,
        port: int = None,
        db: int = None,
        password: Optional[str] = None,
        prefix: str = None,
        connection_pool_size: int = None,
    ):
        """
        Inicializa o RedisManager.
        
        Args:
            host: Host do Redis (default: valor da variável de ambiente REDIS_CREW_HOST ou "redis-crew")
            port: Porta do Redis (default: valor da variável de ambiente REDIS_CREW_PORT ou 6380)
            db: Banco de dados Redis (default: valor da variável de ambiente REDIS_CREW_DB ou 0)
            password: Senha do Redis (default: valor da variável de ambiente REDIS_CREW_PASSWORD)
            prefix: Prefixo para todas as chaves (default: valor da variável de ambiente REDIS_CREW_PREFIX ou "mcp-crew")
            connection_pool_size: Tamanho do pool de conexões (default: valor da variável de ambiente REDIS_CREW_POOL_SIZE ou 10)
        """
        # Usar valores de variáveis de ambiente ou defaults
        self.prefix = prefix or os.getenv('REDIS_CREW_PREFIX', 'mcp-crew')
        
        # Em desenvolvimento, usar localhost com a porta 6380 para o redis-crew
        host = host or os.getenv('REDIS_CREW_HOST', 'localhost')
        port = port or int(os.getenv('REDIS_CREW_PORT', 6380))
        db = db if db is not None else int(os.getenv('REDIS_CREW_DB', 0))
        password = password or os.getenv('REDIS_CREW_PASSWORD')
        connection_pool_size = connection_pool_size or int(os.getenv('REDIS_CREW_POOL_SIZE', 10))
        
        # Criar pool de conexões
        self.connection_pool = redis.ConnectionPool(
            host=host,
            port=port,
            db=db,
            password=password,
            max_connections=connection_pool_size,
            decode_responses=True,
            socket_timeout=5,
            socket_connect_timeout=5,
            retry_on_timeout=True
        )
        self.client = redis.Redis(connection_pool=self.connection_pool)
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=int(os.getenv('REDIS_CIRCUIT_BREAKER_THRESHOLD', 5)),
            reset_timeout=int(os.getenv('REDIS_CIRCUIT_BREAKER_TIMEOUT', 30))
        )
        
        # Verificar conexão
        try:
            self.client.ping()
            self.is_available = True
            logger.info("✅ RedisManager inicializado com conexão para %s:%s/db%s", host, port, db)
        except RedisError as e:
            self.is_available = False
            logger.warning("⚠️ Redis não disponível: %s. Sistema funcionará com fallback local.", str(e))
        
    def _get_key(self, tenant_id: str, data_type: str, identifier: str) -> str:
        """Gera uma chave Redis com o formato adequado para particionamento por tenant."""
        return f"{self.prefix}:{tenant_id}:{data_type}:{identifier}"
    
    def _execute_with_circuit_breaker(self, func, *args, **kwargs):
        """Executa uma função com proteção de circuit breaker."""
        if not self.circuit_breaker.allow_request():
            logger.error("Circuit breaker aberto, rejeitando requisição")
            raise RedisError("Circuit breaker aberto")
            
        try:
            result = func(*args, **kwargs)
            self.circuit_breaker.record_success()
            return result
        except RedisError as e:
            logger.error("Erro ao executar operação Redis: %s", str(e))
            self.circuit_breaker.record_failure()
            raise
    
    def set(self, tenant_id: str, data_type: str, identifier: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Armazena um valor no Redis com TTL configurável e fallback para cache local."""
        key = self._get_key(tenant_id, data_type, identifier)
        local_cache_key = f"{tenant_id}:{data_type}:{identifier}"
        
        # Usa TTL padrão se não especificado
        if ttl is None:
            ttl = DEFAULT_TTL.get(data_type, 3600)  # 1 hora como padrão se tipo desconhecido
        
        # Armazenar no cache local para fallback
        if not hasattr(self, '_local_cache'):
            self._local_cache = {}
        self._local_cache[local_cache_key] = value
            
        # Se o Redis não está disponível, usar apenas cache local
        if not self.is_available:
            logger.debug("Redis indisponível, usando apenas cache local para %s", key)
            return True
            
        try:
            # Serializa o valor como JSON
            serialized_value = json.dumps(value)
            
            # Executa o SET com proteção de circuit breaker
            return self._execute_with_circuit_breaker(
                lambda: self.client.setex(key, ttl, serialized_value) is True
            )
        except (RedisError, TypeError) as e:
            logger.error("Erro ao armazenar no Redis: %s", str(e))
            return False
    
    def get(self, tenant_id: str, data_type: str, identifier: str) -> Optional[Any]:
        """Recupera um valor do Redis com fallback para cache local."""
        key = self._get_key(tenant_id, data_type, identifier)
        local_cache_key = f"{tenant_id}:{data_type}:{identifier}"
        
        # Verificar se o Redis está disponível
        if not self.is_available:
            # Fallback para cache local
            if hasattr(self, '_local_cache') and local_cache_key in self._local_cache:
                logger.debug("Usando cache local para %s", key)
                return self._local_cache.get(local_cache_key)
            return None
        
        try:
            # Executa o GET com proteção de circuit breaker
            result = self._execute_with_circuit_breaker(lambda: self.client.get(key))
            
            if result is None:
                return None
                
            # Deserializa o valor JSON
            value = json.loads(result)
            
            # Armazenar no cache local para fallback
            if not hasattr(self, '_local_cache'):
                self._local_cache = {}
            self._local_cache[local_cache_key] = value
            
            return value
        except (RedisError, json.JSONDecodeError) as e:
            logger.error("Erro ao recuperar do Redis: %s", str(e))
            
            # Fallback para cache local
            if hasattr(self, '_local_cache') and local_cache_key in self._local_cache:
                logger.debug("Fallback para cache local após erro: %s", str(e))
                return self._local_cache.get(local_cache_key)
            
            return None
    
    def delete(self, tenant_id: str, data_type: str, identifier: str) -> bool:
        """Remove um valor do Redis e do cache local."""
        key = self._get_key(tenant_id, data_type, identifier)
        local_cache_key = f"{tenant_id}:{data_type}:{identifier}"
        
        # Remover do cache local
        if hasattr(self, '_local_cache') and local_cache_key in self._local_cache:
            del self._local_cache[local_cache_key]
        
        # Se o Redis não está disponível, considerar sucesso após remover do cache local
        if not self.is_available:
            return True
        
        try:
            # Executa o DELETE com proteção de circuit breaker
            return self._execute_with_circuit_breaker(lambda: self.client.delete(key) > 0)
        except RedisError as e:
            logger.error("Erro ao remover do Redis: %s", str(e))
            return False
    
    def exists(self, tenant_id: str, data_type: str, identifier: str) -> bool:
        """Verifica se uma chave existe no Redis ou no cache local."""
        key = self._get_key(tenant_id, data_type, identifier)
        local_cache_key = f"{tenant_id}:{data_type}:{identifier}"
        
        # Verificar no cache local primeiro
        if hasattr(self, '_local_cache') and local_cache_key in self._local_cache:
            return True
        
        # Se o Redis não está disponível, verificar apenas no cache local
        if not self.is_available:
            return False
        
        try:
            # Executa o EXISTS com proteção de circuit breaker
            return self._execute_with_circuit_breaker(lambda: self.client.exists(key) > 0)
        except RedisError as e:
            logger.error("Erro ao verificar existência no Redis: %s", str(e))
            return False
            
    # Métodos específicos para cache de ferramentas descobertas
    
    def set_tool_discovery_cache(self, tenant_id: str, mcp_id: str, tools: List[Dict]) -> bool:
        """Armazena ferramentas descobertas no cache."""
        return self.set(tenant_id, DataType.TOOL_DISCOVERY, mcp_id, tools)
    
    def get_tool_discovery_cache(self, tenant_id: str, mcp_id: str) -> Optional[List[Dict]]:
        """Recupera ferramentas descobertas do cache."""
        return self.get(tenant_id, DataType.TOOL_DISCOVERY, mcp_id)
    
    def clear_tool_discovery_cache(self, tenant_id: str, mcp_id: str) -> bool:
        """Limpa o cache de ferramentas descobertas para um MCP específico."""
        return self.delete(tenant_id, DataType.TOOL_DISCOVERY, mcp_id)
    
    # Métodos específicos para contexto de conversas
    
    def set_conversation_context(self, tenant_id: str, conversation_id: str, context: Dict, importance: str = 'default') -> bool:
        """Armazena contexto de conversa no cache com TTL baseado na importância.
        
        Args:
            tenant_id: ID do tenant (account_id)
            conversation_id: ID da conversa
            context: Dicionário com o contexto da conversa
            importance: Nível de importância ('high', 'medium', 'low', 'default')
        """
        # Obter TTL específico baseado na importância
        ttl = CONVERSATION_CONTEXT_TTL.get(importance, CONVERSATION_CONTEXT_TTL['default'])
        return self.set(tenant_id, DataType.CONVERSATION_CONTEXT, conversation_id, context, ttl=ttl)
    
    def get_conversation_context(self, tenant_id: str, conversation_id: str) -> Optional[Dict]:
        """Recupera contexto de conversa do cache."""
        return self.get(tenant_id, DataType.CONVERSATION_CONTEXT, conversation_id)
    
    def update_conversation_context(self, tenant_id: str, conversation_id: str, update_func, importance: str = 'default') -> bool:
        """Atualiza contexto de conversa usando uma função de atualização.
        
        Args:
            tenant_id: ID do tenant (account_id)
            conversation_id: ID da conversa
            update_func: Função que recebe o contexto atual e retorna o contexto atualizado
            importance: Nível de importância ('high', 'medium', 'low', 'default')
        """
        try:
            # Recupera o contexto atual
            context = self.get_conversation_context(tenant_id, conversation_id) or {}
            
            # Aplica a função de atualização
            updated_context = update_func(context)
            
            # Armazena o contexto atualizado com o nível de importância especificado
            return self.set_conversation_context(tenant_id, conversation_id, updated_context, importance)
        except Exception as e:
            logger.error("Erro ao atualizar contexto de conversa: %s", str(e))
            return False
    
    # Métodos específicos para resultados de consultas
    
    def set_query_result(self, tenant_id: str, query_hash: str, result: Any) -> bool:
        """Armazena resultado de consulta no cache."""
        return self.set(tenant_id, DataType.QUERY_RESULT, query_hash, result)
    
    def get_query_result(self, tenant_id: str, query_hash: str) -> Optional[Any]:
        """Recupera resultado de consulta do cache."""
        return self.get(tenant_id, DataType.QUERY_RESULT, query_hash)
    
    # Métodos específicos para embeddings
    
    def set_embedding(self, tenant_id: str, text_hash: str, embedding: List[float]) -> bool:
        """Armazena embedding no cache."""
        return self.set(tenant_id, DataType.EMBEDDING, text_hash, embedding)
    
    def get_embedding(self, tenant_id: str, text_hash: str) -> Optional[List[float]]:
        """Recupera embedding do cache."""
        return self.get(tenant_id, DataType.EMBEDDING, text_hash)
    
    # Métodos para gerenciamento de chaves
    
    def get_keys_by_pattern(self, tenant_id: str, data_type: str, pattern: str = "*") -> List[str]:
        """Recupera chaves que correspondem a um padrão."""
        full_pattern = self._get_key(tenant_id, data_type, pattern)
        
        try:
            keys = self._execute_with_circuit_breaker(lambda: self.client.keys(full_pattern))
            return keys or []
        except RedisError as e:
            logger.error("Erro ao buscar chaves por padrão: %s", str(e))
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """Recupera estatísticas do Redis."""
        if not self.is_available:
            return {
                "status": "indisponível",
                "local_cache_items": len(getattr(self, '_local_cache', {})),
                "circuit_breaker_open": self.circuit_breaker.is_open,
                "circuit_breaker_failures": self.circuit_breaker.failure_count,
            }
            
        try:
            info = self._execute_with_circuit_breaker(lambda: self.client.info())
            return {
                "status": "disponível",
                "used_memory": info.get("used_memory_human", "N/A"),
                "clients_connected": info.get("connected_clients", 0),
                "uptime_days": info.get("uptime_in_days", 0),
                "total_keys": sum(db.get("keys", 0) for db_name, db in info.items() if db_name.startswith("db")),
                "circuit_breaker_open": self.circuit_breaker.is_open,
                "circuit_breaker_failures": self.circuit_breaker.failure_count,
                "local_cache_items": len(getattr(self, '_local_cache', {})),
            }
        except RedisError as e:
            logger.error("Erro ao recuperar estatísticas do Redis: %s", str(e))
            return {"error": str(e)}

# Instância global do RedisManager
redis_manager = RedisManager()
