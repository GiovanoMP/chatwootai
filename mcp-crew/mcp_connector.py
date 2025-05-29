"""
Conectores para MCPs específicos.

Este módulo define a interface e implementações para conectores de MCPs,
permitindo que o MCP-Crew se comunique com diferentes MCPs específicos
(Mercado Livre, Instagram, Facebook, etc.) de forma padronizada.
"""

import abc
import json
import time
import uuid
from enum import Enum
from typing import Dict, List, Optional, Any, Union

import requests
from requests.exceptions import RequestException

from ..utils.logging import get_logger

logger = get_logger(__name__)

class MCPStatus(Enum):
    """Status de um MCP."""
    DISCONNECTED = "disconnected"  # Não conectado
    CONNECTING = "connecting"      # Conectando
    CONNECTED = "connected"        # Conectado
    ERROR = "error"                # Erro de conexão


class MCPConnector(abc.ABC):
    """
    Interface base para conectores de MCPs.
    
    Esta classe define a interface que todos os conectores de MCPs
    devem implementar para garantir compatibilidade com o MCP-Crew.
    """
    
    def __init__(
        self,
        mcp_id: str,
        name: str,
        endpoint: str,
        credentials: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Inicializa um novo conector de MCP.
        
        Args:
            mcp_id: Identificador único do MCP
            name: Nome do MCP
            endpoint: URL base do MCP
            credentials: Credenciais de autenticação
            config: Configurações adicionais
        """
        self.id = mcp_id
        self.name = name
        self.endpoint = endpoint
        self.credentials = credentials
        self.config = config or {}
        self.status = MCPStatus.DISCONNECTED
        self.last_error = None
        self.session = requests.Session()
        
        logger.info(f"Conector MCP criado: {self.name} ({self.id})")
    
    @abc.abstractmethod
    async def connect(self) -> bool:
        """
        Estabelece conexão com o MCP.
        
        Returns:
            True se conectado com sucesso, False caso contrário
        """
        pass
    
    @abc.abstractmethod
    async def disconnect(self) -> bool:
        """
        Encerra a conexão com o MCP.
        
        Returns:
            True se desconectado com sucesso, False caso contrário
        """
        pass
    
    @abc.abstractmethod
    async def is_connected(self) -> bool:
        """
        Verifica se está conectado ao MCP.
        
        Returns:
            True se conectado, False caso contrário
        """
        pass
    
    @abc.abstractmethod
    async def execute_operation(
        self,
        operation: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Executa uma operação no MCP.
        
        Args:
            operation: Nome da operação
            params: Parâmetros da operação
            data: Dados para a operação
            
        Returns:
            Resultado da operação
        """
        pass
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Converte o conector para um dicionário.
        
        Returns:
            Dicionário representando o conector
        """
        return {
            "id": self.id,
            "name": self.name,
            "endpoint": self.endpoint,
            "status": self.status.value,
            "config": self.config
        }


class MercadoLivreMCPConnector(MCPConnector):
    """
    Conector para o MCP do Mercado Livre.
    
    Implementa a interface MCPConnector para comunicação com o MCP do Mercado Livre.
    """
    
    def __init__(
        self,
        mcp_id: str,
        endpoint: str,
        client_id: str,
        client_secret: str,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Inicializa um novo conector para o MCP do Mercado Livre.
        
        Args:
            mcp_id: Identificador único do MCP
            endpoint: URL base do MCP
            client_id: ID do cliente (credencial do Mercado Livre)
            client_secret: Chave secreta do cliente (credencial do Mercado Livre)
            config: Configurações adicionais
        """
        credentials = {
            "client_id": client_id,
            "client_secret": client_secret
        }
        
        super().__init__(
            mcp_id=mcp_id,
            name="Mercado Livre",
            endpoint=endpoint,
            credentials=credentials,
            config=config
        )
        
        self.access_token = None
        self.token_expiry = 0
        
        logger.info(f"Conector MCP Mercado Livre criado: {self.id}")
    
    async def connect(self) -> bool:
        """
        Estabelece conexão com o MCP do Mercado Livre.
        
        Realiza autenticação OAuth 2.0 para obter token de acesso.
        
        Returns:
            True se conectado com sucesso, False caso contrário
        """
        try:
            self.status = MCPStatus.CONNECTING
            logger.info(f"Conectando ao MCP Mercado Livre: {self.id}")
            
            # Verifica se já tem um token válido
            if self.access_token and time.time() < self.token_expiry - 60:
                self.status = MCPStatus.CONNECTED
                return True
            
            # Obtém novo token
            token_url = f"{self.endpoint}/oauth/token"
            payload = {
                "grant_type": "client_credentials",
                "client_id": self.credentials["client_id"],
                "client_secret": self.credentials["client_secret"]
            }
            
            response = self.session.post(token_url, data=payload)
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data["access_token"]
            self.token_expiry = time.time() + token_data["expires_in"]
            
            # Configura o cabeçalho de autorização para futuras requisições
            self.session.headers.update({
                "Authorization": f"Bearer {self.access_token}"
            })
            
            self.status = MCPStatus.CONNECTED
            logger.info(f"Conectado ao MCP Mercado Livre: {self.id}")
            return True
            
        except Exception as e:
            self.status = MCPStatus.ERROR
            self.last_error = str(e)
            logger.error(f"Erro ao conectar ao MCP Mercado Livre: {e}")
            return False
    
    async def disconnect(self) -> bool:
        """
        Encerra a conexão com o MCP do Mercado Livre.
        
        Returns:
            True se desconectado com sucesso, False caso contrário
        """
        try:
            # Limpa o token e cabeçalhos
            self.access_token = None
            self.token_expiry = 0
            
            if "Authorization" in self.session.headers:
                del self.session.headers["Authorization"]
            
            self.status = MCPStatus.DISCONNECTED
            logger.info(f"Desconectado do MCP Mercado Livre: {self.id}")
            return True
            
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Erro ao desconectar do MCP Mercado Livre: {e}")
            return False
    
    async def is_connected(self) -> bool:
        """
        Verifica se está conectado ao MCP do Mercado Livre.
        
        Returns:
            True se conectado, False caso contrário
        """
        # Verifica se tem token e se não está expirado
        if not self.access_token or time.time() >= self.token_expiry:
            return False
        
        return self.status == MCPStatus.CONNECTED
    
    async def execute_operation(
        self,
        operation: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Executa uma operação no MCP do Mercado Livre.
        
        Args:
            operation: Nome da operação
            params: Parâmetros da operação
            data: Dados para a operação
            
        Returns:
            Resultado da operação
        """
        # Garante que está conectado
        if not await self.is_connected():
            success = await self.connect()
            if not success:
                raise ConnectionError(f"Não foi possível conectar ao MCP Mercado Livre: {self.last_error}")
        
        try:
            # Mapeia a operação para o endpoint e método HTTP correspondentes
            endpoint, method = self._map_operation(operation)
            url = f"{self.endpoint}{endpoint}"
            
            # Executa a requisição
            if method == "GET":
                response = self.session.get(url, params=params)
            elif method == "POST":
                response = self.session.post(url, params=params, json=data)
            elif method == "PUT":
                response = self.session.put(url, params=params, json=data)
            elif method == "DELETE":
                response = self.session.delete(url, params=params)
            else:
                raise ValueError(f"Método HTTP não suportado: {method}")
            
            response.raise_for_status()
            
            # Retorna o resultado como dicionário
            if response.content:
                return response.json()
            return {"success": True}
            
        except RequestException as e:
            # Trata erros de requisição
            self.last_error = str(e)
            
            # Se o erro for de autenticação, tenta reconectar
            if e.response and e.response.status_code == 401:
                logger.warning("Token expirado, tentando reconectar...")
                await self.connect()
                # Tenta novamente a operação
                return await self.execute_operation(operation, params, data)
            
            logger.error(f"Erro ao executar operação {operation} no MCP Mercado Livre: {e}")
            raise
    
    def _map_operation(self, operation: str) -> tuple:
        """
        Mapeia uma operação para o endpoint e método HTTP correspondentes.
        
        Args:
            operation: Nome da operação
            
        Returns:
            Tupla (endpoint, método HTTP)
        """
        # Mapeamento de operações para endpoints e métodos
        operations_map = {
            # Produtos
            "list_products": ("/products", "GET"),
            "get_product": ("/products/{product_id}", "GET"),
            "create_product": ("/products", "POST"),
            "update_product": ("/products/{product_id}", "PUT"),
            "delete_product": ("/products/{product_id}", "DELETE"),
            
            # Pedidos
            "list_orders": ("/orders", "GET"),
            "get_order": ("/orders/{order_id}", "GET"),
            "update_order": ("/orders/{order_id}", "PUT"),
            
            # Mensagens
            "list_messages": ("/messages/orders/{order_id}", "GET"),
            "send_message": ("/messages/orders/{order_id}", "POST"),
            
            # Categorias
            "list_categories": ("/categories", "GET"),
            "get_category": ("/categories/{category_id}", "GET"),
            
            # Análise de dados
            "sales_metrics": ("/analytics/sales", "GET"),
            "performance_metrics": ("/analytics/performance", "GET"),
            
            # Webhooks
            "register_webhook": ("/webhooks", "POST"),
            "list_webhooks": ("/webhooks", "GET"),
            "delete_webhook": ("/webhooks/{webhook_id}", "DELETE"),
        }
        
        if operation not in operations_map:
            raise ValueError(f"Operação não suportada: {operation}")
        
        return operations_map[operation]


class MCPConnectorRegistry:
    """
    Registro de conectores de MCPs.
    
    Gerencia o registro e recuperação de conectores de MCPs.
    """
    
    def __init__(self):
        """Inicializa o registro de conectores."""
        self.connectors: Dict[str, MCPConnector] = {}
        logger.info("MCPConnectorRegistry inicializado")
    
    def register_connector(self, connector: MCPConnector) -> str:
        """
        Registra um conector de MCP.
        
        Args:
            connector: Conector a ser registrado
            
        Returns:
            ID do conector registrado
        """
        self.connectors[connector.id] = connector
        logger.info(f"Conector registrado: {connector.name} ({connector.id})")
        return connector.id
    
    def get_connector(self, connector_id: str) -> Optional[MCPConnector]:
        """
        Obtém um conector pelo ID.
        
        Args:
            connector_id: ID do conector
            
        Returns:
            Conector correspondente ou None se não encontrado
        """
        return self.connectors.get(connector_id)
    
    def remove_connector(self, connector_id: str) -> bool:
        """
        Remove um conector do registro.
        
        Args:
            connector_id: ID do conector
            
        Returns:
            True se o conector foi removido, False caso contrário
        """
        if connector_id in self.connectors:
            connector = self.connectors.pop(connector_id)
            logger.info(f"Conector removido: {connector.name} ({connector_id})")
            return True
        return False
    
    def get_all_connectors(self) -> List[MCPConnector]:
        """
        Obtém todos os conectores registrados.
        
        Returns:
            Lista de todos os conectores
        """
        return list(self.connectors.values())
    
    def get_connectors_by_name(self, name: str) -> List[MCPConnector]:
        """
        Obtém conectores pelo nome.
        
        Args:
            name: Nome dos conectores
            
        Returns:
            Lista de conectores com o nome especificado
        """
        return [
            connector for connector in self.connectors.values()
            if connector.name == name
        ]
