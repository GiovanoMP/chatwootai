#!/usr/bin/env python3
"""
Fábrica de Crews para o ChatwootAI

Este módulo implementa o CrewFactory, responsável por criar instâncias de crews
e agentes a partir de configurações YAML, garantindo a correta inicialização
de todos os componentes necessários.
"""

import logging
from typing import Dict, Any, List, Optional, Type, Union

from crewai import Agent, Crew, Task
from src.core.domain.domain_manager import DomainManager
from src.core.domain.domain_registry import get_domain_registry
from src.core.domain.domain_loader import ConfigurationError
from src.core.crews.generic_crew import GenericCrew

# Configurar logging
logger = logging.getLogger(__name__)

class CrewFactory:
    """
    Fábrica para criar crews e agentes a partir de configurações YAML.

    Responsável por instanciar dinamicamente crews e agentes com base nas
    configurações de domínio, garantindo que todos os componentes necessários
    sejam corretamente inicializados.
    """

    def __init__(self, data_proxy_agent=None, memory_system=None, tool_registry=None, domain_manager=None):
        """
        Inicializa a fábrica de crews.

        Args:
            data_proxy_agent: Instância do DataProxyAgent para acesso a dados
            memory_system: Sistema de memória para persistência
            tool_registry: Registro de ferramentas disponíveis
            domain_manager: Gerenciador de domínios para multi-tenancy
        """
        self.data_proxy_agent = data_proxy_agent
        self.memory_system = memory_system
        self.tool_registry = tool_registry
        self.domain_manager = domain_manager

        # Cache de crews para evitar recriação desnecessária
        self.crew_cache = {}

        # Mapeamento de tipos de agentes para classes concretas
        self.agent_types = {}

        # Mapeamento de tipos de crews para classes concretas
        self.crew_types = {}

        logger.info("CrewFactory inicializado")

    def register_agent_type(self, type_name: str, agent_class: Type):
        """
        Registra um tipo de agente para uso na fábrica.

        Args:
            type_name: Nome do tipo de agente (usado no YAML)
            agent_class: Classe concreta do agente
        """
        self.agent_types[type_name] = agent_class
        logger.debug(f"Tipo de agente registrado: {type_name}")

    def register_crew_type(self, type_name: str, crew_class: Type):
        """
        Registra um tipo de crew para uso na fábrica.

        Args:
            type_name: Nome do tipo de crew (usado no YAML)
            crew_class: Classe concreta da crew
        """
        self.crew_types[type_name] = crew_class
        logger.debug(f"Tipo de crew registrado: {type_name}")

    def create_crew(self, crew_id: str, domain_name: str = None, account_id: str = None) -> GenericCrew:
        """
        Cria uma instância de GenericCrew a partir da configuração do domínio e account_id.

        Args:
            crew_id: ID da crew a ser criada
            domain_name: Nome do domínio (se None, usa o domínio ativo)
            account_id: ID interno da conta (se None, usa account_1 como padrão)

        Returns:
            Instância da GenericCrew

        Raises:
            ValueError: Se o DomainManager não estiver configurado
            ConfigurationError: Se o domínio ou a crew não forem encontrados
        """
        if not self.domain_manager:
            raise ValueError("DomainManager não configurado no CrewFactory")

        # Se o domínio não for especificado, usar o domínio ativo
        if domain_name is None:
            domain_name = self.domain_manager.get_active_domain()
            logger.debug(f"Usando domínio ativo: {domain_name}")

        # Se o account_id não for especificado, isso é um erro crítico
        if account_id is None:
            error_msg = "ERRO CRÍTICO: Account ID não especificado. Impossível criar crew sem um account_id válido."
            logger.error(error_msg)
            raise ValueError(error_msg)

        try:
            # Obter a configuração do domínio, passando o account_id
            domain_config = self.domain_manager.get_domain_config(domain_name, account_id=account_id)
            if not domain_config:
                raise ConfigurationError(f"Domínio '{domain_name}' ou account_id '{account_id}' não encontrado ou configuração vazia")

            # Obter informações detalhadas do domínio
            domain_info = {
                "name": domain_name,
                "display_name": domain_config.get("display_name", domain_name),
                "description": domain_config.get("description", ""),
                "version": domain_config.get("version", "1.0.0"),
                "settings": domain_config.get("settings", {})
            }

            logger.info(f"Criando crew para domínio: {domain_info['display_name']} (v{domain_info['version']})")

            # Obter a configuração da crew
            crews_config = domain_config.get("crew", {})
            crew_config = crews_config.get(crew_id)

            if not crew_config:
                raise ConfigurationError(f"Crew '{crew_id}' não encontrada no domínio '{domain_name}'")

            logger.info(f"Criando GenericCrew {crew_id} para domínio {domain_name}")

            # Inicializar plugins para o domínio se houver um plugin manager disponível
            # Sistema de plugins é opcional - se não estiver disponível, continuamos sem ele
            active_plugins = []
            try:
                from src.plugins.core.plugin_manager import get_plugin_manager
                plugin_manager = get_plugin_manager()

                # DIAGNÓSTICO: Verificar os parâmetros sendo passados
                logger.info(f"DIAGNÓSTICO: Inicializando plugins para domínio={domain_name} e account_id={account_id}")

                # Passar explicitamente o account_id para o método initialize_plugins_for_domain
                active_plugins = plugin_manager.initialize_plugins_for_domain(domain_name, account_id=account_id)

                logger.info(f"Plugins inicializados para domínio {domain_name} e account_id {account_id}: {', '.join(active_plugins) if active_plugins else 'nenhum'}")
            except ImportError:
                logger.info(f"Sistema de plugins não disponível - continuando sem plugins para o domínio {domain_name}")
            except Exception as e:
                logger.warning(f"Erro ao inicializar plugins para domínio {domain_name} e account_id {account_id}: {str(e)}")

            # Criar agentes
            agents = self._create_agents_from_config(crew_config.get("agents", []), domain_name)

            # Criar tarefas
            # As tarefas estão definidas diretamente no campo 'tasks' do YAML, não em 'workflow'
            tasks = self._create_tasks_from_workflow({
                "tasks": crew_config.get("tasks", [])
            }, agents)

            # Criar a crew base do CrewAI
            # Remover 'tasks' da configuração para evitar duplicação
            crew_kwargs = {k: v for k, v in crew_config.items()
                          if k not in ["id", "type", "agents", "workflow", "tasks"]}

            # Adicionar parâmetros obrigatórios
            crew_kwargs.update({
                "agents": agents,
                "tasks": tasks,
                "verbose": True
            })

            # Adicionar memory_system se disponível
            if self.memory_system:
                crew_kwargs["memory"] = self.memory_system

            # Criar a crew base do CrewAI
            base_crew = Crew(**crew_kwargs)

            # Não podemos modificar o ID da crew após a criação, pois é um campo congelado
            # Em vez disso, vamos armazenar o ID personalizado em um dicionário de metadados

            # Criar um dicionário de metadados para a crew
            crew_metadata = {
                "custom_id": crew_id,
                "domain_name": domain_name,
                "domain_info": domain_info,
                "active_plugins": active_plugins
            }

            # Armazenar os metadados como um atributo da classe
            if not hasattr(self, 'crew_metadata'):
                self.crew_metadata = {}

            # Usar o ID gerado automaticamente como chave
            self.crew_metadata[base_crew.id] = crew_metadata

            # Criar a GenericCrew que encapsula a crew base
            generic_crew = GenericCrew(
                crew=base_crew,
                domain_name=domain_name,
                crew_id=crew_id,
                data_proxy_agent=self.data_proxy_agent,
                agent_id_map=getattr(self, 'agent_id_map', {}),
                task_id_map=getattr(self, 'task_id_map', {})
            )

            # Adicionar ao cache
            cache_key = f"{domain_name}:{crew_id}"
            self.crew_cache[cache_key] = generic_crew

            logger.info(f"GenericCrew {crew_id} criada com {len(agents)} agentes e {len(tasks)} tarefas")

            return generic_crew

        except ConfigurationError as ce:
            logger.error(f"Erro de configuração ao criar crew: {str(ce)}")
            raise
        except Exception as e:
            logger.error(f"Erro ao criar crew {crew_id} para domínio {domain_name}: {str(e)}")
            raise ConfigurationError(f"Falha ao criar crew: {str(e)}")

    def _create_agents_from_config(self, agents_config: List[Union[Dict[str, Any], str]], domain_name: str) -> List[Agent]:
        """
        Cria agentes a partir da configuração.

        Args:
            agents_config: Lista de configurações de agentes (dicionários) ou IDs de agentes (strings)
            domain_name: Nome do domínio

        Returns:
            Lista de agentes instanciados

        Raises:
            ConfigurationError: Se houver erro na configuração dos agentes
        """
        agents = []

        try:
            # Obter configuração de domínio para personalização de agentes
            domain_config = None
            domain_info = {}

            if self.domain_manager:
                try:
                    domain_config = self.domain_manager.get_domain_config(domain_name)
                    if domain_config:
                        # Extrair informações detalhadas do domínio
                        domain_info = {
                            "name": domain_name,
                            "display_name": domain_config.get("display_name", domain_name),
                            "description": domain_config.get("description", ""),
                            "version": domain_config.get("version", "1.0.0"),
                            "settings": domain_config.get("settings", {})
                        }
                except ConfigurationError:
                    logger.warning(f"Domínio '{domain_name}' não encontrado, usando configuração padrão para agentes")

            # Obter configurações globais de agentes do domínio
            domain_agent_defaults = {}
            if domain_config:
                domain_agent_defaults = domain_config.get("agent_defaults", {})

            # Obter configurações de agentes do domínio
            domain_agents_config = {}
            if domain_config and "agents" in domain_config:
                domain_agents_config = domain_config.get("agents", {})

            # Obter informações sobre plugins ativos para o domínio
            active_plugins = []
            try:
                from src.plugins.core.plugin_manager import get_plugin_manager
                plugin_manager = get_plugin_manager()
                active_plugins = plugin_manager.get_active_plugins_for_domain(domain_name)
                logger.debug(f"Plugins ativos para domínio {domain_name}: {', '.join(active_plugins) if active_plugins else 'nenhum'}")
            except Exception as e:
                logger.warning(f"Erro ao obter plugins ativos para domínio {domain_name}: {str(e)}")

            # Processar cada agente na configuração
            for agent_item in agents_config:
                # Verificar se o item é um ID de agente (string) ou uma configuração completa (dicionário)
                if isinstance(agent_item, str):
                    # É um ID de agente, buscar configuração no domínio
                    agent_id = agent_item
                    if agent_id not in domain_agents_config:
                        logger.warning(f"Agente '{agent_id}' não encontrado na configuração do domínio {domain_name}, ignorando")
                        continue

                    agent_config = domain_agents_config[agent_id]
                    agent_type = agent_config.get("type", "default")
                    logger.debug(f"Usando configuração do domínio para o agente {agent_id}")
                else:
                    # É uma configuração completa
                    agent_config = agent_item
                    agent_id = agent_config.get("id")
                    agent_type = agent_config.get("type", "default")

                if not agent_id:
                    logger.warning("Agente sem ID na configuração, ignorando")
                    continue

                logger.debug(f"Criando agente {agent_id} do tipo {agent_type} para domínio {domain_name}")

                # Mesclar configurações do domínio com as específicas do agente
                # Prioridade: configuração específica do agente > configuração do tipo de agente > configuração global
                effective_config = {}

                # 1. Configuração global do domínio
                if domain_agent_defaults:
                    effective_config.update(domain_agent_defaults)

                # 2. Configuração específica para o tipo de agente
                if domain_agent_defaults and agent_type in domain_agent_defaults:
                    effective_config.update(domain_agent_defaults.get(agent_type, {}))

                # 3. Configuração específica do agente (maior prioridade)
                effective_config.update(agent_config)

                # Personalizar o backstory com informações do domínio se existir um template
                backstory = effective_config.get("backstory", "")
                if "{domain}" in backstory and domain_info:
                    backstory = backstory.format(
                        domain=domain_info.get("display_name", domain_name),
                        domain_description=domain_info.get("description", ""),
                        domain_version=domain_info.get("version", "1.0.0")
                    )

                # Obter ferramentas para o agente
                tools = self._get_tools_for_agent(effective_config.get("tools", []))

                # Adicionar ferramentas específicas de plugins ativos
                plugin_tools = self._get_plugin_tools_for_agent(agent_id, active_plugins)
                if plugin_tools:
                    tools.extend(plugin_tools)

                # Determinar a classe concreta do agente
                agent_class = self.agent_types.get(agent_type, Agent)

                # Criar o agente sem tentar definir o ID diretamente
                # A biblioteca CrewAI gera um ID automaticamente
                agent_kwargs = {
                    "role": effective_config.get("role", "Assistente"),
                    "goal": effective_config.get("goal", "Ajudar o usuário"),
                    "backstory": backstory,
                    "verbose": True,
                    "tools": tools,
                    "allow_delegation": effective_config.get("allow_delegation", True),
                    "llm": effective_config.get("llm", None)
                }

                # Adicionar outros parâmetros da configuração
                for k, v in effective_config.items():
                    if k not in ["id", "type", "role", "goal", "backstory", "tools", "allow_delegation", "llm"]:
                        agent_kwargs[k] = v

                # Criar o agente
                agent = agent_class(**agent_kwargs)

                # Não podemos adicionar atributos personalizados ao objeto Agent da CrewAI
                # Em vez disso, vamos usar um dicionário separado para armazenar metadados

                # Criar um dicionário de mapeamento para associar IDs personalizados aos objetos Agent
                # Isso permite recuperar o agente pelo ID personalizado posteriormente
                if not hasattr(self, 'agent_id_map'):
                    self.agent_id_map = {}

                # Criar um dicionário para armazenar metadados dos agentes
                if not hasattr(self, 'agent_metadata'):
                    self.agent_metadata = {}

                # Adicionar o agente ao dicionário de mapeamento
                self.agent_id_map[agent_id] = agent

                # Armazenar metadados separadamente
                self.agent_metadata[agent_id] = {
                    "domain_name": domain_name,
                    "domain_info": domain_info,
                    "active_plugins": active_plugins
                }

                # Configurar e adicionar DataProxyAgent se disponível
                if self.data_proxy_agent:
                    try:
                        # Configurar o DataProxyAgent com informações do domínio
                        if hasattr(self.data_proxy_agent, 'set_domain_context'):
                            self.data_proxy_agent.set_domain_context(
                                domain_name=domain_name,
                                domain_info=domain_info,
                                agent_id=agent_id
                            )
                            logger.debug(f"DataProxyAgent configurado com contexto do domínio {domain_name} para o agente {agent_id}")

                        # Associar o DataProxyAgent ao agente
                        if hasattr(agent, 'set_data_proxy'):
                            agent.set_data_proxy(self.data_proxy_agent)
                            logger.debug(f"DataProxyAgent associado ao agente {agent_id}")
                        else:
                            logger.warning(f"Agente {agent_id} não suporta DataProxyAgent (método set_data_proxy não encontrado)")
                    except Exception as e:
                        logger.warning(f"Erro ao configurar DataProxyAgent para o agente {agent_id}: {str(e)}")

                agents.append(agent)

            return agents

        except Exception as e:
            logger.error(f"Erro ao criar agentes para domínio {domain_name}: {str(e)}")
            raise ConfigurationError(f"Falha ao criar agentes: {str(e)}")

    def _get_tools_for_agent(self, tool_names: List[str]) -> List[Any]:
        """
        Obtém as ferramentas para um agente.

        Args:
            tool_names: Lista de nomes de ferramentas

        Returns:
            Lista de ferramentas instanciadas
        """
        if not self.tool_registry:
            return []

        tools = []

        for tool_name in tool_names:
            tool = self.tool_registry.get_tool(tool_name)
            if tool:
                tools.append(tool)
            else:
                logger.warning(f"Ferramenta {tool_name} não encontrada no registro")

        return tools

    def _get_plugin_tools_for_agent(self, agent_id: str, active_plugins: List[str]) -> List[Any]:
        """
        Obtém ferramentas específicas de plugins para um agente.

        Args:
            agent_id: ID do agente
            active_plugins: Lista de plugins ativos

        Returns:
            Lista de ferramentas de plugins para o agente
        """
        if not self.tool_registry or not active_plugins:
            return []

        plugin_tools = []

        try:
            from src.plugins.core.plugin_manager import get_plugin_manager
            plugin_manager = get_plugin_manager()

            # Para cada plugin ativo, verificar se ele fornece ferramentas para este agente
            for plugin_name in active_plugins:
                try:
                    # Obter ferramentas específicas do plugin para este agente
                    tools = plugin_manager.get_tools_for_agent(plugin_name, agent_id)
                    if tools:
                        plugin_tools.extend(tools)
                        logger.debug(f"Adicionadas {len(tools)} ferramentas do plugin {plugin_name} para o agente {agent_id}")
                except Exception as e:
                    logger.warning(f"Erro ao obter ferramentas do plugin {plugin_name} para o agente {agent_id}: {str(e)}")
        except Exception as e:
            logger.warning(f"Erro ao carregar ferramentas de plugins: {str(e)}")

        return plugin_tools

    def _create_tasks_from_workflow(self, workflow: Dict[str, Any], agents: List[Agent]) -> List[Task]:
        """
        Cria tarefas a partir da definição de workflow.

        Args:
            workflow: Configuração de workflow
            agents: Lista de agentes disponíveis

        Returns:
            Lista de tarefas instanciadas
        """
        tasks = []

        # Criar um mapeamento de IDs de tarefas, semelhante ao que fizemos com os agentes
        if not hasattr(self, 'task_id_map'):
            self.task_id_map = {}

        # Criar um dicionário para armazenar metadados das tarefas
        if not hasattr(self, 'task_metadata'):
            self.task_metadata = {}

        # Usar o mapeamento de IDs de agentes que criamos no _create_agents_from_config
        agent_map = getattr(self, 'agent_id_map', {})

        # Se não temos um mapeamento, criamos um usando apenas os IDs gerados automaticamente
        # Isso é um fallback, mas não deve ser necessário se o _create_agents_from_config foi executado corretamente
        if not agent_map:
            logger.warning("Mapeamento de IDs de agentes não encontrado, usando IDs gerados automaticamente")
            for agent in agents:
                agent_map[agent.id] = agent

        # Criar tarefas
        for i, task_config in enumerate(workflow.get("tasks", [])):
            # Não usamos o ID da tarefa do YAML, pois a biblioteca CrewAI gerencia isso internamente
            # Apenas para fins de log
            task_display_id = task_config.get("id", f"task_{i+1}")
            agent_id = task_config.get("agent")

            if not agent_id:
                logger.warning(f"Tarefa {task_display_id} sem agente na configuração, ignorando")
                continue

            # Obter o agente para a tarefa
            agent = agent_map.get(agent_id)
            if not agent:
                logger.warning(f"Agente {agent_id} não encontrado para tarefa {task_display_id}")
                continue

            # Criar a tarefa - NÃO definir o ID, pois a biblioteca CrewAI gerencia isso internamente
            task = Task(
                description=task_config.get("description", ""),
                expected_output=task_config.get("expected_output", ""),
                agent=agent,
                # Parâmetros adicionais da configuração
                **{k: v for k, v in task_config.items() if k not in ["id", "agent", "description", "expected_output"]}
            )

            # Adicionar a tarefa ao dicionário de mapeamento
            self.task_id_map[task_display_id] = task

            # Armazenar metadados separadamente
            self.task_metadata[task_display_id] = {
                "original_config": task_config,
                "agent_id": agent_id
            }

            tasks.append(task)

        return tasks


    def get_crew_for_domain(self, crew_id: str, domain_name: str, account_id: str) -> GenericCrew:
        """
        Obtém uma crew para um domínio e account_id específicos, criando-a se necessário.

        Args:
            crew_id: ID da crew
            domain_name: Nome do domínio
            account_id: ID interno da conta

        Returns:
            Instância da crew
        """
        if not account_id:
            raise ValueError("[ERRO] account_id é obrigatório para criação de crews. Forneça o ID da conta vinculada ao domínio.")
        # Se o domínio não for especificado, usar o domínio ativo
        if domain_name is None and self.domain_manager:
            domain_name = self.domain_manager.get_active_domain()

        # Chave para o cache
        cache_key = f"{domain_name}:{account_id}:{crew_id}"

        # Verificar se já existe no cache
        if cache_key in self.crew_cache:
            return self.crew_cache[cache_key]

        # Criar a crew
        return self.create_crew(crew_id, domain_name, account_id)

    def invalidate_cache(self, domain_name: str = None, crew_id: str = None):
        """
        Invalida o cache de crews.

        Args:
            domain_name: Nome do domínio para invalidar (se None, invalida todos)
            crew_id: ID da crew para invalidar (se None, invalida todas do domínio)
        """
        if domain_name is None and crew_id is None:
            # Invalidar todo o cache
            self.crew_cache.clear()
            logger.info("Cache de crews completamente invalidado")
            return

        keys_to_remove = []

        for key in self.crew_cache.keys():
            domain, crew = key.split(":")

            if domain_name and domain != domain_name:
                continue

            if crew_id and crew != crew_id:
                continue

            keys_to_remove.append(key)

        for key in keys_to_remove:
            del self.crew_cache[key]

        logger.info(f"Cache invalidado para {len(keys_to_remove)} crews")

# Singleton para a fábrica de crews
_crew_factory = None

def get_crew_factory(force_new=False, data_proxy_agent=None, memory_system=None, tool_registry=None, domain_manager=None) -> CrewFactory:
    """
    Obtém a instância singleton da fábrica de crews.

    Args:
        force_new: Se True, força a criação de uma nova instância
        data_proxy_agent: DataProxyAgent opcional
        memory_system: Sistema de memória opcional
        tool_registry: Registro de ferramentas opcional
        domain_manager: Gerenciador de domínios opcional

    Returns:
        Instância do CrewFactory
    """
    global _crew_factory

    if _crew_factory is None or force_new:
        _crew_factory = CrewFactory(
            data_proxy_agent=data_proxy_agent,
            memory_system=memory_system,
            tool_registry=tool_registry,
            domain_manager=domain_manager
        )

    return _crew_factory
