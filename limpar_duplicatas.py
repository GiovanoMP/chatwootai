#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para limpar vetores duplicados no Qdrant.
Este script identifica e remove documentos duplicados, mantendo apenas um vetor por documento.
"""

from qdrant_client import QdrantClient
from qdrant_client.http import models
import argparse
import sys
import json
from collections import defaultdict

def main():
    parser = argparse.ArgumentParser(description='Limpar vetores duplicados no Qdrant')
    parser.add_argument('--host', default='localhost', help='Host do Qdrant (padrão: localhost)')
    parser.add_argument('--port', type=int, default=6333, help='Porta do Qdrant (padrão: 6333)')
    parser.add_argument('--account_id', default='account_1', help='ID da conta (padrão: account_1)')
    parser.add_argument('--force', action='store_true', help='Excluir sem confirmação')
    parser.add_argument('--dry-run', action='store_true', help='Apenas mostrar o que seria feito, sem excluir')
    
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
        
        # Buscar documentos no Qdrant
        print(f"Buscando documentos para account_id={args.account_id}...")
        
        points = client.scroll(
            collection_name="support_documents",
            scroll_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="account_id",
                        match=models.MatchValue(value=args.account_id)
                    )
                ]
            ),
            limit=1000,  # Limite alto para buscar todos os documentos
            with_payload=True,
            with_vectors=False,
        )[0]
        
        if not points:
            print(f"Nenhum documento encontrado para account_id={args.account_id}")
            return
        
        # Agrupar documentos por document_id
        docs_by_id = defaultdict(list)
        for point in points:
            doc_id = point.payload.get("document_id")
            if doc_id:
                docs_by_id[doc_id].append(point)
        
        # Identificar duplicatas
        duplicates = {doc_id: points for doc_id, points in docs_by_id.items() if len(points) > 1}
        
        if not duplicates:
            print("Nenhuma duplicata encontrada.")
            return
        
        # Imprimir resumo das duplicatas
        print(f"\nEncontradas duplicatas para {len(duplicates)} documentos:")
        
        total_duplicates = 0
        for doc_id, doc_points in duplicates.items():
            print(f"document_id={doc_id}: {len(doc_points)} vetores")
            # Imprimir detalhes do primeiro documento
            point = doc_points[0]
            print(f"  Nome: {point.payload.get('name')}")
            print(f"  Tipo: {point.payload.get('document_type')}")
            
            # Listar IDs dos pontos
            point_ids = [p.id for p in doc_points]
            print(f"  IDs: {', '.join(point_ids)}")
            
            total_duplicates += len(doc_points) - 1
        
        print(f"\nTotal de duplicatas a serem removidas: {total_duplicates}")
        
        if args.dry_run:
            print("\nModo dry-run ativado. Nenhuma alteração será feita.")
            return
        
        # Perguntar ao usuário se deseja excluir as duplicatas
        if not args.force:
            resposta = input("\nDeseja excluir as duplicatas? (s/n): ")
            if resposta.lower() != "s":
                print("Operação cancelada")
                return
        
        # Para cada grupo de documentos duplicados, manter apenas o com ID determinístico
        # ou o primeiro se não houver ID determinístico
        points_to_delete = []
        
        for doc_id, doc_points in duplicates.items():
            # Verificar se existe um ponto com ID determinístico
            deterministic_id = f"{args.account_id}_{doc_id}"
            deterministic_point = None
            
            for point in doc_points:
                if point.id == deterministic_id:
                    deterministic_point = point
                    break
            
            # Se não houver ponto com ID determinístico, usar o primeiro
            if not deterministic_point:
                deterministic_point = doc_points[0]
            
            # Adicionar todos os outros pontos à lista de exclusão
            for point in doc_points:
                if point.id != deterministic_point.id:
                    points_to_delete.append(point.id)
        
        # Excluir os pontos
        if points_to_delete:
            print(f"\nExcluindo {len(points_to_delete)} pontos duplicados...")
            
            # Excluir em lotes de 100 para evitar problemas com requisições muito grandes
            batch_size = 100
            for i in range(0, len(points_to_delete), batch_size):
                batch = points_to_delete[i:i+batch_size]
                client.delete(
                    collection_name="support_documents",
                    points_selector=models.PointIdsList(
                        points=batch
                    )
                )
            
            print(f"Excluídos {len(points_to_delete)} pontos duplicados com sucesso!")
        else:
            print("Nenhum ponto para excluir")
    
    except Exception as e:
        print(f"Erro: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
