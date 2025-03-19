#!/usr/bin/env python3
"""
Script para atualizar o esquema da tabela products, adicionando a coluna detailed_description.
"""
import os
import sys
import logging
from dotenv import load_dotenv

# Adicionar o diretório raiz do projeto ao sys.path para poder importar os módulos
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

# Importar após configurar o sys.path
from src.services.data.data_service_hub import DataServiceHub

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_product_schema():
    """Atualiza o esquema da tabela products."""
    # Carregar variáveis de ambiente
    env_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
    load_dotenv(env_path)
    print(f"Carregando variáveis de ambiente de: {env_path}")
    
    # Inicializar o hub de serviços de dados
    hub = DataServiceHub()
    
    # Verificar se a coluna já existe
    check_column_query = """
    SELECT column_name 
    FROM information_schema.columns 
    WHERE table_name = 'products' 
    AND column_name = 'detailed_description';
    """
    
    result = hub.execute_query(check_column_query, {})
    
    if result and len(result) > 0:
        print("A coluna 'detailed_description' já existe na tabela 'products'.")
        return True
    
    # Adicionar a coluna
    try:
        add_column_query = """
        ALTER TABLE products 
        ADD COLUMN detailed_description TEXT;
        """
        
        hub.execute_query(add_column_query, {})
        print("✅ Coluna 'detailed_description' adicionada com sucesso à tabela 'products'.")
        return True
    except Exception as e:
        print(f"❌ Erro ao adicionar coluna 'detailed_description': {str(e)}")
        return False

if __name__ == "__main__":
    update_product_schema()
