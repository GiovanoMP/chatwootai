"""
Implementação do padrão Service Locator para gerenciamento de dependências.

Este módulo fornece uma implementação simples do padrão Service Locator,
que permite o registro e a obtenção de serviços por tipo, facilitando
a injeção de dependências e o desacoplamento de componentes.
"""
from typing import Dict, Type, Any, Optional, TypeVar, Generic, cast

# Tipo genérico para representar qualquer classe
T = TypeVar('T')

class ServiceLocator:
    """
    Implementação do padrão Service Locator para gerenciamento de dependências.
    
    Permite registrar e obter serviços por tipo, facilitando a injeção de
    dependências e o desacoplamento de componentes.
    """
    
    def __init__(self):
        """Inicializa o localizador de serviços."""
        self._services: Dict[Type, Any] = {}
    
    def register(self, service_class: Type[T], instance: T) -> None:
        """
        Registra uma instância de serviço pelo seu tipo.
        
        Args:
            service_class: Classe do serviço a ser registrado
            instance: Instância do serviço
        """
        self._services[service_class] = instance
    
    def get(self, service_class: Type[T]) -> Optional[T]:
        """
        Obtém uma instância de serviço pelo seu tipo.
        
        Args:
            service_class: Classe do serviço a ser obtido
            
        Returns:
            Instância do serviço ou None se não encontrado
        """
        return self._services.get(service_class)
    
    def has(self, service_class: Type[T]) -> bool:
        """
        Verifica se um serviço está registrado.
        
        Args:
            service_class: Classe do serviço a verificar
            
        Returns:
            True se o serviço estiver registrado, False caso contrário
        """
        return service_class in self._services
    
    def remove(self, service_class: Type[T]) -> None:
        """
        Remove um serviço do registro.
        
        Args:
            service_class: Classe do serviço a remover
        """
        if service_class in self._services:
            del self._services[service_class]
