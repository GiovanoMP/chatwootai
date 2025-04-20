"""
Arquivo de compatibilidade para o agente de embedding de documentos de suporte.

Este arquivo importa o agente do novo local para manter a compatibilidade
com o código existente.
"""

import logging
from odoo_api.embedding_agents.business_rules.support_docs_agent import get_support_document_agent, SupportDocumentEmbeddingAgent

logger = logging.getLogger(__name__)

# Aviso de depreciação
logger.warning(
    "O módulo 'odoo_api.embedding_agents.support_document_agent' está depreciado. "
    "Use 'odoo_api.embedding_agents.business_rules.support_docs_agent' em seu lugar."
)
