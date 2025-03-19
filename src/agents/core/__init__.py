"""
Agentes core do sistema.

Este pacote contém os agentes fundamentais do sistema, incluindo o DataProxyAgent,
que é o intermediário obrigatório para acesso a dados.
"""

from .data_proxy_agent import DataProxyAgent

__all__ = ["DataProxyAgent"]
