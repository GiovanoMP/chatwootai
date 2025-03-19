"""
Classe base para todos os plugins do ChatwootAI.
"""
from typing import Dict, Any, Optional


class BasePlugin:
    """
    Classe base para todos os plugins do ChatwootAI.
    
    Os plugins permitem estender as funcionalidades do sistema sem modificar o código base,
    facilitando a adaptação para diferentes domínios de negócio.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Inicializa o plugin com a configuração fornecida.
        
        Args:
            config: Dicionário contendo a configuração do plugin
        """
        self.config = config
        self.name = self.__class__.__name__
        self.enabled = config.get("enabled", True)
        self.initialize()
    
    def initialize(self):
        """
        Método para inicialização adicional do plugin.
        Deve ser sobrescrito pelas classes filhas se necessário.
        """
        pass
    
    def validate_config(self) -> bool:
        """
        Valida se a configuração do plugin está correta.
        
        Returns:
            bool: True se a configuração é válida, False caso contrário
        """
        return True
    
    def get_config_value(self, key: str, default: Any = None) -> Any:
        """
        Obtém um valor da configuração do plugin.
        
        Args:
            key: Chave do valor na configuração
            default: Valor padrão caso a chave não exista
            
        Returns:
            Any: Valor da configuração ou o valor padrão
        """
        return self.config.get(key, default)
    
    def is_enabled(self) -> bool:
        """
        Verifica se o plugin está habilitado.
        
        Returns:
            bool: True se o plugin está habilitado, False caso contrário
        """
        return self.enabled
    
    def disable(self):
        """
        Desabilita o plugin.
        """
        self.enabled = False
    
    def enable(self):
        """
        Habilita o plugin.
        """
        self.enabled = True
    
    def execute(self, *args, **kwargs) -> Any:
        """
        Método principal para execução do plugin.
        Deve ser implementado pelas classes filhas.
        
        Returns:
            Any: Resultado da execução do plugin
        """
        raise NotImplementedError("O método execute deve ser implementado pela classe filha")
