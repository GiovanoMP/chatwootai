"""
Pacote de Serviços de Dados para o ChatwootAI.

Este pacote implementa a camada de serviços de dados da aplicação,
facilitando o acesso consistente a diferentes fontes de dados e
implementando um sistema de cache em dois níveis.
"""

from .data_service_hub import DataServiceHub
from .base_data_service import BaseDataService

__all__ = ['DataServiceHub', 'BaseDataService']
