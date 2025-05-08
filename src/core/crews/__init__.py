"""
Pacote de crews para o ChatwootAI.

Este pacote contém as implementações de crews para diferentes canais de comunicação,
bem como a fábrica de crews responsável por criar instâncias apropriadas.
"""

from src.core.crews.base_crew import BaseCrew
from src.core.crews.crew_factory import CrewFactory, get_crew_factory
from src.core.crews.channels import WhatsAppCrew, DefaultCrew

__all__ = [
    'BaseCrew',
    'CrewFactory',
    'get_crew_factory',
    'WhatsAppCrew',
    'DefaultCrew'
]
