"""
Gerenciador de domínios de negócio do ChatwootAI.
"""
import os
import logging
from typing import Dict, Any, Optional, List

from .domain_loader import DomainLoader

logger = logging.getLogger(__name__)


class DomainManager:
    """
    Gerenciador de domínios de negócio do ChatwootAI.
    
    Responsável por gerenciar o domínio ativo e fornecer acesso às configurações
    específicas de cada domínio de negócio.
    """
    
    def __init__(self, domains_dir: str = None, default_domain: str = "cosmetics"):
        """
        Inicializa o gerenciador de domínios.
        
        Args:
            domains_dir: Diretório contendo os arquivos YAML de domínios
            default_domain: Nome do domínio padrão
        """
        self.loader = DomainLoader(domains_dir)
        self.default_domain = default_domain
        self.active_domain_name = default_domain
        self.active_domain_config = None
    
    def initialize(self):
        """
        Inicializa o gerenciador carregando o domínio padrão.
        """
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
                logger.error("Nenhum domínio disponível encontrado")
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
    
    def list_domains(self) -> List[Dict[str, Any]]:
        """
        Lista todos os domínios disponíveis com informações básicas.
        
        Returns:
            List[Dict[str, Any]]: Lista de informações de domínios
        """
        domain_names = self.loader.list_available_domains()
        domains_info = []
        
        for domain_name in domain_names:
            domain_info = self.loader.get_domain_info(domain_name)
            domain_info["active"] = (domain_name == self.active_domain_name)
            domains_info.append(domain_info)
        
        return domains_info
    
    def get_business_rules(self, category: str = None, domain_name: str = None) -> Dict[str, Any]:
        """
        Obtém as regras de negócio de um domínio específico.
        
        Args:
            category: Categoria específica de regras (opcional)
            domain_name: Nome do domínio (se None, usa o domínio ativo)
            
        Returns:
            Dict[str, Any]: Regras de negócio do domínio
        """
        domain_config = self.get_domain_config(domain_name)
        
        if not domain_config or "domain_config" not in domain_config:
            return {}
        
        business_rules = domain_config.get("domain_config", {}).get("business_rules", {})
        
        if category and category in business_rules:
            return business_rules[category]
        
        return business_rules
    
    def get_agent_config(self, agent_type: str, agent_name: str = None, domain_name: str = None) -> Dict[str, Any]:
        """
        Obtém a configuração de um agente específico para um domínio.
        
        Args:
            agent_type: Tipo do agente (sales, support, scheduling)
            agent_name: Nome do agente (opcional)
            domain_name: Nome do domínio (se None, usa o domínio ativo)
            
        Returns:
            Dict[str, Any]: Configuração do agente
        """
        domain_config = self.get_domain_config(domain_name)
        
        if not domain_config or "agents" not in domain_config:
            return {}
        
        agents_config = domain_config.get("agents", {})
        
        if agent_type not in agents_config:
            return {}
        
        agent_type_config = agents_config[agent_type]
        
        if agent_name and agent_name in agent_type_config:
            return agent_type_config[agent_name]
        
        return agent_type_config
    
    def get_plugins(self, domain_name: str = None) -> List[str]:
        """
        Obtém a lista de plugins para um domínio específico.
        
        Args:
            domain_name: Nome do domínio (se None, usa o domínio ativo)
            
        Returns:
            List[str]: Lista de plugins do domínio
        """
        domain_config = self.get_domain_config(domain_name)
        
        if not domain_config or "plugins" not in domain_config:
            return []
        
        return domain_config.get("plugins", [])
