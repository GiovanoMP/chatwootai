#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para limpar completamente um documento específico no Qdrant.
Este script remove TODOS os vetores associados a um account_id e document_id específicos.
"""

from qdrant_client import QdrantClient
from qdrant_client.http import models
import argparse
import sys
import json
import time

def main():
    parser = argparse.ArgumentParser(description='Limpar completamente um documento específico no Qdrant')
    parser.add_argument('--host', default='localhost', help='Host do Qdrant (padrão: localhost)')
    parser.add_argument('--port', type=int, default=6333, help='Porta do Qdrant (padrão: 6333)')
    parser.add_argument('--account_id', required=True, help='ID da conta')
    parser.add_argument('--document_id', required=True, help='ID do documento')
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
        
        # Buscar documentos no Qdrant
        print(f"Buscando documentos para account_id={args.account_id} e document_id={args.document_id}...")
        
        points = client.scroll(
            collection_name="support_documents",
            scroll_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="account_id",
                        match=models.MatchValue(value=args.account_id)
                    ),
                    models.FieldCondition(
                        key="document_id",
                        match=models.MatchValue(value=args.document_id)
                    )
                ]
            ),
            limit=100,  # Limite alto para buscar todos os documentos
            with_payload=True,
            with_vectors=False,
        )[0]
        
        if not points:
            print(f"Nenhum documento encontrado para account_id={args.account_id} e document_id={args.document_id}")
            return
        
        # Imprimir resumo dos documentos encontrados
        print(f"\nEncontrados {len(points)} documentos:")
        
        for i, point in enumerate(points):
            print(f"\nDocumento {i+1}:")
            print(f"  ID: {point.id}")
            print(f"  Nome: {point.payload.get('name', 'N/A')}")
            print(f"  Tipo: {point.payload.get('document_type', 'N/A')}")
            
            # Verificar se o documento usa o novo formato estruturado
            if "metadata" in point.payload:
                print(f"  Formato: Estruturado (novo)")
                print(f"  Última atualização: {point.payload.get('metadata', {}).get('last_updated', 'N/A')}")
                print(f"  Processado por IA: {point.payload.get('metadata', {}).get('ai_processed', False)}")
                print(f"  Tem dados estruturados: {point.payload.get('metadata', {}).get('has_structured_data', False)}")
            else:
                print(f"  Formato: Legado (antigo)")
                print(f"  Última atualização: {point.payload.get('last_updated', 'N/A')}")
                print(f"  Processado por IA: {point.payload.get('ai_processed', False)}")
        
        # Perguntar ao usuário se deseja excluir os documentos
        if not args.force:
            resposta = input("\nDeseja excluir TODOS estes documentos? (s/n): ")
            if resposta.lower() != "s":
                print("Operação cancelada")
                return
        
        # Excluir os documentos
        point_ids = [point.id for point in points]
        
        print(f"\nExcluindo {len(point_ids)} documentos...")
        
        # Excluir em lotes de 10 para evitar problemas com requisições muito grandes
        batch_size = 10
        for i in range(0, len(point_ids), batch_size):
            batch = point_ids[i:i+batch_size]
            client.delete(
                collection_name="support_documents",
                points_selector=models.PointIdsList(
                    points=batch
                )
            )
            # Pequena pausa para evitar sobrecarga
            time.sleep(0.5)
        
        print(f"Excluídos {len(point_ids)} documentos com sucesso!")
        
        # Verificar se a exclusão foi bem-sucedida
        verification_points = client.scroll(
            collection_name="support_documents",
            scroll_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="account_id",
                        match=models.MatchValue(value=args.account_id)
                    ),
                    models.FieldCondition(
                        key="document_id",
                        match=models.MatchValue(value=args.document_id)
                    )
                ]
            ),
            limit=10,
            with_payload=False,
            with_vectors=False,
        )[0]
        
        if verification_points:
            print(f"ATENÇÃO: Ainda existem {len(verification_points)} documentos no Qdrant!")
            print("Tente executar o script novamente.")
        else:
            print("Verificação concluída: Nenhum documento encontrado após a exclusão.")
    
    except Exception as e:
        print(f"Erro: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
