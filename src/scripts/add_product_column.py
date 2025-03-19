#!/usr/bin/env python3
"""
Script para adicionar a coluna detailed_description à tabela products.
"""
import psycopg2
import os
from dotenv import load_dotenv

def add_column():
    """Adiciona a coluna detailed_description à tabela products."""
    # Carregar variáveis de ambiente
    env_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
    load_dotenv(env_path)
    
    # Configurações de conexão
    conn_params = {
        'host': os.environ.get('POSTGRES_HOST', 'localhost'),
        'port': os.environ.get('POSTGRES_PORT', '5433'),
        'user': os.environ.get('POSTGRES_USER', 'postgres'),
        'password': os.environ.get('POSTGRES_PASSWORD', 'postgres'),
        'database': os.environ.get('POSTGRES_DB', 'chatwootai')
    }
    
    print(f"Conectando ao PostgreSQL: {conn_params['host']}:{conn_params['port']}/{conn_params['database']}")
    
    try:
        # Conectar ao banco de dados
        conn = psycopg2.connect(**conn_params)
        conn.autocommit = True  # Importante para evitar transações abertas
        cursor = conn.cursor()
        
        # Verificar se a coluna já existe
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'products' 
            AND column_name = 'detailed_description';
        """)
        
        exists = cursor.fetchone()
        
        if exists:
            print("A coluna 'detailed_description' já existe na tabela 'products'.")
        else:
            # Adicionar a coluna
            cursor.execute("""
                ALTER TABLE products 
                ADD COLUMN detailed_description TEXT;
            """)
            print("✅ Coluna 'detailed_description' adicionada com sucesso à tabela 'products'.")
            
        # Fechar conexão
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        return False

if __name__ == "__main__":
    add_column()
