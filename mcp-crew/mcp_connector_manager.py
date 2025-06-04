"""
Gerenciador de Conectores MCP para o MCP-Crew.

Este módulo implementa o MCPConnectorManager, responsável por gerenciar
os conectores MCP, incluindo sua criação, configuração e ciclo de vida.
Suporta multi-tenancy via account_id e integração com o CrewAI.
"""

import asyncio
import aiohttp
from typing import Dict, List, Optional, Any, Union, Type
import time
from enum import Enum
import json

from .mcp_connector import MCPConnector, MCPConnectorRegistry, MCPStatus
from .context_manager import ContextManager, ContextType

from utils.logging import get_logger
logger = get_logger(__name__)


class MCPConnectorManager:
    """
    Gerenciador de conectores MCP.
    
    Responsável por gerenciar o ciclo de vida dos conectores MCP,
    incluindo criação, configuração, conexão e desconexão.
    Suporta multi-tenancy via account_id.
    """
    
    def __init__(self, context_manager: ContextManager):
        """
        Inicializa o gerenciador de conectores MCP.
        
        Args:
            context_manager: Gerenciador de contexto para armazenar dados relacionados aos conectores
        """
        self.registry = MCPConnectorRegistry()
        self.context_manager = context_manager
        self.session = None
        logger.info("MCPConnectorManager inicializado")
    
    async def initialize(self):
        """
        Inicializa o gerenciador, criando a sessão HTTP compartilhada.
        """
        if self.session is None:
            self.session = aiohttp.ClientSession()
            logger.info("Sessão HTTP compartilhada criada")
        return self
    
    async def shutdown(self):
        """
        Encerra o gerenciador, fechando a sessão HTTP compartilhada
        e desconectando todos os conectores.
        """
        # Desconecta todos os conectores
        for connector in self.registry.get_all_connectors():
            try:
                await connector.disconnect()
            except Exception as e:
                logger.error(f"Erro ao desconectar conector {connector.mcp_id}: {e}")
        
        # Fecha a sessão HTTP
        if self.session:
            await self.session.close()
            self.session = None
            logger.info("Sessão HTTP compartilhada fechada")
    
    async def create_connector(
        self,
        connector_type: Type[MCPConnector],
        mcp_id: str,
        base_url: str,
        config: Dict[str, Any]
    ) -> MCPConnector:
        """
        Cria um novo conector MCP.
        
        Args:
            connector_type: Tipo de conector a ser criado (classe)
            mcp_id: ID único do MCP
            base_url: URL base do MCP
            config: Configurações específicas do conector
            
        Returns:
            Conector MCP criado
        """
        if self.session is None:
            await self.initialize()
        
        # Cria o conector
        connector = connector_type(
            mcp_id=mcp_id,
            base_url=base_url,
            session=self.session,
            **config
        )
        
        # Registra o conector
        self.registry.register_connector(connector)
        
        logger.info(f"Conector {mcp_id} criado e registrado")
        return connector
    
    async def connect_all(self) -> Dict[str, bool]:
        """
        Conecta todos os conectores registrados.
        
        Returns:
            Dicionário com o resultado da conexão para cada conector
        """
        results = {}
        for connector in self.registry.get_all_connectors():
            try:
                results[connector.mcp_id] = await connector.connect()
            except Exception as e:
                logger.error(f"Erro ao conectar conector {connector.mcp_id}: {e}")
                results[connector.mcp_id] = False
        
        return results
    
    async def connect(self, mcp_id: str) -> bool:
        """
        Conecta um conector específico.
        
        Args:
            mcp_id: ID do conector
            
        Returns:
            True se conectado com sucesso, False caso contrário
        """
        connector = self.registry.get_connector(mcp_id)
        if not connector:
            logger.error(f"Conector {mcp_id} não encontrado")
            return False
        
        try:
            return await connector.connect()
        except Exception as e:
            logger.error(f"Erro ao conectar conector {mcp_id}: {e}")
            return False
    
    async def disconnect(self, mcp_id: str) -> bool:
        """
        Desconecta um conector específico.
        
        Args:
            mcp_id: ID do conector
            
        Returns:
            True se desconectado com sucesso, False caso contrário
        """
        connector = self.registry.get_connector(mcp_id)
        if not connector:
            logger.error(f"Conector {mcp_id} não encontrado")
            return False
        
        try:
            return await connector.disconnect()
        except Exception as e:
            logger.error(f"Erro ao desconectar conector {mcp_id}: {e}")
            return False
    
    async def execute_operation(
        self,
        mcp_id: str,
        account_id: str,
        operation: str,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, str]] = None,
        payload: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Executa uma operação em um conector específico.
        
        Args:
            mcp_id: ID do conector
            account_id: ID da conta (tenant)
            operation: Nome da operação
            method: Método HTTP
            endpoint: Endpoint da API
            params: Parâmetros da URL
            payload: Dados do corpo da requisição
            headers: Cabeçalhos HTTP adicionais
            
        Returns:
            Resultado da operação
        """
        connector = self.registry.get_connector(mcp_id)
        if not connector:
            logger.error(f"Conector {mcp_id} não encontrado")
            raise ValueError(f"Conector {mcp_id} não encontrado")
        
        # Verifica se o conector está conectado
        if not await connector.is_connected():
            logger.info(f"Conector {mcp_id} não está conectado. Tentando conectar...")
            if not await connector.connect():
                logger.error(f"Falha ao conectar conector {mcp_id}")
                raise ConnectionError(f"Falha ao conectar conector {mcp_id}")
        
        # Executa a operação
        try:
            result = await connector.execute_operation(
                account_id=account_id,
                operation=operation,
                method=method,
                endpoint=endpoint,
                params=params,
                payload=payload,
                headers=headers
            )
            
            # Armazena o resultado no contexto
            context_data = {
                "operation": operation,
                "mcp_id": mcp_id,
                "result": result,
                "timestamp": time.time()
            }
            
            self.context_manager.create_context(
                context_type=ContextType.TASK,
                owner_id=f"{account_id}:{mcp_id}",
                data=context_data,
                ttl=3600,  # 1 hora
                metadata={
                    "account_id": account_id,
                    "mcp_id": mcp_id,
                    "operation": operation
                }
            )
            
            return result
        except Exception as e:
            logger.error(f"Erro ao executar operação {operation} no conector {mcp_id}: {e}")
            raise
    
    def get_connector_status(self, mcp_id: str) -> Dict[str, Any]:
        """
        Obtém o status de um conector específico.
        
        Args:
            mcp_id: ID do conector
            
        Returns:
            Dicionário com informações de status do conector
        """
        connector = self.registry.get_connector(mcp_id)
        if not connector:
            logger.error(f"Conector {mcp_id} não encontrado")
            return {"error": f"Conector {mcp_id} não encontrado"}
        
        return connector.to_dict()
    
    def get_all_connectors_status(self) -> List[Dict[str, Any]]:
        """
        Obtém o status de todos os conectores registrados.
        
        Returns:
            Lista de dicionários com informações de status dos conectores
        """
        return [connector.to_dict() for connector in self.registry.get_all_connectors()]
    
    def get_connector_by_account(self, account_id: str, mcp_id: str) -> Optional[MCPConnector]:
        """
        Obtém um conector para uma conta específica.
        
        Args:
            account_id: ID da conta (tenant)
            mcp_id: ID do conector
            
        Returns:
            Conector MCP ou None se não encontrado
        """
        connector = self.registry.get_connector(mcp_id)
        if not connector:
            logger.error(f"Conector {mcp_id} não encontrado para conta {account_id}")
            return None
        
        # Verifica se o conector está associado à conta
        contexts = self.context_manager.get_contexts_by_owner(
            owner_id=f"{account_id}:{mcp_id}",
            context_type=ContextType.TASK
        )
        
        if not contexts:
            logger.warning(f"Conector {mcp_id} não tem contextos associados à conta {account_id}")
        
        return connector
    
    def to_crewai_tools(self, mcp_id: str) -> List[Dict[str, Any]]:
        """
        Converte um conector MCP em ferramentas para o CrewAI.
        
        Args:
            mcp_id: ID do conector
            
        Returns:
            Lista de ferramentas no formato esperado pelo CrewAI
        """
        connector = self.registry.get_connector(mcp_id)
        if not connector:
            logger.error(f"Conector {mcp_id} não encontrado")
            return []
        
        # Define as ferramentas básicas para o conector
        tools = [
            {
                "name": f"{mcp_id}_status",
                "description": f"Verifica o status do conector {mcp_id}",
                "function": lambda: connector.to_dict()
            },
            {
                "name": f"{mcp_id}_connect",
                "description": f"Conecta ao {mcp_id}",
                "function": lambda: asyncio.run(connector.connect())
            }
        ]
        
        # Adiciona ferramentas específicas do conector
        # Isso depende da implementação de cada conector
        # e pode ser estendido nas classes derivadas
        
        return tools
