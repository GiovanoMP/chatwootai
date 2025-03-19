"""
Módulo de agentes adaptáveis para diferentes domínios de negócio.
"""

from .adaptable_agent import AdaptableAgent
from .sales_agent import SalesAgent
from .support_agent import SupportAgent
from .scheduling_agent import SchedulingAgent

__all__ = [
    "AdaptableAgent",
    "SalesAgent",
    "SupportAgent",
    "SchedulingAgent"
]
