"""
Registry de ferramentas do ChatwootAI.

Este módulo implementa o registro centralizado de ferramentas,
permitindo que o DataProxyAgent gerencie todas as ferramentas do sistema
sem duplicação em agentes individuais.
"""
import logging
from typing import Dict, Any, List, Optional, Type, Callable
import inspect
import importlib
from functools import lru_cache

from src.core.exceptions import ConfigurationError

logger = logging.getLogger(__name__)


class ToolRegistryError(Exception):
    """Exceção para erros relacionados ao registro de ferramentas."""
    pass


class Tool:
    """Representação básica de uma ferramenta no sistema."""
    
    def __init__(self, name: str, description: str, config: Dict[str, Any] = None):
        """
        Inicializa uma ferramenta.
        
        Args:
            name: Nome da ferramenta
            description: Descrição da ferramenta
            config: Configuração específica para esta ferramenta
        """
        self.name = name
        self.description = description
        self.config = config or {}
    
    def __repr__(self) -> str:
        return f"Tool(name={self.name})"


class ToolRegistry:
    """
    Registro centralizado de ferramentas do ChatwootAI.
    
    Responsável por gerenciar todas as ferramentas disponíveis no sistema,
    permitindo o carregamento dinâmico, instanciação e acesso a ferramentas
    a partir de configurações YAML.
    """
    
    def __init__(self):
        """Inicializa o registro de ferramentas."""
        self._tools: Dict[str, Dict[str, Any]] = {}
        self._instances: Dict[str, object] = {}
        self._class_cache: Dict[str, Type] = {}
        
    @property
    def tools(self) -> Dict[str, Dict[str, Any]]:
        """Propriedade para acesso às ferramentas registradas."""
        return self._tools
        
    @tools.setter
    def tools(self, value: Dict[str, Dict[str, Any]]):
        """Setter para a propriedade tools."""
        self._tools = value
        
    @property
    def tool_instances(self) -> Dict[str, object]:
        """Propriedade para acesso às instâncias de ferramentas."""
        return self._instances
        
    @tool_instances.setter
    def tool_instances(self, value: Dict[str, object]):
        """Setter para a propriedade tool_instances."""
        self._instances = value
    
    def register_tool(self, tool_id: str, tool_config: Dict[str, Any]) -> None:
        """
        Registra uma ferramenta no registry.
        
        Args:
            tool_id: Identificador único da ferramenta
            tool_config: Configuração da ferramenta
            
        Raises:
            ToolRegistryError: Se a configuração for inválida
        """
        if not tool_config:
            raise ToolRegistryError(f"Configuração vazia para ferramenta {tool_id}")
            
        if "name" not in tool_config:
            tool_config["name"] = tool_id
            
        # Verifica se o campo 'type' está presente
        if "type" not in tool_config:
            raise ConfigurationError(f"Configuração de ferramenta inválida: falta o campo 'type'")
            
        # Verifica se a descrição está no nível principal ou dentro do campo config
        has_description = "description" in tool_config
        has_config_description = "config" in tool_config and "description" in tool_config["config"]
        
        if not has_description and not has_config_description:
            raise ToolRegistryError(f"Descrição não encontrada para ferramenta {tool_id}")
            
        if "class" not in tool_config:
            raise ToolRegistryError(f"Classe não especificada para ferramenta {tool_id}")
        
        # Registra a configuração
        self._tools[tool_id] = tool_config.copy()
        logger.debug(f"Ferramenta registrada: {tool_id}")
    
    def register_tools_from_config(self, tools_config: Dict[str, Dict[str, Any]]) -> None:
        """
        Registra múltiplas ferramentas a partir de uma configuração.
        
        Args:
            tools_config: Dicionário de configurações de ferramentas
        """
        for tool_id, tool_config in tools_config.items():
            try:
                self.register_tool(tool_id, tool_config)
            except ToolRegistryError as e:
                logger.error(f"Erro ao registrar ferramenta {tool_id}: {str(e)}")
    
    def get_tool_config(self, tool_id: str) -> Dict[str, Any]:
        """
        Obtém a configuração de uma ferramenta registrada.
        
        Args:
            tool_id: Identificador da ferramenta
            
        Returns:
            Dict[str, Any]: Configuração da ferramenta
            
        Raises:
            ConfigurationError: Se a ferramenta não estiver registrada
        """
        if tool_id not in self._tools:
            raise ConfigurationError(f"Ferramenta '{tool_id}' não encontrada no registro")
            
        return self._tools[tool_id]
    
    def get_tool_ids(self) -> List[str]:
        """
        Obtém todos os IDs de ferramentas registradas.
        
        Returns:
            List[str]: Lista de IDs de ferramentas
        """
        return list(self._tools.keys())
        
    def get_tool_class(self, class_path: str) -> Type:
        """
        Obtém a classe de uma ferramenta a partir do caminho completo.
        
        Args:
            class_path: Caminho completo para a classe (ex: 'package.module.ClassName')
            
        Returns:
            Type: Classe da ferramenta
            
        Raises:
            ImportError: Se o módulo ou a classe não puderem ser importados
            AttributeError: Se a classe não existir no módulo
        """
        # Verifica se a classe já está no cache
        if class_path in self._class_cache:
            return self._class_cache[class_path]
            
        try:
            # Divide o caminho em módulo e nome da classe
            module_path, class_name = class_path.rsplit(".", 1)
            
            # Importa o módulo
            module = importlib.import_module(module_path)
            
            # Obtém a classe do módulo
            tool_class = getattr(module, class_name)
            
            # Armazena no cache
            self._class_cache[class_path] = tool_class
        except (ImportError, AttributeError) as e:
            # Captura erros de importação ou atributo não encontrado
            logger.error(f"Erro ao carregar classe {class_path}: {str(e)}")
            raise ConfigurationError(f"Não foi possível carregar a classe da ferramenta: {str(e)}")
        
        return tool_class
    
    def get_tool_info(self, tool_id: str) -> Optional[Tool]:
        """
        Obtém informações básicas sobre uma ferramenta.
        
        Args:
            tool_id: Identificador da ferramenta
            
        Returns:
            Optional[Tool]: Objeto Tool com informações ou None se não encontrada
        """
        config = self.get_tool_config(tool_id)
        if not config:
            return None
            
        return Tool(
            name=config.get("name", tool_id),
            description=config.get("description", ""),
            config=config.get("parameters", {})
        )
    
    def _load_tool_class(self, class_path: str) -> Type:
        """
        Carrega dinamicamente a classe de uma ferramenta.
        
        Args:
            class_path: Caminho completo para a classe
            
        Returns:
            Type: Classe da ferramenta
            
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
    
    @lru_cache(maxsize=32)
    def get_tool_instance(self, tool_id: str, **kwargs) -> Any:
        """
        Obtém ou cria uma instância de ferramenta.
        
        O cache garante que a mesma instância seja reutilizada para
        o mesmo conjunto de argumentos, melhorando a performance.
        
        Args:
            tool_id: Identificador da ferramenta
            **kwargs: Argumentos adicionais para a inicialização da ferramenta
            
        Returns:
            Any: Instância da ferramenta
            
        Raises:
            ToolRegistryError: Se a ferramenta não estiver registrada ou não puder ser instanciada
            ConfigurationError: Se a ferramenta não estiver registrada
        """
        # Verifica se a ferramenta já está no cache de instâncias
        if tool_id in self._instances:
            logger.debug(f"Ferramenta obtida do cache: {tool_id}")
            return self._instances[tool_id]
        
        try:
            # Obtém a configuração da ferramenta (isso já lança ConfigurationError se não encontrada)
            config = self.get_tool_config(tool_id)
            
            # Carrega a classe da ferramenta
            class_path = config.get("class")
            if not class_path:
                raise ToolRegistryError(f"Classe não especificada para ferramenta {tool_id}")
                
            # Obtém a classe da ferramenta (isso já lança ConfigurationError se não encontrada)
            tool_class = self.get_tool_class(class_path)
            
            # Obtém os parâmetros da configuração
            tool_config = config.get("config", {})
            
            # Mescla parâmetros da configuração com kwargs
            params = {}
            if tool_config:
                params.update(tool_config)
            params.update(kwargs)
            
            # Verifica se a classe herda de BaseTool (da CrewAI)
            from crewai.tools.base_tool import BaseTool
            
            # Instancia a ferramenta de forma diferente dependendo do tipo
            if issubclass(tool_class, BaseTool):
                # Para ferramentas CrewAI, passamos os parâmetros diretamente
                instance = tool_class(**params)
                
                # Se a descrição foi fornecida nos parâmetros, definimos diretamente na instância
                # Isso é necessário porque a classe BaseTool formata a descrição de uma maneira específica
                if "description" in params:
                    # Sobrescreve o atributo description na instância
                    instance.description = params["description"]
            else:
                # Para outras ferramentas, filtramos os parâmetros válidos
                # com base na assinatura do método __init__
                valid_params = {}
                sig = inspect.signature(tool_class.__init__)
                for param_name, param in sig.parameters.items():
                    if param_name == "self":
                        continue
                    if param_name in params:
                        valid_params[param_name] = params[param_name]
                    elif param.default == inspect.Parameter.empty:
                        raise ToolRegistryError(f"Parâmetro obrigatório {param_name} não fornecido para {tool_id}")
                
                # Instancia a ferramenta com os parâmetros filtrados
                instance = tool_class(**valid_params)
            
            # Armazena a instância no cache
            self._instances[tool_id] = instance
            
            logger.debug(f"Ferramenta instanciada: {tool_id}")
            return instance
            
        except (ImportError, AttributeError) as e:
            logger.error(f"Erro ao carregar classe para ferramenta {tool_id}: {str(e)}")
            raise ToolRegistryError(f"Não foi possível carregar a classe da ferramenta {tool_id}: {str(e)}")
        except Exception as e:
            logger.error(f"Erro ao instanciar ferramenta {tool_id}: {str(e)}")
            raise ToolRegistryError(f"Não foi possível instanciar a ferramenta {tool_id}: {str(e)}")
    
    def get_tools_for_agent(self, agent_tools: List[str]) -> List[Any]:
        """
        Obtém todas as instâncias de ferramentas para um agente específico.
        
        Args:
            agent_tools: Lista de IDs de ferramentas configuradas para o agente
            
        Returns:
            List[Any]: Lista de instâncias de ferramentas
        """
        tools = []
        
        for tool_id in agent_tools:
            try:
                tool = self.get_tool_instance(tool_id)
                tools.append(tool)
            except ToolRegistryError as e:
                logger.warning(f"Ferramenta {tool_id} não disponível: {str(e)}")
        
        return tools
    
    def clear_cache(self) -> None:
        """Limpa o cache de instâncias de ferramentas."""
        self.get_tool_instance.cache_clear()
        logger.debug("Cache de ferramentas limpo")
    
    def reset(self) -> None:
        """Reseta completamente o registro, removendo todas as ferramentas e instâncias."""
        self._tools = {}
        self._instances = {}
        self._class_cache = {}
        self.clear_cache()
        logger.info("Registry de ferramentas e instâncias resetado")
    
    def get_tools_by_type(self, tool_type: str) -> List[str]:
        """
        Retorna os IDs de todas as ferramentas de um determinado tipo.
        
        Args:
            tool_type: Tipo de ferramenta a ser filtrado
            
        Returns:
            List[str]: Lista de IDs de ferramentas do tipo especificado
        """
        tool_ids = []
        
        for tool_id, config in self._tools.items():
            if config.get("type") == tool_type:
                tool_ids.append(tool_id)
                
        return tool_ids
    
    def get_tool_instances_by_type(self, tool_type: str) -> List[Any]:
        """
        Retorna instâncias de todas as ferramentas de um determinado tipo.
        
        Args:
            tool_type: Tipo de ferramenta a ser filtrado
            
        Returns:
            List[Any]: Lista de instâncias de ferramentas do tipo especificado
        """
        tool_ids = self.get_tools_by_type(tool_type)
        instances = []
        
        for tool_id in tool_ids:
            try:
                instance = self.get_tool_instance(tool_id)
                instances.append(instance)
            except Exception as e:
                logger.warning(f"Erro ao instanciar ferramenta {tool_id}: {str(e)}")
                
        return instances
    
    def get_all_tool_instances(self) -> List[Any]:
        """
        Retorna todas as instâncias de ferramentas atualmente no cache.
        
        Returns:
            List[Any]: Lista com todas as instâncias de ferramentas
        """
        return list(self._instances.values())
