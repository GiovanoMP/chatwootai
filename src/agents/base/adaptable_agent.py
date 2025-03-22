"""
Agente base adaptável para diferentes domínios de negócio.
"""
from typing import Dict, List, Any, Optional
import logging
from abc import ABC, abstractmethod
from pydantic import ConfigDict

from src.agents.base.functional_agent import FunctionalAgent
from src.core.domain import DomainManager
from src.plugins.core.plugin_manager import PluginManager

logger = logging.getLogger(__name__)


class AdaptableAgent(FunctionalAgent, ABC):
    """
    Agente base adaptável para diferentes domínios de negócio.
    
    Esta classe estende o FunctionalAgent e adiciona funcionalidades para
    adaptar o comportamento do agente de acordo com o domínio de negócio.
    """
    # Configuração do modelo Pydantic para permitir tipos arbitrários
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    def __init__(self, 
                 agent_config: Dict[str, Any], 
                 memory_system=None, 
                 data_proxy_agent=None, 
                 domain_manager=None, 
                 plugin_manager=None):
        """
        Inicializa o agente adaptável.
        
        Args:
            agent_config: Configuração do agente
            memory_system: Sistema de memória compartilhada
            data_proxy_agent: Agente proxy para acesso a dados
            domain_manager: Gerenciador de domínios de negócio
            plugin_manager: Gerenciador de plugins
        """
        # Extrai o tipo de função do agente
        function_type = agent_config.pop("function_type", "unknown")
        
        # Prepara os dados para o modelo Pydantic
        model_data = {
            "function_type": function_type,
            "memory_system": memory_system
        }
        
        # Armazena atributos no dicionário privado para evitar problemas com Pydantic
        self.__dict__["_data_proxy_agent"] = data_proxy_agent
        self.__dict__["_domain_manager"] = domain_manager or DomainManager()
        self.__dict__["_plugin_manager"] = plugin_manager or PluginManager(config={})
        self.__dict__["_domain_config"] = {}
        self.__dict__["_domain_plugins"] = []
        
        # Chama o construtor da classe pai com os parâmetros necessários
        super().__init__(
            **model_data,
            **agent_config
        )
        
        # Carrega a configuração específica do domínio para este agente
        self.__dict__["_domain_config"] = self._load_domain_config(agent_config)
        
        # Carrega os plugins específicos do domínio
        self.__dict__["_domain_plugins"] = self._load_domain_plugins()
    
    # Propriedades para acessar os atributos privados
    @property
    def data_proxy_agent(self):
        """Retorna o agente proxy para acesso a dados."""
        return self.__dict__.get("_data_proxy_agent")
    
    @property
    def domain_manager(self):
        """Retorna o gerenciador de domínios de negócio."""
        return self.__dict__.get("_domain_manager")
    
    @property
    def plugin_manager(self):
        """Retorna o gerenciador de plugins."""
        return self.__dict__.get("_plugin_manager")
    
    @property
    def domain_config(self):
        """Retorna a configuração específica do domínio."""
        return self.__dict__.get("_domain_config", {})
    
    @property
    def domain_plugins(self):
        """Retorna os plugins específicos do domínio."""
        return self.__dict__.get("_domain_plugins", [])
    
    def _load_domain_config(self, agent_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Carrega a configuração específica do domínio para este agente.
        
        Args:
            agent_config: Configuração do agente (opcional)
            
        Returns:
            Dict[str, Any]: Configuração específica do domínio
        """
        agent_type = self.get_agent_type()
        agent_name = agent_config.get("name", None) if agent_config else None
        
        if self.domain_manager:
            return self.domain_manager.get_agent_config(agent_type, agent_name)
        return {}
    
    def _load_domain_plugins(self) -> List[Any]:
        """
        Carrega os plugins específicos do domínio.
        
        Returns:
            List[Any]: Plugins específicos do domínio
        """
        if not self.domain_manager:
            logger.warning("Nenhum gerenciador de domínio disponível. Retornando lista vazia de plugins.")
            return []
            
        domain_name = getattr(self.domain_manager, 'active_domain_name', None)
        if not domain_name:
            logger.warning("Nenhum domínio ativo encontrado. Retornando lista vazia de plugins.")
            return []
            
        if not self.plugin_manager:
            logger.warning("Nenhum gerenciador de plugins disponível. Retornando lista vazia de plugins.")
            return []
            
        return self.plugin_manager.get_domain_plugins(domain_name, self.get_agent_type())
    
    @abstractmethod
    def get_agent_type(self) -> str:
        """
        Obtém o tipo do agente.
        
        Returns:
            str: Tipo do agente
        """
        pass
    
    def adapt_prompt(self, prompt: str) -> str:
        """
        Adapta um prompt de acordo com o domínio de negócio.
        
        Args:
            prompt: Prompt original
            
        Returns:
            str: Prompt adaptado
        """
        if not self.domain_manager:
            return prompt
            
        domain_info = self.domain_manager.get_active_domain()
        if not domain_info:
            return prompt
            
        # Substitui placeholders no prompt
        adapted_prompt = prompt.replace("{domain_name}", domain_info.get("name", ""))
        
        # Adiciona regras específicas do domínio se disponíveis
        if "rules" in domain_info:
            rules_text = "\n".join([f"- {rule}" for rule in domain_info["rules"]])
            adapted_prompt = adapted_prompt.replace("{domain_rules}", rules_text)
        
        # Substitui outros placeholders com valores do domínio
        for key, value in domain_info.items():
            placeholder = "{" + key + "}"
            if placeholder in adapted_prompt:
                adapted_prompt = adapted_prompt.replace(placeholder, str(value))
        
        return adapted_prompt
    
    def adapt_response(self, response: str) -> str:
        """
        Adapta uma resposta de acordo com o domínio de negócio.
        
        Args:
            response: Resposta original
            
        Returns:
            str: Resposta adaptada
        """
        if not self.domain_manager:
            return response
            
        domain_info = self.domain_manager.get_active_domain()
        if not domain_info:
            return response
            
        # Adiciona assinatura personalizada com base no domínio
        if "signature" in domain_info:
            response += f"\n\n{domain_info['signature']}"
        
        return response
    
    def execute_task(self, task: Any) -> str:
        """
        Executa uma tarefa usando o agente.
        
        Args:
            task: Tarefa a ser executada
            
        Returns:
            str: Resultado da execução da tarefa
        """
        # Implementação padrão que pode ser sobrescrita por subclasses
        logger.warning("Método execute_task não implementado na classe base. Retornando mensagem padrão.")
        return "Tarefa não implementada."
