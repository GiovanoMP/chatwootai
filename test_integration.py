#!/usr/bin/env python
"""
Script para testar a integração entre o MCP-Odoo e o serviço de vetorização.
"""

import os
import sys
import json
import logging
import requests
from dotenv import load_dotenv

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()

def test_generate_description():
    """Testa a geração de descrição de produto."""
    logger.info("Testando geração de descrição de produto...")
    
    # Configurações do MCP-Odoo
    mcp_url = os.environ.get("MCP_ODOO_URL", "http://localhost:8000")
    mcp_token = os.environ.get("MCP_ODOO_TOKEN", "")
    account_id = os.environ.get("MCP_ODOO_ACCOUNT_ID", "account_2")
    product_id = int(os.environ.get("TEST_PRODUCT_ID", "1"))
    
    # Preparar a requisição
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {mcp_token}' if mcp_token else ''
    }
    
    payload = {
        'account_id': account_id,
        'product_id': product_id
    }
    
    # Fazer a requisição ao MCP-Odoo
    try:
        logger.info(f"Chamando MCP-Odoo para gerar descrição para o produto {product_id}")
        response = requests.post(
            f"{mcp_url}/tools/generate_product_description",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        # Verificar resposta
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                logger.info("Descrição gerada com sucesso!")
                logger.info(f"Descrição: {result.get('description')}")
                return True
            else:
                logger.error(f"Erro do MCP-Odoo: {result.get('error')}")
        else:
            logger.error(f"Erro na chamada ao MCP-Odoo: {response.status_code} - {response.text}")
        
        return False
    except Exception as e:
        logger.error(f"Exceção ao chamar MCP-Odoo: {str(e)}")
        return False

def test_sync_product():
    """Testa a sincronização de produto com o banco de dados vetorial."""
    logger.info("Testando sincronização de produto com o banco de dados vetorial...")
    
    # Configurações do MCP-Odoo
    mcp_url = os.environ.get("MCP_ODOO_URL", "http://localhost:8000")
    mcp_token = os.environ.get("MCP_ODOO_TOKEN", "")
    account_id = os.environ.get("MCP_ODOO_ACCOUNT_ID", "account_2")
    product_id = int(os.environ.get("TEST_PRODUCT_ID", "1"))
    
    # Preparar a requisição
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {mcp_token}' if mcp_token else ''
    }
    
    payload = {
        'account_id': account_id,
        'product_id': product_id,
        'description': "Esta é uma descrição de teste para sincronização. Produto de alta qualidade com excelente acabamento e durabilidade. Ideal para uso em ambientes corporativos e residenciais."
    }
    
    # Fazer a requisição ao MCP-Odoo
    try:
        logger.info(f"Chamando MCP-Odoo para sincronizar produto {product_id}")
        response = requests.post(
            f"{mcp_url}/tools/sync_product_to_vector_db",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        # Verificar resposta
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                logger.info("Produto sincronizado com sucesso!")
                logger.info(f"Vector ID: {result.get('vector_id')}")
                return True
            else:
                logger.error(f"Erro do MCP-Odoo: {result.get('error')}")
        else:
            logger.error(f"Erro na chamada ao MCP-Odoo: {response.status_code} - {response.text}")
        
        return False
    except Exception as e:
        logger.error(f"Exceção ao chamar MCP-Odoo: {str(e)}")
        return False

def test_semantic_search():
    """Testa a busca semântica de produtos."""
    logger.info("Testando busca semântica de produtos...")
    
    # Configurações do MCP-Odoo
    mcp_url = os.environ.get("MCP_ODOO_URL", "http://localhost:8000")
    mcp_token = os.environ.get("MCP_ODOO_TOKEN", "")
    account_id = os.environ.get("MCP_ODOO_ACCOUNT_ID", "account_2")
    query = os.environ.get("TEST_SEARCH_QUERY", "produto de alta qualidade")
    
    # Preparar a requisição
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {mcp_token}' if mcp_token else ''
    }
    
    payload = {
        'account_id': account_id,
        'query': query,
        'limit': 5
    }
    
    # Fazer a requisição ao MCP-Odoo
    try:
        logger.info(f"Chamando MCP-Odoo para busca semântica: '{query}'")
        response = requests.post(
            f"{mcp_url}/tools/semantic_search",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        # Verificar resposta
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                logger.info("Busca realizada com sucesso!")
                logger.info(f"Resultados encontrados: {result.get('count')}")
                
                # Exibir resultados
                for i, item in enumerate(result.get('results', [])):
                    product_data = item.get('product_data', {})
                    logger.info(f"Resultado {i+1}:")
                    logger.info(f"  Produto: {product_data.get('name', 'N/A')}")
                    logger.info(f"  Preço: {product_data.get('price', 'N/A')}")
                    logger.info(f"  Score: {item.get('score', 'N/A')}")
                    logger.info("---")
                
                return True
            else:
                logger.error(f"Erro do MCP-Odoo: {result.get('error')}")
        else:
            logger.error(f"Erro na chamada ao MCP-Odoo: {response.status_code} - {response.text}")
        
        return False
    except Exception as e:
        logger.error(f"Exceção ao chamar MCP-Odoo: {str(e)}")
        return False

def main():
    """Função principal para testar a integração."""
    logger.info("Iniciando testes de integração...")
    
    # Testar geração de descrição
    if test_generate_description():
        logger.info("Teste de geração de descrição: SUCESSO")
    else:
        logger.error("Teste de geração de descrição: FALHA")
    
    # Testar sincronização de produto
    if test_sync_product():
        logger.info("Teste de sincronização de produto: SUCESSO")
    else:
        logger.error("Teste de sincronização de produto: FALHA")
    
    # Testar busca semântica
    if test_semantic_search():
        logger.info("Teste de busca semântica: SUCESSO")
    else:
        logger.error("Teste de busca semântica: FALHA")
    
    logger.info("Testes de integração concluídos.")

if __name__ == "__main__":
    main()
