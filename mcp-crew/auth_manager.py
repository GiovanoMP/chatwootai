"""
Gerenciador de Autorizações para o MCP-Crew.

Este módulo é responsável pelo controle de autorizações e permissões, incluindo:
- Definição de políticas de acesso
- Verificação de permissões
- Controle de ações autônomas vs. ações que requerem aprovação
- Auditoria de ações
"""

import logging
import time
import uuid
from enum import Enum
from typing import Dict, List, Optional, Any, Callable

from ..utils.logging import get_logger

logger = get_logger(__name__)

class PermissionLevel(Enum):
    """Níveis de permissão para ações no sistema."""
    READ = 0       # Apenas leitura
    EXECUTE = 1    # Execução de ações pré-aprovadas
    WRITE = 2      # Modificação de dados
    ADMIN = 3      # Controle administrativo completo


class ActionType(Enum):
    """Tipos de ações que podem ser realizadas no sistema."""
    QUERY = "query"                # Consulta de informações
    DATA_MODIFICATION = "modify"   # Modificação de dados
    COMMUNICATION = "communicate"  # Comunicação com outros agentes/sistemas
    SYSTEM = "system"              # Operações de sistema
    AUTONOMOUS = "autonomous"      # Ações autônomas


class AuthorizationPolicy:
    """
    Define uma política de autorização para o sistema.
    
    Atributos:
        id (str): Identificador único da política
        name (str): Nome da política
        description (str): Descrição da política
        rules (Dict): Regras de autorização
        require_approval (Dict): Ações que requerem aprovação
    """
    
    def __init__(
        self,
        name: str,
        description: str,
        rules: Optional[Dict[str, Dict[ActionType, PermissionLevel]]] = None,
        require_approval: Optional[Dict[str, List[ActionType]]] = None
    ):
        """
        Inicializa uma nova política de autorização.
        
        Args:
            name: Nome da política
            description: Descrição da política
            rules: Regras de autorização por papel
            require_approval: Ações que requerem aprovação por papel
        """
        self.id = str(uuid.uuid4())
        self.name = name
        self.description = description
        self.rules = rules or {}
        self.require_approval = require_approval or {}
        
        logger.info(f"Política de autorização criada: {self.name}")
    
    def add_rule(self, role: str, action_type: ActionType, permission_level: PermissionLevel) -> None:
        """
        Adiciona uma regra de autorização.
        
        Args:
            role: Papel do agente
            action_type: Tipo de ação
            permission_level: Nível de permissão
        """
        if role not in self.rules:
            self.rules[role] = {}
        
        self.rules[role][action_type] = permission_level
        logger.debug(f"Regra adicionada para {role}: {action_type.value} -> {permission_level.name}")
    
    def set_approval_requirement(self, role: str, action_type: ActionType, required: bool) -> None:
        """
        Define se uma ação requer aprovação.
        
        Args:
            role: Papel do agente
            action_type: Tipo de ação
            required: Se a aprovação é necessária
        """
        if role not in self.require_approval:
            self.require_approval[role] = []
        
        if required and action_type not in self.require_approval[role]:
            self.require_approval[role].append(action_type)
        elif not required and action_type in self.require_approval[role]:
            self.require_approval[role].remove(action_type)
        
        logger.debug(f"Requisito de aprovação para {role}/{action_type.value}: {required}")
    
    def check_permission(self, role: str, action_type: ActionType, required_level: PermissionLevel) -> bool:
        """
        Verifica se um papel tem permissão para uma ação.
        
        Args:
            role: Papel do agente
            action_type: Tipo de ação
            required_level: Nível de permissão necessário
            
        Returns:
            True se tem permissão, False caso contrário
        """
        if role not in self.rules or action_type not in self.rules[role]:
            return False
        
        return self.rules[role][action_type].value >= required_level.value
    
    def requires_approval(self, role: str, action_type: ActionType) -> bool:
        """
        Verifica se uma ação requer aprovação.
        
        Args:
            role: Papel do agente
            action_type: Tipo de ação
            
        Returns:
            True se requer aprovação, False caso contrário
        """
        if role not in self.require_approval:
            return False
        
        return action_type in self.require_approval[role]
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Converte a política para um dicionário.
        
        Returns:
            Dicionário representando a política
        """
        # Converte os enums para strings para facilitar a serialização
        rules_dict = {}
        for role, actions in self.rules.items():
            rules_dict[role] = {action.value: level.value for action, level in actions.items()}
        
        approval_dict = {}
        for role, actions in self.require_approval.items():
            approval_dict[role] = [action.value for action in actions]
        
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "rules": rules_dict,
            "require_approval": approval_dict
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AuthorizationPolicy':
        """
        Cria uma política a partir de um dicionário.
        
        Args:
            data: Dicionário contendo os dados da política
            
        Returns:
            Instância de AuthorizationPolicy
        """
        # Converte as strings de volta para enums
        rules = {}
        for role, actions in data.get("rules", {}).items():
            rules[role] = {
                ActionType(action): PermissionLevel(level)
                for action, level in actions.items()
            }
        
        require_approval = {}
        for role, actions in data.get("require_approval", {}).items():
            require_approval[role] = [ActionType(action) for action in actions]
        
        policy = cls(
            name=data["name"],
            description=data["description"],
            rules=rules,
            require_approval=require_approval
        )
        policy.id = data["id"]
        return policy


class AuditLog:
    """
    Registro de auditoria para ações no sistema.
    
    Atributos:
        id (str): Identificador único do registro
        timestamp (float): Timestamp da ação
        agent_id (str): ID do agente que realizou a ação
        action_type (ActionType): Tipo de ação
        details (Dict): Detalhes da ação
        approved (bool): Se a ação foi aprovada
        approver_id (Optional[str]): ID do aprovador, se aplicável
    """
    
    def __init__(
        self,
        agent_id: str,
        action_type: ActionType,
        details: Dict[str, Any],
        approved: bool = True,
        approver_id: Optional[str] = None
    ):
        """
        Inicializa um novo registro de auditoria.
        
        Args:
            agent_id: ID do agente que realizou a ação
            action_type: Tipo de ação
            details: Detalhes da ação
            approved: Se a ação foi aprovada
            approver_id: ID do aprovador, se aplicável
        """
        self.id = str(uuid.uuid4())
        self.timestamp = time.time()
        self.agent_id = agent_id
        self.action_type = action_type
        self.details = details
        self.approved = approved
        self.approver_id = approver_id
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Converte o registro para um dicionário.
        
        Returns:
            Dicionário representando o registro
        """
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "agent_id": self.agent_id,
            "action_type": self.action_type.value,
            "details": self.details,
            "approved": self.approved,
            "approver_id": self.approver_id
        }


class AuthManager:
    """
    Gerenciador de autorizações para o MCP-Crew.
    
    Responsável por gerenciar políticas de autorização, verificar permissões,
    controlar aprovações e manter registros de auditoria.
    """
    
    def __init__(self):
        """Inicializa o gerenciador de autorizações."""
        self.policies: Dict[str, AuthorizationPolicy] = {}
        self.active_policy_id: Optional[str] = None
        self.audit_logs: List[AuditLog] = []
        self.pending_approvals: Dict[str, Dict[str, Any]] = {}
        self.approval_callbacks: Dict[str, Callable] = {}
        
        # Cria uma política padrão
        self._create_default_policy()
        
        logger.info("AuthManager inicializado")
    
    def _create_default_policy(self) -> None:
        """Cria uma política de autorização padrão."""
        default_policy = AuthorizationPolicy(
            name="Default Policy",
            description="Política padrão com permissões básicas"
        )
        
        # Define regras padrão
        for action_type in ActionType:
            # Administradores têm permissão total
            default_policy.add_rule("admin", action_type, PermissionLevel.ADMIN)
            
            # Analistas têm permissão de leitura e execução
            default_policy.add_rule("analyst", action_type, PermissionLevel.EXECUTE)
            
            # Usuários comuns têm permissão de leitura
            default_policy.add_rule("user", action_type, PermissionLevel.READ)
        
        # Ações autônomas requerem aprovação para analistas
        default_policy.set_approval_requirement("analyst", ActionType.AUTONOMOUS, True)
        
        # Registra a política e define como ativa
        self.register_policy(default_policy)
        self.set_active_policy(default_policy.id)
    
    def register_policy(self, policy: AuthorizationPolicy) -> str:
        """
        Registra uma nova política de autorização.
        
        Args:
            policy: Política a ser registrada
            
        Returns:
            ID da política registrada
        """
        self.policies[policy.id] = policy
        logger.info(f"Política registrada: {policy.name} ({policy.id})")
        return policy.id
    
    def get_policy(self, policy_id: str) -> Optional[AuthorizationPolicy]:
        """
        Obtém uma política pelo ID.
        
        Args:
            policy_id: ID da política
            
        Returns:
            Política correspondente ou None se não encontrada
        """
        return self.policies.get(policy_id)
    
    def set_active_policy(self, policy_id: str) -> bool:
        """
        Define a política ativa.
        
        Args:
            policy_id: ID da política
            
        Returns:
            True se a política foi definida, False caso contrário
        """
        if policy_id in self.policies:
            self.active_policy_id = policy_id
            logger.info(f"Política ativa definida: {self.policies[policy_id].name} ({policy_id})")
            return True
        return False
    
    def get_active_policy(self) -> Optional[AuthorizationPolicy]:
        """
        Obtém a política ativa.
        
        Returns:
            Política ativa ou None se não houver
        """
        if self.active_policy_id:
            return self.policies.get(self.active_policy_id)
        return None
    
    def check_permission(
        self,
        agent_id: str,
        role: str,
        action_type: ActionType,
        required_level: PermissionLevel
    ) -> bool:
        """
        Verifica se um agente tem permissão para uma ação.
        
        Args:
            agent_id: ID do agente
            role: Papel do agente
            action_type: Tipo de ação
            required_level: Nível de permissão necessário
            
        Returns:
            True se tem permissão, False caso contrário
        """
        policy = self.get_active_policy()
        if not policy:
            logger.warning("Nenhuma política ativa definida")
            return False
        
        has_permission = policy.check_permission(role, action_type, required_level)
        
        # Registra a verificação no log
        self.audit_logs.append(AuditLog(
            agent_id=agent_id,
            action_type=action_type,
            details={
                "role": role,
                "required_level": required_level.name,
                "permission_granted": has_permission
            }
        ))
        
        if has_permission:
            logger.debug(f"Permissão concedida: {agent_id} ({role}) -> {action_type.value}")
        else:
            logger.warning(f"Permissão negada: {agent_id} ({role}) -> {action_type.value}")
        
        return has_permission
    
    def requires_approval(self, role: str, action_type: ActionType) -> bool:
        """
        Verifica se uma ação requer aprovação.
        
        Args:
            role: Papel do agente
            action_type: Tipo de ação
            
        Returns:
            True se requer aprovação, False caso contrário
        """
        policy = self.get_active_policy()
        if not policy:
            logger.warning("Nenhuma política ativa definida")
            return True  # Por segurança, assume que requer aprovação
        
        return policy.requires_approval(role, action_type)
    
    def request_approval(
        self,
        agent_id: str,
        role: str,
        action_type: ActionType,
        details: Dict[str, Any],
        callback: Optional[Callable] = None
    ) -> str:
        """
        Solicita aprovação para uma ação.
        
        Args:
            agent_id: ID do agente
            role: Papel do agente
            action_type: Tipo de ação
            details: Detalhes da ação
            callback: Função a ser chamada quando a aprovação for decidida
            
        Returns:
            ID da solicitação de aprovação
        """
        request_id = str(uuid.uuid4())
        
        self.pending_approvals[request_id] = {
            "agent_id": agent_id,
            "role": role,
            "action_type": action_type,
            "details": details,
            "timestamp": time.time()
        }
        
        if callback:
            self.approval_callbacks[request_id] = callback
        
        logger.info(f"Solicitação de aprovação criada: {request_id} - {agent_id} ({role}) -> {action_type.value}")
        return request_id
    
    def approve_action(self, request_id: str, approver_id: str) -> bool:
        """
        Aprova uma ação pendente.
        
        Args:
            request_id: ID da solicitação de aprovação
            approver_id: ID do aprovador
            
        Returns:
            True se a ação foi aprovada, False caso contrário
        """
        if request_id not in self.pending_approvals:
            logger.warning(f"Solicitação de aprovação não encontrada: {request_id}")
            return False
        
        request = self.pending_approvals.pop(request_id)
        
        # Registra a aprovação no log
        self.audit_logs.append(AuditLog(
            agent_id=request["agent_id"],
            action_type=request["action_type"],
            details=request["details"],
            approved=True,
            approver_id=approver_id
        ))
        
        logger.info(f"Ação aprovada: {request_id} por {approver_id}")
        
        # Executa o callback, se existir
        if request_id in self.approval_callbacks:
            callback = self.approval_callbacks.pop(request_id)
            try:
                callback(True, approver_id)
(Content truncated due to size limit. Use line ranges to read in chunks)