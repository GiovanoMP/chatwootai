#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para limpar vetores duplicados no Qdrant.
Este script lista todos os documentos de suporte para um determinado account_id
e permite excluí-los para resolver o problema de múltiplas vetorizações.
"""

from qdrant_client import QdrantClient
from qdrant_client.http import models
import argparse
import sys

def main():
    parser = argparse.ArgumentParser(description='Limpar vetores duplicados no Qdrant')
    parser.add_argument('--host', default='localhost', help='Host do Qdrant (padrão: localhost)')
    parser.add_argument('--port', type=int, default=6333, help='Porta do Qdrant (padrão: 6333)')
    parser.add_argument('--account_id', default='account_1', help='ID da conta (padrão: account_1)')
    parser.add_argument('--document_id', help='ID do documento específico (opcional)')
    parser.add_argument('--force', action='store_true', help='Excluir sem confirmação')
    
    args = parser.parse_args()
    
    try:
        # Conectar ao Qdrant
        print(f"Conectando ao Qdrant em {args.host}:{args.port}...")
        client = QdrantClient(host=args.host, port=args.port)
        
        # Verificar se a coleção existe
        collections = client.get_collections()
        collection_names = [c.name for c in collections.collections]
        
        if "support_documents" not in collection_names:
            print("Coleção 'support_documents' não encontrada no Qdrant.")
            return
        
        # Construir o filtro
        filter_conditions = [
            models.FieldCondition(
                key="account_id",
                match=models.MatchValue(value=args.account_id)
            )
        ]
        
        # Adicionar filtro por document_id se especificado
        if args.document_id:
            filter_conditions.append(
                models.FieldCondition(
                    key="document_id",
                    match=models.MatchValue(value=str(args.document_id))
                )
            )
        
        # Buscar documentos no Qdrant
        print(f"Buscando documentos para account_id={args.account_id}...")
        if args.document_id:
            print(f"Filtrando por document_id={args.document_id}")
            
        points = client.scroll(
            collection_name="support_documents",
            scroll_filter=models.Filter(must=filter_conditions),
            limit=100,
            with_payload=True,
            with_vectors=False,
        )[0]
        
        # Verificar se encontrou documentos
        if not points:
            print(f"Nenhum documento encontrado para account_id={args.account_id}")
            if args.document_id:
                print(f"e document_id={args.document_id}")
            return
        
        # Imprimir os documentos encontrados
        print(f"\nEncontrados {len(points)} documentos:")
        
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
            # Imprimir detalhes do primeiro documento
            point = doc_points[0]
            print(f"  Nome: {point.payload.get('name')}")
            print(f"  Tipo: {point.payload.get('document_type')}")
        
        # Perguntar ao usuário se deseja excluir todos os documentos
        if not args.force:
            resposta = input("\nDeseja excluir todos os documentos encontrados? (s/n): ")
            if resposta.lower() != "s":
                print("Operação cancelada")
                return
        
        # Excluir todos os documentos
        ids_to_delete = [point.id for point in points]
        
        if ids_to_delete:
            print(f"\nExcluindo {len(ids_to_delete)} documentos...")
            client.delete(
                collection_name="support_documents",
                points_selector=models.PointIdsList(
                    points=ids_to_delete
                )
            )
            print(f"Excluídos {len(ids_to_delete)} documentos com sucesso!")
        else:
            print("Nenhum documento para excluir")
    
    except Exception as e:
        print(f"Erro: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
