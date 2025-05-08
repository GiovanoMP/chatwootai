"""
Pacote de crews específicas por canal para o ChatwootAI.

Este pacote contém as implementações de crews específicas para diferentes
canais de comunicação, como WhatsApp, Instagram, etc.
"""

from src.core.crews.channels.whatsapp_crew import WhatsAppCrew
from src.core.crews.channels.default_crew import DefaultCrew

__all__ = [
    'WhatsAppCrew',
    'DefaultCrew'
]
