"""
Conectores para MCPs específicos.

Este módulo define a interface e implementações para conectores de MCPs,
permitindo que o MCP-Crew se comunique com diferentes MCPs específicos
(Mercado Livre, Instagram, Facebook, etc.) de forma padronizada.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, Optional, Mapping, List # Added List for registry typing

import aiohttp
import time

# Use the project's logging setup
from ..utils.logging import get_logger # Assuming this is the correct relative path
logger = get_logger(__name__)


class MCPStatus(Enum):
    """Status de um MCP."""
    DISCONNECTED = "disconnected"  # Não conectado
    CONNECTING = "connecting"      # Conectando
    CONNECTED = "connected"        # Conectado
    ERROR = "error"                # Erro de conexão


class MCPConnector(ABC):
    """Abstract Base Class for MCP Connectors."""
    
    def __init__(self, mcp_id: str, base_url: str, session: aiohttp.ClientSession):
        self.mcp_id = mcp_id
        self.base_url = base_url
        self.status = MCPStatus.DISCONNECTED
        self.last_error: Optional[str] = None
        self.session: aiohttp.ClientSession = session
        
        logger.info(f"MCPConnector created: {self.mcp_id}")
    
    @abstractmethod
    async def connect(self) -> bool:
        """
        Estabelece conexão com o MCP.
        
        Returns:
            True se conectado com sucesso, False caso contrário
        """
        pass
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """
        Encerra a conexão com o MCP.
        
        Returns:
            True se desconectado com sucesso, False caso contrário
        """
        pass
    
    @abstractmethod
    async def is_connected(self) -> bool:
        """
        Verifica se está conectado ao MCP.
        
        Returns:
            True se conectado, False caso contrário
        """
        pass
    
    @abstractmethod
    async def execute_operation(
        self,
        account_id: str, # Identifier for the tenant
        operation: str, # e.g., 'get_user_info', 'post_message', 'list_products'
        method: str, # HTTP method (GET, POST, PUT, DELETE, etc.)
        endpoint: str, # Relative API endpoint path (e.g., /users, /products/{id})
        params: Optional[Mapping[str, str]] = None, # URL query parameters
        payload: Optional[Any] = None, # Request body (e.g., dict for JSON, aiohttp.FormData for form data)
        headers: Optional[Mapping[str, str]] = None # Custom request headers
    ) -> Dict[str, Any]:
        """Executes a specific operation on the MCP."""
        pass
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Converte o conector para um dicionário com informações básicas.
        
        Returns:
            Dicionário representando o conector
        """
        return {
            "mcp_id": self.mcp_id,
            "base_url": self.base_url,
            "status": self.status.value,
            "last_error": self.last_error
        }


class MercadoLivreMCPConnector(MCPConnector):
    """
    Conector para o MCP do Mercado Livre.
    
    Implementa a interface MCPConnector para comunicação com o MCP do Mercado Livre.
    """
    
    def __init__(
        self,
        mcp_id: str,
        base_url: str, 
        client_id: str,
        client_secret: str,
        session: aiohttp.ClientSession, 
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Inicializa um novo conector para o MCP do Mercado Livre.
        
        Args:
            mcp_id: Identificador único do MCP.
            base_url: URL base do MCP do Mercado Livre.
            client_id: ID do cliente (credencial do Mercado Livre).
            client_secret: Chave secreta do cliente (credencial do Mercado Livre).
            session: Instância de aiohttp.ClientSession para requisições HTTP.
            config: Configurações adicionais (ex: token_url, redirect_uri).
        """
        super().__init__(mcp_id=mcp_id, base_url=base_url, session=session)
        
        self.client_id = client_id
        self.client_secret = client_secret
        
        _config = config or {}
        self.token_url = _config.get("token_url", "https://api.mercadolibre.com/oauth/token")
        # redirect_uri is often needed for OAuth flows, even if just for server-side.
        # It should match what's configured in the Mercado Livre app settings.
        self.redirect_uri = _config.get("redirect_uri", "YOUR_APP_REDIRECT_URI") 
        
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.token_expires_at: Optional[float] = None # Store token expiry time (timestamp)
        
        logger.info(f"MercadoLivreMCPConnector ({self.mcp_id}) configured.")

    async def connect(self) -> bool:
        """
        Estabelece conexão com o MCP do Mercado Livre.
        Realiza autenticação OAuth 2.0 para obter token de acesso.
        NOTA: Esta implementação é um esboço e precisará ser adaptada para aiohttp.
        """
        self.status = MCPStatus.CONNECTING
        logger.info(f"MercadoLivreMCPConnector ({self.mcp_id}): Attempting to connect and authenticate.")
        try:
            auth_payload = {
                'grant_type': 'client_credentials',
                'client_id': self.client_id,
                'client_secret': self.client_secret
            }
            
            # SIMULATED SUCCESS FOR NOW - REPLACE WITH ACTUAL AIOHTTP CALL
            logger.warning(f"MercadoLivreMCPConnector ({self.mcp_id}): connect() is using simulated success. Replace with actual aiohttp call.")
            # Example of actual call (needs to be uncommented and tested):
            # async with self.session.post(self.token_url, data=auth_payload) as resp:
            #     if resp.status == 200:
            #         token_data = await resp.json()
            #         self.access_token = token_data.get("access_token")
            #         self.refresh_token = token_data.get("refresh_token") # If applicable
            #         expires_in = token_data.get("expires_in")
            #         if expires_in:
            #             self.token_expires_at = time.time() + expires_in
            #         if not self.access_token:
            #             raise ValueError("Access token not found in response.")
            #         self.status = MCPStatus.CONNECTED
            #         logger.info(f"MercadoLivreMCPConnector ({self.mcp_id}): Successfully connected and authenticated.")
            #         return True
            #     else:
            #         error_details = await resp.text()
            #         self.last_error = f"Authentication failed: {resp.status} - {error_details}"
            #         logger.error(f"MercadoLivreMCPConnector ({self.mcp_id}): {self.last_error}")
            #         self.status = MCPStatus.ERROR
            #         return False
            
            self.access_token = "simulated_access_token"
            self.token_expires_at = time.time() + 3600 
            self.status = MCPStatus.CONNECTED
            logger.info(f"MercadoLivreMCPConnector ({self.mcp_id}): Successfully connected (simulated).")
            return True

        except Exception as e: # Catch aiohttp.ClientError or similar specific exceptions
            self.last_error = f"Connection/Authentication error: {str(e)}"
            logger.error(f"MercadoLivreMCPConnector ({self.mcp_id}): {self.last_error}")
            self.status = MCPStatus.ERROR
            return False

    async def disconnect(self) -> bool:
        """
        Encerra a conexão com o MCP do Mercado Livre.
        (Invalidates token or cleans up session if necessary)
        """
        logger.info(f"MercadoLivreMCPConnector ({self.mcp_id}): Disconnecting.")
        self.access_token = None
        self.refresh_token = None
        self.token_expires_at = None
        self.status = MCPStatus.DISCONNECTED
        return True

    async def is_connected(self) -> bool:
        """
        Verifica se está conectado e o token é válido.
        """
        if self.status == MCPStatus.CONNECTED and self.access_token:
            if self.token_expires_at and time.time() < self.token_expires_at:
                return True
            else:
                logger.info(f"MercadoLivreMCPConnector ({self.mcp_id}): Token expired or missing expiry info.")
                self.status = MCPStatus.DISCONNECTED
                return False
        return False

    async def execute_operation(
        self,
        account_id: str,
        operation: str, 
        method: str,    
        endpoint: str,  
        params: Optional[Mapping[str, str]] = None,
        payload: Optional[Any] = None, 
        headers: Optional[Mapping[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Executa uma operação no MCP do Mercado Livre usando aiohttp.
        """
        if not await self.is_connected():
            logger.warning(f"MercadoLivreMCPConnector ({self.mcp_id}): Not connected. Attempting to reconnect for operation '{operation}'.")
            if not await self.connect():
                raise ConnectionError(f"Failed to connect to Mercado Livre for account {account_id} to perform operation {operation}.")

        request_headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "X-Account-ID": account_id 
        }
        if headers:
            request_headers.update(headers)

        full_url = f"{self.base_url}{endpoint}"
        
        logger.debug(
            f"MercadoLivreMCPConnector ({self.mcp_id}) Account({account_id}): "
            f"Executing '{method} {full_url}' for operation '{operation}'. "
            f"Params: {params}, Payload: {payload is not None}"
        )

        try:
            # SIMULATED RESPONSE FOR NOW - REPLACE WITH ACTUAL AIOHTTP CALL
            logger.warning(
                f"MercadoLivreMCPConnector ({self.mcp_id}) Account({account_id}): "
                f"execute_operation() for '{operation}' is using simulated success. Replace with actual aiohttp call."
            )
            # Example of actual call (needs to be uncommented and tested):
            # async with self.session.request(
            #     method=method.upper(),
            #     url=full_url,
            #     params=params,
            #     json=payload if isinstance(payload, dict) else None, 
            #     data=payload if not isinstance(payload, dict) else None,
            #     headers=request_headers,
            #     timeout=aiohttp.ClientTimeout(total=30) # Example timeout
            # ) as response:
            #     response.raise_for_status() 
            #     return await response.json() 

            return {"status": "success", "operation": operation, "data": "simulated_data_for_" + endpoint, "account_id": account_id}

        except aiohttp.ClientResponseError as e:
            logger.error(
                f"MercadoLivreMCPConnector ({self.mcp_id}) Account({account_id}): "
                f"HTTP error during operation '{operation}': {e.status} {e.message} - {e.headers}"
            )
            return {"error": str(e), "status_code": e.status, "details": e.message, "url": str(e.request_info.url) if e.request_info else full_url}
        except aiohttp.ClientError as e: 
            logger.error(
                f"MercadoLivreMCPConnector ({self.mcp_id}) Account({account_id}): "
                f"Client error during operation '{operation}': {str(e)}"
            )
            self.status = MCPStatus.ERROR 
            self.last_error = str(e)
            raise ConnectionError(f"Mercado Livre API request failed for operation {operation}: {str(e)}") from e
        except Exception as e:
            logger.exception(
                f"MercadoLivreMCPConnector ({self.mcp_id}) Account({account_id}): "
                f"Unexpected error during operation '{operation}'"
            )
            raise

    def _map_operation(self, operation: str) -> tuple[str, str]:
        """
        Mapeia uma operação para o endpoint e método HTTP correspondentes.
        DEPRECATED or to be re-evaluated: The new execute_operation takes method and endpoint directly.
        This mapping might still be useful internally or for a higher-level abstraction.
        """
        logger.warning("_map_operation might be deprecated or need re-evaluation with the new execute_operation signature.")
        operations_map = {
            "list_products": ("/products", "GET"),
            "get_product": ("/products/{product_id}", "GET"),
            "get_my_user_info": ("/users/me", "GET"), 
        }
        
        if operation not in operations_map:
            raise ValueError(f"Operação não suportada ou não mapeada: {operation}")
        
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
    
    def register_connector(self, connector: MCPConnector):
        """
        Registra um conector de MCP.
        """
        if not isinstance(connector, MCPConnector):
            raise TypeError("Can only register instances of MCPConnector.")
        
        if connector.mcp_id in self.connectors:
            logger.warning(f"Connector with ID '{connector.mcp_id}' already registered. Overwriting.")
            
        self.connectors[connector.mcp_id] = connector
        logger.info(f"Connector registered: ID '{connector.mcp_id}' of type {type(connector).__name__}")
    
    def get_connector(self, mcp_id: str) -> Optional[MCPConnector]:
        """
        Obtém um conector pelo ID.
        """
        return self.connectors.get(mcp_id)
    
    def remove_connector(self, mcp_id: str) -> bool:
        """
        Remove um conector do registro.
        """
        if mcp_id in self.connectors:
            connector = self.connectors.pop(mcp_id)
            logger.info(f"Connector removed: ID '{connector.mcp_id}' of type {type(connector).__name__}")
            return True
        logger.warning(f"Attempted to remove non-existent connector with ID '{mcp_id}'.")
        return False
    
    def get_all_connectors(self) -> List[MCPConnector]: # Changed to List from typing
        """
        Obtém todos os conectores registrados.
        """
        return list(self.connectors.values())


import abc
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, Optional, Mapping
import aiohttp
import time
from utils.logging import logger
from requests.exceptions import RequestException

from ..utils.logging import get_logger

logger = get_logger(__name__)

class MCPStatus(Enum):
    """Status de um MCP."""
    DISCONNECTED = "disconnected"  # Não conectado
    CONNECTING = "connecting"      # Conectando
    CONNECTED = "connected"        # Conectado
    ERROR = "error"                # Erro de conexão


class MCPConnector(ABC):
    """Abstract Base Class for MCP Connectors."""
    """
    Interface base para conectores de MCPs.
    
    Esta classe define a interface que todos os conectores de MCPs
    devem implementar para garantir compatibilidade com o MCP-Crew.
    """
    
    def __init__(self, mcp_id: str, base_url: str, session: aiohttp.ClientSession):
        self.mcp_id = mcp_id
        self.base_url = base_url
        self.status = MCPStatus.DISCONNECTED
        self.last_error: Optional[str] = None
        self.session: aiohttp.ClientSession = session
        
        logger.info(f"Conector MCP criado: {self.mcp_id} ({self.mcp_id})")
    
    @abstractmethod
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
