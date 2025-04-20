#!/usr/bin/env python
"""
Script para testar o acesso ao Qdrant.

Este script demonstra como acessar o Qdrant diretamente para recuperar regras de negócio.
"""

import asyncio
import argparse
from typing import List, Dict, Any
from qdrant_client.http import models

from odoo_api.services.vector_service import get_vector_service


async def search_business_rules(query: str, account_id: str = "account_1", limit: int = 5) -> List[Dict[str, Any]]:
    """
    Busca regras de negócio no Qdrant.
    
    Args:
        query: A consulta do usuário
        account_id: ID da conta do cliente
        limit: Número máximo de resultados
        
    Returns:
        Lista de regras de negócio
    """
    print(f"Buscando regras de negócio para a consulta: '{query}'")
    
    # Inicializar o serviço de vetores
    vector_service = await get_vector_service()
    
    # Gerar embedding para a consulta
    query_embedding = await vector_service.generate_embedding(query)
    
    # Buscar regras de negócio relevantes
    search_results = vector_service.qdrant_client.search(
        collection_name="business_rules",
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
            "score": hit.score,
            "id": hit.id,
            "is_temporary": hit.payload.get("is_temporary", False),
            "priority": hit.payload.get("priority", 3)
        })
    
    # Ordenar por prioridade (menor número = maior prioridade) e depois por score (maior = melhor)
    results.sort(key=lambda x: (x.get("priority", 3), -x.get("score", 0)))
    
    return results


async def get_all_business_rules(account_id: str = "account_1", limit: int = 20) -> List[Dict[str, Any]]:
    """
    Recupera todas as regras de negócio para uma conta.
    
    Args:
        account_id: ID da conta do cliente
        limit: Número máximo de resultados
        
    Returns:
        Lista de regras de negócio
    """
    print(f"Recuperando todas as regras de negócio para a conta: '{account_id}'")
    
    # Inicializar o serviço de vetores
    vector_service = await get_vector_service()
    
    # Buscar todas as regras de negócio
    scroll_results = vector_service.qdrant_client.scroll(
        collection_name="business_rules",
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
    
    # Extrair informações relevantes
    results = []
    if scroll_results and len(scroll_results) > 0 and scroll_results[0]:
        for point in scroll_results[0]:
            results.append({
                "text": point.payload.get("text", ""),
                "id": point.id,
                "is_temporary": point.payload.get("is_temporary", False),
                "priority": point.payload.get("priority", 3)
            })
    
    # Ordenar por prioridade (menor número = maior prioridade)
    results.sort(key=lambda x: x.get("priority", 3))
    
    return results


async def get_company_metadata(account_id: str = "account_1") -> Dict[str, Any]:
    """
    Recupera os metadados da empresa.
    
    Args:
        account_id: ID da conta do cliente
        
    Returns:
        Metadados da empresa
    """
    print(f"Recuperando metadados da empresa para a conta: '{account_id}'")
    
    # Inicializar o serviço de vetores
    vector_service = await get_vector_service()
    
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
            return {
                "text": point.payload.get("text", ""),
                "company_name": point.payload.get("company_name", "Sandra Cosméticos"),
                "greeting_message": point.payload.get("greeting_message", "Olá, obrigada por entrar em contato com a Sandra Cosméticos! Como posso ajudar hoje?")
            }
    except Exception as e:
        print(f"Erro ao buscar metadados da empresa: {e}")
    
    # Valores padrão se não encontrar nada
    return {
        "text": "Comercializamos cosméticos online e presencialmente, nossos canais de venda são Instagram, Facebook, Mercado Livre e WhatsApp.",
        "company_name": "Sandra Cosméticos",
        "greeting_message": "Olá, obrigada por entrar em contato com a Sandra Cosméticos! Como posso ajudar hoje?"
    }


async def list_collections() -> List[str]:
    """
    Lista todas as coleções disponíveis no Qdrant.
    
    Returns:
        Lista de nomes de coleções
    """
    print("Listando coleções disponíveis no Qdrant")
    
    # Inicializar o serviço de vetores
    vector_service = await get_vector_service()
    
    # Listar coleções
    collections = vector_service.qdrant_client.get_collections()
    
    return [c.name for c in collections.collections]


async def main():
    """Função principal."""
    parser = argparse.ArgumentParser(description="Teste de acesso ao Qdrant")
    parser.add_argument("--account_id", type=str, default="account_1", help="ID da conta do cliente")
    parser.add_argument("--query", type=str, help="Consulta para buscar regras de negócio")
    parser.add_argument("--list_collections", action="store_true", help="Listar coleções disponíveis")
    parser.add_argument("--all_rules", action="store_true", help="Recuperar todas as regras de negócio")
    parser.add_argument("--company_metadata", action="store_true", help="Recuperar metadados da empresa")
    args = parser.parse_args()
    
    # Listar coleções disponíveis
    if args.list_collections:
        collections = await list_collections()
        print(f"Coleções disponíveis: {collections}")
    
    # Recuperar metadados da empresa
    if args.company_metadata:
        metadata = await get_company_metadata(args.account_id)
        print(f"Metadados da empresa:")
        for key, value in metadata.items():
            print(f"  {key}: {value}")
    
    # Recuperar todas as regras de negócio
    if args.all_rules:
        rules = await get_all_business_rules(args.account_id)
        print(f"Encontradas {len(rules)} regras de negócio:")
        for i, rule in enumerate(rules, 1):
            print(f"  {i}. {'[TEMPORÁRIA]' if rule.get('is_temporary') else '[PERMANENTE]'} {rule.get('text')[:100]}...")
    
    # Buscar regras de negócio com base na consulta
    if args.query:
        rules = await search_business_rules(args.query, args.account_id)
        print(f"Encontradas {len(rules)} regras de negócio para a consulta '{args.query}':")
        for i, rule in enumerate(rules, 1):
            print(f"  {i}. Score: {rule.get('score'):.4f} | {'[TEMPORÁRIA]' if rule.get('is_temporary') else '[PERMANENTE]'} {rule.get('text')[:100]}...")


if __name__ == "__main__":
    asyncio.run(main())
