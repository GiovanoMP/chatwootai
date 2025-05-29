import logging
import uuid
from typing import Any, Dict, List, Optional

from pydantic import BaseModel
from qdrant_client import AsyncQdrantClient, models

from mcp_server_qdrant.embeddings.base import EmbeddingProvider
from mcp_server_qdrant.settings import MultiTenantSettings

logger = logging.getLogger(__name__)

Metadata = Dict[str, Any]


class Entry(BaseModel):
    """
    Uma entrada única na coleção Qdrant.
    """

    content: str
    metadata: Optional[Metadata] = None


class QdrantConnector:
    """
    Encapsula a conexão com um servidor Qdrant e todos os métodos para interagir com ele.
    Implementa suporte multi-tenant prefixando os nomes das coleções com o ID do tenant.
    
    :param qdrant_url: URL do servidor Qdrant.
    :param qdrant_api_key: Chave de API para o servidor Qdrant.
    :param collection_name: Nome da coleção padrão a ser usada. Se não fornecido, cada ferramenta
                           exigirá que o nome da coleção seja fornecido.
    :param embedding_provider: Provedor de embeddings a ser usado.
    :param qdrant_local_path: Caminho para o diretório de armazenamento do cliente Qdrant, se o modo local for usado.
    :param multi_tenant_settings: Configurações para suporte multi-tenant.
    """

    def __init__(
        self,
        qdrant_url: Optional[str],
        qdrant_api_key: Optional[str],
        collection_name: Optional[str],
        embedding_provider: EmbeddingProvider,
        multi_tenant_settings: MultiTenantSettings,
        qdrant_local_path: Optional[str] = None,
    ):
        self._qdrant_url = qdrant_url.rstrip("/") if qdrant_url else None
        self._qdrant_api_key = qdrant_api_key
        self._default_collection_name = collection_name
        self._embedding_provider = embedding_provider
        self._multi_tenant_settings = multi_tenant_settings
        self._client = AsyncQdrantClient(
            location=qdrant_url, api_key=qdrant_api_key, path=qdrant_local_path
        )
        
        logger.info(f"Inicializado QdrantConnector com multi-tenant: {multi_tenant_settings.enabled}")
        if multi_tenant_settings.enabled:
            logger.info(f"Tenant padrão: {multi_tenant_settings.default_tenant}")
            logger.info(f"Coleções permitidas: {multi_tenant_settings.allowed_collections}")

    def _get_tenant_collection_name(self, collection_name: str, tenant_id: Optional[str] = None) -> str:
        """
        Obtém o nome da coleção prefixado com o ID do tenant, se o modo multi-tenant estiver ativado.
        :param collection_name: Nome base da coleção.
        :param tenant_id: ID do tenant. Se não fornecido, usa o tenant padrão.
        :return: Nome da coleção prefixado com o ID do tenant.
        """
        if not self._multi_tenant_settings.enabled:
            return collection_name
            
        tenant = tenant_id or self._multi_tenant_settings.default_tenant
        return f"{tenant}_{collection_name}"

    def _validate_collection(self, collection_name: str) -> bool:
        """
        Valida se a coleção está na lista de coleções permitidas.
        :param collection_name: Nome da coleção a ser validada.
        :return: True se a coleção for válida, False caso contrário.
        """
        # Extrai o nome base da coleção (sem o prefixo do tenant)
        if self._multi_tenant_settings.enabled and "_" in collection_name:
            base_collection = collection_name.split("_", 1)[1]
        else:
            base_collection = collection_name
            
        return base_collection in self._multi_tenant_settings.allowed_collections

    async def get_collection_names(self, tenant_id: Optional[str] = None) -> List[str]:
        """
        Obtém os nomes de todas as coleções no servidor Qdrant para um tenant específico.
        :param tenant_id: ID do tenant. Se não fornecido, usa o tenant padrão.
        :return: Lista de nomes de coleções.
        """
        response = await self._client.get_collections()
        
        if not self._multi_tenant_settings.enabled:
            return [collection.name for collection in response.collections]
            
        tenant = tenant_id or self._multi_tenant_settings.default_tenant
        prefix = f"{tenant}_"
        
        return [
            collection.name 
            for collection in response.collections 
            if collection.name.startswith(prefix)
        ]

    async def store(
        self, 
        entry: Entry, 
        collection_name: str, 
        tenant_id: Optional[str] = None
    ):
        """
        Armazena informações na coleção Qdrant, junto com os metadados especificados.
        :param entry: Entrada a ser armazenada na coleção Qdrant.
        :param collection_name: Nome da coleção para armazenar as informações.
        :param tenant_id: ID do tenant. Se não fornecido, usa o tenant padrão.
        """
        # Valida a coleção
        if not self._validate_collection(collection_name):
            raise ValueError(f"Coleção não permitida: {collection_name}")
            
        # Prefixo do tenant
        full_collection_name = self._get_tenant_collection_name(collection_name, tenant_id)
        
        logger.info(f"Armazenando em {full_collection_name}: {entry.content[:50]}...")
        await self._ensure_collection_exists(full_collection_name)

        # Gera o embedding do documento
        embeddings = await self._embedding_provider.embed_documents([entry.content])

        # Adiciona ao Qdrant
        vector_name = self._embedding_provider.get_vector_name()
        payload = {"document": entry.content, "metadata": entry.metadata}
        await self._client.upsert(
            collection_name=full_collection_name,
            points=[
                models.PointStruct(
                    id=uuid.uuid4().hex,
                    vector={vector_name: embeddings[0]},
                    payload=payload,
                )
            ],
        )

    async def search(
        self, 
        query: str, 
        collection_name: str, 
        tenant_id: Optional[str] = None, 
        limit: int = 20
    ) -> List[Entry]:
        """
        Encontra pontos na coleção Qdrant. Se não houver entradas encontradas, uma lista vazia é retornada.
        :param query: Consulta a ser usada para a busca.
        :param collection_name: Nome da coleção para buscar.
        :param tenant_id: ID do tenant. Se não fornecido, usa o tenant padrão.
        :param limit: Número máximo de entradas a retornar.
        :return: Lista de entradas encontradas.
        """
        # Valida a coleção
        if not self._validate_collection(collection_name):
            raise ValueError(f"Coleção não permitida: {collection_name}")
            
        # Prefixo do tenant
        full_collection_name = self._get_tenant_collection_name(collection_name, tenant_id)
        
        logger.info(f"Buscando em {full_collection_name}: {query}")
        
        collection_exists = await self._client.collection_exists(full_collection_name)
        if not collection_exists:
            logger.warning(f"Coleção {full_collection_name} não existe")
            return []

        # Gera o embedding da consulta
        query_vector = await self._embedding_provider.embed_query(query)
        vector_name = self._embedding_provider.get_vector_name()

        # Busca no Qdrant
        search_results = await self._client.query_points(
            collection_name=full_collection_name,
            query=query_vector,
            using=vector_name,
            limit=limit,
        )

        return [
            Entry(
                content=result.payload["document"],
                metadata=result.payload.get("metadata"),
            )
            for result in search_results.points
        ]

    async def _ensure_collection_exists(self, collection_name: str):
        """
        Garante que a coleção exista, criando-a se necessário.
        :param collection_name: Nome da coleção a garantir que exista.
        """
        collection_exists = await self._client.collection_exists(collection_name)
        if not collection_exists:
            logger.info(f"Criando coleção {collection_name}")
            # Cria a coleção com o tamanho de vetor apropriado
            vector_size = self._embedding_provider.get_vector_size()

            # Usa o nome do vetor conforme definido no provedor de embeddings
            vector_name = self._embedding_provider.get_vector_name()
            await self._client.create_collection(
                collection_name=collection_name,
                vectors_config={
                    vector_name: models.VectorParams(
                        size=vector_size,
                        distance=models.Distance.COSINE,
                    )
                },
            )
