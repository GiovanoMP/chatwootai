#!/usr/bin/env python
"""
Script para testar a conexão com o Qdrant.
"""

import os
import argparse
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http import models
from openai import OpenAI


def parse_args():
    """
    Analisa os argumentos da linha de comando.
    
    Returns:
        Argumentos analisados
    """
    parser = argparse.ArgumentParser(description="Teste de conexão com o Qdrant")
    parser.add_argument("--qdrant_url", type=str, help="URL do servidor Qdrant")
    parser.add_argument("--qdrant_api_key", type=str, help="Chave API do Qdrant")
    parser.add_argument("--openai_api_key", type=str, help="Chave API do OpenAI")
    return parser.parse_args()


def test_qdrant_connection(qdrant_url, qdrant_api_key):
    """
    Testa a conexão com o Qdrant.
    
    Args:
        qdrant_url: URL do servidor Qdrant
        qdrant_api_key: Chave API do Qdrant
    """
    print(f"Testando conexão com o Qdrant em {qdrant_url}...")
    
    # Inicializar cliente Qdrant
    client = QdrantClient(
        url=qdrant_url,
        api_key=qdrant_api_key
    )
    
    # Listar coleções
    collections = client.get_collections()
    
    print(f"Conexão bem-sucedida! Coleções disponíveis: {[c.name for c in collections.collections]}")
    
    return client


def test_openai_connection(openai_api_key):
    """
    Testa a conexão com o OpenAI.
    
    Args:
        openai_api_key: Chave API do OpenAI
    """
    print(f"Testando conexão com o OpenAI...")
    
    # Inicializar cliente OpenAI
    client = OpenAI(api_key=openai_api_key)
    
    # Gerar embedding
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input="Teste de conexão com o OpenAI"
    )
    
    print(f"Conexão bem-sucedida! Dimensão do embedding: {len(response.data[0].embedding)}")
    
    return client


def main():
    """Função principal."""
    # Carregar variáveis de ambiente
    load_dotenv()
    
    # Analisar argumentos
    args = parse_args()
    
    # Obter credenciais
    qdrant_url = args.qdrant_url or os.getenv("QDRANT_URL") or "http://localhost:6333"
    qdrant_api_key = args.qdrant_api_key or os.getenv("QDRANT_API_KEY")
    openai_api_key = args.openai_api_key or os.getenv("OPENAI_API_KEY")
    
    # Testar conexão com o Qdrant
    qdrant_client = test_qdrant_connection(qdrant_url, qdrant_api_key)
    
    # Testar conexão com o OpenAI
    if openai_api_key:
        openai_client = test_openai_connection(openai_api_key)
    else:
        print("Chave API do OpenAI não fornecida. Pulando teste de conexão com o OpenAI.")


if __name__ == "__main__":
    main()
