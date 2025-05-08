import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

class Settings(BaseSettings):
    """Configurações da aplicação"""

    # Configurações do banco de dados
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/config_service")

    # Configurações da API
    API_KEY: str = os.getenv("API_KEY", "development-api-key")
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    # Configurações do servidor
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))

    # Configurações da aplicação
    APP_NAME: str = "Config Service API"
    APP_DESCRIPTION: str = "API para gerenciamento de configurações"
    APP_VERSION: str = "1.0.0"

    model_config = {
        "env_file": ".env",
        "extra": "ignore"
    }

# Instância global das configurações
settings = Settings()
