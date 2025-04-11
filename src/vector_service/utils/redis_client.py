"""
Cliente Redis

Este módulo contém funções para criar e gerenciar o cliente Redis.
"""

import os
import redis
import logging

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Variáveis globais
_redis_client = None

def get_redis_client():
    """
    Obtém uma instância do cliente Redis.
    
    Returns:
        redis.Redis: Cliente Redis configurado ou None se não disponível
    """
    global _redis_client
    
    if _redis_client is not None:
        return _redis_client
    
    # Verificar se Redis está habilitado
    redis_enabled = os.environ.get("REDIS_ENABLED", "true").lower() == "true"
    if not redis_enabled:
        logger.info("Redis is disabled by configuration")
        return None
    
    # Obter configurações do ambiente
    redis_host = os.environ.get("REDIS_HOST", "localhost")
    redis_port = int(os.environ.get("REDIS_PORT", 6379))
    redis_db = int(os.environ.get("REDIS_DB", 0))
    redis_password = os.environ.get("REDIS_PASSWORD")
    
    # Configurar cliente
    try:
        if redis_password:
            logger.info(f"Connecting to Redis at {redis_host}:{redis_port} with password")
            _redis_client = redis.Redis(
                host=redis_host,
                port=redis_port,
                db=redis_db,
                password=redis_password,
                decode_responses=False
            )
        else:
            logger.info(f"Connecting to Redis at {redis_host}:{redis_port} without password")
            _redis_client = redis.Redis(
                host=redis_host,
                port=redis_port,
                db=redis_db,
                decode_responses=False
            )
        
        # Verificar conexão
        _redis_client.ping()
        logger.info("Successfully connected to Redis")
        
        return _redis_client
    except Exception as e:
        logger.error(f"Error connecting to Redis: {str(e)}")
        return None
