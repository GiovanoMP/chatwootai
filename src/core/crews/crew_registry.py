#!/usr/bin/env python3
"""
Registro de Crews para o ChatwootAI

Este módulo implementa o CrewRegistry, responsável por gerenciar instâncias
de crews, garantindo que sejam criadas apenas uma vez e reutilizadas quando
necessário, melhorando a performance do sistema.
"""

import logging
from typing import Dict, Any, Optional

from crewai import Crew
from src.core.crews.crew_factory import get_crew_factory
from src.core.domain.domain_registry import get_domain_registry

# Configurar logging
logger = logging.getLogger(__name__)

class CrewRegistry:
    """
    Registro centralizado de crews instanciadas.
    
    Responsável por gerenciar instâncias de crews, garantindo que sejam criadas
    apenas uma vez e reutilizadas quando necessário, melhorando a performance
    do sistema e mantendo a consistência entre interações.
    """
    
    def __init__(self, crew_factory=None):
        """
        Inicializa o registro de crews.
        
        Args:
            crew_factory: Fábrica para criar novas instâncias de crews
        """
        self.crew_factory = crew_factory or get_crew_factory()
        self._crews = {}  # Cache de crews instanciadas
        
        logger.info("CrewRegistry inicializado")
    
    def get_crew(self, crew_id: str, domain_name: str, crew_config: Dict[str, Any] = None) -> Crew:
        """
        Obtém uma crew pelo ID, usando cache quando possível.
        
        Args:
            crew_id: Identificador da crew
            domain_name: Nome do domínio
            crew_config: Configuração opcional, se não fornecida será obtida do domínio
            
        Returns:
            Instância da crew
        """
        # Chave de cache composta
        cache_key = f"{domain_name}:{crew_id}"
        
        # Verificar cache de instâncias
        if cache_key in self._crews:
            logger.debug(f"Usando crew em cache: {crew_id} (domínio: {domain_name})")
            return self._crews[cache_key]
        
        # Se não fornecida, obter configuração do domínio
        if not crew_config:
            logger.debug(f"Obtendo configuração para crew {crew_id} do domínio {domain_name}")
            domain_registry = get_domain_registry()
            domain_config = domain_registry.get_domain_config(domain_name)
            
            if not domain_config:
                raise ValueError(f"Domínio não encontrado: {domain_name}")
                
            crews_config = domain_config.get("crews", {})
            crew_config = crews_config.get(crew_id)
            
            if not crew_config:
                raise ValueError(f"Configuração para crew {crew_id} não encontrada no domínio {domain_name}")
        
        # Criar nova instância da crew
        logger.info(f"Criando nova instância da crew {crew_id} para domínio {domain_name}")
        crew = self.crew_factory.create_crew(crew_config, domain_name)
        
        # Armazenar em cache
        self._crews[cache_key] = crew
        
        return crew
    
    def invalidate_crew(self, crew_id: str, domain_name: str) -> bool:
        """
        Invalida o cache de uma crew específica.
        
        Args:
            crew_id: Identificador da crew
            domain_name: Nome do domínio
            
        Returns:
            True se invalidado com sucesso, False caso contrário
        """
        cache_key = f"{domain_name}:{crew_id}"
        if cache_key in self._crews:
            del self._crews[cache_key]
            logger.info(f"Crew {crew_id} invalidada para domínio {domain_name}")
            return True
        
        return False
    
    def invalidate_domain(self, domain_name: str) -> int:
        """
        Invalida todas as crews de um domínio específico.
        
        Args:
            domain_name: Nome do domínio
            
        Returns:
            Número de crews invalidadas
        """
        keys_to_remove = []
        for key in self._crews.keys():
            if key.startswith(f"{domain_name}:"):
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self._crews[key]
        
        logger.info(f"{len(keys_to_remove)} crews invalidadas para domínio {domain_name}")
        return len(keys_to_remove)
    
    def list_cached_crews(self) -> Dict[str, str]:
        """
        Lista todas as crews em cache.
        
        Returns:
            Dicionário com chaves de cache e IDs de crews
        """
        return {key: crew.id for key, crew in self._crews.items()}
    
    def get_crew_count(self) -> int:
        """
        Retorna o número de crews em cache.
        
        Returns:
            Número de crews em cache
        """
        return len(self._crews)


# Singleton para o registro de crews
_crew_registry = None

def get_crew_registry(force_new=False, crew_factory=None) -> CrewRegistry:
    """
    Obtém a instância singleton do registro de crews.
    
    Args:
        force_new: Se True, força a criação de uma nova instância
        crew_factory: Fábrica de crews opcional
        
    Returns:
        Instância do CrewRegistry
    """
    global _crew_registry
    
    if _crew_registry is None or force_new:
        _crew_registry = CrewRegistry(crew_factory)
        
    return _crew_registry
