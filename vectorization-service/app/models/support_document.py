"""
Modelos para documentos de suporte.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any

class SupportDocument(BaseModel):
    """Modelo para documento de suporte."""

    id: int
    name: str
    document_type: str
    content: str
    last_updated: str

class SupportDocumentSync(BaseModel):
    """Modelo para sincronização de documentos de suporte."""

    account_id: str
    business_rule_id: int
    documents: List[SupportDocument] = Field(default_factory=list)

class SupportDocumentResponse(BaseModel):
    """Modelo para resposta de sincronização de documentos de suporte."""

    success: bool
    data: Dict[str, Any]
    message: str

# Nota: As classes relacionadas a metadados da empresa foram removidas
# Os dados da empresa agora são enviados pelo MongoDB via outro módulo
