#!/usr/bin/env python3
"""
CrewFactory para o ChatwootAI

Este módulo implementa o CrewFactory, responsável por criar instâncias de crews
específicas por canal com base na configuração YAML.
"""

import logging
from typing import Dict, Any, Optional, Type

from src.core.config import get_config_registry
from src.core.crews.base_crew import BaseCrew
from src.core.crews.channels import WhatsAppCrew, DefaultCrew

# Configurar logging
logger = logging.getLogger(__name__)

class CrewFactory:
    """
    Fábrica de crews específicas por canal.
    
    Esta classe é responsável por criar instâncias de crews específicas por canal
    com base na configuração YAML, determinando o tipo de crew apropriado para
    cada canal de comunicação.
    """
    
    def __init__(self, config_registry=None):
        """
        Inicializa a fábrica de crews.
        
        Args:
            config_registry: Registro de configurações opcional
        """
        self.config_registry = config_registry or get_config_registry()
        
        # Mapeamento de canais para classes de crew
        self.channel_crews = {
            "whatsapp": WhatsAppCrew,
            "default": DefaultCrew
        }
        
        # Cache de crews para evitar recriação desnecessária
        self.crew_cache = {}
        
        logger.info("CrewFactory inicializado")
    
    async def create_crew(self, crew_type: str, domain_name: str, account_id: str, channel_type: str = None) -> BaseCrew:
        """
        Cria uma instância de crew específica por canal.
        
        Args:
            crew_type: Tipo de crew (ex: "customer_service", "analytics")
            domain_name: Nome do domínio
            account_id: ID da conta
            channel_type: Tipo de canal (ex: "whatsapp", "instagram")
            
        Returns:
            Instância da crew
            
        Raises:
            ValueError: Se o tipo de crew ou canal for desconhecido
        """
        # Determinar o tipo de canal
        effective_channel = channel_type or "default"
        
        # Obter a classe de crew apropriada para o canal
        crew_class = self.channel_crews.get(effective_channel)
        if not crew_class:
            logger.warning(f"Canal desconhecido: {effective_channel}, usando DefaultCrew")
            crew_class = DefaultCrew
        
        # Carregar configuração
        config = await self.config_registry.get_config(domain_name, account_id)
        
        # Criar a crew
        crew = crew_class(config=config, domain_name=domain_name, account_id=account_id)
        
        logger.info(f"Crew criada: {crew_class.__name__} para {domain_name}/{account_id} (canal: {effective_channel})")
        return crew
    
    async def get_crew(self, crew_type: str, domain_name: str, account_id: str, channel_type: str = None) -> BaseCrew:
        """
        Obtém uma crew para um domínio, account_id e canal específicos, criando-a se necessário.
        
        Args:
            crew_type: Tipo de crew (ex: "customer_service", "analytics")
            domain_name: Nome do domínio
            account_id: ID da conta
            channel_type: Tipo de canal (ex: "whatsapp", "instagram")
            
        Returns:
            Instância da crew
        """
        # Determinar o tipo de canal
        effective_channel = channel_type or "default"
        
        # Chave de cache
        cache_key = f"crew:{crew_type}:{effective_channel}:{domain_name}:{account_id}"
        
        # Verificar cache
        if cache_key in self.crew_cache:
            logger.debug(f"Usando crew em cache: {cache_key}")
            return self.crew_cache[cache_key]
        
        # Criar nova crew
        crew = await self.create_crew(
            crew_type=crew_type,
            domain_name=domain_name,
            account_id=account_id,
            channel_type=effective_channel
        )
        
        # Armazenar em cache
        self.crew_cache[cache_key] = crew
        
        return crew
    
    def register_channel_crew(self, channel_type: str, crew_class: Type[BaseCrew]) -> None:
        """
        Registra uma classe de crew para um tipo de canal específico.
        
        Args:
            channel_type: Tipo de canal (ex: "whatsapp", "instagram")
            crew_class: Classe de crew
        """
        self.channel_crews[channel_type] = crew_class
        logger.info(f"Classe de crew registrada para canal {channel_type}: {crew_class.__name__}")
    
    def invalidate_crew(self, crew_type: str, domain_name: str, account_id: str, channel_type: str = None) -> bool:
        """
        Invalida o cache de uma crew específica.
        
        Args:
            crew_type: Tipo de crew (ex: "customer_service", "analytics")
            domain_name: Nome do domínio
            account_id: ID da conta
            channel_type: Tipo de canal (ex: "whatsapp", "instagram")
            
        Returns:
            True se invalidado com sucesso, False caso contrário
        """
        # Determinar o tipo de canal
        effective_channel = channel_type or "default"
        
        # Chave de cache
        cache_key = f"crew:{crew_type}:{effective_channel}:{domain_name}:{account_id}"
        
        # Remover do cache
        if cache_key in self.crew_cache:
            del self.crew_cache[cache_key]
            logger.info(f"Cache de crew invalidado: {cache_key}")
            return True
        
        return False

# Instância singleton
_crew_factory = None

def get_crew_factory(force_new=False, config_registry=None) -> CrewFactory:
    """
    Obtém a instância singleton do CrewFactory.
    
    Args:
        force_new: Se True, força a criação de uma nova instância
        config_registry: Registro de configurações opcional
        
    Returns:
        Instância do CrewFactory
    """
    global _crew_factory
    
    if _crew_factory is None or force_new:
        _crew_factory = CrewFactory(config_registry=config_registry)
    
    return _crew_factory
