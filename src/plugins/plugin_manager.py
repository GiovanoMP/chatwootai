"""
Gerenciador de plugins do ChatwootAI.
"""
import importlib
import logging
import os
from typing import Dict, List, Any, Type, Optional

from .base import BasePlugin

logger = logging.getLogger(__name__)


class PluginManager:
    """
    Gerenciador de plugins do ChatwootAI.
    
    Responsável por carregar, inicializar e gerenciar os plugins do sistema,
    permitindo a extensão das funcionalidades para diferentes domínios de negócio.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Inicializa o gerenciador de plugins.
        
        Args:
            config: Configuração do sistema
        """
        self.config = config
        self.plugins: Dict[str, BasePlugin] = {}
        self.plugin_configs = config.get("plugins", {})
        self.plugin_paths = config.get("plugin_paths", ["src.plugins"])
    
    def discover_plugins(self) -> List[str]:
        """
        Descobre os plugins disponíveis no sistema.
        
        Returns:
            List[str]: Lista de nomes de plugins descobertos
        """
        discovered_plugins = []
        
        # Plugins configurados explicitamente
        if "enabled_plugins" in self.config:
            return self.config["enabled_plugins"]
        
        # Descoberta automática baseada no domínio de negócio ativo
        active_domain = self.config.get("active_domain")
        if active_domain and "plugins" in active_domain:
            return active_domain["plugins"]
        
        return discovered_plugins
    
    def load_plugin(self, plugin_name: str) -> Optional[BasePlugin]:
        """
        Carrega um plugin pelo nome.
        
        Args:
            plugin_name: Nome do plugin a ser carregado
            
        Returns:
            Optional[BasePlugin]: Instância do plugin carregado ou None se falhar
        """
        if plugin_name in self.plugins:
            logger.info(f"Plugin {plugin_name} já está carregado")
            return self.plugins[plugin_name]
        
        try:
            # Tenta importar o módulo do plugin
            module_path = plugin_name.replace(".", "_")
            for base_path in self.plugin_paths:
                try:
                    module = importlib.import_module(f"{base_path}.{plugin_name}")
                    break
                except ImportError:
                    continue
            else:
                logger.error(f"Não foi possível encontrar o plugin {plugin_name}")
                return None
            
            # Procura pela classe do plugin no módulo
            plugin_class = None
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if isinstance(attr, type) and issubclass(attr, BasePlugin) and attr != BasePlugin:
                    plugin_class = attr
                    break
            
            if not plugin_class:
                logger.error(f"Não foi encontrada uma classe de plugin válida em {plugin_name}")
                return None
            
            # Obtém a configuração do plugin
            plugin_config = self.plugin_configs.get(plugin_name, {})
            
            # Instancia o plugin
            plugin_instance = plugin_class(plugin_config)
            
            # Armazena o plugin carregado
            self.plugins[plugin_name] = plugin_instance
            
            logger.info(f"Plugin {plugin_name} carregado com sucesso")
            return plugin_instance
            
        except Exception as e:
            logger.error(f"Erro ao carregar o plugin {plugin_name}: {str(e)}")
            return None
    
    def load_plugins(self) -> Dict[str, BasePlugin]:
        """
        Carrega todos os plugins descobertos.
        
        Returns:
            Dict[str, BasePlugin]: Dicionário de plugins carregados
        """
        plugin_names = self.discover_plugins()
        
        for plugin_name in plugin_names:
            self.load_plugin(plugin_name)
        
        return self.plugins
    
    def get_plugin(self, plugin_name: str) -> Optional[BasePlugin]:
        """
        Obtém um plugin pelo nome.
        
        Args:
            plugin_name: Nome do plugin
            
        Returns:
            Optional[BasePlugin]: Instância do plugin ou None se não encontrado
        """
        if plugin_name in self.plugins:
            return self.plugins[plugin_name]
        
        return self.load_plugin(plugin_name)
    
    def execute_plugin(self, plugin_name: str, action: str = None, **kwargs) -> Any:
        """
        Executa um plugin pelo nome e ação específica.
        
        Args:
            plugin_name: Nome do plugin
            action: Nome da ação a ser executada (método do plugin)
            **kwargs: Argumentos nomeados para a ação
            
        Returns:
            Any: Resultado da execução do plugin
        """
        plugin = self.get_plugin(plugin_name)
        
        if not plugin:
            logger.error(f"Plugin {plugin_name} não encontrado")
            return None
        
        if not plugin.is_enabled():
            logger.warning(f"Plugin {plugin_name} está desabilitado")
            return None
        
        try:
            if action and hasattr(plugin, action):
                # Executa o método específico do plugin
                method = getattr(plugin, action)
                return method(**kwargs)
            else:
                # Executa o método padrão execute
                return plugin.execute(**kwargs)
        except Exception as e:
            logger.error(f"Erro ao executar {action or 'execute'} do plugin {plugin_name}: {str(e)}")
            return None
            
    def get_plugins_for_domain(self, domain_name: str) -> Dict[str, BasePlugin]:
        """
        Obtém os plugins disponíveis para um domínio específico.
        
        Args:
            domain_name: Nome do domínio
            
        Returns:
            Dict[str, BasePlugin]: Dicionário com os plugins disponíveis para o domínio
        """
        domain_plugins = {}
        
        # Filtra os plugins que têm o prefixo do domínio
        for plugin_name, plugin in self.plugins.items():
            if plugin_name.startswith(f"{domain_name}_"):
                domain_plugins[plugin_name] = plugin
        
        logger.info(f"Encontrados {len(domain_plugins)} plugins para o domínio {domain_name}")
        return domain_plugins
        
    def has_plugin(self, plugin_name: str) -> bool:
        """
        Verifica se um plugin está disponível.
        
        Args:
            plugin_name: Nome do plugin
            
        Returns:
            bool: True se o plugin está disponível, False caso contrário
        """
        return plugin_name in self.plugins or self.load_plugin(plugin_name) is not None
