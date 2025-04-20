"""
Arquivo de compatibilidade para o agente de embedding de metadados da empresa.

Este arquivo importa o agente do novo local para manter a compatibilidade
com o código existente.
"""

import logging
from odoo_api.embedding_agents.business_rules.company_metadata_agent import get_company_metadata_agent, CompanyMetadataEmbeddingAgent

logger = logging.getLogger(__name__)

# Aviso de depreciação
logger.warning(
    "O módulo 'odoo_api.embedding_agents.company_metadata_agent' está depreciado. "
    "Use 'odoo_api.embedding_agents.business_rules.company_metadata_agent' em seu lugar."
)
