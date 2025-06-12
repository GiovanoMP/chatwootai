"""
MCP Dynamic Tool Discovery - Sistema de Descoberta Dinâmica de Ferramentas
Responsável por descobrir e gerenciar ferramentas de MCPs dinamicamente
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.config import Config, redis_manager, serialize_json, deserialize_json, get_tools_cache_key

logger = logging.getLogger(__name__)

@dataclass
class ToolMetadata:
    """Metadados de uma ferramenta MCP"""
    name: str
    description: str
    parameters: Dict[str, Any]
    mcp_source: str
    last_updated: float
    cache_key: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ToolMetadata':
        return cls(**data)

class MCPToolDiscovery:
    """Sistema de descoberta dinâmica de ferramentas de MCPs"""
    
    def __init__(self):
        self.discovered_tools: Dict[str, Dict[str, ToolMetadata]] = {}
        self.last_discovery_time: Dict[str, float] = {}
        self.discovery_lock = asyncio.Lock()
        
    async def discover_all_tools(self, account_id: str, force_refresh: bool = False) -> Dict[str, List[ToolMetadata]]:
        """Descobre ferramentas de todos os MCPs configurados"""
        async with self.discovery_lock:
            all_tools = {}
            
            # Usar ThreadPoolExecutor para descoberta paralela
            with ThreadPoolExecutor(max_workers=len(Config.MCP_REGISTRY)) as executor:
                future_to_mcp = {
                    executor.submit(self._discover_mcp_tools, account_id, mcp_name, mcp_config, force_refresh): mcp_name
                    for mcp_name, mcp_config in Config.MCP_REGISTRY.items()
                    if mcp_config.enabled
                }
                
                for future in as_completed(future_to_mcp):
                    mcp_name = future_to_mcp[future]
                    try:
                        tools = future.result()
                        if tools:
                            all_tools[mcp_name] = tools
                            logger.info(f"✅ Descobertas {len(tools)} ferramentas do {mcp_name}")
                    except Exception as e:
                        logger.error(f"❌ Erro ao descobrir ferramentas do {mcp_name}: {e}")
                        all_tools[mcp_name] = []
            
            return all_tools
    
    def _discover_mcp_tools(self, account_id: str, mcp_name: str, mcp_config, force_refresh: bool = False) -> List[ToolMetadata]:
        """Descobre ferramentas de um MCP específico"""
        cache_key = get_tools_cache_key(account_id, mcp_name, "all")
        
        # Verificar cache primeiro (se não forçar refresh)
        if not force_refresh:
            cached_tools = self._get_tools_from_cache(cache_key)
            if cached_tools:
                logger.debug(f"🔄 Ferramentas do {mcp_name} carregadas do cache")
                return cached_tools
        
        # Descobrir ferramentas do MCP
        try:
            tools = self._fetch_tools_from_mcp(mcp_name, mcp_config)
            if tools:
                # Armazenar no cache
                self._store_tools_in_cache(cache_key, tools, mcp_config.cache_ttl)
                logger.info(f"🔍 Descobertas {len(tools)} ferramentas do {mcp_name}")
                return tools
        except Exception as e:
            logger.error(f"❌ Erro ao descobrir ferramentas do {mcp_name}: {e}")
        
        return []
    
    def _fetch_tools_from_mcp(self, mcp_name: str, mcp_config) -> List[ToolMetadata]:
        """Busca ferramentas diretamente do MCP"""
        tools = []
        
        try:
            # Diferentes estratégias de descoberta baseadas no tipo de MCP
            if mcp_name == 'mcp-mongodb':
                tools = self._discover_mongodb_tools(mcp_config)
            elif mcp_name == 'mcp-redis':
                tools = self._discover_redis_tools(mcp_config)
            elif mcp_name == 'mcp-chatwoot':
                tools = self._discover_chatwoot_tools(mcp_config)
            elif mcp_name == 'mcp-qdrant':
                tools = self._discover_qdrant_tools(mcp_config)
            else:
                # Estratégia genérica para MCPs que seguem padrão
                tools = self._discover_generic_mcp_tools(mcp_config)
                
        except Exception as e:
            logger.error(f"Erro ao buscar ferramentas do {mcp_name}: {e}")
            
        return tools
    
    def _discover_mongodb_tools(self, mcp_config) -> List[ToolMetadata]:
        """Descobre ferramentas do MCP-MongoDB"""
        tools = []
        try:
            # MCP-MongoDB expõe endpoint /resources
            response = requests.get(f"{mcp_config.url}/resources", timeout=mcp_config.timeout)
            response.raise_for_status()
            
            resources_data = response.json()
            
            # Ferramentas padrão do MongoDB MCP
            standard_tools = [
                {
                    "name": "query_company_services",
                    "description": "Consulta serviços da empresa com filtros específicos",
                    "parameters": {
                        "filter": {"type": "object", "description": "Filtros para a consulta"},
                        "tenant_id": {"type": "string", "description": "ID do tenant"}
                    }
                },
                {
                    "name": "aggregate_company_services", 
                    "description": "Executa pipeline de agregação nos serviços da empresa",
                    "parameters": {
                        "pipeline": {"type": "array", "description": "Pipeline de agregação MongoDB"},
                        "tenant_id": {"type": "string", "description": "ID do tenant"}
                    }
                },
                {
                    "name": "query_tenants",
                    "description": "Consulta informações de tenants",
                    "parameters": {
                        "filter": {"type": "object", "description": "Filtros para a consulta"}
                    }
                },
                {
                    "name": "get_company_config",
                    "description": "Obtém configuração específica da empresa",
                    "parameters": {
                        "config_key": {"type": "string", "description": "Chave da configuração"},
                        "tenant_id": {"type": "string", "description": "ID do tenant"}
                    }
                }
            ]
            
            for tool_data in standard_tools:
                tool = ToolMetadata(
                    name=tool_data["name"],
                    description=tool_data["description"],
                    parameters=tool_data["parameters"],
                    mcp_source=mcp_config.name,
                    last_updated=time.time(),
                    cache_key=get_tools_cache_key("*", mcp_config.name, tool_data["name"])
                )
                tools.append(tool)
                
        except Exception as e:
            logger.error(f"Erro ao descobrir ferramentas MongoDB: {e}")
            
        return tools
    
    def _discover_redis_tools(self, mcp_config) -> List[ToolMetadata]:
        """Descobre ferramentas do MCP-Redis"""
        tools = []
        
        # Ferramentas padrão do Redis MCP
        redis_tools = [
            {
                "name": "string_get",
                "description": "Obtém valor de uma chave string no Redis",
                "parameters": {
                    "key": {"type": "string", "description": "Chave para buscar"}
                }
            },
            {
                "name": "string_set",
                "description": "Define valor de uma chave string no Redis",
                "parameters": {
                    "key": {"type": "string", "description": "Chave para definir"},
                    "value": {"type": "string", "description": "Valor para armazenar"},
                    "ttl": {"type": "integer", "description": "TTL em segundos (opcional)"}
                }
            },
            {
                "name": "hash_hget",
                "description": "Obtém valor de um campo em hash Redis",
                "parameters": {
                    "name": {"type": "string", "description": "Nome do hash"},
                    "key": {"type": "string", "description": "Campo do hash"}
                }
            },
            {
                "name": "hash_hset",
                "description": "Define valor de um campo em hash Redis",
                "parameters": {
                    "name": {"type": "string", "description": "Nome do hash"},
                    "key": {"type": "string", "description": "Campo do hash"},
                    "value": {"type": "string", "description": "Valor para armazenar"}
                }
            },
            {
                "name": "list_lpush",
                "description": "Adiciona elemento ao início de uma lista Redis",
                "parameters": {
                    "key": {"type": "string", "description": "Nome da lista"},
                    "value": {"type": "string", "description": "Valor para adicionar"}
                }
            },
            {
                "name": "stream_xadd",
                "description": "Adiciona mensagem a um Redis Stream",
                "parameters": {
                    "stream": {"type": "string", "description": "Nome do stream"},
                    "fields": {"type": "object", "description": "Campos da mensagem"},
                    "maxlen": {"type": "integer", "description": "Tamanho máximo do stream (opcional)"}
                }
            }
        ]
        
        for tool_data in redis_tools:
            tool = ToolMetadata(
                name=tool_data["name"],
                description=tool_data["description"],
                parameters=tool_data["parameters"],
                mcp_source=mcp_config.name,
                last_updated=time.time(),
                cache_key=get_tools_cache_key("*", mcp_config.name, tool_data["name"])
            )
            tools.append(tool)
            
        return tools
    
    def _discover_chatwoot_tools(self, mcp_config) -> List[ToolMetadata]:
        """Descobre ferramentas do MCP-Chatwoot"""
        tools = []
        
        # Ferramentas padrão do Chatwoot MCP
        chatwoot_tools = [
            {
                "name": "get_conversation",
                "description": "Obtém detalhes de uma conversa específica",
                "parameters": {
                    "conversation_id": {"type": "string", "description": "ID da conversa"}
                }
            },
            {
                "name": "reply_to_conversation",
                "description": "Responde a uma conversa existente",
                "parameters": {
                    "conversation_id": {"type": "string", "description": "ID da conversa"},
                    "message": {"type": "string", "description": "Mensagem para enviar"}
                }
            },
            {
                "name": "list_conversations",
                "description": "Lista conversas com filtros",
                "parameters": {
                    "status": {"type": "string", "description": "Status da conversa (opcional)"},
                    "assignee_id": {"type": "string", "description": "ID do responsável (opcional)"}
                }
            },
            {
                "name": "create_contact",
                "description": "Cria um novo contato no Chatwoot",
                "parameters": {
                    "name": {"type": "string", "description": "Nome do contato"},
                    "email": {"type": "string", "description": "Email do contato"},
                    "phone": {"type": "string", "description": "Telefone do contato (opcional)"}
                }
            },
            {
                "name": "search_contacts",
                "description": "Pesquisa contatos por critérios",
                "parameters": {
                    "query": {"type": "string", "description": "Termo de busca"}
                }
            }
        ]
        
        for tool_data in chatwoot_tools:
            tool = ToolMetadata(
                name=tool_data["name"],
                description=tool_data["description"],
                parameters=tool_data["parameters"],
                mcp_source=mcp_config.name,
                last_updated=time.time(),
                cache_key=get_tools_cache_key("*", mcp_config.name, tool_data["name"])
            )
            tools.append(tool)
            
        return tools
    
    def _discover_qdrant_tools(self, mcp_config) -> List[ToolMetadata]:
        """Descobre ferramentas do MCP-Qdrant"""
        tools = []
        
        # Ferramentas padrão do Qdrant MCP
        qdrant_tools = [
            {
                "name": "search_semantic",
                "description": "Busca semântica usando embeddings vetoriais",
                "parameters": {
                    "collection": {"type": "string", "description": "Nome da coleção"},
                    "query_text": {"type": "string", "description": "Texto para busca semântica"},
                    "limit": {"type": "integer", "description": "Número máximo de resultados"}
                }
            },
            {
                "name": "store_embedding",
                "description": "Armazena embedding vetorial com metadados",
                "parameters": {
                    "collection": {"type": "string", "description": "Nome da coleção"},
                    "text": {"type": "string", "description": "Texto para gerar embedding"},
                    "metadata": {"type": "object", "description": "Metadados associados"}
                }
            },
            {
                "name": "filter_search",
                "description": "Busca com filtros específicos",
                "parameters": {
                    "collection": {"type": "string", "description": "Nome da coleção"},
                    "filters": {"type": "object", "description": "Filtros para aplicar"},
                    "limit": {"type": "integer", "description": "Número máximo de resultados"}
                }
            }
        ]
        
        for tool_data in qdrant_tools:
            tool = ToolMetadata(
                name=tool_data["name"],
                description=tool_data["description"],
                parameters=tool_data["parameters"],
                mcp_source=mcp_config.name,
                last_updated=time.time(),
                cache_key=get_tools_cache_key("*", mcp_config.name, tool_data["name"])
            )
            tools.append(tool)
            
        return tools
    
    def _discover_generic_mcp_tools(self, mcp_config) -> List[ToolMetadata]:
        """Estratégia genérica para descoberta de ferramentas MCP"""
        tools = []
        
        try:
            # Tentar endpoint padrão /tools ou /resources
            for endpoint in ['/tools', '/resources', '/capabilities']:
                try:
                    response = requests.get(f"{mcp_config.url}{endpoint}", timeout=mcp_config.timeout)
                    if response.status_code == 200:
                        data = response.json()
                        # Processar resposta baseada na estrutura
                        if 'tools' in data:
                            tools = self._parse_tools_response(data['tools'], mcp_config)
                        elif isinstance(data, list):
                            tools = self._parse_tools_response(data, mcp_config)
                        break
                except requests.RequestException:
                    continue
                    
        except Exception as e:
            logger.error(f"Erro na descoberta genérica: {e}")
            
        return tools
    
    def _parse_tools_response(self, tools_data: List[Dict], mcp_config) -> List[ToolMetadata]:
        """Parseia resposta de ferramentas de um MCP"""
        tools = []
        
        for tool_data in tools_data:
            try:
                tool = ToolMetadata(
                    name=tool_data.get('name', ''),
                    description=tool_data.get('description', ''),
                    parameters=tool_data.get('parameters', {}),
                    mcp_source=mcp_config.name,
                    last_updated=time.time(),
                    cache_key=get_tools_cache_key("*", mcp_config.name, tool_data.get('name', ''))
                )
                tools.append(tool)
            except Exception as e:
                logger.error(f"Erro ao parsear ferramenta: {e}")
                
        return tools
    
    def _get_tools_from_cache(self, cache_key: str) -> Optional[List[ToolMetadata]]:
        """Obtém ferramentas do cache Redis"""
        try:
            cached_data = redis_manager.get(cache_key)
            if cached_data:
                tools_data = deserialize_json(cached_data)
                return [ToolMetadata.from_dict(tool_dict) for tool_dict in tools_data]
        except Exception as e:
            logger.error(f"Erro ao obter ferramentas do cache: {e}")
        return None
    
    def _store_tools_in_cache(self, cache_key: str, tools: List[ToolMetadata], ttl: int):
        """Armazena ferramentas no cache Redis"""
        try:
            tools_data = [tool.to_dict() for tool in tools]
            serialized_data = serialize_json(tools_data)
            redis_manager.set(cache_key, serialized_data, ttl)
        except Exception as e:
            logger.error(f"Erro ao armazenar ferramentas no cache: {e}")
    
    async def invalidate_tools_cache(self, account_id: str, mcp_name: Optional[str] = None):
        """Invalida cache de ferramentas"""
        try:
            if mcp_name:
                # Invalidar cache de um MCP específico
                cache_key = get_tools_cache_key(account_id, mcp_name, "all")
                redis_manager.delete(cache_key)
                logger.info(f"🗑️ Cache de ferramentas do {mcp_name} invalidado")
            else:
                # Invalidar cache de todos os MCPs
                for mcp_name in Config.MCP_REGISTRY.keys():
                    cache_key = get_tools_cache_key(account_id, mcp_name, "all")
                    redis_manager.delete(cache_key)
                logger.info(f"🗑️ Cache de todas as ferramentas invalidado para {account_id}")
        except Exception as e:
            logger.error(f"Erro ao invalidar cache: {e}")
    
    def get_available_tools_summary(self, account_id: str) -> Dict[str, int]:
        """Obtém resumo das ferramentas disponíveis por MCP"""
        summary = {}
        
        for mcp_name in Config.MCP_REGISTRY.keys():
            cache_key = get_tools_cache_key(account_id, mcp_name, "all")
            cached_tools = self._get_tools_from_cache(cache_key)
            summary[mcp_name] = len(cached_tools) if cached_tools else 0
            
        return summary

# Instância global do descobridor de ferramentas
tool_discovery = MCPToolDiscovery()

