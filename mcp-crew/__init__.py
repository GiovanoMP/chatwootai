"""
Módulo core do MCP-Crew.

Este módulo contém os componentes centrais do MCP-Crew, incluindo:
- Gerenciamento de agentes
- Controle de autorizações
- Protocolos de comunicação
- Gerenciamento de contexto
- Integração com Redis
"""

from .agent_manager import AgentManager
from .auth_manager import AuthManager
from .communication import CommunicationProtocol
from .context_manager import ContextManager
from .redis_integration import RedisManager

__all__ = [
    'AgentManager',
    'AuthManager',
    'CommunicationProtocol',
    'ContextManager',
    'RedisManager',
]
