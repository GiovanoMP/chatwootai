"""
Módulo de tasks para o projeto ChatwootAI.

Este módulo contém as definições de tasks para as diferentes crews
e agentes do sistema, seguindo as melhores práticas do CrewAI.
"""

from src.tasks.whatsapp_tasks import create_whatsapp_tasks
from src.tasks.hub_tasks import create_hub_tasks
from src.tasks.sales_tasks import create_sales_tasks

__all__ = [
    'create_whatsapp_tasks',
    'create_hub_tasks',
    'create_sales_tasks',
]
