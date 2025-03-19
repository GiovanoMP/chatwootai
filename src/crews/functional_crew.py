"""
Base para as crews funcionais da arquitetura hub-and-spoke.

Este módulo implementa a classe base para as crews funcionais,
que são responsáveis por processar mensagens de acordo com suas especialidades.
"""

import logging
from typing import Dict, List, Any, Optional
import json

from crewai import Crew, Agent, Task
from src.core.cache.agent_cache import RedisAgentCache

from src.core.memory import MemorySystem
from src.services.data.data_service_hub import DataServiceHub
from src.agents.data_proxy_agent import DataProxyAgent
from src.agents.functional_agents import FunctionalAgent
from src.agents.adaptable.sales_agent import SalesAgent
from src.agents.adaptable.support_agent import SupportAgent
from src.agents.adaptable.scheduling_agent import SchedulingAgent

logger = logging.getLogger(__name__)


class FunctionalCrew:
    """
    Base para as crews funcionais.
    
    Esta classe serve como base para todas as crews funcionais,
    como vendas, suporte, informações e agendamentos.
    """
    
    def __init__(self, 
                 crew_type: str,
                 memory_system: MemorySystem,
                 data_service_hub: DataServiceHub,
                 agent_cache: Optional[RedisAgentCache] = None,
                 additional_tools: Optional[List[Any]] = None):
        """
        Inicializa a crew funcional.
        
        Args:
            crew_type: Tipo da crew (sales, support, info, scheduling)
            memory_system: Sistema de memória compartilhada
            data_service_hub: Hub central para todos os serviços de dados
            agent_cache: Cache para resultados de agentes
            additional_tools: Ferramentas adicionais para os agentes
        """
        self.crew_type = crew_type
        self.memory_system = memory_system
        self.data_service_hub = data_service_hub
        self.agent_cache = agent_cache
        self.additional_tools = additional_tools or []
        
        # Inicializa a crew
        self._initialize_crew()
    
    def _initialize_crew(self):
        """
        Inicializa a crew com os agentes necessários.
        """
        # Cria os agentes
        self.agents = self._create_agents()
        
        # Cria as tarefas
        self.tasks = self._create_tasks()
        
        # Cria a crew
        crew_kwargs = {
            "agents": self.agents,
            "tasks": self.tasks,
            "verbose": True,
            "process": self._get_process_type()
        }
        
        # Adiciona o agent_cache se disponível
        if self.agent_cache:
            crew_kwargs["agent_cache"] = self.agent_cache
            
        self.crew = Crew(**crew_kwargs)
    
    def _create_agents(self) -> List[Agent]:
        """
        Cria os agentes necessários para a crew.
        
        Returns:
            List[Agent]: Lista de agentes
        """
        # Este método deve ser sobrescrito pelas classes filhas
        raise NotImplementedError("Este método deve ser implementado pelas classes filhas")
    
    def _create_tasks(self) -> List[Task]:
        """
        Cria as tarefas necessárias para a crew.
        
        Returns:
            List[Task]: Lista de tarefas
        """
        # Este método deve ser sobrescrito pelas classes filhas
        raise NotImplementedError("Este método deve ser implementado pelas classes filhas")
    
    def _get_process_type(self) -> str:
        """
        Obtém o tipo de processamento da crew.
        
        Returns:
            str: Tipo de processamento (sequential ou hierarchical)
        """
        # Por padrão, usa processamento sequencial
        return "sequential"
    
    def process_message(self, message: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa uma mensagem.
        
        Args:
            message: Mensagem a ser processada
            context: Contexto da conversa
            
        Returns:
            Dict[str, Any]: Resultado do processamento
        """
        # Verifica se há resultado em cache
        cache_key = f"process:{self.crew_type}:{message.get('id', '')}"
        cached_result = self.cache_tool.get(cache_key)
        
        if cached_result:
            logger.info(f"Usando resultado em cache para mensagem {message.get('id', '')}")
            return cached_result
        
        # Executa a crew para processar a mensagem
        result = self.crew.kickoff(
            inputs={
                "message": message,
                "context": context
            }
        )
        
        # Converte o resultado para dicionário, se necessário
        if isinstance(result, str):
            try:
                result = json.loads(result)
            except json.JSONDecodeError:
                result = {"response": result}
        
        # Armazena o resultado em cache
        self.cache_tool.set(cache_key, result, ttl=3600)  # Cache por 1 hora
        
        return result
