import logging

from mcp_server_qdrant.embeddings.base import EmbeddingProvider
from mcp_server_qdrant.embeddings.fastembed import FastEmbedProvider
from mcp_server_qdrant.embeddings.types import EmbeddingProviderType
from mcp_server_qdrant.settings import EmbeddingProviderSettings

logger = logging.getLogger(__name__)


def create_embedding_provider(settings: EmbeddingProviderSettings) -> EmbeddingProvider:
    """
    Cria um provedor de embeddings com base nas configurações.
    :param settings: Configurações do provedor de embeddings.
    :return: Provedor de embeddings.
    """
    if settings.provider_type == EmbeddingProviderType.FASTEMBED:
        logger.info(f"Criando provedor FastEmbed com modelo {settings.model_name}")
        return FastEmbedProvider(settings.model_name)
    else:
        raise ValueError(f"Provedor de embeddings não suportado: {settings.provider_type}")
