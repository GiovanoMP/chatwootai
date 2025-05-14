"""
Configurações do serviço de vetorização.
"""

from pydantic_settings import BaseSettings
from typing import Optional, Dict, Any, List

class Settings(BaseSettings):
    """Configurações do serviço de vetorização."""

    # Configurações gerais
    APP_NAME: str = "Vectorization Service"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # Configurações de API
    API_PREFIX: str = "/api/v1"
    API_KEY: str = "development-api-key"

    # Configurações do OpenAI
    OPENAI_API_KEY: str = ""
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    ENRICHMENT_MODEL: str = "gpt-4o-mini"

    # Limites de tokens
    MAX_EMBEDDING_TOKENS: int = 8192  # Limite para o modelo de embedding
    MAX_ENRICHMENT_TOKENS: int = 150  # Limite para enriquecimento
    MIN_DESCRIPTION_LENGTH: int = 100  # Tamanho mínimo para considerar enriquecimento

    # Configurações de chunking para documentos
    DOCUMENT_CHUNK_SIZE: int = 800  # Tamanho aproximado de cada chunk em caracteres
    DOCUMENT_CHUNK_OVERLAP: int = 150  # Sobreposição entre chunks em caracteres
    ENABLE_DOCUMENT_CHUNKING: bool = True  # Habilitar chunking de documentos

    # Configurações do Qdrant
    QDRANT_HOST: str = "qdrant"
    QDRANT_PORT: int = 6333
    QDRANT_API_KEY: Optional[str] = None
    EMBEDDING_DIMENSION: int = 1536  # Dimensão para o modelo text-embedding-3-small

    # Configurações do Redis
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None
    REDIS_DB: int = 0
    REDIS_CACHE_TTL: int = 3600  # 1 hora
    REDIS_METADATA_TTL: int = 86400  # 24 horas
    REDIS_SYNC_METADATA_TTL: int = 604800  # 7 dias

    # Configurações de retry
    RETRY_MAX_ATTEMPTS: int = 3
    RETRY_MIN_SECONDS: int = 1
    RETRY_MAX_SECONDS: int = 10

    # Timeout padrão
    TIMEOUT_DEFAULT: int = 30

    class Config:
        env_file = ".env"

settings = Settings()
