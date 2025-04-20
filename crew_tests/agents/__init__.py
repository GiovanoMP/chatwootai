"""
Definições de agentes para o CrewAI.
"""

from .customer_service import create_customer_service_agents, create_customer_service_tasks

__all__ = ['create_customer_service_agents', 'create_customer_service_tasks']
