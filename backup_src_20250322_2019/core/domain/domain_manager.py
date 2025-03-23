"""
Gerenciador de domínios de negócio do ChatwootAI.

Este módulo implementa o gerenciamento de domínios de negócio,
permitindo a troca dinâmica entre domínios e o acesso às suas configurações.
"""
import os
import logging
from typing import Dict, Any, Optional, List, Type, Set
import importlib

from .domain_loader import DomainLoader, DomainMetadata, ConfigurationError

logger = logging.getLogger(__name__)


class DomainManager:
    """
    Gerenciador de domínios de negócio do ChatwootAI.
    
    Responsável por gerenciar o domínio ativo e fornecer acesso às configurações
    específicas de cada domínio de negócio, usando a nova estrutura de configuração YAML.
    """
    
    def __init__(self, domains_dir: str = None, default_domain: str = "cosmetics"):
        """
        Inicializa o gerenciador de domínios.
        
        Args:
            domains_dir: Diretório contendo os diretórios de domínios
            default_domain: Nome do domínio padrão
        """
        self.loader = DomainLoader(domains_dir)
        self.default_domain = default_domain
        self.active_domain_name = default_domain
        self.active_domain_config = None
        self._class_cache = {}  # Cache para classes carregadas dinamicamente
    
    def initialize(self):
        """
        Inicializa o gerenciador carregando o domínio padrão.
        
        Raises:
            ConfigurationError: Se nenhum domínio puder ser carregado
        """
        logger.info(f"Inicializando DomainManager com domínio padrão: {self.default_domain}")
        self.active_domain_config = self.loader.load_domain(self.default_domain)
        
        if not self.active_domain_config:
            logger.warning(f"Domínio padrão não encontrado: {self.default_domain}")
            # Tenta carregar qualquer domínio disponível
            available_domains = self.loader.list_available_domains()
            if available_domains:
                self.active_domain_name = available_domains[0]
                self.active_domain_config = self.loader.load_domain(self.active_domain_name)
                logger.info(f"Usando domínio alternativo: {self.active_domain_name}")
            else:
                error_msg = "Nenhum domínio disponível encontrado"
                logger.error(error_msg)
                raise ConfigurationError(error_msg)
        else:
            logger.info(f"Domínio padrão carregado: {self.default_domain}")
    
    def get_active_domain(self) -> Dict[str, Any]:
        """
        Obtém a configuração do domínio ativo.
        
        Returns:
            Dict[str, Any]: Configuração do domínio ativo
        """
        if not self.active_domain_config:
            self.initialize()
        
        return self.active_domain_config or {}
    
    def get_active_domain_name(self) -> str:
        """
        Obtém o nome do domínio ativo.
        
        Returns:
            str: Nome do domínio ativo
        """
        return self.active_domain_name
    
    def switch_domain(self, domain_name: str) -> bool:
        """
        Altera o domínio ativo.
        
        Args:
            domain_name: Nome do novo domínio ativo
            
        Returns:
            bool: True se a alteração foi bem-sucedida, False caso contrário
        """
        domain_config = self.loader.load_domain(domain_name)
        
        if not domain_config:
            logger.error(f"Não foi possível carregar o domínio: {domain_name}")
            return False
        
        self.active_domain_name = domain_name
        self.active_domain_config = domain_config
        logger.info(f"Domínio ativo alterado para: {domain_name}")
        
        return True
    
    def get_domain_config(self, domain_name: str = None) -> Dict[str, Any]:
        """
        Obtém a configuração de um domínio específico.
        
        Args:
            domain_name: Nome do domínio (se None, usa o domínio ativo)
            
        Returns:
            Dict[str, Any]: Configuração do domínio
        """
        if domain_name is None:
            return self.get_active_domain()
        
        return self.loader.load_domain(domain_name) or {}
    
    def list_domains(self) -> List[DomainMetadata]:
        """
        Lista todos os domínios disponíveis com informações básicas.
        
        Returns:
            List[DomainMetadata]: Lista de metadados de domínios
        """
        domain_names = self.loader.list_available_domains()
        domains_info = []
        
        for domain_name in domain_names:
            domain_info = self.loader.get_domain_info(domain_name)
            domains_info.append(domain_info)
        
        return domains_info
    
    def get_agents_config(self, domain_name: str = None) -> Dict[str, Any]:
        """
        Obtém as configurações de todos os agentes de um domínio.
        
        Args:
            domain_name: Nome do domínio (se None, usa o domínio ativo)
            
        Returns:
            Dict[str, Any]: Configurações de agentes
        """
        domain_config = self.get_domain_config(domain_name)
        return domain_config.get("agents", {})
    
    def get_agent_config(self, agent_name: str, domain_name: str = None) -> Dict[str, Any]:
        """
        Obtém a configuração de um agente específico.
        
        Args:
            agent_name: Nome do agente
            domain_name: Nome do domínio (se None, usa o domínio ativo)
            
        Returns:
            Dict[str, Any]: Configuração do agente
        """
        agents_config = self.get_agents_config(domain_name)
        return agents_config.get(agent_name, {})
    
    def get_tools_config(self, domain_name: str = None) -> Dict[str, Any]:
        """
        Obtém as configurações de todas as ferramentas de um domínio.
        
        Args:
            domain_name: Nome do domínio (se None, usa o domínio ativo)
            
        Returns:
            Dict[str, Any]: Configurações de ferramentas
        """
        domain_config = self.get_domain_config(domain_name)
        return domain_config.get("tools", {})
    
    def get_tool_config(self, tool_name: str, domain_name: str = None) -> Dict[str, Any]:
        """
        Obtém a configuração de uma ferramenta específica.
        
        Args:
            tool_name: Nome da ferramenta
            domain_name: Nome do domínio (se None, usa o domínio ativo)
            
        Returns:
            Dict[str, Any]: Configuração da ferramenta
        """
        tools_config = self.get_tools_config(domain_name)
        return tools_config.get(tool_name, {})
    
    def get_crew_config(self, domain_name: str = None) -> Dict[str, Any]:
        """
        Obtém a configuração da crew de um domínio.
        
        Args:
            domain_name: Nome do domínio (se None, usa o domínio ativo)
            
        Returns:
            Dict[str, Any]: Configuração da crew
        """
        domain_config = self.get_domain_config(domain_name)
        return domain_config.get("crew", {})
    
    def get_integrations_config(self, domain_name: str = None) -> Dict[str, Any]:
        """
        Obtém as configurações de integrações de um domínio.
        
        Args:
            domain_name: Nome do domínio (se None, usa o domínio ativo)
            
        Returns:
            Dict[str, Any]: Configurações de integrações
        """
        domain_config = self.get_domain_config(domain_name)
        return domain_config.get("integrations", {})
    
    def get_integration_config(self, integration_name: str, domain_name: str = None) -> Dict[str, Any]:
        """
        Obtém a configuração de uma integração específica.
        
        Args:
            integration_name: Nome da integração
            domain_name: Nome do domínio (se None, usa o domínio ativo)
            
        Returns:
            Dict[str, Any]: Configuração da integração
        """
        integrations_config = self.get_integrations_config(domain_name)
        return integrations_config.get(integration_name, {})
    
    def get_memory_config(self, domain_name: str = None) -> Dict[str, Any]:
        """
        Obtém a configuração de memória de um domínio.
        
        Args:
            domain_name: Nome do domínio (se None, usa o domínio ativo)
            
        Returns:
            Dict[str, Any]: Configuração de memória
        """
        domain_config = self.get_domain_config(domain_name)
        return domain_config.get("memory", {})
    
    def get_plugins_config(self, domain_name: str = None) -> Dict[str, Any]:
        """
        Obtém as configurações de plugins de um domínio.
        
        Args:
            domain_name: Nome do domínio (se None, usa o domínio ativo)
            
        Returns:
            Dict[str, Any]: Configurações de plugins
        """
        domain_config = self.get_domain_config(domain_name)
        return domain_config.get("plugins", {})
    
    def get_agent_tools(self, agent_name: str, domain_name: str = None) -> List[str]:
        """
        Obtém a lista de ferramentas configuradas para um agente específico.
        
        Args:
            agent_name: Nome do agente
            domain_name: Nome do domínio (se None, usa o domínio ativo)
            
        Returns:
            List[str]: Lista de nomes de ferramentas
        """
        agent_config = self.get_agent_config(agent_name, domain_name)
        return agent_config.get("tools", [])
    
    def load_class(self, class_path: str) -> Type:
        """
        Carrega dinamicamente uma classe a partir de seu caminho completo.
        
        Args:
            class_path: Caminho completo para a classe (ex: "src.tools.search.BasicSearchTool")
            
        Returns:
            Type: Classe carregada
            
        Raises:
            ImportError: Se a classe não puder ser carregada
        """
        if class_path in self._class_cache:
            return self._class_cache[class_path]
            
        try:
            # Divide o caminho em módulo e nome da classe
            module_path, class_name = class_path.rsplit(".", 1)
            
            # Importa o módulo
            module = importlib.import_module(module_path)
            
            # Obtém a classe do módulo
            class_obj = getattr(module, class_name)
            
            # Armazena em cache
            self._class_cache[class_path] = class_obj
            
            return class_obj
        except (ImportError, AttributeError) as e:
            logger.error(f"Erro ao carregar classe {class_path}: {str(e)}")
            raise ImportError(f"Não foi possível carregar a classe: {class_path}")
    
    def validate_domains(self) -> Dict[str, List[str]]:
        """
        Valida todos os domínios disponíveis.
        
        Returns:
            Dict[str, List[str]]: Dicionário de problemas por domínio
        """
        domain_names = self.loader.list_available_domains()
        validation_results = {}
        
        for domain_name in domain_names:
            problems = self.loader.validate_domain_structure(domain_name)
            if problems:
                validation_results[domain_name] = problems
        
        return validation_results
