"""
Módulo para gerenciar múltiplas instâncias do Chatwoot enviando webhooks.

Este módulo implementa um sistema de roteamento que permite que o servidor webhook
processe eventos de diferentes instâncias do Chatwoot e os encaminhe para
os handlers apropriados.
"""

import os
import logging
from typing import Dict, Any, Optional
import json
from datetime import datetime

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class InstanceConfig:
    """
    Classe para armazenar a configuração de uma instância do Chatwoot.
    
    Attributes:
        instance_id: Identificador único da instância
        name: Nome amigável da instância
        api_key: Chave de API para autenticação com a instância
        base_url: URL base da API da instância
        account_id: ID da conta na instância
        webhook_token: Token de autenticação para o webhook
        created_at: Data de criação da configuração
        updated_at: Data da última atualização da configuração
    """
    
    def __init__(
        self,
        instance_id: str,
        name: str,
        api_key: str,
        base_url: str,
        account_id: int,
        webhook_token: str
    ):
        self.instance_id = instance_id
        self.name = name
        self.api_key = api_key
        self.base_url = base_url
        self.account_id = account_id
        self.webhook_token = webhook_token
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte a configuração para um dicionário."""
        return {
            "instance_id": self.instance_id,
            "name": self.name,
            "api_key": self.api_key,
            "base_url": self.base_url,
            "account_id": self.account_id,
            "webhook_token": self.webhook_token,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'InstanceConfig':
        """Cria uma instância a partir de um dicionário."""
        instance = cls(
            instance_id=data["instance_id"],
            name=data["name"],
            api_key=data["api_key"],
            base_url=data["base_url"],
            account_id=data["account_id"],
            webhook_token=data["webhook_token"]
        )
        instance.created_at = datetime.fromisoformat(data["created_at"])
        instance.updated_at = datetime.fromisoformat(data["updated_at"])
        return instance


class MultiInstanceManager:
    """
    Gerenciador de múltiplas instâncias do Chatwoot.
    
    Esta classe mantém um registro de todas as instâncias do Chatwoot configuradas
    e fornece métodos para autenticar e rotear webhooks para os handlers apropriados.
    """
    
    def __init__(self, config_file: str = None):
        """
        Inicializa o gerenciador de instâncias.
        
        Args:
            config_file: Caminho para o arquivo de configuração JSON (opcional)
        """
        self.instances: Dict[str, InstanceConfig] = {}
        self.token_to_instance: Dict[str, str] = {}
        self.config_file = config_file or os.path.join(
            os.path.dirname(__file__), '..', '..', 'config', 'instances.json'
        )
        
        # Carrega as configurações existentes
        self._load_config()
        
        # Se não houver configurações, cria uma configuração padrão
        if not self.instances:
            self._create_default_instance()
    
    def _load_config(self) -> None:
        """Carrega as configurações de instâncias do arquivo JSON."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    
                for instance_data in data.get("instances", []):
                    instance = InstanceConfig.from_dict(instance_data)
                    self.instances[instance.instance_id] = instance
                    self.token_to_instance[instance.webhook_token] = instance.instance_id
                
                logger.info(f"Carregadas {len(self.instances)} configurações de instâncias")
            else:
                logger.warning(f"Arquivo de configuração não encontrado: {self.config_file}")
        except Exception as e:
            logger.error(f"Erro ao carregar configurações: {e}")
    
    def _save_config(self) -> None:
        """Salva as configurações de instâncias no arquivo JSON."""
        try:
            # Cria o diretório se não existir
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            data = {
                "instances": [instance.to_dict() for instance in self.instances.values()]
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Configurações salvas em {self.config_file}")
        except Exception as e:
            logger.error(f"Erro ao salvar configurações: {e}")
    
    def _create_default_instance(self) -> None:
        """Cria uma configuração padrão baseada nas variáveis de ambiente."""
        try:
            instance = InstanceConfig(
                instance_id="default",
                name="Instância Padrão",
                api_key=os.getenv('CHATWOOT_API_KEY', ''),
                base_url=os.getenv('CHATWOOT_BASE_URL', ''),
                account_id=int(os.getenv('CHATWOOT_ACCOUNT_ID', '1')),
                webhook_token=os.getenv('WEBHOOK_AUTH_TOKEN', 'efetivia_webhook_secret_token_2025')
            )
            
            self.instances["default"] = instance
            self.token_to_instance[instance.webhook_token] = "default"
            
            # Salva a configuração
            self._save_config()
            
            logger.info("Criada configuração padrão baseada nas variáveis de ambiente")
        except Exception as e:
            logger.error(f"Erro ao criar configuração padrão: {e}")
    
    def add_instance(
        self,
        instance_id: str,
        name: str,
        api_key: str,
        base_url: str,
        account_id: int,
        webhook_token: str
    ) -> InstanceConfig:
        """
        Adiciona uma nova instância do Chatwoot.
        
        Args:
            instance_id: Identificador único da instância
            name: Nome amigável da instância
            api_key: Chave de API para autenticação com a instância
            base_url: URL base da API da instância
            account_id: ID da conta na instância
            webhook_token: Token de autenticação para o webhook
            
        Returns:
            A configuração da instância criada
        """
        instance = InstanceConfig(
            instance_id=instance_id,
            name=name,
            api_key=api_key,
            base_url=base_url,
            account_id=account_id,
            webhook_token=webhook_token
        )
        
        self.instances[instance_id] = instance
        self.token_to_instance[webhook_token] = instance_id
        
        # Salva a configuração
        self._save_config()
        
        logger.info(f"Adicionada nova instância: {instance_id} ({name})")
        return instance
    
    def remove_instance(self, instance_id: str) -> bool:
        """
        Remove uma instância do Chatwoot.
        
        Args:
            instance_id: Identificador da instância a ser removida
            
        Returns:
            True se a instância foi removida, False caso contrário
        """
        if instance_id in self.instances:
            instance = self.instances[instance_id]
            
            # Remove do mapeamento de tokens
            if instance.webhook_token in self.token_to_instance:
                del self.token_to_instance[instance.webhook_token]
            
            # Remove da lista de instâncias
            del self.instances[instance_id]
            
            # Salva a configuração
            self._save_config()
            
            logger.info(f"Removida instância: {instance_id}")
            return True
        
        logger.warning(f"Tentativa de remover instância inexistente: {instance_id}")
        return False
    
    def get_instance_by_token(self, token: str) -> Optional[InstanceConfig]:
        """
        Obtém a configuração de uma instância pelo token de autenticação.
        
        Args:
            token: Token de autenticação do webhook
            
        Returns:
            Configuração da instância ou None se não encontrada
        """
        instance_id = self.token_to_instance.get(token)
        if instance_id:
            return self.instances.get(instance_id)
        return None
    
    def get_instance_by_id(self, instance_id: str) -> Optional[InstanceConfig]:
        """
        Obtém a configuração de uma instância pelo ID.
        
        Args:
            instance_id: Identificador da instância
            
        Returns:
            Configuração da instância ou None se não encontrada
        """
        return self.instances.get(instance_id)
    
    def get_all_instances(self) -> Dict[str, InstanceConfig]:
        """
        Obtém todas as instâncias configuradas.
        
        Returns:
            Dicionário com todas as instâncias
        """
        return self.instances
    
    def authenticate_webhook(self, auth_header: str) -> Optional[InstanceConfig]:
        """
        Autentica uma requisição de webhook pelo cabeçalho de autorização.
        
        Args:
            auth_header: Cabeçalho de autorização (formato: "Bearer TOKEN")
            
        Returns:
            Configuração da instância se autenticada, None caso contrário
        """
        if not auth_header or not auth_header.startswith("Bearer "):
            return None
        
        token = auth_header.replace("Bearer ", "")
        return self.get_instance_by_token(token)
    
    def get_instance_count(self) -> int:
        """
        Obtém o número de instâncias configuradas.
        
        Returns:
            Número de instâncias
        """
        return len(self.instances)


# Instância global do gerenciador
_instance = None

def get_instance_manager() -> MultiInstanceManager:
    """
    Obtém a instância global do gerenciador de instâncias.
    
    Returns:
        Instância do MultiInstanceManager
    """
    global _instance
    if _instance is None:
        _instance = MultiInstanceManager()
    return _instance
