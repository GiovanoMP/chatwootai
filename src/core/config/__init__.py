"""
Pacote de configuração para o ChatwootAI.

Este pacote contém os componentes responsáveis por carregar e gerenciar
as configurações YAML dos clientes.
"""

from src.core.config.config_registry import ConfigRegistry, get_config_registry
from src.core.config.config_loader import ConfigLoader

__all__ = [
    'ConfigRegistry',
    'get_config_registry',
    'ConfigLoader'
]
