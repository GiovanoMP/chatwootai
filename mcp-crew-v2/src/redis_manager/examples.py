"""
Exemplos de uso do RedisManager para o MCP-Crew v2.

Este módulo contém exemplos de como utilizar o RedisManager
em diferentes contextos do MCP-Crew.
"""

import hashlib
import json
import logging
from typing import Dict, List, Optional

from src.redis_manager.redis_manager import RedisManager, DataType

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def exemplo_cache_tool_discovery():
    """Exemplo de uso do RedisManager para cache de ferramentas descobertas."""
    # Inicializa o RedisManager
    redis_manager = RedisManager(
        host="redis-crew",
        port=6380,
        prefix="mcp-crew",
    )
    
    # Tenant e MCP IDs para o exemplo
    tenant_id = "tenant1"
    mcp_id = "mongodb"
    
    # Exemplo de ferramentas descobertas
    tools = [
        {
            "name": "find_documents",
            "description": "Encontra documentos em uma coleção MongoDB",
            "parameters": {
                "collection": "string",
                "query": "object",
                "limit": "integer",
            },
        },
        {
            "name": "insert_document",
            "description": "Insere um documento em uma coleção MongoDB",
            "parameters": {
                "collection": "string",
                "document": "object",
            },
        },
    ]
    
    # Armazena as ferramentas no cache
    success = redis_manager.set_tool_discovery_cache(tenant_id, mcp_id, tools)
    logger.info("Ferramentas armazenadas no cache: %s", success)
    
    # Recupera as ferramentas do cache
    cached_tools = redis_manager.get_tool_discovery_cache(tenant_id, mcp_id)
    logger.info("Ferramentas recuperadas do cache: %s", cached_tools)
    
    # Limpa o cache
    cleared = redis_manager.clear_tool_discovery_cache(tenant_id, mcp_id)
    logger.info("Cache limpo: %s", cleared)


def exemplo_contexto_conversa():
    """Exemplo de uso do RedisManager para contexto de conversas."""
    # Inicializa o RedisManager
    redis_manager = RedisManager(
        host="redis-crew",
        port=6380,
        prefix="mcp-crew",
    )
    
    # Tenant e ID de conversa para o exemplo
    tenant_id = "tenant1"
    conversation_id = "conv123"
    
    # Exemplo de contexto inicial
    context = {
        "user_name": "João",
        "last_query": "Como posso ajudar com vendas?",
        "session_data": {
            "start_time": "2023-06-12T10:00:00",
            "messages_count": 1,
        },
    }
    
    # Armazena o contexto
    success = redis_manager.set_conversation_context(tenant_id, conversation_id, context)
    logger.info("Contexto armazenado: %s", success)
    
    # Recupera o contexto
    cached_context = redis_manager.get_conversation_context(tenant_id, conversation_id)
    logger.info("Contexto recuperado: %s", cached_context)
    
    # Atualiza o contexto usando uma função
    def update_context(current_context):
        current_context["session_data"]["messages_count"] += 1
        current_context["last_query"] = "Quais são os produtos mais vendidos?"
        return current_context
    
    updated = redis_manager.update_conversation_context(tenant_id, conversation_id, update_context)
    logger.info("Contexto atualizado: %s", updated)
    
    # Recupera o contexto atualizado
    updated_context = redis_manager.get_conversation_context(tenant_id, conversation_id)
    logger.info("Contexto atualizado recuperado: %s", updated_context)


def exemplo_cache_consultas():
    """Exemplo de uso do RedisManager para cache de resultados de consultas."""
    # Inicializa o RedisManager
    redis_manager = RedisManager(
        host="redis-crew",
        port=6380,
        prefix="mcp-crew",
    )
    
    # Tenant para o exemplo
    tenant_id = "tenant1"
    
    # Exemplo de consulta
    query = {
        "collection": "produtos",
        "filter": {"categoria": "eletrônicos"},
        "sort": {"preco": 1},
        "limit": 10,
    }
    
    # Gera um hash para a consulta
    query_hash = hashlib.md5(json.dumps(query, sort_keys=True).encode()).hexdigest()
    
    # Exemplo de resultado de consulta
    result = [
        {"id": 1, "nome": "Smartphone", "preco": 1200.00},
        {"id": 2, "nome": "Fones de ouvido", "preco": 150.00},
        {"id": 3, "nome": "Carregador", "preco": 50.00},
    ]
    
    # Armazena o resultado no cache
    success = redis_manager.set_query_result(tenant_id, query_hash, result)
    logger.info("Resultado armazenado no cache: %s", success)
    
    # Recupera o resultado do cache
    cached_result = redis_manager.get_query_result(tenant_id, query_hash)
    logger.info("Resultado recuperado do cache: %s", cached_result)


def exemplo_embeddings():
    """Exemplo de uso do RedisManager para cache de embeddings."""
    # Inicializa o RedisManager
    redis_manager = RedisManager(
        host="redis-crew",
        port=6380,
        prefix="mcp-crew",
    )
    
    # Tenant para o exemplo
    tenant_id = "tenant1"
    
    # Exemplo de texto
    text = "Como posso ajudar com vendas de produtos eletrônicos?"
    
    # Gera um hash para o texto
    text_hash = hashlib.md5(text.encode()).hexdigest()
    
    # Exemplo de embedding (normalmente seria gerado por um modelo)
    embedding = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    
    # Armazena o embedding no cache
    success = redis_manager.set_embedding(tenant_id, text_hash, embedding)
    logger.info("Embedding armazenado no cache: %s", success)
    
    # Recupera o embedding do cache
    cached_embedding = redis_manager.get_embedding(tenant_id, text_hash)
    logger.info("Embedding recuperado do cache: %s", cached_embedding)


def exemplo_estatisticas():
    """Exemplo de uso do RedisManager para obter estatísticas."""
    # Inicializa o RedisManager
    redis_manager = RedisManager(
        host="redis-crew",
        port=6380,
        prefix="mcp-crew",
    )
    
    # Obtém estatísticas
    stats = redis_manager.get_stats()
    logger.info("Estatísticas do Redis: %s", stats)


if __name__ == "__main__":
    # Executa todos os exemplos
    exemplo_cache_tool_discovery()
    exemplo_contexto_conversa()
    exemplo_cache_consultas()
    exemplo_embeddings()
    exemplo_estatisticas()
