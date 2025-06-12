from typing import Optional
from pymongo import MongoClient
from common.config import MONGODB_URI, MONGODB_DB
from common.models import TenantConfig

class TenantManager:
    def __init__(self):
        self.client = MongoClient(MONGODB_URI)
        self.db = self.client[MONGODB_DB]
        self.collection = self.db['tenant_configs']

    def get_tenant_config(self, account_id: int) -> Optional[TenantConfig]:
        """Obtém configuração do tenant pelo account_id."""
        config = self.collection.find_one({'account_id': account_id})
        if config:
            return TenantConfig(**config)
        return None

    def validate_tenant_access(self, account_id: int, inbox_id: int) -> bool:
        """
        Valida acesso do tenant:
        1. Verifica se o tenant existe e está ativo
        2. Verifica se a inbox está autorizada
        """
        config = self.get_tenant_config(account_id)
        if not config or not config.is_active:
            return False
            
        # Se não há inboxes especificadas, permite todas
        if not config.allowed_inboxes:
            return True
            
        return inbox_id in config.allowed_inboxes

    def create_tenant(self, config: TenantConfig) -> bool:
        """Cria ou atualiza configuração do tenant."""
        try:
            self.collection.update_one(
                {'account_id': config.account_id},
                {'$set': config.dict()},
                upsert=True
            )
            return True
        except Exception:
            return False
