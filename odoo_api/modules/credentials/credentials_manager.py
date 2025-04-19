# -*- coding: utf-8 -*-

"""
Gerenciador de credenciais para o sistema AI.
"""

import os
import yaml
import logging
from typing import Dict, Any, Optional

from odoo_api.config.settings import settings
from odoo_api.core.exceptions import ValidationError

logger = logging.getLogger(__name__)

class CredentialsManager:
    """Gerenciador de credenciais para o sistema AI."""
    
    def __init__(self, domain: str, account_id: str):
        """
        Inicializa o gerenciador de credenciais.
        
        Args:
            domain: Domínio da conta
            account_id: ID da conta
        """
        self.domain = domain
        self.account_id = account_id
        self.config_file = os.path.join(
            settings.CONFIG_DIR, 
            "domains", 
            domain, 
            account_id, 
            "config.yaml"
        )
        
    def load_config(self) -> Dict[str, Any]:
        """
        Carrega a configuração do arquivo YAML.
        
        Returns:
            Configuração
        """
        if not os.path.exists(self.config_file):
            logger.warning(f"Configuration file {self.config_file} not found")
            return {}
            
        try:
            with open(self.config_file, "r") as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            return {}
            
    def save_config(self, config: Dict[str, Any]) -> bool:
        """
        Salva a configuração no arquivo YAML.
        
        Args:
            config: Configuração
            
        Returns:
            True se a operação for bem-sucedida
        """
        # Garantir que o diretório existe
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        
        try:
            with open(self.config_file, "w") as f:
                yaml.dump(config, f, default_flow_style=False)
            return True
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            return False
            
    def update_credential(self, section: str, key: str, value: str) -> bool:
        """
        Atualiza uma credencial específica.
        
        Args:
            section: Seção da credencial
            key: Chave da credencial
            value: Valor da credencial
            
        Returns:
            True se a operação for bem-sucedida
        """
        config = self.load_config()
        
        # Garantir que a seção credentials existe
        if "credentials" not in config:
            config["credentials"] = {}
            
        # Garantir que a subseção existe
        if section not in config["credentials"]:
            config["credentials"][section] = {}
            
        # Atualizar o valor
        config["credentials"][section][key] = value
        
        # Salvar a configuração
        return self.save_config(config)
        
    def get_credential(self, section: str, key: str) -> Optional[str]:
        """
        Obtém uma credencial específica.
        
        Args:
            section: Seção da credencial
            key: Chave da credencial
            
        Returns:
            Valor da credencial ou None se não encontrada
        """
        config = self.load_config()
        
        if "credentials" in config and section in config["credentials"] and key in config["credentials"][section]:
            return config["credentials"][section][key]
            
        return None
        
    def test_credential(self, section: str, key: str) -> bool:
        """
        Testa uma credencial específica.
        
        Args:
            section: Seção da credencial
            key: Chave da credencial
            
        Returns:
            True se a credencial for válida
        """
        value = self.get_credential(section, key)
        
        if not value:
            return False
            
        # Implementar testes específicos para cada tipo de credencial
        if section == "odoo":
            return self._test_odoo_credential(key, value)
        elif section == "social_media":
            return self._test_social_media_credential(key, value)
        elif section == "api_keys":
            return self._test_api_key(key, value)
            
        return True  # Assumir válido se não houver teste específico
        
    def _test_odoo_credential(self, key: str, value: str) -> bool:
        """
        Testa uma credencial do Odoo.
        
        Args:
            key: Chave da credencial
            value: Valor da credencial
            
        Returns:
            True se a credencial for válida
        """
        # TODO: Implementar teste de conexão com o Odoo
        return True
        
    def _test_social_media_credential(self, key: str, value: str) -> bool:
        """
        Testa uma credencial de rede social.
        
        Args:
            key: Chave da credencial
            value: Valor da credencial
            
        Returns:
            True se a credencial for válida
        """
        # TODO: Implementar teste de conexão com a rede social
        return True
        
    def _test_api_key(self, key: str, value: str) -> bool:
        """
        Testa uma chave de API.
        
        Args:
            key: Chave da credencial
            value: Valor da credencial
            
        Returns:
            True se a credencial for válida
        """
        # TODO: Implementar teste da chave de API
        return True
        
    def get_all_credentials(self) -> Dict[str, Dict[str, str]]:
        """
        Obtém todas as credenciais.
        
        Returns:
            Todas as credenciais
        """
        config = self.load_config()
        return config.get("credentials", {})
        
    def update_all_credentials(self, credentials: Dict[str, Dict[str, str]]) -> bool:
        """
        Atualiza todas as credenciais.
        
        Args:
            credentials: Todas as credenciais
            
        Returns:
            True se a operação for bem-sucedida
        """
        config = self.load_config()
        
        # Atualizar as credenciais
        config["credentials"] = credentials
        
        # Salvar a configuração
        return self.save_config(config)


# Função para obter o gerenciador de credenciais
def get_credentials_manager(domain: str, account_id: str) -> CredentialsManager:
    """
    Obtém o gerenciador de credenciais.
    
    Args:
        domain: Domínio da conta
        account_id: ID da conta
        
    Returns:
        Gerenciador de credenciais
    """
    return CredentialsManager(domain, account_id)
