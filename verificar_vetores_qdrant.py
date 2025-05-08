#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para verificar vetores no Qdrant.
Este script lista todos os documentos de suporte para um determinado account_id
e document_id, permitindo verificar se há duplicações.
"""

from qdrant_client import QdrantClient
from qdrant_client.http import models
import argparse
import sys
import json

def main():
    parser = argparse.ArgumentParser(description='Verificar vetores no Qdrant')
    parser.add_argument('--host', default='localhost', help='Host do Qdrant (padrão: localhost)')
    parser.add_argument('--port', type=int, default=6333, help='Porta do Qdrant (padrão: 6333)')
    parser.add_argument('--account_id', default='account_1', help='ID da conta (padrão: account_1)')
    parser.add_argument('--document_id', help='ID do documento específico (opcional)')
    parser.add_argument('--detailed', action='store_true', help='Mostrar detalhes completos dos documentos')
    parser.add_argument('--json', action='store_true', help='Saída em formato JSON')
    
    args = parser.parse_args()
    
    try:
        # Conectar ao Qdrant
        if not args.json:
            print(f"Conectando ao Qdrant em {args.host}:{args.port}...")
        client = QdrantClient(host=args.host, port=args.port)
        
        # Verificar se a coleção existe
        collections = client.get_collections()
        collection_names = [c.name for c in collections.collections]
        
        if "support_documents" not in collection_names:
            if args.json:
                print(json.dumps({"error": "Coleção 'support_documents' não encontrada no Qdrant."}))
            else:
                print("Coleção 'support_documents' não encontrada no Qdrant.")
            return 1
        
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
        if not args.json:
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
            if args.json:
                print(json.dumps({"count": 0, "documents": []}))
            else:
                print(f"Nenhum documento encontrado para account_id={args.account_id}")
                if args.document_id:
                    print(f"e document_id={args.document_id}")
            return 0
        
        # Preparar resultado
        if args.json:
            result = {
                "count": len(points),
                "documents": []
            }
            
            for point in points:
                doc = {
                    "id": point.id,
                    "document_id": point.payload.get("document_id"),
                    "name": point.payload.get("name"),
                    "document_type": point.payload.get("document_type"),
                    "last_updated": point.payload.get("last_updated")
                }
                
                if args.detailed:
                    doc["payload"] = point.payload
                
                result["documents"].append(doc)
            
            print(json.dumps(result, indent=2))
        else:
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
                
                # Imprimir detalhes de cada documento
                for i, point in enumerate(doc_points):
                    print(f"  Documento {i+1}:")
                    print(f"    ID: {point.id}")
                    print(f"    Nome: {point.payload.get('name')}")
                    print(f"    Tipo: {point.payload.get('document_type')}")
                    print(f"    Última atualização: {point.payload.get('last_updated')}")
                    
                    if args.detailed:
                        print(f"    Payload completo:")
                        for key, value in point.payload.items():
                            if isinstance(value, str) and len(value) > 100:
                                value = value[:100] + "..."
                            print(f"      {key}: {value}")
    
    except Exception as e:
        if args.json:
            print(json.dumps({"error": str(e)}))
        else:
            print(f"Erro: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
