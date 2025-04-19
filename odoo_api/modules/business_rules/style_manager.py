# -*- coding: utf-8 -*-

"""
Gerenciador de estilo para a crew de atendimento ao cliente.
"""

import os
import yaml
import logging
from typing import Dict, Any, Optional

from odoo_api.config.settings import settings
from odoo_api.core.exceptions import ValidationError

logger = logging.getLogger(__name__)

class CustomerServiceStyleManager:
    """Gerenciador de estilo para a crew de atendimento ao cliente."""
    
    def __init__(self, domain: str, account_id: str):
        """
        Inicializa o gerenciador de estilo.
        
        Args:
            domain: Domínio da conta
            account_id: ID da conta
        """
        self.domain = domain
        self.account_id = account_id
        self.crew_config_file = os.path.join(
            settings.CONFIG_DIR, 
            "domains", 
            domain, 
            account_id, 
            "crews", 
            "customer_service", 
            "config.yaml"
        )
        
    def load_config(self) -> Dict[str, Any]:
        """
        Carrega a configuração da crew.
        
        Returns:
            Configuração da crew
        """
        if not os.path.exists(self.crew_config_file):
            logger.warning(f"Crew configuration file {self.crew_config_file} not found")
            return {}
            
        try:
            with open(self.crew_config_file, "r") as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            logger.error(f"Failed to load crew configuration: {e}")
            return {}
            
    def save_config(self, config: Dict[str, Any]) -> bool:
        """
        Salva a configuração da crew.
        
        Args:
            config: Configuração da crew
            
        Returns:
            True se a operação for bem-sucedida
        """
        # Garantir que o diretório existe
        os.makedirs(os.path.dirname(self.crew_config_file), exist_ok=True)
        
        try:
            with open(self.crew_config_file, "w") as f:
                yaml.dump(config, f, default_flow_style=False)
            return True
        except Exception as e:
            logger.error(f"Failed to save crew configuration: {e}")
            return False
            
    def update_style(self, style_config: Dict[str, Any]) -> bool:
        """
        Atualiza as configurações de estilo da crew.
        
        Args:
            style_config: Configurações de estilo
            
        Returns:
            True se a operação for bem-sucedida
        """
        config = self.load_config()
        
        # Atualizar a seção de estilo
        config["style"] = style_config
        
        # Salvar a configuração
        return self.save_config(config)
        
    def get_style(self) -> Dict[str, Any]:
        """
        Obtém as configurações de estilo da crew.
        
        Returns:
            Configurações de estilo
        """
        config = self.load_config()
        return config.get("style", {})
        
    def update_greeting(self, greeting_enabled: bool, greeting_message: str) -> bool:
        """
        Atualiza a saudação da crew.
        
        Args:
            greeting_enabled: Se a saudação está habilitada
            greeting_message: Mensagem de saudação
            
        Returns:
            True se a operação for bem-sucedida
        """
        config = self.load_config()
        
        # Garantir que a seção de estilo existe
        if "style" not in config:
            config["style"] = {}
            
        # Garantir que a seção de saudação existe
        if "greeting" not in config["style"]:
            config["style"]["greeting"] = {}
            
        # Atualizar a saudação
        config["style"]["greeting"]["enabled"] = greeting_enabled
        config["style"]["greeting"]["message"] = greeting_message
        
        # Salvar a configuração
        return self.save_config(config)
        
    def update_farewell(self, farewell_enabled: bool, farewell_message: str) -> bool:
        """
        Atualiza a despedida da crew.
        
        Args:
            farewell_enabled: Se a despedida está habilitada
            farewell_message: Mensagem de despedida
            
        Returns:
            True se a operação for bem-sucedida
        """
        config = self.load_config()
        
        # Garantir que a seção de estilo existe
        if "style" not in config:
            config["style"] = {}
            
        # Garantir que a seção de despedida existe
        if "farewell" not in config["style"]:
            config["style"]["farewell"] = {}
            
        # Atualizar a despedida
        config["style"]["farewell"]["enabled"] = farewell_enabled
        config["style"]["farewell"]["message"] = farewell_message
        
        # Salvar a configuração
        return self.save_config(config)
        
    def update_emojis(self, emojis_enabled: bool, emojis_frequency: str) -> bool:
        """
        Atualiza o uso de emojis da crew.
        
        Args:
            emojis_enabled: Se o uso de emojis está habilitado
            emojis_frequency: Frequência de uso de emojis (none, minimal, moderate, frequent)
            
        Returns:
            True se a operação for bem-sucedida
        """
        # Validar a frequência
        valid_frequencies = ["none", "minimal", "moderate", "frequent"]
        if emojis_frequency not in valid_frequencies:
            raise ValidationError(f"Invalid emoji frequency: {emojis_frequency}. Valid values are: {', '.join(valid_frequencies)}")
            
        config = self.load_config()
        
        # Garantir que a seção de estilo existe
        if "style" not in config:
            config["style"] = {}
            
        # Garantir que a seção de emojis existe
        if "emojis" not in config["style"]:
            config["style"]["emojis"] = {}
            
        # Atualizar os emojis
        config["style"]["emojis"]["enabled"] = emojis_enabled
        config["style"]["emojis"]["frequency"] = emojis_frequency
        
        # Salvar a configuração
        return self.save_config(config)
        
    def update_tone(self, formal: int, friendly: int, technical: int) -> bool:
        """
        Atualiza o tom da crew.
        
        Args:
            formal: Nível de formalidade (1-5)
            friendly: Nível de amigabilidade (1-5)
            technical: Nível técnico (1-5)
            
        Returns:
            True se a operação for bem-sucedida
        """
        # Validar os níveis
        for name, value in [("formal", formal), ("friendly", friendly), ("technical", technical)]:
            if not 1 <= value <= 5:
                raise ValidationError(f"Invalid {name} level: {value}. Valid values are 1-5")
                
        config = self.load_config()
        
        # Garantir que a seção de estilo existe
        if "style" not in config:
            config["style"] = {}
            
        # Garantir que a seção de tom existe
        if "tone" not in config["style"]:
            config["style"]["tone"] = {}
            
        # Atualizar o tom
        config["style"]["tone"]["formal"] = formal
        config["style"]["tone"]["friendly"] = friendly
        config["style"]["tone"]["technical"] = technical
        
        # Salvar a configuração
        return self.save_config(config)
        
    def get_greeting(self) -> Dict[str, Any]:
        """
        Obtém a configuração de saudação.
        
        Returns:
            Configuração de saudação
        """
        style = self.get_style()
        return style.get("greeting", {"enabled": False, "message": ""})
        
    def get_farewell(self) -> Dict[str, Any]:
        """
        Obtém a configuração de despedida.
        
        Returns:
            Configuração de despedida
        """
        style = self.get_style()
        return style.get("farewell", {"enabled": False, "message": ""})
        
    def get_emojis(self) -> Dict[str, Any]:
        """
        Obtém a configuração de emojis.
        
        Returns:
            Configuração de emojis
        """
        style = self.get_style()
        return style.get("emojis", {"enabled": False, "frequency": "none"})
        
    def get_tone(self) -> Dict[str, Any]:
        """
        Obtém a configuração de tom.
        
        Returns:
            Configuração de tom
        """
        style = self.get_style()
        return style.get("tone", {"formal": 3, "friendly": 3, "technical": 3})


# Função para obter o gerenciador de estilo
def get_customer_service_style_manager(domain: str, account_id: str) -> CustomerServiceStyleManager:
    """
    Obtém o gerenciador de estilo para a crew de atendimento ao cliente.
    
    Args:
        domain: Domínio da conta
        account_id: ID da conta
        
    Returns:
        Gerenciador de estilo
    """
    return CustomerServiceStyleManager(domain, account_id)
