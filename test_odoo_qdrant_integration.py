#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para testar a integração entre o Odoo (semantic_product_description) e o MCP-Qdrant.
Este script simula o envio de dados de produtos do Odoo para o MCP-Qdrant.
"""

import json
import requests
import argparse
from typing import Dict, List, Any, Optional

# Configurações padrão
DEFAULT_TENANT_ID = "account_1"
DEFAULT_MCP_QDRANT_URL = "http://localhost:8002"
DEFAULT_API_KEY = "development-api-key"


class QdrantIntegrationTester:
    """Classe para testar a integração entre o Odoo e o MCP-Qdrant."""

    def __init__(
        self, 
        tenant_id: str = DEFAULT_TENANT_ID,
        mcp_qdrant_url: str = DEFAULT_MCP_QDRANT_URL,
        api_key: str = DEFAULT_API_KEY
    ):
        """
        Inicializa o testador de integração.
        
        Args:
            tenant_id: ID do tenant (account_id)
            mcp_qdrant_url: URL do servidor MCP-Qdrant
            api_key: Chave de API para autenticação
        """
        self.tenant_id = tenant_id
        self.mcp_qdrant_url = mcp_qdrant_url.rstrip("/")
        self.api_key = api_key
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}" if api_key else ""
        }
        
        print(f"🔧 Configurado para tenant: {tenant_id}")
        print(f"🔧 URL do MCP-Qdrant: {mcp_qdrant_url}")
        
    def check_health(self) -> bool:
        """Verifica se o servidor MCP-Qdrant está acessível."""
        try:
            response = requests.get(f"{self.mcp_qdrant_url}/health", headers=self.headers)
            if response.status_code == 200:
                print("✅ MCP-Qdrant está acessível e funcionando corretamente!")
                return True
            else:
                print(f"❌ MCP-Qdrant retornou status code: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Erro ao conectar ao MCP-Qdrant: {str(e)}")
            return False
            
    def list_collections(self) -> List[str]:
        """Lista as coleções disponíveis para o tenant."""
        try:
            response = requests.post(
                f"{self.mcp_qdrant_url}/tools/listCollections",
                headers=self.headers,
                json={"tenant_id": self.tenant_id}
            )
            
            if response.status_code == 200:
                collections = response.json()
                print(f"📋 Coleções disponíveis para tenant {self.tenant_id}:")
                for collection in collections:
                    print(f"  - {collection}")
                return collections
            else:
                print(f"❌ Erro ao listar coleções: {response.status_code}")
                print(response.text)
                return []
        except Exception as e:
            print(f"❌ Erro ao listar coleções: {str(e)}")
            return []
            
    def store_product(self, product_data: Dict[str, Any]) -> bool:
        """
        Armazena dados de um produto no Qdrant.
        
        Args:
            product_data: Dados do produto a serem armazenados
            
        Returns:
            bool: True se o armazenamento foi bem-sucedido, False caso contrário
        """
        try:
            # Preparar os dados para armazenamento
            product_content = f"""
Nome: {product_data.get('name', 'N/A')}
Descrição: {product_data.get('description', 'N/A')}
Categoria: {product_data.get('category', 'N/A')}
Preço: {product_data.get('price', 0.0)}
SKU: {product_data.get('default_code', 'N/A')}
            """
            
            # Enviar para o MCP-Qdrant
            response = requests.post(
                f"{self.mcp_qdrant_url}/tools/qdrant-store",
                headers=self.headers,
                json={
                    "information": product_content,
                    "collection_name": "products",
                    "tenant_id": self.tenant_id,
                    "metadata": {
                        "product_id": product_data.get("id", 0),
                        "name": product_data.get("name", ""),
                        "default_code": product_data.get("default_code", ""),
                        "price": product_data.get("price", 0.0),
                        "category": product_data.get("category", "")
                    }
                }
            )
            
            if response.status_code == 200:
                print(f"✅ Produto '{product_data.get('name')}' armazenado com sucesso!")
                return True
            else:
                print(f"❌ Erro ao armazenar produto: {response.status_code}")
                print(response.text)
                return False
        except Exception as e:
            print(f"❌ Erro ao armazenar produto: {str(e)}")
            return False
            
    def search_similar_products(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Busca produtos similares por descrição semântica.
        
        Args:
            query: Consulta para busca semântica
            limit: Número máximo de resultados
            
        Returns:
            List[Dict[str, Any]]: Lista de produtos encontrados
        """
        try:
            response = requests.post(
                f"{self.mcp_qdrant_url}/tools/searchSimilarProducts",
                headers=self.headers,
                json={
                    "query": query,
                    "tenant_id": self.tenant_id,
                    "limit": limit
                }
            )
            
            if response.status_code == 200:
                results = response.json()
                print(f"🔍 Resultados para busca: '{query}'")
                for i, result in enumerate(results):
                    print(f"  {i+1}. {result}")
                return results
            else:
                print(f"❌ Erro na busca: {response.status_code}")
                print(response.text)
                return []
        except Exception as e:
            print(f"❌ Erro na busca: {str(e)}")
            return []
            
    def run_full_test(self, sample_products: List[Dict[str, Any]]) -> None:
        """
        Executa um teste completo de integração.
        
        Args:
            sample_products: Lista de produtos de exemplo para testar
        """
        print("\n🚀 Iniciando teste completo de integração Odoo-Qdrant...")
        
        # Verificar saúde do servidor
        if not self.check_health():
            print("❌ Teste abortado devido a problemas de conexão.")
            return
            
        # Listar coleções existentes
        print("\n📋 Verificando coleções existentes...")
        self.list_collections()
        
        # Armazenar produtos de exemplo
        print("\n💾 Armazenando produtos de exemplo...")
        for product in sample_products:
            self.store_product(product)
            
        # Buscar produtos similares
        print("\n🔍 Testando busca semântica...")
        search_queries = [
            "smartphone com câmera de alta resolução",
            "notebook para jogos",
            "monitor ultrawide"
        ]
        
        for query in search_queries:
            print(f"\nBusca: '{query}'")
            self.search_similar_products(query)
            
        print("\n✅ Teste de integração concluído!")


def main():
    """Função principal."""
    parser = argparse.ArgumentParser(description="Testador de integração Odoo-Qdrant")
    parser.add_argument("--tenant", default=DEFAULT_TENANT_ID, help="ID do tenant")
    parser.add_argument("--url", default=DEFAULT_MCP_QDRANT_URL, help="URL do MCP-Qdrant")
    parser.add_argument("--key", default=DEFAULT_API_KEY, help="Chave de API")
    args = parser.parse_args()
    
    # Produtos de exemplo para teste
    sample_products = [
        {
            "id": 1,
            "name": "iPhone 13 Pro",
            "description": "Smartphone avançado com câmera tripla de 12MP, tela Super Retina XDR de 6.1 polegadas e chip A15 Bionic.",
            "default_code": "IP13PRO-128",
            "price": 999.99,
            "category": "Smartphones"
        },
        {
            "id": 2,
            "name": "MacBook Pro 16",
            "description": "Notebook profissional com chip M1 Pro, tela Liquid Retina XDR de 16 polegadas, 16GB de RAM e 512GB de SSD.",
            "default_code": "MBP16-M1P",
            "price": 2499.99,
            "category": "Notebooks"
        },
        {
            "id": 3,
            "name": "Samsung Galaxy S21",
            "description": "Smartphone com câmera de 64MP, tela Dynamic AMOLED 2X de 6.2 polegadas e processador Exynos 2100.",
            "default_code": "SGS21-128",
            "price": 799.99,
            "category": "Smartphones"
        },
        {
            "id": 4,
            "name": "Dell XPS 15",
            "description": "Notebook premium com processador Intel Core i7, tela InfinityEdge de 15.6 polegadas, 32GB de RAM e 1TB de SSD.",
            "default_code": "DXPS15-I7",
            "price": 1899.99,
            "category": "Notebooks"
        },
        {
            "id": 5,
            "name": "LG UltraWide Monitor",
            "description": "Monitor ultrawide de 34 polegadas com resolução WQHD, taxa de atualização de 144Hz e tempo de resposta de 1ms.",
            "default_code": "LGUW34-144",
            "price": 699.99,
            "category": "Monitores"
        }
    ]
    
    # Criar e executar o testador
    tester = QdrantIntegrationTester(
        tenant_id=args.tenant,
        mcp_qdrant_url=args.url,
        api_key=args.key
    )
    
    tester.run_full_test(sample_products)


if __name__ == "__main__":
    main()
