"""
Arquivo de compatibilidade para manter as importações existentes funcionando.

Este módulo importa as configurações da nova localização para manter
a compatibilidade com o código existente.
"""

from odoo_api.infrastructure.config.settings import settings

# Re-exportar para manter a compatibilidade
__all__ = ["settings"]
