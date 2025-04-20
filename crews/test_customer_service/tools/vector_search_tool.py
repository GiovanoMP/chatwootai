"""
Ferramenta de busca vetorial para o CrewAI.

Esta ferramenta permite que os agentes realizem buscas no Qdrant
para encontrar regras de negócio, documentos de suporte e metadados da empresa.
"""

from typing import Dict, List, Any, Optional
import asyncio
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from qdrant_client.http import models

from odoo_api.services.vector_service import get_vector_service


class VectorSearchInput(BaseModel):
    """Modelo de entrada para a ferramenta de busca vetorial."""

    query: str = Field(description="A consulta do usuário")
    account_id: str = Field(description="ID da conta do cliente")
    collection_name: str = Field(description="Nome da coleção no Qdrant (business_rules, support_documents, company_metadata)")
    limit: int = Field(default=10, description="Número máximo de resultados")
    search_type: str = Field(default="semantic", description="Tipo de busca: 'semantic' (busca semântica) ou 'all' (todas as regras)")


class VectorSearchTool(BaseTool):
    """Ferramenta para buscar informações no Qdrant."""

    name: str = "vector_search"
    description: str = """
    Busca informações no banco de dados vetorial Qdrant.
    Use esta ferramenta para encontrar regras de negócio, documentos de suporte ou metadados da empresa.

    Parâmetros:
    - query: A consulta do usuário
    - account_id: ID da conta do cliente
    - collection_name: Nome da coleção no Qdrant (business_rules, support_documents, company_metadata)
    - limit: Número máximo de resultados (padrão: 10)
    - search_type: Tipo de busca: 'semantic' (busca semântica) ou 'all' (todas as regras) (padrão: 'semantic')
    """

    def _run(self, query: str, account_id: str, collection_name: str, limit: int = 10, search_type: str = "semantic") -> List[Dict[str, Any]]:
        """
        Executa a busca no Qdrant.

        Args:
            query: A consulta do usuário
            account_id: ID da conta do cliente
            collection_name: Nome da coleção no Qdrant
            limit: Número máximo de resultados
            search_type: Tipo de busca

        Returns:
            Lista de resultados
        """
        # Executar a busca de forma assíncrona
        return asyncio.run(self._async_run(query, account_id, collection_name, limit, search_type))

    async def _async_run(self, query: str, account_id: str, collection_name: str, limit: int = 10, search_type: str = "semantic") -> List[Dict[str, Any]]:
        """
        Executa a busca no Qdrant de forma assíncrona.

        Args:
            query: A consulta do usuário
            account_id: ID da conta do cliente
            collection_name: Nome da coleção no Qdrant
            limit: Número máximo de resultados
            search_type: Tipo de busca

        Returns:
            Lista de resultados
        """
        # Inicializar o serviço de vetores
        vector_service = await get_vector_service()

        # Se for busca de metadados da empresa, usar uma abordagem diferente
        if collection_name == "company_metadata":
            return await self._search_company_metadata(vector_service, account_id)

        # Se for busca de todas as regras, usar scroll
        if search_type == "all":
            return await self._search_all(vector_service, account_id, collection_name, limit)

        # Caso contrário, fazer busca semântica
        return await self._search_semantic(vector_service, query, account_id, collection_name, limit)

    async def _search_company_metadata(self, vector_service, account_id: str) -> List[Dict[str, Any]]:
        """
        Busca metadados da empresa.

        Args:
            vector_service: Serviço de vetores
            account_id: ID da conta do cliente

        Returns:
            Lista com os metadados da empresa
        """
        try:
            # Buscar metadados da empresa usando scroll
            scroll_results = vector_service.qdrant_client.scroll(
                collection_name="company_metadata",
                scroll_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="account_id",
                            match=models.MatchValue(
                                value=account_id
                            )
                        )
                    ]
                ),
                limit=1
            )

            if scroll_results and len(scroll_results) > 0 and scroll_results[0]:
                point = scroll_results[0][0]  # Primeiro ponto do primeiro batch
                return [{
                    "text": point.payload.get("text", ""),
                    "company_name": point.payload.get("company_name", "Sandra Cosméticos"),
                    "greeting_message": point.payload.get("greeting_message", "Olá, obrigada por entrar em contato com a Sandra Cosméticos! Como posso ajudar hoje?"),
                    "account_id": account_id,
                    "id": point.id,
                    "score": 1.0
                }]
        except Exception as e:
            print(f"Erro ao buscar metadados da empresa: {e}")

        # Valores padrão se não encontrar nada
        return [{
            "text": "Comercializamos cosméticos online e presencialmente, nossos canais de venda são Instagram, Facebook, Mercado Livre e WhatsApp.",
            "company_name": "Sandra Cosméticos",
            "greeting_message": "Olá, obrigada por entrar em contato com a Sandra Cosméticos! Como posso ajudar hoje?",
            "account_id": account_id,
            "id": "default",
            "score": 1.0
        }]

    async def _search_all(self, vector_service, account_id: str, collection_name: str, limit: int) -> List[Dict[str, Any]]:
        """
        Busca todos os documentos de uma coleção para uma conta.

        Args:
            vector_service: Serviço de vetores
            account_id: ID da conta do cliente
            collection_name: Nome da coleção no Qdrant
            limit: Número máximo de resultados

        Returns:
            Lista de resultados
        """
        try:
            # Buscar todos os documentos da coleção para a conta
            scroll_results = vector_service.qdrant_client.scroll(
                collection_name=collection_name,
                scroll_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="account_id",
                            match=models.MatchValue(
                                value=account_id
                            )
                        )
                    ]
                ),
                limit=limit
            )

            results = []
            if scroll_results and len(scroll_results) > 0 and scroll_results[0]:
                for point in scroll_results[0]:
                    results.append({
                        "text": point.payload.get("text", ""),
                        "id": point.id,
                        "account_id": account_id,
                        "is_temporary": point.payload.get("is_temporary", False),
                        "priority": point.payload.get("priority", 3),
                        "score": 0.5  # Score padrão
                    })

            # Ordenar por prioridade (menor número = maior prioridade)
            results.sort(key=lambda x: x.get("priority", 3))

            return results[:limit]
        except Exception as e:
            print(f"Erro ao buscar todos os documentos: {e}")
            return []

    async def _search_semantic(self, vector_service, query: str, account_id: str, collection_name: str, limit: int) -> List[Dict[str, Any]]:
        """
        Realiza uma busca semântica no Qdrant.

        Args:
            vector_service: Serviço de vetores
            query: A consulta do usuário
            account_id: ID da conta do cliente
            collection_name: Nome da coleção no Qdrant
            limit: Número máximo de resultados

        Returns:
            Lista de resultados
        """
        try:
            # Expandir a consulta para melhorar os resultados
            expanded_query = self._expand_query(query)

            # Gerar embedding para a consulta expandida
            query_embedding = await vector_service.generate_embedding(expanded_query)

            # Buscar documentos relevantes
            search_results = vector_service.qdrant_client.search(
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
                limit=limit
            )

            # Extrair informações relevantes
            results = []
            for hit in search_results:
                results.append({
                    "text": hit.payload.get("text", ""),
                    "id": hit.id,
                    "account_id": account_id,
                    "is_temporary": hit.payload.get("is_temporary", False),
                    "priority": hit.payload.get("priority", 3),
                    "score": hit.score
                })

            # Ordenar por prioridade (menor número = maior prioridade) e depois por score (maior = melhor)
            results.sort(key=lambda x: (x.get("priority", 3), -x.get("score", 0)))

            return results
        except Exception as e:
            print(f"Erro ao realizar busca semântica: {e}")
            return []

    def _expand_query(self, query: str) -> str:
        """
        Expande a consulta para melhorar os resultados da busca semântica.

        Args:
            query: A consulta original

        Returns:
            Consulta expandida
        """
        # Palavras-chave para expansão da consulta
        keywords = {
            'shampoo': ['shampoo', 'cabelo', 'xampu', 'lavar cabelo', 'cuidados com cabelo'],
            'frete': ['frete', 'entrega', 'grátis', 'gratis', 'delivery', 'envio'],
            'presente': ['presente', 'embalagem', 'embrulho', 'gift', 'embalagem para presente'],
            'promoção': ['promo', 'desconto', 'oferta', 'especial', 'cupom', 'preço reduzido'],
            'produto': ['produto', 'item', 'mercadoria', 'cosmético', 'beleza']
        }

        # Verificar quais palavras-chave estão na consulta
        matched_categories = []
        for category, terms in keywords.items():
            if any(term in query.lower() for term in terms):
                matched_categories.append(category)

        # Se encontramos categorias, expandir a consulta
        if matched_categories:
            expanded_terms = []
            for category in matched_categories:
                expanded_terms.extend(keywords[category])
            expanded_query = f"{query} {' '.join(expanded_terms)}"
            return expanded_query

        return query
