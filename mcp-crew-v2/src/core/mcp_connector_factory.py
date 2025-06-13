#!/usr/bin/env python3
"""
MCP Connector Factory - Fábrica de conectores para MCPs
Responsável por criar e gerenciar conectores para diferentes MCPs
"""

import logging
import importlib.util
import logging
from typing import Dict, Any, List, Optional, Type, Union
from dataclasses import asdict

from src.core.tool_metadata import ToolMetadata
# Importar adaptadores locais
from src.connectors.mongodb_adapter import MongoDBAdapter
from src.connectors.chatwoot_dynamic_adapter import ChatwootDynamicAdapter

logger = logging.getLogger(__name__)

class MCPConnectorFactory:
    """
    Fábrica de conectores para MCPs.
    Responsável por criar instâncias de conectores para diferentes MCPs.
    """
    
    def get_connector(self, mcp_name: str, config: Any) -> Optional[Any]:
        """
        Obtém um conector para o MCP especificado.
        
        Args:
            mcp_name: Nome do MCP (mongodb, chatwoot, redis, qdrant)
            config: Configuração do MCP (pode ser Dict ou MCPConfig)
            
        Returns:
            Instância do conector ou None se não for possível criar
        """
        try:
            # Remover prefixo 'mcp-' se existir
            mcp_name_clean = mcp_name.replace('mcp-', '')
            
            # Extrair URL e outros parâmetros da configuração
            # Verifica se config é um dicionário ou um objeto MCPConfig
            if hasattr(config, 'url'):
                # É um objeto MCPConfig
                url = config.url
                timeout = getattr(config, 'timeout', 10)
                tenant_id = getattr(config, 'tenant_id', 'account_1')
            else:
                # É um dicionário
                url = config.get('url', f'http://localhost:8001')
                timeout = config.get('timeout', 10)
                tenant_id = config.get('tenant_id', 'account_1')
            
            if mcp_name_clean == "mongodb":
                # Usar o adaptador MongoDB local
                try:
                    return MongoDBAdapter(
                        base_url=url, 
                        tenant_id=tenant_id
                    )
                except Exception as e:
                    logger.error(f"Erro ao criar adaptador MongoDB: {e}")
                    return None
            
            elif mcp_name_clean == "chatwoot":
                # Usar o adaptador Chatwoot local
                try:
                    return ChatwootDynamicAdapter(
                        base_url=url
                    )
                except Exception as e:
                    logger.error(f"Erro ao criar adaptador Chatwoot: {e}")
                    return None
            
            elif mcp_name_clean in ['redis', 'qdrant']:
                # Verificar se os módulos MCPAdapt estão disponíveis
                if self._check_module_availability('mcpadapt.core') and self._check_module_availability('mcpadapt.crewai_adapter'):
                    from mcpadapt.core import MCPAdapt
                    from mcpadapt.crewai_adapter import CrewAIAdapter
                    
                    # Configuração para conexão SSE
                    sse_config = {
                        "url": f"{url}/sse",
                        "timeout": timeout
                    }
                    
                    # Retorna uma função que cria o contexto do MCPAdapt
                    # Isso é necessário porque MCPAdapt deve ser usado em um context manager
                    return lambda: MCPAdapt(sse_config, CrewAIAdapter())
            
            logger.warning(f"Nenhum conector disponível para {mcp_name}")
            return None
        except Exception as e:
            logger.error(f"Erro ao obter conector para {mcp_name}: {e}")
            return None
    
    def _check_module_availability(self, module_name: str) -> bool:
        """
        Verifica se um módulo está disponível para importação.
        
        Args:
            module_name: Nome do módulo a verificar
            
        Returns:
            True se o módulo estiver disponível, False caso contrário
        """
        try:
            spec = importlib.util.find_spec(module_name)
            return spec is not None
        except (ImportError, AttributeError):
            return False
    
    @staticmethod
    def convert_adapter_tools_to_metadata(adapter_tools: List[Any], mcp_name: str) -> List[Dict[str, Any]]:
        """
        Converte ferramentas do adaptador para o formato de metadados.
        
        Args:
            adapter_tools: Lista de ferramentas do adaptador
            mcp_name: Nome do MCP
            
        Returns:
            Lista de ferramentas no formato de metadados
        """
        tools_metadata = []
        
        for tool in adapter_tools:
            try:
                # Extrair informações da ferramenta
                tool_metadata = {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": {},
                    "mcp_source": mcp_name
                }
                
                # Tentar extrair parâmetros se disponíveis
                try:
                    if hasattr(tool, 'args_schema') and hasattr(tool.args_schema, 'schema'):
                        schema = tool.args_schema.schema()
                        if 'properties' in schema:
                            for param_name, param_info in schema['properties'].items():
                                tool_metadata["parameters"][param_name] = {
                                    "type": param_info.get('type', 'any'),
                                    "description": param_info.get('description', '')
                                }
                except Exception as e:
                    logger.warning(f"Erro ao extrair parâmetros da ferramenta {tool.name}: {e}")
                
                tools_metadata.append(tool_metadata)
            except Exception as e:
                logger.error(f"Erro ao converter ferramenta para metadados: {e}")
        
        return tools_metadata


# Criar instância global da fábrica de conectores
mcp_connector_factory = MCPConnectorFactory()
