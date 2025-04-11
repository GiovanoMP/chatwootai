"""
API REST para integração com sistemas externos.

Este pacote implementa endpoints REST para receber webhooks de sistemas externos,
permitindo a integração com o ChatwootAI.

Autor: Augment Agent
Data: 26/03/2025
"""

from .main import app

__all__ = ['app']