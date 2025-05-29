from enum import Enum, auto


class EmbeddingProviderType(str, Enum):
    """
    Tipos de provedores de embeddings suportados.
    """

    FASTEMBED = "fastembed"
