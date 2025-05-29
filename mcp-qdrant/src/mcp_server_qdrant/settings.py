from typing import Optional, List

from pydantic import Field
from pydantic_settings import BaseSettings

from mcp_server_qdrant.embeddings.types import EmbeddingProviderType

DEFAULT_TOOL_STORE_DESCRIPTION = (
    "Armazena informações no banco de dados vetorial Qdrant para uso posterior."
)
DEFAULT_TOOL_FIND_DESCRIPTION = (
    "Busca informações no banco de dados vetorial Qdrant. Use esta ferramenta quando precisar: \n"
    " - Encontrar informações por conteúdo semântico \n"
    " - Acessar dados para análise adicional \n"
    " - Obter informações específicas sobre produtos, regras ou procedimentos"
)
DEFAULT_TOOL_SEARCH_PRODUCTS_DESCRIPTION = (
    "Busca produtos similares por descrição semântica. Use esta ferramenta quando precisar: \n"
    " - Encontrar produtos com características similares \n"
    " - Recomendar produtos alternativos \n"
    " - Obter informações detalhadas sobre produtos específicos"
)
DEFAULT_TOOL_SEARCH_RULES_DESCRIPTION = (
    "Busca regras de negócio similares por descrição semântica. Use esta ferramenta quando precisar: \n"
    " - Encontrar regras de negócio aplicáveis a uma situação \n"
    " - Verificar políticas da empresa sobre determinado assunto \n"
    " - Obter orientações sobre procedimentos específicos"
)
DEFAULT_TOOL_LIST_COLLECTIONS_DESCRIPTION = (
    "Lista as coleções vetoriais disponíveis para um tenant específico."
)


class ToolSettings(BaseSettings):
    """
    Configuração para todas as ferramentas.
    """

    tool_store_description: str = Field(
        default=DEFAULT_TOOL_STORE_DESCRIPTION,
        validation_alias="TOOL_STORE_DESCRIPTION",
    )
    tool_find_description: str = Field(
        default=DEFAULT_TOOL_FIND_DESCRIPTION,
        validation_alias="TOOL_FIND_DESCRIPTION",
    )
    tool_search_products_description: str = Field(
        default=DEFAULT_TOOL_SEARCH_PRODUCTS_DESCRIPTION,
        validation_alias="TOOL_SEARCH_PRODUCTS_DESCRIPTION",
    )
    tool_search_rules_description: str = Field(
        default=DEFAULT_TOOL_SEARCH_RULES_DESCRIPTION,
        validation_alias="TOOL_SEARCH_RULES_DESCRIPTION",
    )
    tool_list_collections_description: str = Field(
        default=DEFAULT_TOOL_LIST_COLLECTIONS_DESCRIPTION,
        validation_alias="TOOL_LIST_COLLECTIONS_DESCRIPTION",
    )


class EmbeddingProviderSettings(BaseSettings):
    """
    Configuração para o provedor de embeddings.
    """

    provider_type: EmbeddingProviderType = Field(
        default=EmbeddingProviderType.FASTEMBED,
        validation_alias="EMBEDDING_PROVIDER",
    )
    model_name: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        validation_alias="EMBEDDING_MODEL",
    )


class MultiTenantSettings(BaseSettings):
    """
    Configuração para suporte multi-tenant.
    """

    enabled: bool = Field(default=True, validation_alias="MULTI_TENANT")
    default_tenant: str = Field(default="account_1", validation_alias="DEFAULT_TENANT")
    allowed_collections: List[str] = Field(
        default=["products", "business_rules", "support_procedures", "interactions"],
        validation_alias="ALLOWED_COLLECTIONS",
    )


class QdrantSettings(BaseSettings):
    """
    Configuração para o conector Qdrant.
    """

    location: Optional[str] = Field(default=None, validation_alias="QDRANT_URL")
    api_key: Optional[str] = Field(default=None, validation_alias="QDRANT_API_KEY")
    collection_name: Optional[str] = Field(
        default=None, validation_alias="COLLECTION_NAME"
    )
    local_path: Optional[str] = Field(
        default=None, validation_alias="QDRANT_LOCAL_PATH"
    )
    search_limit: int = Field(default=20, validation_alias="QDRANT_SEARCH_LIMIT")
    read_only: bool = Field(default=False, validation_alias="QDRANT_READ_ONLY")
