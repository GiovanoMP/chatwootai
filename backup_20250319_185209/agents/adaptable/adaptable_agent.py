"""
Agente base adaptável para diferentes domínios de negócio.
"""
from typing import Dict, List, Any, Optional
import logging
from abc import ABC, abstractmethod

from src.agents.functional_agents import FunctionalAgent
from src.core.domain import DomainManager
from src.plugins.plugin_manager import PluginManager

logger = logging.getLogger(__name__)


class AdaptableAgent(FunctionalAgent, ABC):
    """
    Agente base adaptável para diferentes domínios de negócio.
    
    Esta classe estende o FunctionalAgent e adiciona funcionalidades para
    adaptar o comportamento do agente de acordo com o domínio de negócio.
    """
    # Configuração do modelo Pydantic para permitir tipos arbitrários
    model_config = {"arbitrary_types_allowed": True}
    
    # Campos adicionais para o modelo Pydantic
    domain_manager: Optional[DomainManager] = None
    plugin_manager: Optional[PluginManager] = None
    data_proxy_agent: Optional[Any] = None
    domain_config: Optional[Dict[str, Any]] = None
    domain_plugins: Optional[List[Any]] = None
    
    def __init__(self, 
                 agent_config: Dict[str, Any], 
                 memory_system=None, 
                 data_proxy_agent=None, 
                 domain_manager: DomainManager = None, 
                 plugin_manager: PluginManager = None):
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
            "memory_system": memory_system,
            "data_proxy_agent": data_proxy_agent,
            "domain_manager": domain_manager or DomainManager(),
            "plugin_manager": plugin_manager or PluginManager(config={})
        }
        
        # Chama o construtor da classe pai com os parâmetros necessários
        super().__init__(
            **model_data,
            **agent_config
        )
        
        # Carrega a configuração específica do domínio para este agente
        self.domain_config = self._load_domain_config(agent_config)
        
        # Carrega os plugins específicos do domínio
        self.domain_plugins = self._load_domain_plugins()
    
    def _load_domain_config(self, agent_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Carrega a configuração específica do domínio para este agente.
        
        Args:
            agent_config: Configuração do agente (opcional)
            
        Returns:
            Dict[str, Any]: Configuração específica do domínio
        """
        agent_type = self.get_agent_type()
        agent_name = agent_config.get("name", None) if agent_config else self._config.get("name", None)
        
        return self.domain_manager.get_agent_config(agent_type, agent_name)
    
    def _load_domain_plugins(self) -> Dict[str, Any]:
        """
        Carrega os plugins específicos do domínio.
        
        Returns:
            Dict[str, Any]: Plugins específicos do domínio
        """
        domain_name = getattr(self.domain_manager, 'active_domain_name', None)
        if not domain_name:
            logger.warning("Nenhum domínio ativo encontrado. Retornando lista vazia de plugins.")
            return {}
            
        return self.plugin_manager.get_plugins_for_domain(domain_name)
    
    @abstractmethod
    def get_agent_type(self) -> str:
        """
        Obtém o tipo do agente (sales, support, scheduling).
        
        Returns:
            str: Tipo do agente
        """
        pass
    
    def get_business_rules(self, category: str = None) -> Dict[str, Any]:
        """
        Obtém as regras de negócio do domínio ativo.
        
        Args:
            category: Categoria específica de regras (opcional)
            
        Returns:
            Dict[str, Any]: Regras de negócio
        """
        return self.domain_manager.get_business_rules(category)
    
    def execute_plugin(self, plugin_name: str, action: str, **kwargs) -> Any:
        """
        Executa uma ação de um plugin.
        
        Args:
            plugin_name: Nome do plugin
            action: Ação a ser executada
            **kwargs: Parâmetros específicos da ação
            
        Returns:
            Any: Resultado da ação
        """
        return self.plugin_manager.execute_plugin(plugin_name, action, **kwargs)
    
    def adapt_prompt(self, prompt: str) -> str:
        """
        Adapta um prompt de acordo com o domínio de negócio.
        
        Args:
            prompt: Prompt original
            
        Returns:
            str: Prompt adaptado
        """
        # Obtém informações do domínio
        domain_info = self.domain_manager.get_active_domain()
        
        # Substitui placeholders no prompt
        adapted_prompt = prompt
        
        # Substitui o nome do domínio
        if "name" in domain_info:
            adapted_prompt = adapted_prompt.replace("{domain_name}", domain_info["name"])
        
        # Substitui a descrição do domínio
        if "description" in domain_info:
            adapted_prompt = adapted_prompt.replace("{domain_description}", domain_info["description"])
        
        # Substitui regras de negócio específicas
        business_rules = self.get_business_rules()
        for rule_key, rule_value in business_rules.items():
            if isinstance(rule_value, str):
                adapted_prompt = adapted_prompt.replace(f"{{{rule_key}}}", rule_value)
        
        return adapted_prompt
    
    def adapt_response(self, response: str) -> str:
        """
        Adapta uma resposta de acordo com o domínio de negócio.
        
        Args:
            response: Resposta original
            
        Returns:
            str: Resposta adaptada
        """
        # Obtém informações do domínio
        domain_info = self.domain_manager.get_active_domain()
        
        # Adapta a resposta com base nas regras do domínio
        adapted_response = response
        
        # Personaliza a resposta com base no domínio
        if "tone" in domain_info.get("communication_style", {}):
            tone = domain_info["communication_style"]["tone"]
            # Implementar lógica para ajustar o tom da resposta
            # ...
        
        # Adiciona informações específicas do domínio
        if "signature" in domain_info.get("communication_style", {}):
            signature = domain_info["communication_style"]["signature"]
            adapted_response += f"\n\n{signature}"
        
        return adapted_response
