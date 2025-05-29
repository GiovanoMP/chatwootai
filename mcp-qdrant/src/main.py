import logging
import os
import sys

from mcp_server_qdrant.mcp_server import QdrantMCPServer
from mcp_server_qdrant.settings import (
    EmbeddingProviderSettings,
    MultiTenantSettings,
    QdrantSettings,
    ToolSettings,
)

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)


def main():
    """
    Função principal para iniciar o servidor MCP-Qdrant.
    """
    logger.info("Iniciando MCP-Qdrant para ChatwootAI...")

    # Carrega configurações
    tool_settings = ToolSettings()
    qdrant_settings = QdrantSettings()
    embedding_provider_settings = EmbeddingProviderSettings()
    multi_tenant_settings = MultiTenantSettings()

    # Verifica configurações obrigatórias
    if not qdrant_settings.location and not qdrant_settings.local_path:
        logger.error(
            "Configuração inválida: QDRANT_URL ou QDRANT_LOCAL_PATH deve ser fornecido"
        )
        sys.exit(1)

    if qdrant_settings.location and qdrant_settings.local_path:
        logger.error(
            "Configuração inválida: Não é possível fornecer QDRANT_URL e QDRANT_LOCAL_PATH ao mesmo tempo"
        )
        sys.exit(1)

    # Cria e inicia o servidor MCP
    server = QdrantMCPServer(
        tool_settings=tool_settings,
        qdrant_settings=qdrant_settings,
        embedding_provider_settings=embedding_provider_settings,
        multi_tenant_settings=multi_tenant_settings,
        name="mcp-server-qdrant-chatwootai",
        instructions="Servidor MCP para Qdrant com suporte multi-tenant para o ChatwootAI",
    )

    # Obtém o transporte da variável de ambiente ou usa o padrão
    transport = os.environ.get("FASTMCP_TRANSPORT", "stdio")
    logger.info(f"Usando transporte: {transport}")

    # Inicia o servidor com o transporte especificado
    server.run(transport=transport)


if __name__ == "__main__":
    main()
