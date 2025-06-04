"""
Gerenciador de Crews para o MCP-Crew.

Este módulo implementa o CrewManager, responsável por criar, configurar
e gerenciar crews do CrewAI, associando MCPs como ferramentas (tools)
e garantindo suporte a multi-tenancy via account_id.
"""

from typing import Dict, List, Optional, Any, Union, Callable
import asyncio
import time
import uuid
import json

# Importações do CrewAI (necessário instalar: pip install crewai crewai-tools)
try:
    from crewai import Agent, Task, Crew, Process
    from crewai_tools import MCPServerAdapter
except ImportError:
    raise ImportError("CrewAI não encontrado. Instale com: pip install crewai crewai-tools")

from .mcp_connector_manager import MCPConnectorManager
from .context_manager import ContextManager, ContextType

from utils.logging import get_logger
logger = get_logger(__name__)


class CrewManager:
    """
    Gerenciador de Crews para o MCP-Crew.
    
    Responsável por criar, configurar e gerenciar crews do CrewAI,
    associando MCPs como ferramentas (tools) e garantindo suporte
    a multi-tenancy via account_id.
    """
    
    def __init__(
        self,
        connector_manager: MCPConnectorManager,
        context_manager: ContextManager
    ):
        """
        Inicializa o gerenciador de crews.
        
        Args:
            connector_manager: Gerenciador de conectores MCP
            context_manager: Gerenciador de contexto
        """
        self.connector_manager = connector_manager
        self.context_manager = context_manager
        self.crews: Dict[str, Dict[str, Any]] = {}  # {crew_id: {crew, config, account_id}}
        logger.info("CrewManager inicializado")
    
    async def create_crew(
        self,
        account_id: str,
        name: str,
        description: str,
        agents: List[Dict[str, Any]],
        tasks: List[Dict[str, Any]],
        mcp_ids: List[str] = None,
        process: str = "sequential",
        verbose: bool = False,
        config: Dict[str, Any] = None
    ) -> str:
        """
        Cria uma nova crew.
        
        Args:
            account_id: ID da conta (tenant)
            name: Nome da crew
            description: Descrição da crew
            agents: Lista de configurações de agentes
            tasks: Lista de configurações de tarefas
            mcp_ids: Lista de IDs de MCPs a serem associados como ferramentas
            process: Processo de execução (sequential, hierarchical)
            verbose: Modo verboso
            config: Configurações adicionais
            
        Returns:
            ID da crew criada
        """
        crew_id = str(uuid.uuid4())
        
        # Cria os agentes
        crew_agents = []
        for agent_config in agents:
            # Obtém ferramentas dos MCPs especificados para este agente
            tools = []
            agent_mcp_ids = agent_config.get("mcp_ids", mcp_ids or [])
            for mcp_id in agent_mcp_ids:
                # Verifica se o conector está disponível para esta conta
                connector = self.connector_manager.get_connector_by_account(account_id, mcp_id)
                if connector:
                    # Adiciona ferramentas do MCP
                    mcp_tools = self.connector_manager.to_crewai_tools(mcp_id)
                    tools.extend(mcp_tools)
            
            # Cria o agente
            agent = Agent(
                role=agent_config["role"],
                goal=agent_config["goal"],
                backstory=agent_config.get("backstory", ""),
                verbose=agent_config.get("verbose", verbose),
                allow_delegation=agent_config.get("allow_delegation", False),
                tools=tools
            )
            crew_agents.append(agent)
        
        # Cria as tarefas
        crew_tasks = []
        for task_config in tasks:
            # Determina o agente responsável pela tarefa
            agent = None
            if "agent_role" in task_config:
                for a in crew_agents:
                    if a.role == task_config["agent_role"]:
                        agent = a
                        break
            
            if not agent and crew_agents:
                agent = crew_agents[0]  # Usa o primeiro agente se não especificado
            
            # Cria a tarefa
            task = Task(
                description=task_config["description"],
                expected_output=task_config.get("expected_output", ""),
                agent=agent,
                context=task_config.get("context", "")
            )
            crew_tasks.append(task)
        
        # Cria a crew
        crew_process = Process.SEQUENTIAL
        if process.lower() == "hierarchical":
            crew_process = Process.HIERARCHICAL
        
        crew = Crew(
            agents=crew_agents,
            tasks=crew_tasks,
            verbose=verbose,
            process=crew_process,
            config=config or {}
        )
        
        # Armazena a crew
        self.crews[crew_id] = {
            "crew": crew,
            "config": {
                "name": name,
                "description": description,
                "process": process,
                "verbose": verbose
            },
            "account_id": account_id,
            "created_at": time.time()
        }
        
        # Armazena no contexto
        self.context_manager.create_context(
            context_type=ContextType.TASK,
            owner_id=f"{account_id}:crew:{crew_id}",
            data={
                "crew_id": crew_id,
                "name": name,
                "description": description,
                "agents": [a["role"] for a in agents],
                "tasks": [t["description"] for t in tasks],
                "mcp_ids": mcp_ids,
                "created_at": time.time()
            },
            metadata={
                "account_id": account_id,
                "type": "crew"
            }
        )
        
        logger.info(f"Crew {name} ({crew_id}) criada para conta {account_id}")
        return crew_id
    
    async def run_crew(
        self,
        crew_id: str,
        inputs: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Executa uma crew.
        
        Args:
            crew_id: ID da crew
            inputs: Entradas para a execução
            
        Returns:
            Resultado da execução
        """
        if crew_id not in self.crews:
            logger.error(f"Crew {crew_id} não encontrada")
            raise ValueError(f"Crew {crew_id} não encontrada")
        
        crew_data = self.crews[crew_id]
        crew = crew_data["crew"]
        account_id = crew_data["account_id"]
        
        logger.info(f"Executando crew {crew_id} para conta {account_id}")
        
        # Executa a crew
        try:
            # O CrewAI executa de forma síncrona, então usamos run_in_executor
            # para não bloquear o loop de eventos
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: crew.kickoff(inputs=inputs or {})
            )
            
            # Armazena o resultado no contexto
            self.context_manager.create_context(
                context_type=ContextType.TASK,
                owner_id=f"{account_id}:crew:{crew_id}:result",
                data={
                    "crew_id": crew_id,
                    "result": result,
                    "timestamp": time.time()
                },
                metadata={
                    "account_id": account_id,
                    "type": "crew_result"
                }
            )
            
            logger.info(f"Crew {crew_id} executada com sucesso")
            return {"crew_id": crew_id, "result": result}
        except Exception as e:
            logger.error(f"Erro ao executar crew {crew_id}: {e}")
            raise
    
    def get_crew(self, crew_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtém informações sobre uma crew.
        
        Args:
            crew_id: ID da crew
            
        Returns:
            Informações da crew ou None se não encontrada
        """
        if crew_id not in self.crews:
            return None
        
        crew_data = self.crews[crew_id]
        return {
            "crew_id": crew_id,
            "name": crew_data["config"]["name"],
            "description": crew_data["config"]["description"],
            "account_id": crew_data["account_id"],
            "created_at": crew_data.get("created_at", 0)
        }
    
    def get_crews_by_account(self, account_id: str) -> List[Dict[str, Any]]:
        """
        Obtém todas as crews de uma conta.
        
        Args:
            account_id: ID da conta
            
        Returns:
            Lista de informações das crews
        """
        result = []
        for crew_id, crew_data in self.crews.items():
            if crew_data["account_id"] == account_id:
                result.append({
                    "crew_id": crew_id,
                    "name": crew_data["config"]["name"],
                    "description": crew_data["config"]["description"],
                    "created_at": crew_data.get("created_at", 0)
                })
        return result
    
    def delete_crew(self, crew_id: str) -> bool:
        """
        Remove uma crew.
        
        Args:
            crew_id: ID da crew
            
        Returns:
            True se removida com sucesso, False caso contrário
        """
        if crew_id not in self.crews:
            return False
        
        crew_data = self.crews[crew_id]
        account_id = crew_data["account_id"]
        
        # Remove do dicionário
        del self.crews[crew_id]
        
        # Remove contextos associados
        contexts = self.context_manager.get_contexts_by_owner(
            owner_id=f"{account_id}:crew:{crew_id}"
        )
        for context in contexts:
            self.context_manager.delete_context(context.id)
        
        logger.info(f"Crew {crew_id} removida")
        return True
    
    def get_crew_results(self, crew_id: str) -> List[Dict[str, Any]]:
        """
        Obtém os resultados de execução de uma crew.
        
        Args:
            crew_id: ID da crew
            
        Returns:
            Lista de resultados
        """
        if crew_id not in self.crews:
            logger.error(f"Crew {crew_id} não encontrada")
            return []
        
        crew_data = self.crews[crew_id]
        account_id = crew_data["account_id"]
        
        # Busca contextos de resultados
        contexts = self.context_manager.get_contexts_by_owner(
            owner_id=f"{account_id}:crew:{crew_id}:result"
        )
        
        results = []
        for context in contexts:
            results.append(context.data)
        
        return results
