"""
Gerenciador de domínios de negócio do ChatwootAI.

Este módulo implementa o gerenciamento de domínios de negócio,
permitindo a troca dinâmica entre domínios e o acesso às suas configurações.
Suporta multi-tenancy através de persistência em Redis.
"""
import os
import logging
from typing import Dict, Any, Optional, List, Type, Set, Tuple
import importlib
import json
import yaml

from .domain_loader import DomainLoader, DomainMetadata, ConfigurationError
from .domain_registry import get_domain_registry
from src.utils.redis_client import get_redis_client, RedisCache

logger = logging.getLogger(__name__)


class DomainManager:
    """
    Gerenciador de domínios de negócio do ChatwootAI.

    Responsável por gerenciar o domínio ativo e fornecer acesso às configurações
    específicas de cada domínio de negócio, usando a nova estrutura de configuração YAML.
    Suporta multi-tenancy através de persistência em Redis para associação de conversas
    a domínios específicos.
    """

    def __init__(self, domains_dir: str = None, default_domain: str = "cosmetics", redis_client=None):
        """
        Inicializa o gerenciador de domínios.

        Args:
            domains_dir: Diretório contendo os diretórios de domínios
            default_domain: Nome do domínio padrão
            redis_client: Cliente Redis opcional para persistência
        """
        self.loader = DomainLoader(domains_dir)
        self.domains_dir = domains_dir  # Adicionar o atributo domains_dir
        self.default_domain = default_domain
        self.active_domain_name = default_domain
        self.active_domain_config = None
        self._class_cache = {}  # Cache para classes carregadas dinamicamente

        # Inicializar cliente Redis para persistência
        self.redis_client = redis_client or get_redis_client()
        self.redis_cache = RedisCache(self.redis_client) if self.redis_client else None

        # Inicializar registro de domínios para cache eficiente
        self.domain_registry = get_domain_registry()

        # Compatibilidade com a versão anterior para testes
        self.domain_loader = self.loader
        self.domains_cache = {}
        self.active_domain = "default"  # Para compatibilidade com testes antigos

    def initialize(self):
        """
        Inicializa o gerenciador carregando o domínio padrão.

        Raises:
            ConfigurationError: Se nenhum domínio puder ser carregado
        """
        logger.info(f"Inicializando DomainManager com domínio padrão: {self.default_domain}")

        # Usar o domain_registry para obter a configuração
        self.active_domain_config = self.domain_registry.get_domain_config(self.default_domain)

        if not self.active_domain_config:
            logger.warning(f"Domínio padrão não encontrado: {self.default_domain}")
            # Tenta carregar qualquer domínio disponível
            available_domains = self.loader.list_available_domains()
            if available_domains:
                self.active_domain_name = available_domains[0]
                self.active_domain_config = self.domain_registry.get_domain_config(self.active_domain_name)
                logger.info(f"Usando domínio alternativo: {self.active_domain_name}")
            else:
                error_msg = "Nenhum domínio disponível encontrado"
                logger.error(error_msg)
                raise ConfigurationError(error_msg)
        else:
            logger.info(f"Domínio padrão carregado: {self.default_domain}")

    def get_active_domain(self) -> str:
        """
        Obtém o nome do domínio ativo (para compatibilidade com testes antigos).

        Returns:
            str: Nome do domínio ativo
        """
        return self.active_domain

    def get_domain_by_account_id(self, account_id: str) -> Optional[str]:
        """
        Determina o domínio com base no account_id do Chatwoot.

        Args:
            account_id: ID da conta do Chatwoot

        Returns:
            Optional[str]: Nome do domínio ou None se não encontrado
        """
        if not account_id:
            logger.warning("Account ID não fornecido para determinação de domínio")
            return None

        # Converter para string para garantir compatibilidade
        account_id = str(account_id)

        # Tentar obter do registro de domínios
        account_domain_mapping = self.domain_registry.get_account_domain_mapping()

        if account_id in account_domain_mapping:
            mapping = account_domain_mapping[account_id]
            domain_name = mapping.get('domain')
            logger.info(f"Domínio determinado para account_id {account_id}: {domain_name}")
            return domain_name

        logger.warning(f"Nenhum domínio encontrado para account_id: {account_id}")
        return None

    def get_internal_account_id(self, chatwoot_account_id: str) -> Optional[str]:
        """
        Obtém o account_id interno com base no account_id do Chatwoot.

        Args:
            chatwoot_account_id: ID da conta do Chatwoot

        Returns:
            Optional[str]: ID interno da conta ou None se não encontrado
        """
        if not chatwoot_account_id:
            logger.warning("Account ID do Chatwoot não fornecido para determinação do account_id interno")
            return None

        # Converter para string para garantir compatibilidade
        chatwoot_account_id = str(chatwoot_account_id)

        # Tentar obter do registro de domínios
        account_domain_mapping = self.domain_registry.get_account_domain_mapping()

        if chatwoot_account_id in account_domain_mapping:
            mapping = account_domain_mapping[chatwoot_account_id]
            internal_account_id = mapping.get('account_id')
            if internal_account_id:
                logger.info(f"Account ID interno determinado para Chatwoot account_id {chatwoot_account_id}: {internal_account_id}")
                return internal_account_id
            else:
                logger.warning(f"Mapeamento encontrado para account_id {chatwoot_account_id}, mas sem account_id interno definido")

        logger.warning(f"Nenhum account_id interno encontrado para Chatwoot account_id: {chatwoot_account_id}")
        return None

    def get_active_domain_config_internal(self) -> Dict[str, Any]:
        """
        Obtém a configuração do domínio ativo (método interno).

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
        # Usar o domain_registry para obter a configuração
        domain_config = self.domain_registry.get_domain_config(domain_name)

        if not domain_config:
            logger.error(f"Não foi possível carregar o domínio: {domain_name}")
            return False

        self.active_domain_name = domain_name
        self.active_domain_config = domain_config
        logger.info(f"Domínio ativo alterado para: {domain_name}")

        return True

    def set_active_domain(self, domain_name: str) -> None:
        """
        Define o domínio ativo (método de compatibilidade).

        Args:
            domain_name: Nome do novo domínio ativo

        Raises:
            ConfigurationError: Se o domínio não existir
        """
        # Carregar o domínio para verificar se existe
        domain_config = self.domain_loader.load_domain(domain_name)

        if not domain_config:
            error_msg = f"Domínio '{domain_name}' não encontrado"
            logger.error(error_msg)
            raise ConfigurationError(error_msg)

        # Armazenar no cache para compatibilidade com testes antigos
        self.domains_cache[domain_name] = domain_config

        # Atualizar o domínio ativo
        self.active_domain_name = domain_name
        self.active_domain_config = domain_config
        self.active_domain = domain_name  # Para compatibilidade com testes antigos
        logger.info(f"Domínio ativo definido para: {domain_name}")

    def get_domain_config(self, domain_name: str = None, account_id: str = None) -> Dict[str, Any]:
        """
        Obtém a configuração de um domínio específico.

        Na nova arquitetura, o account_id é o identificador principal, e o domínio é apenas
        uma organização de pastas. Se account_id for fornecido, tentamos carregar a configuração
        específica para esse account_id.

        Args:
            domain_name: Nome do domínio (se None, usa o domínio ativo)
            account_id: ID da conta (se fornecido, carrega a configuração específica)

        Returns:
            Dict[str, Any]: Configuração do domínio

        Raises:
            ConfigurationError: Se o domínio não existir (para compatibilidade com testes antigos)
        """
        if domain_name is None:
            return self.get_active_domain_config()

        # Chave de cache que inclui o account_id se fornecido
        cache_key = f"{domain_name}:{account_id}" if account_id else domain_name

        # Verificar o cache
        if cache_key in self.domains_cache:
            return self.domains_cache[cache_key]

        # Se temos um account_id, tentar carregar a configuração específica
        if account_id:
            # Construir o caminho para o arquivo de configuração da conta
            account_file = os.path.join(self.domains_dir, domain_name, f"{account_id}.yaml")

            if os.path.exists(account_file):
                try:
                    # Carregar a configuração da conta
                    with open(account_file, "r", encoding="utf-8") as file:
                        account_config = yaml.safe_load(file) or {}

                    # Armazenar no cache
                    self.domains_cache[cache_key] = account_config
                    return account_config
                except Exception as e:
                    logger.error(f"Erro ao carregar configuração da conta {account_id}: {str(e)}")

        # Se não temos account_id ou não conseguimos carregar a configuração específica,
        # tentar carregar a configuração geral do domínio
        domain_config = self.domain_loader.load_domain(domain_name)
        if domain_config:
            self.domains_cache[domain_name] = domain_config
            return domain_config

        # Usar o domain_registry como fallback
        config = self.domain_registry.get_domain_config(domain_name)
        if not config:
            # Para compatibilidade com testes antigos, lançar erro se o domínio não existir
            error_msg = f"Domínio '{domain_name}' não encontrado"
            logger.error(error_msg)
            raise ConfigurationError(error_msg)

        return config or {}

    def list_domains(self) -> List[DomainMetadata]:
        """
        Lista todos os domínios disponíveis com informações básicas.

        Returns:
            List[DomainMetadata]: Lista de metadados de domínios
        """
        # Usar o domain_registry para listar domínios
        domain_names = self.domain_registry.list_domains()
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

    def get_active_domain_config(self) -> Dict[str, Any]:
        """
        Obtém a configuração do domínio ativo (método de compatibilidade).

        Returns:
            Dict[str, Any]: Configuração do domínio ativo
        """
        # Verificar o cache para compatibilidade com testes antigos
        if self.active_domain in self.domains_cache:
            return self.domains_cache[self.active_domain]

        # Se não estiver em cache, carregar do loader
        domain_config = self.domain_loader.load_domain(self.active_domain)
        if domain_config:
            self.domains_cache[self.active_domain] = domain_config
            return domain_config

        # Usar o domínio padrão como fallback
        return self.get_active_domain_config_internal()

    def get_setting(self, domain_name: str, setting_path: str, default: Any = None) -> Any:
        """
        Obtém uma configuração específica de um domínio usando uma notação de caminho.

        Args:
            domain_name: Nome do domínio
            setting_path: Caminho da configuração (ex: "settings.product_categories")
            default: Valor padrão a ser retornado se a configuração não existir

        Returns:
            Any: Valor da configuração ou o valor padrão

        Raises:
            ConfigurationError: Se o caminho da configuração não existir e nenhum valor padrão for fornecido
        """
        # Obter a configuração do domínio
        if domain_name in self.domains_cache:
            domain_config = self.domains_cache[domain_name]
        else:
            error_msg = f"Domínio '{domain_name}' não encontrado"
            logger.error(error_msg)
            raise ConfigurationError(error_msg)

        # Navegar pelo caminho da configuração
        parts = setting_path.split('.')
        current = domain_config

        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                if default is not None:
                    return default
                error_msg = f"Configuração '{setting_path}' não encontrada no domínio"
                logger.error(error_msg)
                raise ConfigurationError(error_msg)

        return current

    def get_active_domain_setting(self, setting_path: str, default: Any = None) -> Any:
        """
        Obtém uma configuração específica do domínio ativo.

        Args:
            setting_path: Caminho da configuração (ex: "settings.product_categories")
            default: Valor padrão a ser retornado se a configuração não existir

        Returns:
            Any: Valor da configuração ou o valor padrão

        Raises:
            ConfigurationError: Se o caminho da configuração não existir e nenhum valor padrão for fornecido
        """
        return self.get_setting(self.active_domain, setting_path, default)

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

    # Métodos para suporte a multi-tenancy

    def set_conversation_domain(self, conversation_id: str, domain_name: str, account_id: str = None) -> bool:
        """
        Associa uma conversa a um domínio específico.

        Args:
            conversation_id: ID da conversa
            domain_name: Nome do domínio
            account_id: ID da conta (anteriormente client_id)

        Returns:
            bool: True se a associação foi bem-sucedida, False caso contrário
        """
        if not self.redis_cache:
            logger.warning("Redis não disponível para persistência de domínio")
            return False

        # Verificar se o domínio existe
        if not self.domain_registry.domain_exists(domain_name):
            logger.error(f"Domínio não encontrado: {domain_name}")
            return False

        # Dados a serem armazenados
        data = {
            "domain": domain_name,
            "timestamp": self.redis_cache.get_current_timestamp()
        }

        if account_id:
            data["account_id"] = account_id

        # Armazenar a associação no Redis
        key = f"conversation:domain:{conversation_id}"
        try:
            self.redis_client.set(key, json.dumps(data))
            # Definir TTL (30 dias)
            self.redis_client.expire(key, 60 * 60 * 24 * 30)
            logger.info(f"Conversa {conversation_id} associada ao domínio {domain_name}")
            return True
        except Exception as e:
            logger.error(f"Erro ao associar conversa a domínio: {str(e)}")
            return False

    def get_conversation_domain(self, conversation_id: str) -> Tuple[str, Optional[str]]:
        """
        Obtém o domínio associado a uma conversa.

        Args:
            conversation_id: ID da conversa

        Returns:
            Tuple[str, Optional[str]]: (nome do domínio, ID da conta) ou (domínio padrão, None)
        """
        if not self.redis_cache:
            logger.warning("Redis não disponível para recuperar domínio")
            return self.default_domain, None

        # Recuperar a associação do Redis
        key = f"conversation:domain:{conversation_id}"
        try:
            data_str = self.redis_client.get(key)
            if data_str:
                data = json.loads(data_str)
                domain_name = data.get("domain", self.default_domain)
                account_id = data.get("account_id") or data.get("client_id")  # Compatibilidade com dados antigos
                logger.debug(f"Conversa {conversation_id} associada ao domínio {domain_name}")
                return domain_name, account_id
        except Exception as e:
            logger.error(f"Erro ao recuperar domínio da conversa: {str(e)}")

        # Caso não encontre ou ocorra erro, retorna o domínio padrão
        return self.default_domain, None

    def get_account_domain(self, account_id: str) -> str:
        """
        Obtém o domínio padrão associado a uma conta.

        Args:
            account_id: ID da conta (anteriormente client_id)

        Returns:
            str: Nome do domínio padrão da conta ou domínio padrão global
        """
        if not self.redis_cache:
            logger.warning("Redis não disponível para recuperar domínio da conta")
            return self.default_domain

        # Recuperar a associação do Redis usando o novo formato
        key = f"account:domain:{account_id}"
        try:
            domain_name = self.redis_client.get(key)
            if domain_name:
                return domain_name.decode('utf-8')

            # Se não encontrar, tenta o formato antigo para compatibilidade
            legacy_key = f"client:domain:{account_id}"
            domain_name = self.redis_client.get(legacy_key)
            if domain_name:
                logger.info(f"Usando chave legada para compatibilidade: {legacy_key}")
                # Migra para o novo formato
                self.redis_client.set(key, domain_name)
                self.redis_client.expire(key, 60 * 60 * 24 * 90)  # 90 dias
                return domain_name.decode('utf-8')
        except Exception as e:
            logger.error(f"Erro ao recuperar domínio da conta: {str(e)}")

        # Caso não encontre ou ocorra erro, retorna o domínio padrão
        return self.default_domain

    def set_account_domain(self, account_id: str, domain_name: str) -> bool:
        """
        Define o domínio padrão para uma conta.

        Args:
            account_id: ID da conta (anteriormente client_id)
            domain_name: Nome do domínio

        Returns:
            bool: True se a associação foi bem-sucedida, False caso contrário
        """
        if not self.redis_cache:
            logger.warning("Redis não disponível para persistência de domínio")
            return False

        # Verificar se o domínio existe
        if not self.domain_registry.domain_exists(domain_name):
            logger.error(f"Domínio não encontrado: {domain_name}")
            return False

        # Armazenar a associação no Redis
        key = f"account:domain:{account_id}"
        try:
            self.redis_client.set(key, domain_name)
            # Definir TTL (90 dias)
            self.redis_client.expire(key, 60 * 60 * 24 * 90)

            # Para compatibilidade com sistemas legados, manter a chave antiga por um período
            legacy_key = f"client:domain:{account_id}"
            self.redis_client.set(legacy_key, domain_name)
            # TTL menor para a chave legada (30 dias)
            self.redis_client.expire(legacy_key, 60 * 60 * 24 * 30)

            logger.info(f"Conta {account_id} associada ao domínio {domain_name}")
            return True
        except Exception as e:
            logger.error(f"Erro ao associar conta a domínio: {str(e)}")
            return False

    def get_chatwoot_account_id(self, chatwoot_account_id: str) -> Optional[str]:
        """
        Obtém o ID da conta interna associada a uma conta do Chatwoot.

        Args:
            chatwoot_account_id: ID da conta no Chatwoot

        Returns:
            Optional[str]: ID da conta interna ou None se não encontrado
        """
        if not self.redis_cache:
            logger.warning("Redis não disponível para recuperar conta")
            return None

        # Recuperar a associação do Redis usando o novo formato
        key = f"account:chatwoot:{chatwoot_account_id}"
        try:
            account_id = self.redis_client.get(key)
            if account_id:
                return account_id.decode('utf-8')

            # Se não encontrar, tenta o formato antigo para compatibilidade
            legacy_key = f"client:chatwoot:{chatwoot_account_id}"
            account_id = self.redis_client.get(legacy_key)
            if account_id:
                logger.info(f"Usando chave legada para compatibilidade: {legacy_key}")
                # Migra para o novo formato
                self.redis_client.set(key, account_id)
                self.redis_client.expire(key, 60 * 60 * 24 * 90)  # 90 dias
                return account_id.decode('utf-8')
        except Exception as e:
            logger.error(f"Erro ao recuperar conta por ID Chatwoot: {str(e)}")

        return None

    def set_chatwoot_account_id(self, chatwoot_account_id: str, account_id: str) -> bool:
        """
        Associa uma conta do Chatwoot a uma conta interna.

        Args:
            chatwoot_account_id: ID da conta no Chatwoot
            account_id: ID da conta interna (anteriormente client_id)

        Returns:
            bool: True se a associação foi bem-sucedida, False caso contrário
        """
        if not self.redis_cache:
            logger.warning("Redis não disponível para persistência de conta")
            return False

        # Armazenar a associação no Redis usando o novo formato
        key = f"account:chatwoot:{chatwoot_account_id}"
        try:
            self.redis_client.set(key, account_id)
            # Definir TTL (365 dias)
            self.redis_client.expire(key, 60 * 60 * 24 * 365)

            # Para compatibilidade com sistemas legados, manter a chave antiga por um período
            legacy_key = f"client:chatwoot:{chatwoot_account_id}"
            self.redis_client.set(legacy_key, account_id)
            # TTL menor para a chave legada (90 dias)
            self.redis_client.expire(legacy_key, 60 * 60 * 24 * 90)
            logger.info(f"Conta Chatwoot {chatwoot_account_id} associada à conta interna {account_id}")
            return True
        except Exception as e:
            logger.error(f"Erro ao associar conta Chatwoot à conta interna: {str(e)}")
            return False

    def get_domain_for_chatwoot_conversation(self, chatwoot_account_id: str, conversation_id: str) -> str:
        """
        Determina o domínio para uma conversa do Chatwoot.
        Este é um método de conveniência que combina várias consultas para determinar
        o domínio correto para uma conversa, seguindo a lógica de prioridade:
        1. Domínio específico da conversa
        2. Domínio padrão do cliente
        3. Domínio padrão global

        Args:
            chatwoot_account_id: ID da conta no Chatwoot
            conversation_id: ID da conversa

        Returns:
            str: Nome do domínio a ser usado
        """
        # Verificar se a conversa já tem um domínio associado
        domain_name, _ = self.get_conversation_domain(conversation_id)
        if domain_name != self.default_domain:
            return domain_name

        # Se não, verificar o domínio padrão da conta
        account_id = self.get_chatwoot_account_id(chatwoot_account_id)
        if account_id:
            domain_name = self.get_account_domain(account_id)
            # Associar a conversa a este domínio para futuras consultas
            self.set_conversation_domain(conversation_id, domain_name, account_id)
            return domain_name

        # Se não encontrou conta ou domínio, usar o padrão
        return self.default_domain

    def get_domain_for_channel(self, channel_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Determina o domínio e account_id para um canal de comunicação.

        Este método é usado pelo hub.py para determinar o domínio e account_id
        corretos para uma mensagem recebida de um canal específico.

        Args:
            channel_info: Informações do canal (channel_type, sender_id, recipient_id)

        Returns:
            Dict[str, Any]: Informações do domínio e account_id
        """
        # Extrair informações do canal
        channel_type = channel_info.get("channel_type", "unknown")
        sender_id = channel_info.get("sender_id")
        recipient_id = channel_info.get("recipient_id")

        # Verificar se temos informações suficientes
        if not channel_type or not sender_id:
            logger.warning("Informações insuficientes para determinar domínio e account_id")
            return {
                "domain_name": self.default_domain,
                "account_id": None
            }

        # Verificar se temos um mapeamento para este canal no Redis
        if self.redis_cache:
            try:
                # Tentar obter o mapeamento do Redis
                key = f"channel:{channel_type}:{sender_id}"
                mapping = self.redis_client.get(key)
                if mapping:
                    mapping_data = json.loads(mapping.decode('utf-8'))
                    logger.info(f"Mapeamento encontrado para canal {channel_type}:{sender_id}")
                    return mapping_data
            except Exception as e:
                logger.error(f"Erro ao recuperar mapeamento de canal: {str(e)}")

        # Se não encontrou no Redis, verificar no sistema de arquivos
        # Aqui você pode implementar a lógica para mapear canais para domínios/accounts
        # Por exemplo, verificar um arquivo de mapeamento YAML

        # Por enquanto, retornar o domínio padrão
        return {
            "domain_name": self.default_domain,
            "account_id": None
        }
