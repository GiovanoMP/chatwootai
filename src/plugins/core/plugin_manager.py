"""
Gerenciador de plugins do ChatwootAI.
"""
import importlib
import logging
import os
from typing import Dict, List, Any, Type, Optional

# Importando BasePlugin da localização correta na nova estrutura
from ..base.base_plugin import BasePlugin

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
        
        # Lista de caminhos onde os plugins podem ser encontrados (ordem de prioridade)
        self.plugin_paths = config.get("plugin_paths", [
            "src.plugins.core",             # Plugins essenciais do sistema (business_rules, product_search, etc.)
            "src.plugins.implementations",  # Plugins específicos por domínio de negócio
            "src.plugins"                  # Fallback para a raiz (compatibilidade)
        ])
        
        # Configurar nível de log para ver mensagens de debug durante a importação
        logging.getLogger(__name__).setLevel(logging.DEBUG)
    
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
            import_errors = []
            
            for base_path in self.plugin_paths:
                try:
                    full_module_path = f"{base_path}.{plugin_name}"
                    logger.debug(f"Tentando importar {plugin_name} de {full_module_path}")
                    module = importlib.import_module(full_module_path)
                    logger.info(f"Plugin {plugin_name} encontrado em {base_path}")
                    break
                except ImportError as e:
                    import_errors.append(f"- {base_path}: {str(e)}")
                    continue
            else:
                error_details = "\n".join(import_errors)
                logger.error(f"Não foi possível encontrar o plugin {plugin_name}. Erros por caminho:\n{error_details}")
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
        Carrega todos os plugins descobertos. Se nenhum plugin for especificado
        explicitamente na configuração, tentará carregar todos os plugins
        existentes em src.plugins.core automaticamente.
        
        Returns:
            Dict[str, BasePlugin]: Dicionário de plugins carregados
        """
        plugin_names = self.discover_plugins()
        
        # Se não houver plugins especificados, carregar os principais automaticamente
        if not plugin_names:
            logger.info("Nenhum plugin explícito configurado. Carregando plugins essenciais automaticamente.")
            try:
                # Carregar plugins essenciais da pasta core automaticamente
                from src.plugins.core import business_rules_plugin, product_search_plugin, appointment_scheduler
                
                plugin_names = [
                    "business_rules",
                    "product_search",
                    "appointment_scheduler"
                ]
                logger.info(f"Detectados {len(plugin_names)} plugins essenciais para carregamento automático.")
            except ImportError as e:
                logger.warning(f"Não foi possível importar plugins essenciais automaticamente: {e}")
        
        # Carregar todos os plugins da lista
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
        
    def initialize_plugins_for_domain(self, domain_name: str) -> Dict[str, BasePlugin]:
        """
        Inicializa os plugins específicos para um domínio.
        
        Este método é chamado quando uma conversa é iniciada ou quando
        o domínio de uma conversa é determinado, garantindo que todos os
        plugins necessários para o domínio estejam ativos e configurados.
        
        Args:
            domain_name: Nome do domínio
            
        Returns:
            Dict[str, BasePlugin]: Dicionário com os plugins inicializados para o domínio
        """
        logger.info(f"Inicializando plugins para o domínio: {domain_name}")
        
        # Plugins específicos do domínio (prefixados com o nome do domínio)
        domain_specific_plugins = {}
        
        # 1. Carregar plugins específicos do domínio (prefixados com o nome do domínio)
        try:
            # Procurar por plugins com o prefixo do domínio na pasta implementations
            domain_plugin_path = f"src.plugins.implementations.{domain_name}"
            try:
                domain_module = importlib.import_module(domain_plugin_path)
                logger.info(f"Módulo de plugins do domínio {domain_name} encontrado")
                
                # Procurar por classes de plugin no módulo
                for attr_name in dir(domain_module):
                    attr = getattr(domain_module, attr_name)
                    if isinstance(attr, type) and issubclass(attr, BasePlugin) and attr != BasePlugin:
                        plugin_name = f"{domain_name}_{attr_name.lower().replace('plugin', '')}"
                        plugin_config = self.plugin_configs.get(plugin_name, {})
                        plugin_instance = attr(plugin_config)
                        
                        # Armazenar o plugin
                        self.plugins[plugin_name] = plugin_instance
                        domain_specific_plugins[plugin_name] = plugin_instance
                        logger.info(f"Plugin {plugin_name} do domínio {domain_name} inicializado")
            except ImportError as e:
                logger.warning(f"Não foi possível importar módulo de plugins para o domínio {domain_name}: {e}")
        except Exception as e:
            logger.error(f"Erro ao inicializar plugins específicos para o domínio {domain_name}: {e}")
        
        # 2. Verificar configurações do domínio para plugins adicionais
        domain_config = self.config.get("domains", {}).get(domain_name, {})
        if domain_config and "plugins" in domain_config:
            for plugin_name in domain_config["plugins"]:
                if plugin_name not in self.plugins:
                    plugin = self.load_plugin(plugin_name)
                    if plugin:
                        domain_specific_plugins[plugin_name] = plugin
                else:
                    domain_specific_plugins[plugin_name] = self.plugins[plugin_name]
        
        # 3. Inicializar cada plugin (chamar método initialize se existir)
        for plugin_name, plugin in domain_specific_plugins.items():
            try:
                if hasattr(plugin, "initialize"):
                    plugin.initialize(domain_name=domain_name)
                    logger.info(f"Plugin {plugin_name} inicializado para o domínio {domain_name}")
            except Exception as e:
                logger.error(f"Erro ao inicializar plugin {plugin_name} para o domínio {domain_name}: {e}")
        
        return domain_specific_plugins
    
    def deactivate_plugins_for_domain(self, domain_name: str) -> None:
        """
        Desativa os plugins específicos de um domínio.
        
        Este método é chamado quando uma conversa é finalizada,
        permitindo a liberação de recursos e a limpeza de estado
        dos plugins específicos do domínio.
        
        Args:
            domain_name: Nome do domínio
        """
        logger.info(f"Desativando plugins para o domínio: {domain_name}")
        
        # Obter plugins específicos do domínio
        domain_plugins = self.get_plugins_for_domain(domain_name)
        
        # Chamar método shutdown em cada plugin, se existir
        for plugin_name, plugin in domain_plugins.items():
            try:
                if hasattr(plugin, "shutdown"):
                    plugin.shutdown()
                    logger.info(f"Plugin {plugin_name} desativado para o domínio {domain_name}")
            except Exception as e:
                logger.error(f"Erro ao desativar plugin {plugin_name} para o domínio {domain_name}: {e}")
        
        # Opcionalmente, remover plugins específicos do domínio da memória
        # para liberar recursos (apenas se forem exclusivos deste domínio)
        plugins_to_remove = []
        for plugin_name in self.plugins:
            if plugin_name.startswith(f"{domain_name}_"):
                plugins_to_remove.append(plugin_name)
        
        for plugin_name in plugins_to_remove:
            del self.plugins[plugin_name]
            logger.info(f"Plugin {plugin_name} removido da memória")


# Singleton para o gerenciador de plugins
_plugin_manager = None

def get_plugin_manager(force_new=False, config=None):
    """
    Obtém a instância singleton do gerenciador de plugins.
    
    Args:
        force_new: Se True, força a criação de uma nova instância
        config: Configuração opcional para o gerenciador
        
    Returns:
        Instância do PluginManager
    """
    global _plugin_manager
    
    if _plugin_manager is None or force_new:
        if config is None:
            # Configuração padrão se nenhuma for fornecida
            config = {
                "plugin_paths": [
                    "src.plugins.core",
                    "src.plugins.implementations",
                    "src.plugins"
                ]
            }
        
        _plugin_manager = PluginManager(config)
        _plugin_manager.load_plugins()
        logger.info("PluginManager singleton inicializado")
    
    return _plugin_manager
