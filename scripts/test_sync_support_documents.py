#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para testar a sincronização de documentos de suporte.

Este script:
1. Cria documentos de suporte de teste
2. Envia os documentos para o endpoint de sincronização
3. Verifica se os documentos foram armazenados corretamente no Qdrant
"""

import os
import sys
import json
import logging
import asyncio
import requests
from typing import List, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.http import models

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("support-docs-test")

# Configurações
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")
API_URL = os.getenv("API_URL", "http://localhost:8001")
API_TOKEN = os.getenv("API_TOKEN", "account_1-00bfe67a")  # Token para account_1
COLLECTION_NAME = "support_documents"

# Dados de teste
TEST_ACCOUNT = "account_1"
TEST_BUSINESS_RULE_ID = 1  # ID da regra de negócio no Odoo

# Documentos de suporte de teste
TEST_DOCUMENTS = [
    {
        "id": 1,
        "name": "Política de Devolução",
        "document_type": "support",
        "content": """
        Política de Devolução da Empresa

        1. Prazo para devolução: 7 dias após o recebimento do produto.
        2. O produto deve estar em perfeito estado, sem sinais de uso.
        3. A embalagem original deve ser preservada.
        4. Para iniciar uma devolução, entre em contato com nosso SAC.
        5. O valor será estornado em até 30 dias após a aprovação da devolução.
        """
    },
    {
        "id": 2,
        "name": "Formas de Pagamento",
        "document_type": "support",
        "content": """
        Formas de Pagamento Aceitas

        1. Cartão de crédito: Visa, Mastercard, American Express (até 12x sem juros)
        2. Cartão de débito: Visa, Mastercard, Elo
        3. Boleto bancário (vencimento em 3 dias úteis)
        4. PIX (pagamento instantâneo)
        5. Transferência bancária
        """
    },
    {
        "id": 3,
        "name": "Perguntas Frequentes",
        "document_type": "question",
        "content": """
        Perguntas Frequentes (FAQ)

        P: Qual o prazo de entrega?
        R: O prazo varia de acordo com a região, mas geralmente é de 3 a 7 dias úteis.

        P: Como acompanhar meu pedido?
        R: Você receberá um código de rastreamento por e-mail assim que o pedido for despachado.

        P: Vocês entregam em todo o Brasil?
        R: Sim, entregamos em todos os estados brasileiros.

        P: Posso alterar meu pedido após a confirmação?
        R: Alterações só podem ser feitas em até 1 hora após a confirmação do pedido.
        """
    }
]

async def connect_to_qdrant() -> QdrantClient:
    """Conecta ao Qdrant."""
    try:
        client = QdrantClient(
            host=QDRANT_HOST,
            port=QDRANT_PORT,
            api_key=QDRANT_API_KEY,
            timeout=30.0,
            https=False  # Usar HTTP em vez de HTTPS
        )

        # Verificar conexão
        client.get_collections()
        logger.info(f"Conectado ao Qdrant em {QDRANT_HOST}:{QDRANT_PORT}")
        return client

    except Exception as e:
        logger.error(f"Falha ao conectar ao Qdrant: {e}")
        raise

async def cleanup_test_data(client: QdrantClient, account_id: str):
    """Limpa dados de teste anteriores."""
    try:
        # Verificar se a coleção existe
        collections = client.get_collections()
        collection_names = [c.name for c in collections.collections]

        if COLLECTION_NAME not in collection_names:
            logger.info(f"Coleção {COLLECTION_NAME} não existe. Nada para limpar.")
            return

        # Filtrar por account_id
        filter_condition = models.Filter(
            must=[
                models.FieldCondition(
                    key="account_id",
                    match=models.MatchValue(
                        value=account_id
                    )
                )
            ]
        )

        # Obter IDs dos pontos para este account_id
        points = client.scroll(
            collection_name=COLLECTION_NAME,
            scroll_filter=filter_condition,  # Usar scroll_filter em vez de filter
            limit=100,
            with_payload=False,
            with_vectors=False,
        )[0]

        point_ids = [point.id for point in points]

        if not point_ids:
            logger.info(f"Nenhum ponto encontrado para account_id {account_id}. Nada para limpar.")
            return

        # Remover pontos
        client.delete(
            collection_name=COLLECTION_NAME,
            points_selector=models.PointIdsList(
                points=point_ids
            ),
        )

        logger.info(f"Removidos {len(point_ids)} pontos da coleção {COLLECTION_NAME} para account_id {account_id}")

    except Exception as e:
        logger.error(f"Falha ao limpar dados de teste: {e}")

async def sync_support_documents(account_id: str, business_rule_id: int, documents: List[Dict[str, Any]]):
    """Sincroniza documentos de suporte com o sistema de IA."""
    try:
        # Preparar URL
        url = f"{API_URL}/api/v1/business-rules/sync-support-documents"

        # Preparar headers
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_TOKEN}"
        }

        # Preparar dados
        data = {
            "account_id": account_id,
            "business_rule_id": business_rule_id,
            "documents": documents
        }

        # Fazer requisição
        logger.info(f"Enviando {len(documents)} documentos para sincronização...")
        response = requests.post(
            url,
            params={"account_id": account_id},
            headers=headers,
            json=data,
            timeout=30
        )

        # Verificar resposta
        if response.status_code == 200:
            result = response.json()
            logger.info(f"Sincronização concluída: {result}")
            return result
        else:
            logger.error(f"Erro na sincronização: {response.status_code} - {response.text}")
            return None

    except Exception as e:
        logger.error(f"Falha ao sincronizar documentos: {e}")
        return None

async def verify_documents(client: QdrantClient, account_id: str, documents: List[Dict[str, Any]]):
    """Verifica se os documentos foram armazenados corretamente no Qdrant."""
    try:
        # Verificar se a coleção existe
        collections = client.get_collections()
        collection_names = [c.name for c in collections.collections]

        if COLLECTION_NAME not in collection_names:
            logger.error(f"Coleção {COLLECTION_NAME} não existe. Não é possível verificar documentos.")
            return False

        # Filtrar por account_id
        filter_condition = models.Filter(
            must=[
                models.FieldCondition(
                    key="account_id",
                    match=models.MatchValue(
                        value=account_id
                    )
                )
            ]
        )

        # Obter pontos para este account_id
        points = client.scroll(
            collection_name=COLLECTION_NAME,
            scroll_filter=filter_condition,  # Usar scroll_filter em vez de filter
            limit=100,
            with_payload=True,
            with_vectors=False,
        )[0]

        if not points:
            logger.error(f"Nenhum ponto encontrado para account_id {account_id}.")
            return False

        logger.info(f"Encontrados {len(points)} documentos para account_id {account_id}")

        # Verificar se todos os documentos foram armazenados
        doc_ids = [doc["id"] for doc in documents]
        stored_doc_ids = [point.payload.get("document_id") for point in points]

        missing_docs = [doc_id for doc_id in doc_ids if doc_id not in stored_doc_ids]

        if missing_docs:
            logger.warning(f"Documentos não encontrados: {missing_docs}")
            return False

        logger.info("Todos os documentos foram armazenados corretamente!")

        # Exibir detalhes dos documentos armazenados
        for point in points:
            payload = point.payload
            logger.info(f"Documento: {payload.get('name')} (ID: {payload.get('document_id')})")
            logger.info(f"  Tipo: {payload.get('document_type')}")
            logger.info(f"  Última atualização: {payload.get('last_updated')}")

        return True

    except Exception as e:
        logger.error(f"Falha ao verificar documentos: {e}")
        return False

async def test_search_documents(client: QdrantClient, account_id: str, query: str):
    """Testa a busca de documentos por similaridade semântica."""
    try:
        # Importar OpenAI para gerar embeddings
        from openai import OpenAI

        # Obter API key do OpenAI
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            logger.error("OPENAI_API_KEY não definida. Não é possível testar busca.")
            return

        # Criar cliente OpenAI
        openai_client = OpenAI(api_key=openai_api_key)

        # Gerar embedding para a consulta
        logger.info(f"Gerando embedding para a consulta: '{query}'")
        response = openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=query,
            encoding_format="float"
        )
        query_embedding = response.data[0].embedding

        # Filtrar por account_id
        account_filter = models.Filter(
            must=[
                models.FieldCondition(
                    key="account_id",
                    match=models.MatchValue(
                        value=account_id
                    )
                )
            ]
        )

        # Buscar documentos semanticamente similares
        logger.info("Buscando documentos similares...")
        search_results = client.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_embedding,
            query_filter=account_filter,  # Usar query_filter em vez de filter
            limit=3,
            with_payload=True,
            with_vectors=False,
        )

        # Exibir resultados
        if not search_results:
            logger.info("Nenhum documento encontrado para a consulta.")
            return

        logger.info(f"Encontrados {len(search_results)} documentos relevantes:")
        for i, result in enumerate(search_results):
            logger.info(f"{i+1}. {result.payload.get('name')} (Score: {result.score:.4f})")
            logger.info(f"   Tipo: {result.payload.get('document_type')}")
            logger.info(f"   Conteúdo: {result.payload.get('content')[:100]}...")

    except Exception as e:
        logger.error(f"Falha ao testar busca: {e}")

async def main():
    """Função principal."""
    try:
        # Conectar ao Qdrant
        client = await connect_to_qdrant()

        # Limpar dados de teste anteriores
        await cleanup_test_data(client, TEST_ACCOUNT)

        # Sincronizar documentos de suporte
        result = await sync_support_documents(TEST_ACCOUNT, TEST_BUSINESS_RULE_ID, TEST_DOCUMENTS)

        if not result or not result.get("success"):
            logger.error("Falha na sincronização. Abortando teste.")
            return

        # Verificar se os documentos foram armazenados corretamente
        success = await verify_documents(client, TEST_ACCOUNT, TEST_DOCUMENTS)

        if not success:
            logger.error("Falha na verificação dos documentos. Abortando teste.")
            return

        # Perguntar ao usuário se deseja testar a busca
        response = input("Deseja testar a busca de documentos? (s/n): ")

        if response.lower() == "s":
            # Testar busca de documentos
            query = input("Digite sua consulta: ")
            await test_search_documents(client, TEST_ACCOUNT, query)

        logger.info("Teste concluído com sucesso!")

    except Exception as e:
        logger.error(f"Erro durante o teste: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
