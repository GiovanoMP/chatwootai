"""
Carregador de domínios de negócio do ChatwootAI.

Este módulo implementa o sistema de carregamento de configurações YAML para domínios
de negócio, suportando herança, composição e validação de configurações.
"""
import os
import yaml
import logging
import json
from typing import Dict, Any, Optional, List, Set
from pathlib import Path
import copy
from pydantic import BaseModel, ValidationError, Field
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Constantes
BASE_DOMAIN = "_base"
CONFIG_FILE = "config.yaml"
BASE_AGENTS_FILE = "base_agents.yaml"
BASE_TOOLS_FILE = "base_tools.yaml"


class ConfigurationError(Exception):
    """Exceção lançada quando há problemas com a configuração de domínios."""
    pass


@dataclass
class DomainMetadata:
    """Metadados de um domínio carregado."""
    name: str
    path: str
    version: str
    description: str
    inherit: Optional[str] = None
    available: bool = True


class DomainConfig(BaseModel):
    """Modelo para validação da configuração de um domínio."""
    version: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    agents: Dict[str, Any] = Field(default_factory=dict)
    tools: Dict[str, Any] = Field(default_factory=dict)
    crew: Dict[str, Any] = Field(default_factory=dict)
    integrations: Dict[str, Any] = Field(default_factory=dict)
    memory: Dict[str, Any] = Field(default_factory=dict)
    plugins: Dict[str, Any] = Field(default_factory=dict)


class DomainLoader:
    """
    Carregador de domínios de negócio do ChatwootAI.
    
    Responsável por carregar configurações de domínios a partir da nova estrutura YAML,
    suportando herança entre domínios e composição de múltiplos arquivos.
    """
    
    def __init__(self, domains_dir: str = None):
        """
        Inicializa o carregador de domínios.
        
        Args:
            domains_dir: Diretório raiz contendo as pastas de domínios
        """
        self.domains_dir = domains_dir or os.path.join("config", "domains")
        self.domains_cache: Dict[str, Dict[str, Any]] = {}
        self.base_configs: Dict[str, Dict[str, Any]] = {}
        self.base_domain_name = BASE_DOMAIN  # Adicionado para compatibilidade com testes
        
        # Valida a existência do diretório de domínios
        if not os.path.exists(self.domains_dir):
            logger.warning(f"Diretório de domínios não encontrado: {self.domains_dir}")
            Path(self.domains_dir).mkdir(parents=True, exist_ok=True)
            logger.info(f"Diretório de domínios criado: {self.domains_dir}")
    
    def _load_yaml_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Carrega um arquivo YAML.
        
        Args:
            file_path: Caminho para o arquivo YAML
            
        Returns:
            Optional[Dict[str, Any]]: Conteúdo do arquivo ou None se houve erro
        """
        try:
            if not os.path.exists(file_path):
                logger.debug(f"Arquivo não encontrado: {file_path}")
                return None
                
            with open(file_path, "r", encoding="utf-8") as file:
                config = yaml.safe_load(file)
                return config or {}
                
        except Exception as e:
            logger.error(f"Erro ao carregar arquivo {file_path}: {str(e)}")
            return None
    
    def _merge_configs(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """
        Mescla duas configurações, com override tendo precedência.
        
        Esta função implementa uma mesclagem profunda (deep merge) de dicionários,
        permitindo que configurações específicas de domínio sobreponham apenas 
        partes selecionadas das configurações base.
        
        Args:
            base: Configuração base
            override: Configuração que sobrescreve a base
            
        Returns:
            Dict[str, Any]: Configuração mesclada
        """
        if not base:
            return copy.deepcopy(override or {})
            
        if not override:
            return copy.deepcopy(base or {})
        
        # Cria uma cópia profunda da configuração base
        result = copy.deepcopy(base)
        
        # Percorre todos os itens da configuração de sobrescrita
        for key, value in override.items():
            # Se o valor for um dicionário e a chave já existir na base
            if isinstance(value, dict) and key in result and isinstance(result[key], dict):
                # Mescla recursivamente
                result[key] = self._merge_configs(result[key], value)
            else:
                # Substitui completamente
                result[key] = copy.deepcopy(value)
        
        return result
    
    def _load_base_configs(self) -> None:
        """
        Carrega as configurações base (_base) para uso em herança.
        
        Este método carrega os arquivos de configuração do diretório _base,
        que servem como padrões que podem ser herdados por domínios específicos.
        """
        if self.base_configs:  # Já carregou anteriormente
            return
            
        base_dir = os.path.join(self.domains_dir, BASE_DOMAIN)
        
        if not os.path.exists(base_dir) or not os.path.isdir(base_dir):
            logger.warning(f"Diretório de configurações base não encontrado: {base_dir}")
            return
        
        # Carrega os arquivos de configuração base
        agents_file = os.path.join(base_dir, BASE_AGENTS_FILE)
        tools_file = os.path.join(base_dir, BASE_TOOLS_FILE)
        
        self.base_configs["agents"] = self._load_yaml_file(agents_file) or {}
        self.base_configs["tools"] = self._load_yaml_file(tools_file) or {}
        
        logger.debug(f"Configurações base carregadas: {list(self.base_configs.keys())}")
    
    def list_available_domains(self) -> List[str]:
        """
        Lista os domínios de negócio disponíveis.
        
        Returns:
            List[str]: Lista de nomes de domínios disponíveis
        """
        available_domains = []
        
        try:
            # Lista os diretórios no diretório de domínios
            for item in os.listdir(self.domains_dir):
                domain_dir = os.path.join(self.domains_dir, item)
                
                # Verifica se é um diretório e não é o diretório base
                if os.path.isdir(domain_dir) and item != BASE_DOMAIN:
                    # Verifica se existe o arquivo config.yaml
                    config_file = os.path.join(domain_dir, CONFIG_FILE)
                    if os.path.exists(config_file):
                        available_domains.append(item)
        except Exception as e:
            logger.error(f"Erro ao listar domínios disponíveis: {str(e)}")
        
        return available_domains
    
    def load_domain(self, domain_name: str, force_reload: bool = False) -> Optional[Dict[str, Any]]:
        """
        Carrega um domínio de negócio completo, incluindo arquivos de configuração base.
        
        Args:
            domain_name: Nome do domínio a ser carregado
            force_reload: Se True, ignora o cache e força o recarregamento
            
        Returns:
            Optional[Dict[str, Any]]: Configuração completa do domínio ou None se não encontrado
        """
        # Se o domínio já foi carregado e não é forçado o recarregamento, retorna do cache
        if domain_name in self.domains_cache and not force_reload:
            return self.domains_cache[domain_name]
        
        # Carrega as configurações base
        self._load_base_configs()
        
        # Constrói o caminho para o diretório do domínio
        domain_dir = os.path.join(self.domains_dir, domain_name)
        config_file = os.path.join(domain_dir, CONFIG_FILE)
        
        # Verifica se o diretório e o arquivo existem
        if not os.path.exists(domain_dir) or not os.path.isdir(domain_dir):
            logger.error(f"Diretório do domínio não encontrado: {domain_dir}")
            return None
            
        if not os.path.exists(config_file):
            logger.error(f"Arquivo de configuração do domínio não encontrado: {config_file}")
            return None
        
        try:
            # Carrega o arquivo de configuração principal
            domain_config = self._load_yaml_file(config_file)
            
            if not domain_config:
                logger.error(f"Configuração do domínio vazia ou inválida: {domain_name}")
                return None
            
            # Verifica se há herança de outro domínio
            inherit_from = domain_config.get("metadata", {}).get("inherit")
            
            if inherit_from:
                # Carrega o domínio base
                base_domain_config = self.load_domain(inherit_from) if inherit_from != BASE_DOMAIN else {}
                
                if inherit_from != BASE_DOMAIN and not base_domain_config:
                    logger.warning(f"Domínio base '{inherit_from}' não encontrado para '{domain_name}'")
                
                # Mescla com as configurações base
                domain_config = self._merge_configs(base_domain_config, domain_config)
            
            # Mescla com configurações base globais
            if self.base_configs:
                # Mescla agentes base se não houver definição no domínio
                if "agents" not in domain_config and "agents" in self.base_configs:
                    domain_config["agents"] = copy.deepcopy(self.base_configs["agents"].get("agents", {}))
                
                # Mescla ferramentas base se não houver definição no domínio
                if "tools" not in domain_config and "tools" in self.base_configs:
                    domain_config["tools"] = copy.deepcopy(self.base_configs["tools"].get("tools", {}))
            
            # Valida a configuração
            try:
                DomainConfig(**domain_config)
            except ValidationError as e:
                logger.error(f"Configuração do domínio '{domain_name}' inválida: {str(e)}")
                logger.debug(f"Detalhes da validação: {json.dumps(domain_config, indent=2)}")
                return None
            
            # Adiciona metadados importantes
            if "metadata" not in domain_config:
                domain_config["metadata"] = {}
                
            domain_config["metadata"]["name"] = domain_name
            domain_config["metadata"]["path"] = domain_dir
            
            # Armazena a configuração em cache
            self.domains_cache[domain_name] = domain_config
            
            logger.info(f"Domínio carregado com sucesso: {domain_name}")
            return domain_config
            
        except Exception as e:
            logger.error(f"Erro ao carregar o domínio {domain_name}: {str(e)}")
            import traceback
            logger.debug(f"Traceback: {traceback.format_exc()}")
            return None
    
    def get_domain_info(self, domain_name: str) -> DomainMetadata:
        """
        Obtém metadados sobre um domínio sem carregar a configuração completa.
        
        Args:
            domain_name: Nome do domínio
            
        Returns:
            DomainMetadata: Metadados do domínio
        """
        # Verifica se o domínio está em cache
        if domain_name in self.domains_cache:
            config = self.domains_cache[domain_name]
            metadata = config.get("metadata", {})
            
            return DomainMetadata(
                name=domain_name,
                path=metadata.get("path", ""),
                version=config.get("version", "unknown"),
                description=metadata.get("description", ""),
                inherit=metadata.get("inherit"),
                available=True
            )
        
        # Carrega apenas o arquivo de configuração principal
        domain_dir = os.path.join(self.domains_dir, domain_name)
        config_file = os.path.join(domain_dir, CONFIG_FILE)
        
        if not os.path.exists(config_file):
            return DomainMetadata(
                name=domain_name,
                path=domain_dir,
                version="unknown",
                description="Configuração não encontrada",
                available=False
            )
        
        config = self._load_yaml_file(config_file) or {}
        metadata = config.get("metadata", {})
        
        return DomainMetadata(
            name=domain_name,
            path=domain_dir,
            version=config.get("version", "unknown"),
            description=metadata.get("description", ""),
            inherit=metadata.get("inherit"),
            available=True
        )
    
    def reload_domain(self, domain_name: str) -> Optional[Dict[str, Any]]:
        """
        Recarrega a configuração de um domínio, ignorando o cache.
        
        Args:
            domain_name: Nome do domínio a ser recarregado
            
        Returns:
            Optional[Dict[str, Any]]: Configuração atualizada do domínio
        """
        return self.load_domain(domain_name, force_reload=True)
    
    def validate_domain_structure(self, domain_name: str) -> List[str]:
        """
        Valida a estrutura de arquivos de um domínio.
        
        Args:
            domain_name: Nome do domínio a ser validado
            
        Returns:
            List[str]: Lista de problemas encontrados (vazia se não houver problemas)
        """
        problems = []
        domain_dir = os.path.join(self.domains_dir, domain_name)
        
        # Verifica se o diretório existe
        if not os.path.exists(domain_dir):
            problems.append(f"Diretório do domínio não encontrado: {domain_dir}")
            return problems
            
        # Verifica se config.yaml existe
        config_file = os.path.join(domain_dir, CONFIG_FILE)
        if not os.path.exists(config_file):
            problems.append(f"Arquivo config.yaml não encontrado em {domain_dir}")
        else:
            # Valida o conteúdo do config.yaml
            config = self._load_yaml_file(config_file)
            if not config:
                problems.append(f"Arquivo config.yaml vazio ou inválido em {domain_dir}")
            else:
                # Verifica a versão
                if "version" not in config:
                    problems.append(f"Campo 'version' não encontrado em config.yaml de {domain_name}")
                
                # Verifica metadados
                if "metadata" not in config:
                    problems.append(f"Campo 'metadata' não encontrado em config.yaml de {domain_name}")
                elif "description" not in config["metadata"]:
                    problems.append(f"Campo 'description' não encontrado em metadata de {domain_name}")
        
        return problems

    def load_domain_configuration(self, domain_name: str) -> Dict[str, Any]:
        """
        Carrega a configuração de um domínio específico.
        """
        domain_path = os.path.join(self.domains_dir, domain_name, "config.yaml")
        return self._load_yaml_file(domain_path)

    def validate_configuration(self, config: Dict[str, Any]) -> bool:
        """
        Valida uma configuração de domínio.
        """
        required_keys = {"name", "version", "settings"}
        return all(key in config for key in required_keys)
