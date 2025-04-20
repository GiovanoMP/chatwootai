"""
Arquivo de compatibilidade para o agente de embedding de regras de negócio.

Este arquivo importa o agente do novo local para manter a compatibilidade
com o código existente.
"""

import logging
from odoo_api.embedding_agents.business_rules.rules_agent import get_business_rules_agent, BusinessRulesEmbeddingAgent

logger = logging.getLogger(__name__)

# Aviso de depreciação
logger.warning(
    "O módulo 'odoo_api.embedding_agents.business_rules_agent' está depreciado. "
    "Use 'odoo_api.embedding_agents.business_rules.rules_agent' em seu lugar."
)

# Agora importamos a implementação do novo local
