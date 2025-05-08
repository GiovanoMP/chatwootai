#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para testar as correções implementadas no sistema de IA.
Este script limpa os vetores existentes no Qdrant, sincroniza um documento
e verifica se apenas um vetor foi criado.
"""

import requests
import json
import argparse
import sys
import time
from qdrant_client import QdrantClient
from qdrant_client.http import models

def limpar_vetores(client, account_id, document_id=None):
    """Limpa os vetores existentes no Qdrant"""
    print(f"Limpando vetores para account_id={account_id}...")

    # Construir o filtro
    filter_conditions = [
        models.FieldCondition(
            key="account_id",
            match=models.MatchValue(value=account_id)
        )
    ]

    # Adicionar filtro por document_id se especificado
    if document_id:
        filter_conditions.append(
            models.FieldCondition(
                key="document_id",
                match=models.MatchValue(value=str(document_id))
            )
        )

    # Buscar documentos no Qdrant
    points = client.scroll(
        collection_name="support_documents",
        scroll_filter=models.Filter(must=filter_conditions),
        limit=100,
        with_payload=False,
        with_vectors=False,
    )[0]

    if not points:
        print(f"Nenhum documento encontrado para account_id={account_id}")
        return

    # Excluir todos os documentos
    ids_to_delete = [point.id for point in points]

    if ids_to_delete:
        print(f"Excluindo {len(ids_to_delete)} documentos...")
        client.delete(
            collection_name="support_documents",
            points_selector=models.PointIdsList(
                points=ids_to_delete
            )
        )
        print(f"Excluídos {len(ids_to_delete)} documentos com sucesso!")
    else:
        print("Nenhum documento para excluir")

def sincronizar_documento(api_url, account_id, business_rule_id, document_id, document_name, document_type, document_content):
    """Sincroniza um documento com o sistema de IA"""
    print(f"Sincronizando documento {document_id}...")

    # Preparar payload
    payload = {
        "account_id": account_id,
        "business_rule_id": business_rule_id,
        "documents": [
            {
                "id": document_id,
                "name": document_name,
                "document_type": document_type,
                "content": document_content
            }
        ]
    }

    # Fazer a requisição
    # O endpoint correto é /api/v1/business-rules/sync-support-documents
    response = requests.post(
        f"{api_url}/api/v1/business-rules/sync-support-documents",
        json=payload,
        params={"account_id": account_id},  # Adicionar account_id como parâmetro de query
        headers={"Content-Type": "application/json"}
    )

    # Verificar resposta
    if response.status_code == 200:
        result = response.json()
        print(f"Documento sincronizado com sucesso: {json.dumps(result, indent=2)}")
        return result
    else:
        print(f"Erro ao sincronizar documento: {response.status_code} - {response.text}")
        return None

def verificar_vetores(client, account_id, document_id=None):
    """Verifica os vetores existentes no Qdrant"""
    print(f"Verificando vetores para account_id={account_id}...")

    # Construir o filtro
    filter_conditions = [
        models.FieldCondition(
            key="account_id",
            match=models.MatchValue(value=account_id)
        )
    ]

    # Adicionar filtro por document_id se especificado
    if document_id:
        filter_conditions.append(
            models.FieldCondition(
                key="document_id",
                match=models.MatchValue(value=str(document_id))
            )
        )

    # Buscar documentos no Qdrant
    points = client.scroll(
        collection_name="support_documents",
        scroll_filter=models.Filter(must=filter_conditions),
        limit=100,
        with_payload=True,
        with_vectors=False,
    )[0]

    if not points:
        print(f"Nenhum documento encontrado para account_id={account_id}")
        return []

    # Agrupar documentos por document_id
    docs_by_id = {}
    for point in points:
        doc_id = point.payload.get("document_id")
        if doc_id not in docs_by_id:
            docs_by_id[doc_id] = []
        docs_by_id[doc_id].append(point)

    # Imprimir resumo por document_id
    print("\nResumo por document_id:")
    for doc_id, doc_points in docs_by_id.items():
        print(f"document_id={doc_id}: {len(doc_points)} vetores")

        # Imprimir detalhes de cada documento
        for i, point in enumerate(doc_points):
            print(f"  Documento {i+1}:")
            print(f"    ID: {point.id}")
            print(f"    Nome: {point.payload.get('name')}")
            print(f"    Tipo: {point.payload.get('document_type')}")
            print(f"    Última atualização: {point.payload.get('last_updated')}")

    return points

def main():
    parser = argparse.ArgumentParser(description='Testar correções no sistema de IA')
    parser.add_argument('--qdrant-host', default='localhost', help='Host do Qdrant (padrão: localhost)')
    parser.add_argument('--qdrant-port', type=int, default=6333, help='Porta do Qdrant (padrão: 6333)')
    parser.add_argument('--api-url', default='http://localhost:8001', help='URL da API (padrão: http://localhost:8001)')
    parser.add_argument('--account-id', default='account_1', help='ID da conta (padrão: account_1)')
    parser.add_argument('--business-rule-id', type=int, default=1, help='ID da regra de negócio (padrão: 1)')
    parser.add_argument('--document-id', type=int, default=1, help='ID do documento (padrão: 1)')
    parser.add_argument('--skip-clean', action='store_true', help='Pular limpeza de vetores')

    args = parser.parse_args()

    try:
        # Conectar ao Qdrant
        print(f"Conectando ao Qdrant em {args.qdrant_host}:{args.qdrant_port}...")
        client = QdrantClient(host=args.qdrant_host, port=args.qdrant_port)

        # Verificar se a coleção existe
        collections = client.get_collections()
        collection_names = [c.name for c in collections.collections]

        if "support_documents" not in collection_names:
            print("Coleção 'support_documents' não encontrada no Qdrant.")
            return 1

        # Limpar vetores existentes
        if not args.skip_clean:
            limpar_vetores(client, args.account_id, str(args.document_id))

        # Verificar estado inicial
        print("\nEstado inicial:")
        verificar_vetores(client, args.account_id, str(args.document_id))

        # Sincronizar documento
        document_name = "Documento de Teste"
        document_type = "support"
        document_content = """
Este é um documento de teste para verificar se as correções no sistema de IA
estão funcionando corretamente.

O problema era que o sistema estava criando múltiplos vetores para o mesmo documento.
Agora, o sistema deve criar apenas um vetor por documento, usando um ID determinístico
baseado no account_id e document_id.
"""

        sincronizar_documento(
            args.api_url,
            args.account_id,
            args.business_rule_id,
            args.document_id,
            document_name,
            document_type,
            document_content
        )

        # Aguardar um pouco para garantir que a sincronização foi concluída
        print("\nAguardando 2 segundos para garantir que a sincronização foi concluída...")
        time.sleep(2)

        # Verificar estado final
        print("\nEstado final:")
        points = verificar_vetores(client, args.account_id, str(args.document_id))

        # Verificar se apenas um vetor foi criado
        if len(points) == 1:
            print("\nSUCESSO: Apenas um vetor foi criado para o documento!")
            return 0
        else:
            print(f"\nFALHA: Foram criados {len(points)} vetores para o documento!")
            return 1

    except Exception as e:
        print(f"Erro: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
