"""
API REST para integração com o módulo Odoo semantic_product_description.

Este pacote implementa endpoints REST para receber webhooks do módulo Odoo,
permitindo a sincronização de produtos e a geração de descrições semânticas.

Autor: Augment Agent
Data: 26/03/2025
"""

from .api import app
from .routes import router as odoo_router
from .schemas import (
    ProductMetadata,
    WebhookRequest,
    WebhookResponse,
    TaskStatusResponse,
    TaskType,
    TaskStatus
)

# Registrar rotas
app.include_router(odoo_router)

__all__ = [
    'app',
    'ProductMetadata',
    'WebhookRequest',
    'WebhookResponse',
    'TaskStatusResponse',
    'TaskType',
    'TaskStatus'
]
