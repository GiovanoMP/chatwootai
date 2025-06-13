"""
MCP-Crew System v2 - Configuração e Utilitários
Sistema atualizado com provisão dinâmica de ferramentas e compartilhamento de conhecimento
"""

import os
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import json

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configurações do sistema
@dataclass
class MCPConfig:
    """Configuração de um MCP específico"""
    name: str
    url: str
    enabled: bool = True
    cache_ttl: int = 3600  # TTL em segundos para cache de ferramentas
    health_check_interval: int = 300  # Intervalo de health check em segundos
    max_retries: int = 3
    timeout: int = 30

class Config:
    """Configurações centrais do sistema MCP-Crew v2"""
    
    # Configurações Redis
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
    REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None)
    REDIS_DB = int(os.getenv('REDIS_DB', 0))
    
    # Configurações de Cache
    DEFAULT_CACHE_TTL = int(os.getenv('DEFAULT_CACHE_TTL', 3600))
    TOOLS_CACHE_TTL = int(os.getenv('TOOLS_CACHE_TTL', 7200))  # 2 horas para ferramentas
    KNOWLEDGE_CACHE_TTL = int(os.getenv('KNOWLEDGE_CACHE_TTL', 1800))  # 30 min para conhecimento
    
    # Configurações de Performance
    MAX_WORKERS = int(os.getenv('MAX_WORKERS', 4))
    REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', 30))
    MAX_CONCURRENT_REQUESTS = int(os.getenv('MAX_CONCURRENT_REQUESTS', 100))
    
    # Configurações de Segurança
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'mcp-crew-secret-key-change-in-production')
    ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY', 'encryption-key-change-in-production')
    
    # Configurações de MCPs
    MCP_REGISTRY = {
        'mcp-mongodb': MCPConfig(
            name='mcp-mongodb',
            url=os.getenv('MCP_MONGODB_URL', 'http://localhost:8001'),
            cache_ttl=3600
        ),
        'mcp-redis': MCPConfig(
            name='mcp-redis', 
            url=os.getenv('MCP_REDIS_URL', 'http://localhost:8002'),
            cache_ttl=1800
        ),
        'mcp-chatwoot': MCPConfig(
            name='mcp-chatwoot',
            url=os.getenv('MCP_CHATWOOT_URL', 'http://localhost:8004'),
            cache_ttl=900
        ),
        'mcp-qdrant': MCPConfig(
            name='mcp-qdrant',
            url=os.getenv('MCP_QDRANT_URL', 'http://localhost:8003'),
            cache_ttl=7200
        )
    }
    
    # Configurações de Observabilidade
    ENABLE_TRACING = os.getenv('ENABLE_TRACING', 'true').lower() == 'true'
    ENABLE_METRICS = os.getenv('ENABLE_METRICS', 'true').lower() == 'true'
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# Importar o RedisManager robusto
from src.redis_manager.redis_manager import redis_manager, DataType

# Funções utilitárias para trabalhar com o RedisManager
def serialize_json(data: Any) -> str:
    """Serializa dados para JSON"""
    return json.dumps(data)

def deserialize_json(data: str) -> Any:
    """Deserializa dados de JSON"""
    return json.loads(data)

def get_knowledge_cache_key(account_id: str, topic: str, item_id: str) -> str:
    """Gera chave para cache de conhecimento"""
    return f"knowledge:{account_id}:{topic}:{item_id}"

def get_stream_name(account_id: str, stream_type: str) -> str:
    """Gera nome para stream Redis"""
    return f"stream:{account_id}:{stream_type}"


# Utilitários de cache
def get_cache_key(account_id: str, category: str, identifier: str) -> str:
    """Gera chave de cache padronizada"""
    return f"mcp_crew_v2:{account_id}:{category}:{identifier}"

def get_tools_cache_key(account_id: str, mcp_name: str, tool_name: str = "*") -> str:
    """Gera chave de cache para ferramentas"""
    return get_cache_key(account_id, f"tools:{mcp_name}", tool_name)

def get_knowledge_cache_key(account_id: str, topic: str, entity_id: str = "*") -> str:
    """Gera chave de cache para conhecimento"""
    return get_cache_key(account_id, f"knowledge:{topic}", entity_id)

def get_stream_name(account_id: str, stream_type: str) -> str:
    """Gera nome de stream padronizado"""
    return f"mcp_crew_v2:streams:{account_id}:{stream_type}"

# Utilitários de serialização
def serialize_json(data: Any) -> str:
    """Serializa dados para JSON"""
    try:
        return json.dumps(data, ensure_ascii=False, default=str)
    except Exception as e:
        logger.error(f"Erro ao serializar JSON: {e}")
        return "{}"

def deserialize_json(data: str) -> Any:
    """Deserializa dados de JSON"""
    try:
        return json.loads(data)
    except Exception as e:
        logger.error(f"Erro ao deserializar JSON: {e}")
        return {}

# Utilitários de validação
def validate_account_id(account_id: str) -> bool:
    """Valida formato do account_id"""
    if not account_id or not isinstance(account_id, str):
        return False
    return len(account_id) >= 3 and account_id.replace('_', '').replace('-', '').isalnum()

def validate_mcp_config(mcp_config: MCPConfig) -> bool:
    """Valida configuração de MCP"""
    if not mcp_config.name or not mcp_config.url:
        return False
    if not mcp_config.url.startswith(('http://', 'https://')):
        return False
    return True

# Configuração de logging baseada no ambiente
def setup_logging():
    """Configura logging baseado nas configurações"""
    level = getattr(logging, Config.LOG_LEVEL.upper(), logging.INFO)
    logging.getLogger().setLevel(level)
    
    # Configurar formatação específica para produção
    if os.getenv('ENVIRONMENT') == 'production':
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        for handler in logging.getLogger().handlers:
            handler.setFormatter(formatter)

# Inicializar logging
setup_logging()

