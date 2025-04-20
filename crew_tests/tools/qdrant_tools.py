"""
Ferramentas personalizadas para integração com Qdrant.
"""

import os
from typing import Dict, List, Any, Optional, Callable, Type
from pydantic import BaseModel, Field
from langchain.tools import BaseTool
from qdrant_client import QdrantClient
from qdrant_client.http import models
from openai import OpenAI

from ..config import QDRANT_URL, QDRANT_API_KEY, OPENAI_API_KEY, EMBEDDING_MODEL


class QdrantMultiTenantSearchInput(BaseModel):
    """Modelo de entrada para a ferramenta de busca vetorial multi-tenant."""

    query: str = Field(description="A consulta do usuário")
    account_id: str = Field(description="ID da conta do cliente")
    collection_name: str = Field(description="Nome da coleção no Qdrant (business_rules, company_metadata, support_documents)")
    limit: int = Field(default=5, description="Número máximo de resultados")
    score_threshold: float = Field(default=0.35, description="Limiar mínimo de similaridade")


class QdrantMultiTenantSearchTool(BaseTool):
    """
    Ferramenta de busca vetorial multi-tenant para Qdrant.

    Esta ferramenta permite buscar informações em diferentes coleções do Qdrant
    para diferentes contas de cliente.
    """

    name: str = "qdrant_multi_tenant_search"
    description: str = """
    Busca informações no banco de dados vetorial Qdrant para uma conta específica.
    Use esta ferramenta para encontrar regras de negócio, documentos de suporte ou metadados da empresa.

    Parâmetros:
    - query: A consulta do usuário
    - account_id: ID da conta do cliente
    - collection_name: Nome da coleção no Qdrant (business_rules, company_metadata, support_documents)
    - limit: Número máximo de resultados (padrão: 5)
    - score_threshold: Limiar mínimo de similaridade (padrão: 0.35)
    """

    args_schema: Type[BaseModel] = QdrantMultiTenantSearchInput

    # Atributos adicionais
    qdrant_url: str = None
    qdrant_api_key: str = None
    qdrant_client: Any = None
    openai_client: Any = None
    embedding_fn: Callable = None

    def __init__(
        self,
        qdrant_url: Optional[str] = None,
        qdrant_api_key: Optional[str] = None,
        custom_embedding_fn: Optional[Callable[[str], List[float]]] = None
    ):
        """
        Inicializa a ferramenta de busca vetorial multi-tenant.

        Args:
            qdrant_url: URL do servidor Qdrant
            qdrant_api_key: Chave API do Qdrant
            custom_embedding_fn: Função personalizada para gerar embeddings
        """
        super().__init__()

        self.qdrant_url = qdrant_url or QDRANT_URL
        self.qdrant_api_key = qdrant_api_key or QDRANT_API_KEY

        if not self.qdrant_url:
            raise ValueError("QDRANT_URL não está definido")

        # Inicializar cliente Qdrant
        self.qdrant_client = QdrantClient(
            url=self.qdrant_url,
            api_key=self.qdrant_api_key
        )

        # Inicializar cliente OpenAI para embeddings
        self.openai_client = OpenAI(api_key=OPENAI_API_KEY)

        # Função de embedding personalizada ou padrão
        self.embedding_fn = custom_embedding_fn or self._default_embedding_fn

    def _default_embedding_fn(self, text: str) -> List[float]:
        """
        Gera embeddings usando o modelo padrão do OpenAI.

        Args:
            text: Texto para gerar embedding

        Returns:
            Lista de floats representando o embedding
        """
        response = self.openai_client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=text
        )
        return response.data[0].embedding

    def _run(
        self,
        query: str,
        account_id: str,
        collection_name: str,
        limit: int = 5,
        score_threshold: float = 0.35
    ) -> List[Dict[str, Any]]:
        """
        Executa a busca no Qdrant.

        Args:
            query: A consulta do usuário
            account_id: ID da conta do cliente
            collection_name: Nome da coleção no Qdrant
            limit: Número máximo de resultados
            score_threshold: Limiar mínimo de similaridade

        Returns:
            Lista de resultados
        """
        # Verificar se a coleção existe
        if not self.qdrant_client.collection_exists(collection_name):
            return [{"error": f"Coleção '{collection_name}' não existe"}]

        # Gerar embedding para a consulta
        query_embedding = self.embedding_fn(query)

        # Buscar documentos relevantes
        search_results = self.qdrant_client.search(
            collection_name=collection_name,
            query_vector=query_embedding,
            query_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="account_id",
                        match=models.MatchValue(
                            value=account_id
                        )
                    )
                ]
            ),
            limit=limit,
            score_threshold=score_threshold
        )

        # Extrair informações relevantes
        results = []
        for hit in search_results:
            # Remover o embedding do payload para economizar espaço
            payload = {k: v for k, v in hit.payload.items() if k != "embedding"}

            results.append({
                "id": hit.id,
                "metadata": payload,
                "score": hit.score
            })

        return results
