"""
Integração do RedisManager com o sistema de descoberta de ferramentas do MCP-Crew.

Este módulo demonstra como integrar o RedisManager com o MCPToolDiscovery
para implementar cache de ferramentas descobertas.
"""

import hashlib
import json
import logging
import sys
import os

# Adiciona o diretório pai ao path para importar módulos do MCP-Crew
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from redis_manager import RedisManager, DataType
from mcp_tool_discovery import MCPToolDiscovery
from config import Config
from tool_metadata import ToolMetadata

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CachedMCPToolDiscovery(MCPToolDiscovery):
    """
    Extensão do MCPToolDiscovery que implementa cache de ferramentas
    descobertas usando o RedisManager.
    """
    
    def __init__(self, config=None):
        """
        Inicializa o CachedMCPToolDiscovery.
        
        Args:
            config: Configuração do MCP-Crew
        """
        super().__init__(config)
        
        # Inicializa o RedisManager
        self.redis_manager = RedisManager(
            host=os.environ.get("REDIS_HOST", "redis-crew"),
            port=int(os.environ.get("REDIS_PORT", 6380)),
            prefix="mcp-crew",
        )
        logger.info("CachedMCPToolDiscovery inicializado com RedisManager")
    
    def discover_tools(self, mcp_id, tenant_id="default"):
        """
        Descobre ferramentas de um MCP com cache Redis.
        
        Args:
            mcp_id: ID do MCP
            tenant_id: ID do tenant
            
        Returns:
            Lista de ferramentas descobertas
        """
        # Tenta recuperar do cache primeiro
        cached_tools = self.redis_manager.get_tool_discovery_cache(tenant_id, mcp_id)
        
        if cached_tools:
            logger.info("Ferramentas para MCP %s recuperadas do cache", mcp_id)
            return cached_tools
        
        # Se não estiver no cache, descobre as ferramentas normalmente
        logger.info("Cache miss para ferramentas do MCP %s, descobrindo...", mcp_id)
        tools = super().discover_tools(mcp_id)
        
        # Armazena no cache se a descoberta foi bem-sucedida
        if tools:
            self.redis_manager.set_tool_discovery_cache(tenant_id, mcp_id, tools)
            logger.info("Ferramentas para MCP %s armazenadas no cache", mcp_id)
        
        return tools
    
    def clear_tool_cache(self, mcp_id=None, tenant_id="default"):
        """
        Limpa o cache de ferramentas.
        
        Args:
            mcp_id: ID do MCP (se None, limpa para todos os MCPs)
            tenant_id: ID do tenant
            
        Returns:
            True se o cache foi limpo com sucesso
        """
        if mcp_id:
            # Limpa o cache para um MCP específico
            result = self.redis_manager.clear_tool_discovery_cache(tenant_id, mcp_id)
            logger.info("Cache de ferramentas para MCP %s limpo: %s", mcp_id, result)
            return result
        else:
            # Limpa o cache para todos os MCPs
            keys = self.redis_manager.get_keys_by_pattern(tenant_id, DataType.TOOL_DISCOVERY, "*")
            success = True
            
            for key in keys:
                # Extrai o MCP ID da chave
                parts = key.split(":")
                if len(parts) >= 4:
                    mcp_id = parts[3]
                    result = self.redis_manager.clear_tool_discovery_cache(tenant_id, mcp_id)
                    success = success and result
            
            logger.info("Cache de ferramentas para todos os MCPs limpo: %s", success)
            return success


def test_cached_tool_discovery():
    """Testa a integração do RedisManager com o MCPToolDiscovery."""
    # Carrega a configuração
    config = Config()
    
    # Inicializa o CachedMCPToolDiscovery
    discovery = CachedMCPToolDiscovery(config)
    
    # Lista de MCPs para testar
    mcps = ["mongodb", "redis", "qdrant", "chatwoot"]
    tenant_id = "test-tenant"
    
    # Limpa o cache para todos os MCPs
    discovery.clear_tool_cache(tenant_id=tenant_id)
    
    # Primeira descoberta (deve ir para o backend e armazenar no cache)
    for mcp_id in mcps:
        logger.info("Descobrindo ferramentas para MCP %s (primeira vez)", mcp_id)
        tools = discovery.discover_tools(mcp_id, tenant_id=tenant_id)
        logger.info("Ferramentas descobertas para MCP %s: %d", mcp_id, len(tools))
    
    # Segunda descoberta (deve vir do cache)
    for mcp_id in mcps:
        logger.info("Descobrindo ferramentas para MCP %s (segunda vez)", mcp_id)
        tools = discovery.discover_tools(mcp_id, tenant_id=tenant_id)
        logger.info("Ferramentas descobertas para MCP %s: %d", mcp_id, len(tools))
    
    # Limpa o cache para um MCP específico
    mcp_to_clear = mcps[0]
    discovery.clear_tool_cache(mcp_to_clear, tenant_id=tenant_id)
    
    # Terceira descoberta (deve vir do cache para todos exceto o que foi limpo)
    for mcp_id in mcps:
        logger.info("Descobrindo ferramentas para MCP %s (terceira vez)", mcp_id)
        tools = discovery.discover_tools(mcp_id, tenant_id=tenant_id)
        logger.info("Ferramentas descobertas para MCP %s: %d", mcp_id, len(tools))


if __name__ == "__main__":
    test_cached_tool_discovery()
