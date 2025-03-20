"""
Carregador de domínios de negócio do ChatwootAI.
"""
import os
import yaml
import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class DomainLoader:
    """
    Carregador de domínios de negócio do ChatwootAI.
    
    Responsável por carregar as configurações de domínios de negócio a partir de arquivos YAML.
    """
    
    def __init__(self, domains_dir: str = None):
        """
        Inicializa o carregador de domínios.
        
        Args:
            domains_dir: Diretório contendo os arquivos YAML de domínios
        """
        self.domains_dir = domains_dir or os.path.join("src", "business_domain")
        self.domains: Dict[str, Dict[str, Any]] = {}
    
    def load_domain(self, domain_name: str) -> Optional[Dict[str, Any]]:
        """
        Carrega um domínio de negócio específico.
        
        Args:
            domain_name: Nome do domínio a ser carregado
            
        Returns:
            Optional[Dict[str, Any]]: Configuração do domínio ou None se não encontrado
        """
        # Se o domínio já foi carregado, retorna a configuração em cache
        if domain_name in self.domains:
            return self.domains[domain_name]
        
        # Constrói o caminho para o arquivo YAML
        domain_file = os.path.join(self.domains_dir, f"{domain_name}.yaml")
        
        # Verifica se o arquivo existe
        if not os.path.exists(domain_file):
            logger.error(f"Arquivo de configuração do domínio não encontrado: {domain_file}")
            return None
        
        try:
            # Carrega o arquivo YAML
            with open(domain_file, "r", encoding="utf-8") as file:
                domain_config = yaml.safe_load(file)
            
            # Armazena a configuração em cache
            self.domains[domain_name] = domain_config
            
            logger.info(f"Domínio carregado com sucesso: {domain_name}")
            return domain_config
            
        except Exception as e:
            logger.error(f"Erro ao carregar o domínio {domain_name}: {str(e)}")
            return None
    
    def list_available_domains(self) -> List[str]:
        """
        Lista os domínios de negócio disponíveis.
        
        Returns:
            List[str]: Lista de nomes de domínios disponíveis
        """
        available_domains = []
        
        try:
            # Lista os arquivos no diretório de domínios
            for file_name in os.listdir(self.domains_dir):
                # Verifica se é um arquivo YAML
                if file_name.endswith(".yaml"):
                    # Extrai o nome do domínio (sem a extensão .yaml)
                    domain_name = file_name[:-5]
                    available_domains.append(domain_name)
        except Exception as e:
            logger.error(f"Erro ao listar domínios disponíveis: {str(e)}")
        
        return available_domains
    
    def get_domain_info(self, domain_name: str) -> Dict[str, Any]:
        """
        Obtém informações básicas sobre um domínio sem carregar a configuração completa.
        
        Args:
            domain_name: Nome do domínio
            
        Returns:
            Dict[str, Any]: Informações básicas do domínio
        """
        domain_config = self.load_domain(domain_name)
        
        if not domain_config:
            return {
                "name": domain_name,
                "description": "Configuração não encontrada",
                "available": False
            }
        
        return {
            "name": domain_config.get("name", domain_name),
            "description": domain_config.get("description", ""),
            "available": True
        }
    
    def reload_domain(self, domain_name: str) -> Optional[Dict[str, Any]]:
        """
        Recarrega a configuração de um domínio, ignorando o cache.
        
        Args:
            domain_name: Nome do domínio a ser recarregado
            
        Returns:
            Optional[Dict[str, Any]]: Configuração atualizada do domínio
        """
        # Remove o domínio do cache
        if domain_name in self.domains:
            del self.domains[domain_name]
        
        # Carrega novamente
        return self.load_domain(domain_name)
