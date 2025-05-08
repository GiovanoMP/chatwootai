from sqlalchemy.orm import Session
from app.models.mapping import ChatwootMapping
from app.schemas.mapping import MappingCreate, MappingUpdate
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class MappingService:
    """
    Serviço para gerenciar mapeamentos entre Chatwoot e tenants.
    """

    def __init__(self, db: Session):
        """
        Inicializa o serviço com uma sessão do banco de dados.

        Args:
            db: Sessão do banco de dados
        """
        self.db = db

    def get_latest_mapping(self) -> Optional[ChatwootMapping]:
        """
        Obtém o mapeamento mais recente.

        Returns:
            Mapeamento mais recente ou None se não existir
        """
        return self.db.query(ChatwootMapping).order_by(ChatwootMapping.version.desc()).first()

    def get_latest_mapping_data(self) -> Optional[Dict[str, Any]]:
        """
        Obtém os dados do mapeamento mais recente.

        Returns:
            Dados do mapeamento ou None se não existir
        """
        mapping = self.get_latest_mapping()
        if mapping:
            return mapping.mapping_data
        return None

    def create_or_update_mapping(self, mapping_data: Dict[str, Any]) -> ChatwootMapping:
        """
        Cria ou atualiza o mapeamento.

        Args:
            mapping_data: Dados do mapeamento

        Returns:
            Mapeamento atualizado
        """
        # Obter a versão atual
        latest_mapping = self.get_latest_mapping()
        new_version = 1 if not latest_mapping else latest_mapping.version + 1

        # Criar novo registro
        new_mapping = ChatwootMapping(
            version=new_version,
            mapping_data=mapping_data
        )

        self.db.add(new_mapping)
        self.db.commit()
        self.db.refresh(new_mapping)

        logger.info(f"Mapeamento atualizado para versão {new_version}")

        return new_mapping

    def merge_mapping(self, partial_mapping: Dict[str, Any]) -> ChatwootMapping:
        """
        Mescla um mapeamento parcial com o existente.

        Args:
            partial_mapping: Dados parciais do mapeamento

        Returns:
            Mapeamento mesclado
        """
        current_mapping = self.get_latest_mapping_data() or {
            "accounts": {},
            "inboxes": {},
            "fallbacks": [],
            "special_numbers": []
        }

        # Mesclar accounts
        if "accounts" in partial_mapping:
            for account_id, account_data in partial_mapping["accounts"].items():
                current_mapping["accounts"][account_id] = account_data

        # Mesclar inboxes
        if "inboxes" in partial_mapping:
            for inbox_id, inbox_data in partial_mapping["inboxes"].items():
                current_mapping["inboxes"][inbox_id] = inbox_data

        # Atualizar fallbacks e special_numbers se fornecidos
        if "fallbacks" in partial_mapping:
            current_mapping["fallbacks"] = partial_mapping["fallbacks"]

        if "special_numbers" in partial_mapping:
            current_mapping["special_numbers"] = partial_mapping["special_numbers"]

        logger.info(f"Mesclando mapeamento parcial com o existente")

        # Salvar o mapeamento mesclado
        return self.create_or_update_mapping(current_mapping)

# Funções de compatibilidade para código existente
def get_latest_mapping(db: Session) -> Optional[Dict[str, Any]]:
    """
    Obtém o mapeamento mais recente.

    Args:
        db: Sessão do banco de dados

    Returns:
        Dados do mapeamento ou None se não existir
    """
    service = MappingService(db)
    return service.get_latest_mapping_data()

def create_or_update_mapping(db: Session, mapping_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Cria ou atualiza o mapeamento.

    Args:
        db: Sessão do banco de dados
        mapping_data: Dados do mapeamento

    Returns:
        Dados do mapeamento atualizado
    """
    service = MappingService(db)
    mapping = service.create_or_update_mapping(mapping_data)
    return mapping.mapping_data

def merge_mapping(db: Session, partial_mapping: Dict[str, Any]) -> Dict[str, Any]:
    """
    Mescla um mapeamento parcial com o existente.

    Args:
        db: Sessão do banco de dados
        partial_mapping: Dados parciais do mapeamento

    Returns:
        Dados do mapeamento mesclado
    """
    service = MappingService(db)
    mapping = service.merge_mapping(partial_mapping)
    return mapping.mapping_data
