"""
Gerenciador de Agentes para o MCP-Crew.

Este módulo é responsável por gerenciar os agentes de IA, incluindo:
- Registro e remoção de agentes
- Atribuição de papéis e responsabilidades
- Coordenação de comunicação entre agentes
- Monitoramento de status e desempenho
"""

import logging
import uuid
from typing import Dict, List, Optional, Any

from ..utils.logging import get_logger

logger = get_logger(__name__)

class Agent:
    """
    Classe que representa um agente de IA no sistema MCP-Crew.
    
    Atributos:
        id (str): Identificador único do agente
        name (str): Nome do agente
        role (str): Papel/função do agente
        capabilities (List[str]): Lista de capacidades do agente
        status (str): Status atual do agente
        metadata (Dict): Metadados adicionais do agente
    """
    
    def __init__(
        self,
        name: str,
        role: str,
        capabilities: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Inicializa um novo agente.
        
        Args:
            name: Nome do agente
            role: Papel/função do agente
            capabilities: Lista de capacidades do agente
            metadata: Metadados adicionais do agente
        """
        self.id = str(uuid.uuid4())
        self.name = name
        self.role = role
        self.capabilities = capabilities or []
        self.status = "idle"
        self.metadata = metadata or {}
        
        logger.info(f"Agente criado: {self.name} ({self.role})")
    
    def update_status(self, status: str) -> None:
        """
        Atualiza o status do agente.
        
        Args:
            status: Novo status do agente
        """
        old_status = self.status
        self.status = status
        logger.debug(f"Status do agente {self.name} atualizado: {old_status} -> {status}")
    
    def add_capability(self, capability: str) -> None:
        """
        Adiciona uma nova capacidade ao agente.
        
        Args:
            capability: Capacidade a ser adicionada
        """
        if capability not in self.capabilities:
            self.capabilities.append(capability)
            logger.debug(f"Capacidade adicionada ao agente {self.name}: {capability}")
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Converte o agente para um dicionário.
        
        Returns:
            Dicionário representando o agente
        """
        return {
            "id": self.id,
            "name": self.name,
            "role": self.role,
            "capabilities": self.capabilities,
            "status": self.status,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Agent':
        """
        Cria um agente a partir de um dicionário.
        
        Args:
            data: Dicionário contendo os dados do agente
            
        Returns:
            Instância de Agent
        """
        agent = cls(
            name=data["name"],
            role=data["role"],
            capabilities=data.get("capabilities", []),
            metadata=data.get("metadata", {})
        )
        agent.id = data["id"]
        agent.status = data["status"]
        return agent


class AgentManager:
    """
    Gerenciador de agentes para o MCP-Crew.
    
    Responsável por gerenciar o ciclo de vida dos agentes, incluindo
    registro, remoção, atribuição de tarefas e coordenação.
    """
    
    def __init__(self):
        """Inicializa o gerenciador de agentes."""
        self.agents: Dict[str, Agent] = {}
        self.agent_groups: Dict[str, List[str]] = {}
        logger.info("AgentManager inicializado")
    
    def register_agent(self, agent: Agent) -> str:
        """
        Registra um novo agente no sistema.
        
        Args:
            agent: Agente a ser registrado
            
        Returns:
            ID do agente registrado
        """
        self.agents[agent.id] = agent
        logger.info(f"Agente registrado: {agent.name} ({agent.id})")
        return agent.id
    
    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """
        Obtém um agente pelo ID.
        
        Args:
            agent_id: ID do agente
            
        Returns:
            Agente correspondente ou None se não encontrado
        """
        return self.agents.get(agent_id)
    
    def remove_agent(self, agent_id: str) -> bool:
        """
        Remove um agente do sistema.
        
        Args:
            agent_id: ID do agente a ser removido
            
        Returns:
            True se o agente foi removido, False caso contrário
        """
        if agent_id in self.agents:
            agent = self.agents.pop(agent_id)
            logger.info(f"Agente removido: {agent.name} ({agent_id})")
            
            # Remove o agente de todos os grupos
            for group_id, agent_ids in self.agent_groups.items():
                if agent_id in agent_ids:
                    self.agent_groups[group_id].remove(agent_id)
                    logger.debug(f"Agente {agent_id} removido do grupo {group_id}")
            
            return True
        return False
    
    def create_group(self, group_id: str, agent_ids: Optional[List[str]] = None) -> None:
        """
        Cria um novo grupo de agentes.
        
        Args:
            group_id: ID do grupo
            agent_ids: Lista de IDs de agentes para adicionar ao grupo
        """
        if group_id in self.agent_groups:
            logger.warning(f"Grupo {group_id} já existe, será sobrescrito")
        
        self.agent_groups[group_id] = []
        
        if agent_ids:
            for agent_id in agent_ids:
                if agent_id in self.agents:
                    self.agent_groups[group_id].append(agent_id)
                else:
                    logger.warning(f"Agente {agent_id} não encontrado, não será adicionado ao grupo {group_id}")
        
        logger.info(f"Grupo {group_id} criado com {len(self.agent_groups[group_id])} agentes")
    
    def add_agent_to_group(self, group_id: str, agent_id: str) -> bool:
        """
        Adiciona um agente a um grupo.
        
        Args:
            group_id: ID do grupo
            agent_id: ID do agente
            
        Returns:
            True se o agente foi adicionado, False caso contrário
        """
        if group_id not in self.agent_groups:
            logger.warning(f"Grupo {group_id} não encontrado")
            return False
        
        if agent_id not in self.agents:
            logger.warning(f"Agente {agent_id} não encontrado")
            return False
        
        if agent_id not in self.agent_groups[group_id]:
            self.agent_groups[group_id].append(agent_id)
            logger.debug(f"Agente {agent_id} adicionado ao grupo {group_id}")
            return True
        
        logger.debug(f"Agente {agent_id} já está no grupo {group_id}")
        return False
    
    def get_agents_by_role(self, role: str) -> List[Agent]:
        """
        Obtém todos os agentes com um determinado papel.
        
        Args:
            role: Papel/função dos agentes
            
        Returns:
            Lista de agentes com o papel especificado
        """
        return [agent for agent in self.agents.values() if agent.role == role]
    
    def get_agents_by_capability(self, capability: str) -> List[Agent]:
        """
        Obtém todos os agentes com uma determinada capacidade.
        
        Args:
            capability: Capacidade dos agentes
            
        Returns:
            Lista de agentes com a capacidade especificada
        """
        return [
            agent for agent in self.agents.values() 
            if capability in agent.capabilities
        ]
    
    def get_agents_in_group(self, group_id: str) -> List[Agent]:
        """
        Obtém todos os agentes em um determinado grupo.
        
        Args:
            group_id: ID do grupo
            
        Returns:
            Lista de agentes no grupo especificado
        """
        if group_id not in self.agent_groups:
            logger.warning(f"Grupo {group_id} não encontrado")
            return []
        
        return [
            self.agents[agent_id] for agent_id in self.agent_groups[group_id]
            if agent_id in self.agents
        ]
    
    def get_all_agents(self) -> List[Agent]:
        """
        Obtém todos os agentes registrados.
        
        Returns:
            Lista de todos os agentes
        """
        return list(self.agents.values())
    
    def update_agent_status(self, agent_id: str, status: str) -> bool:
        """
        Atualiza o status de um agente.
        
        Args:
            agent_id: ID do agente
            status: Novo status
            
        Returns:
            True se o status foi atualizado, False caso contrário
        """
        agent = self.get_agent(agent_id)
        if agent:
            agent.update_status(status)
            return True
        return False
