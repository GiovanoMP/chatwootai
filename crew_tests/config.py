"""
Configurações para os testes de integração do CrewAI com Qdrant.
"""

import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configurações do Qdrant
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
QDRANT_URL = f"http://{QDRANT_HOST}:{QDRANT_PORT}"
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")

# Configurações do OpenAI (para embeddings e LLM)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Configurações padrão
DEFAULT_ACCOUNT_ID = "account_1"
DEFAULT_COLLECTION_PREFIX = "crew_test"

# Coleções do Qdrant
COLLECTIONS = {
    "business_rules": f"{DEFAULT_COLLECTION_PREFIX}_business_rules",
    "company_metadata": f"{DEFAULT_COLLECTION_PREFIX}_company_metadata",
    "support_documents": f"{DEFAULT_COLLECTION_PREFIX}_support_documents",
    "memory_short_term": f"{DEFAULT_COLLECTION_PREFIX}_memory_short_term",
    "memory_entity": f"{DEFAULT_COLLECTION_PREFIX}_memory_entity"
}

# Configurações de memória
MEMORY_ENABLED = True

# Configurações de embedding
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSION = 1536  # Dimensão para o modelo text-embedding-3-small

# Configurações de LLM
LLM_MODEL = "gpt-4o-mini"
