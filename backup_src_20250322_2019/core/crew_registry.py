"""
Registro de crews para gerenciar diferentes tipos de crews no sistema.
"""

import logging
from typing import Dict, Any, Optional
from src.core.base_crew import BaseCrew

logger = logging.getLogger(__name__)

class CrewRegistry:
    """
    Registro de crews para gerenciar diferentes tipos de crews no sistema.
    
    Esta classe permite registrar, recuperar e gerenciar crews por tipo.
    """
    
    def __init__(self):
        """
        Inicializa o registro de crews.
        """
        self.crews = {}
        logger.info("Registro de crews inicializado")
    
    def register_crew(self, crew_type: str, crew: BaseCrew) -> None:
        """
        Registra uma crew no sistema.
        
        Args:
            crew_type: Tipo da crew (ex: "whatsapp", "hub", "sales")
            crew: Instância da crew
        """
        self.crews[crew_type] = crew
        logger.info(f"Crew '{crew_type}' registrada com sucesso")
    
    def get_crew(self, crew_type: str) -> Optional[BaseCrew]:
        """
        Obtém uma crew pelo tipo.
        
        Args:
            crew_type: Tipo da crew
            
        Returns:
            Instância da crew ou None se não encontrada
        """
        crew = self.crews.get(crew_type)
        if crew is None:
            logger.warning(f"Crew '{crew_type}' não encontrada no registro")
        return crew
    
    def list_crews(self) -> Dict[str, BaseCrew]:
        """
        Lista todas as crews registradas.
        
        Returns:
            Dicionário com todas as crews registradas
        """
        return self.crews
    
    def unregister_crew(self, crew_type: str) -> bool:
        """
        Remove uma crew do registro.
        
        Args:
            crew_type: Tipo da crew
            
        Returns:
            True se a crew foi removida, False caso contrário
        """
        if crew_type in self.crews:
            del self.crews[crew_type]
            logger.info(f"Crew '{crew_type}' removida do registro")
            return True
        logger.warning(f"Tentativa de remover crew '{crew_type}' que não existe no registro")
        return False
