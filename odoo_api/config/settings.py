"""
Configurações da aplicação.

Este módulo define as configurações da aplicação, incluindo variáveis de ambiente,
configurações de serviços externos, etc.
"""

import os
from typing import Optional, Dict, Any, List
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    """Configurações da aplicação."""

    # Configurações gerais
    DEBUG: bool = Field(default=True, env="DEBUG")
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")

    # Configurações de API
    API_HOST: str = Field(default="0.0.0.0", env="API_HOST")
    API_PORT: int = Field(default=8000, env="API_PORT")
    API_PREFIX: str = Field(default="/api/v1", env="API_PREFIX")

    # Configurações de timeout
    TIMEOUT_DEFAULT: int = Field(default=30, env="TIMEOUT_DEFAULT")
    CACHE_TTL_DEFAULT: int = Field(default=86400, env="CACHE_TTL_DEFAULT")  # 24 horas

    # Configurações de retry
    RETRY_MAX_ATTEMPTS: int = Field(default=3, env="RETRY_MAX_ATTEMPTS")
    RETRY_MIN_SECONDS: int = Field(default=1, env="RETRY_MIN_SECONDS")
    RETRY_MAX_SECONDS: int = Field(default=10, env="RETRY_MAX_SECONDS")

    # Configurações de OpenAI
    OPENAI_API_KEY: str = Field(default="", env="OPENAI_API_KEY")
    OPENAI_MODEL: str = Field(default="gpt-4o-mini", env="OPENAI_MODEL")

    # Configurações de embedding
    EMBEDDING_MODEL: str = Field(default="text-embedding-3-small", env="EMBEDDING_MODEL")
    EMBEDDING_DIMENSION: int = Field(default=1536, env="EMBEDDING_DIMENSION")

    # Configurações de Qdrant
    QDRANT_HOST: str = Field(default="localhost", env="QDRANT_HOST")
    QDRANT_PORT: int = Field(default=6333, env="QDRANT_PORT")
    QDRANT_API_KEY: Optional[str] = Field(default=None, env="QDRANT_API_KEY")

    # Configurações de Redis
    REDIS_HOST: str = Field(default="localhost", env="REDIS_HOST")
    REDIS_PORT: int = Field(default=6379, env="REDIS_PORT")
    REDIS_DB: int = Field(default=0, env="REDIS_DB")
    REDIS_PASSWORD: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    REDIS_URL: Optional[str] = Field(default=None, env="REDIS_URL")

    # Configurações de diretórios
    CONFIG_DIR: str = Field(default="config", env="CONFIG_DIR")

    # Configurações de logging
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FORMAT: str = Field(default="%(asctime)s - %(name)s - %(levelname)s - %(message)s", env="LOG_FORMAT")

    # Configurações do Chatwoot
    CHATWOOT_API_KEY: Optional[str] = Field(default=None, env="CHATWOOT_API_KEY")
    CHATWOOT_BASE_URL: Optional[str] = Field(default=None, env="CHATWOOT_BASE_URL")
    CHATWOOT_ACCOUNT_ID: Optional[str] = Field(default=None, env="CHATWOOT_ACCOUNT_ID")

    # Configurações do Webhook
    WEBHOOK_PORT: Optional[int] = Field(default=None, env="WEBHOOK_PORT")
    WEBHOOK_HOST: Optional[str] = Field(default=None, env="WEBHOOK_HOST")
    WEBHOOK_DOMAIN: Optional[str] = Field(default=None, env="WEBHOOK_DOMAIN")
    WEBHOOK_USE_HTTPS: Optional[bool] = Field(default=None, env="WEBHOOK_USE_HTTPS")
    WEBHOOK_AUTH_TOKEN: Optional[str] = Field(default=None, env="WEBHOOK_AUTH_TOKEN")

    # Configurações do Servidor
    SERVER_PORT: Optional[int] = Field(default=None, env="SERVER_PORT")
    SERVER_HOST: Optional[str] = Field(default=None, env="SERVER_HOST")

    # Configurações do Ngrok
    NGROK_AUTH_TOKEN: Optional[str] = Field(default=None, env="NGROK_AUTH_TOKEN")

    class Config:
        """Configurações do Pydantic."""

        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "allow"  # Permite variáveis extras


# Instância global das configurações
settings = Settings()
