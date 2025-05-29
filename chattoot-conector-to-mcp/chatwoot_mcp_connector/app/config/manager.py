"""
Gerenciador de configuração do conector.
Carrega e gerencia configurações do sistema.
"""

import json
import os
import logging
from app.utils.logger import get_logger

# Configuração do logger
logger = get_logger(__name__)

class ConfigManager:
    """
    Gerenciador de configuração do conector.
    """
    
    def __init__(self, config_path):
        """
        Inicializa o gerenciador de configuração.
        
        Args:
            config_path: Caminho para o arquivo de configuração
        """
        self.config_path = config_path
        self.config = self._load_config()
    
    def _load_config(self):
        """
        Carrega a configuração do arquivo.
        
        Returns:
            Dicionário com a configuração
        """
        try:
            # Verifica se o arquivo existe
            if not os.path.exists(self.config_path):
                logger.warning(f"Arquivo de configuração não encontrado: {self.config_path}")
                return self._get_default_config()
            
            # Carrega o arquivo
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            
            logger.info(f"Configuração carregada de {self.config_path}")
            return config
        
        except Exception as e:
            logger.error(f"Erro ao carregar configuração: {str(e)}")
            return self._get_default_config()
    
    def _get_default_config(self):
        """
        Retorna a configuração padrão.
        
        Returns:
            Dicionário com a configuração padrão
        """
        return {
            'DEBUG': True,
            'CHATWOOT_API_URL': os.environ.get('CHATWOOT_API_URL', ''),
            'CHATWOOT_API_ACCESS_TOKEN': os.environ.get('CHATWOOT_API_ACCESS_TOKEN', ''),
            'CHATWOOT_WEBHOOK_SECRET': os.environ.get('CHATWOOT_WEBHOOK_SECRET', ''),
            'MCP_CREW_API_URL': os.environ.get('MCP_CREW_API_URL', ''),
            'MCP_CREW_API_KEY': os.environ.get('MCP_CREW_API_KEY', ''),
            'MCP_CREW_DECISION_ENGINE_URL': os.environ.get('MCP_CREW_DECISION_ENGINE_URL', ''),
            'MAX_CONTEXT_MESSAGES': 10,
            'ROUTING_RULES': {
                'default_crew': 'suporte',
                'rules': []
            }
        }
    
    def get_config(self):
        """
        Obtém a configuração atual.
        
        Returns:
            Dicionário com a configuração
        """
        return self.config
    
    def update_config(self, new_config):
        """
        Atualiza a configuração.
        
        Args:
            new_config: Novos valores de configuração
            
        Returns:
            Boolean indicando sucesso ou falha
        """
        try:
            # Atualiza a configuração em memória
            self.config.update(new_config)
            
            # Salva a configuração no arquivo
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            
            logger.info(f"Configuração atualizada e salva em {self.config_path}")
            return True
        
        except Exception as e:
            logger.error(f"Erro ao atualizar configuração: {str(e)}")
            return False
    
    def get_value(self, key, default=None):
        """
        Obtém um valor específico da configuração.
        
        Args:
            key: Chave da configuração
            default: Valor padrão se a chave não existir
            
        Returns:
            Valor da configuração
        """
        return self.config.get(key, default)
    
    def set_value(self, key, value):
        """
        Define um valor específico na configuração.
        
        Args:
            key: Chave da configuração
            value: Novo valor
            
        Returns:
            Boolean indicando sucesso ou falha
        """
        try:
            # Atualiza o valor
            self.config[key] = value
            
            # Salva a configuração no arquivo
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            
            logger.info(f"Valor de configuração '{key}' atualizado")
            return True
        
        except Exception as e:
            logger.error(f"Erro ao definir valor de configuração: {str(e)}")
            return False
