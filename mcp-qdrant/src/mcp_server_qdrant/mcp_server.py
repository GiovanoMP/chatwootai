import json
import logging
from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import Context, FastMCP

from mcp_server_qdrant.embeddings.factory import create_embedding_provider
from mcp_server_qdrant.qdrant import Entry, Metadata, QdrantConnector
from mcp_server_qdrant.settings import (
    EmbeddingProviderSettings,
    MultiTenantSettings,
    QdrantSettings,
    ToolSettings,
)

logger = logging.getLogger(__name__)


class QdrantMCPServer(FastMCP):
    """
    Servidor MCP para Qdrant com suporte multi-tenant para o ChatwootAI.
    """

    def __init__(
        self,
        tool_settings: ToolSettings,
        qdrant_settings: QdrantSettings,
        embedding_provider_settings: EmbeddingProviderSettings,
        multi_tenant_settings: MultiTenantSettings,
        name: str = "mcp-server-qdrant",
        instructions: str | None = None,
        **settings: Any,
    ):
        self.tool_settings = tool_settings
        self.qdrant_settings = qdrant_settings
        self.embedding_provider_settings = embedding_provider_settings
        self.multi_tenant_settings = multi_tenant_settings

        self.embedding_provider = create_embedding_provider(embedding_provider_settings)
        self.qdrant_connector = QdrantConnector(
            qdrant_settings.location,
            qdrant_settings.api_key,
            qdrant_settings.collection_name,
            self.embedding_provider,
            self.multi_tenant_settings,
            qdrant_settings.local_path,
        )

        super().__init__(name=name, instructions=instructions, **settings)

        self.setup_tools()

    def format_entry(self, entry: Entry) -> str:
        """
        Formata uma entrada para exibição.
        Sobrescreva este método em sua subclasse para personalizar o formato da entrada.
        """
        entry_metadata = json.dumps(entry.metadata) if entry.metadata else ""
        return f"<entry><content>{entry.content}</content><metadata>{entry_metadata}</metadata></entry>"

    def setup_tools(self):
        """
        Registra as ferramentas no servidor.
        """

        async def store(
            ctx: Context,
            information: str,
            collection_name: str,
            tenant_id: str = self.multi_tenant_settings.default_tenant,
            metadata: Metadata = None,  # type: ignore
        ) -> str:
            """
            Armazena informações no Qdrant.
            :param ctx: Contexto da requisição.
            :param information: Informação a ser armazenada.
            :param collection_name: Nome da coleção para armazenar a informação.
            :param tenant_id: ID do tenant. Se não fornecido, usa o tenant padrão.
            :param metadata: Metadados JSON opcionais para armazenar com a informação.
            :return: Mensagem indicando que a informação foi armazenada.
            """
            await ctx.debug(f"Armazenando informação {information} no Qdrant para tenant {tenant_id}")

            entry = Entry(content=information, metadata=metadata)

            try:
                await self.qdrant_connector.store(entry, collection_name, tenant_id)
                return f"Informação armazenada: {information} na coleção {collection_name} para tenant {tenant_id}"
            except ValueError as e:
                error_msg = f"Erro ao armazenar informação: {str(e)}"
                await ctx.debug(error_msg)
                return error_msg

        async def store_with_default_collection(
            ctx: Context,
            information: str,
            tenant_id: str = self.multi_tenant_settings.default_tenant,
            metadata: Metadata = None,  # type: ignore
        ) -> str:
            assert self.qdrant_settings.collection_name is not None
            return await store(
                ctx, information, self.qdrant_settings.collection_name, tenant_id, metadata
            )

        async def find(
            ctx: Context,
            query: str,
            collection_name: str,
            tenant_id: str = self.multi_tenant_settings.default_tenant,
        ) -> List[str]:
            """
            Busca memórias no Qdrant.
            :param ctx: Contexto da requisição.
            :param query: Consulta a ser usada para a busca.
            :param collection_name: Nome da coleção para buscar.
            :param tenant_id: ID do tenant. Se não fornecido, usa o tenant padrão.
            :return: Lista de entradas encontradas.
            """
            await ctx.debug(f"Buscando resultados para consulta {query} no tenant {tenant_id}")

            try:
                entries = await self.qdrant_connector.search(
                    query,
                    collection_name,
                    tenant_id,
                    limit=self.qdrant_settings.search_limit,
                )
                
                if not entries:
                    return [f"Nenhuma informação encontrada para a consulta '{query}' na coleção {collection_name}"]
                
                content = [
                    f"Resultados para a consulta '{query}' na coleção {collection_name}:",
                ]
                for entry in entries:
                    content.append(self.format_entry(entry))
                return content
            except ValueError as e:
                error_msg = f"Erro ao buscar informação: {str(e)}"
                await ctx.debug(error_msg)
                return [error_msg]

        async def find_with_default_collection(
            ctx: Context,
            query: str,
            tenant_id: str = self.multi_tenant_settings.default_tenant,
        ) -> List[str]:
            assert self.qdrant_settings.collection_name is not None
            return await find(ctx, query, self.qdrant_settings.collection_name, tenant_id)

        async def search_similar_products(
            ctx: Context,
            query: str,
            tenant_id: str = self.multi_tenant_settings.default_tenant,
            limit: int = 5,
        ) -> List[str]:
            """
            Busca produtos similares por descrição semântica.
            :param ctx: Contexto da requisição.
            :param query: Consulta a ser usada para a busca.
            :param tenant_id: ID do tenant. Se não fornecido, usa o tenant padrão.
            :param limit: Número máximo de produtos a retornar.
            :return: Lista de produtos encontrados.
            """
            await ctx.debug(f"Buscando produtos similares para: {query}")
            
            try:
                entries = await self.qdrant_connector.search(
                    query,
                    "products",
                    tenant_id,
                    limit=limit,
                )
                
                if not entries:
                    return [f"Nenhum produto similar encontrado para: '{query}'"]
                
                content = [
                    f"Produtos similares para: '{query}':",
                ]
                for entry in entries:
                    content.append(self.format_entry(entry))
                return content
            except ValueError as e:
                error_msg = f"Erro ao buscar produtos: {str(e)}"
                await ctx.debug(error_msg)
                return [error_msg]

        async def search_similar_rules(
            ctx: Context,
            query: str,
            tenant_id: str = self.multi_tenant_settings.default_tenant,
            limit: int = 5,
        ) -> List[str]:
            """
            Busca regras de negócio similares por descrição semântica.
            :param ctx: Contexto da requisição.
            :param query: Consulta a ser usada para a busca.
            :param tenant_id: ID do tenant. Se não fornecido, usa o tenant padrão.
            :param limit: Número máximo de regras a retornar.
            :return: Lista de regras encontradas.
            """
            await ctx.debug(f"Buscando regras de negócio similares para: {query}")
            
            try:
                entries = await self.qdrant_connector.search(
                    query,
                    "business_rules",
                    tenant_id,
                    limit=limit,
                )
                
                if not entries:
                    return [f"Nenhuma regra de negócio similar encontrada para: '{query}'"]
                
                content = [
                    f"Regras de negócio similares para: '{query}':",
                ]
                for entry in entries:
                    content.append(self.format_entry(entry))
                return content
            except ValueError as e:
                error_msg = f"Erro ao buscar regras de negócio: {str(e)}"
                await ctx.debug(error_msg)
                return [error_msg]

        async def list_collections(
            ctx: Context,
            tenant_id: str = self.multi_tenant_settings.default_tenant,
        ) -> List[str]:
            """
            Lista as coleções disponíveis para um tenant específico.
            :param ctx: Contexto da requisição.
            :param tenant_id: ID do tenant. Se não fornecido, usa o tenant padrão.
            :return: Lista de nomes de coleções.
            """
            await ctx.debug(f"Listando coleções para tenant {tenant_id}")
            
            try:
                collections = await self.qdrant_connector.get_collection_names(tenant_id)
                
                if not collections:
                    return [f"Nenhuma coleção encontrada para o tenant {tenant_id}"]
                
                content = [
                    f"Coleções disponíveis para o tenant {tenant_id}:",
                ]
                for collection in collections:
                    content.append(f"- {collection}")
                return content
            except Exception as e:
                error_msg = f"Erro ao listar coleções: {str(e)}"
                await ctx.debug(error_msg)
                return [error_msg]

        # Registra as ferramentas dependendo da configuração

        # Ferramenta de busca
        if self.qdrant_settings.collection_name:
            self.add_tool(
                find_with_default_collection,
                name="qdrant-find",
                description=self.tool_settings.tool_find_description,
            )
        else:
            self.add_tool(
                find,
                name="qdrant-find",
                description=self.tool_settings.tool_find_description,
            )

        # Ferramentas de armazenamento (se não for somente leitura)
        if not self.qdrant_settings.read_only:
            if self.qdrant_settings.collection_name:
                self.add_tool(
                    store_with_default_collection,
                    name="qdrant-store",
                    description=self.tool_settings.tool_store_description,
                )
            else:
                self.add_tool(
                    store,
                    name="qdrant-store",
                    description=self.tool_settings.tool_store_description,
                )

        # Ferramentas específicas do ChatwootAI
        self.add_tool(
            search_similar_products,
            name="searchSimilarProducts",
            description=self.tool_settings.tool_search_products_description,
        )
        
        self.add_tool(
            search_similar_rules,
            name="searchSimilarRules",
            description=self.tool_settings.tool_search_rules_description,
        )
        
        self.add_tool(
            list_collections,
            name="listCollections",
            description=self.tool_settings.tool_list_collections_description,
        )
