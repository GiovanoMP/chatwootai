#!/usr/bin/env python3
"""
Script para verificar as conexões com os serviços (PostgreSQL, Redis, Qdrant).
"""

import os
import sys
import redis
import psycopg2
import requests
import json
from pathlib import Path
from tabulate import tabulate

# Carregar variáveis de ambiente do arquivo .env
try:
    from dotenv import load_dotenv
    # Carregar variáveis de ambiente do arquivo .env no diretório raiz do projeto
    dotenv_path = Path(__file__).resolve().parents[2] / '.env'
    load_dotenv(dotenv_path)
    print(f"Carregando variáveis de ambiente de: {dotenv_path}")
except ImportError:
    print("Pacote python-dotenv não instalado. Variáveis de ambiente não serão carregadas do arquivo .env")

def check_postgres_connection():
    """Verifica a conexão com o PostgreSQL."""
    print("\n===== Teste de Conexão PostgreSQL =====\n")
    
    # Variáveis de ambiente
    pg_host = os.environ.get('POSTGRES_HOST', 'localhost')
    pg_port = os.environ.get('POSTGRES_PORT', '5433')
    pg_user = os.environ.get('POSTGRES_USER', 'postgres')
    pg_password = os.environ.get('POSTGRES_PASSWORD', 'postgres')
    pg_db = os.environ.get('POSTGRES_DB', 'chatwootai')
    
    print(f"Variáveis de ambiente encontradas:")
    print(f"  POSTGRES_HOST: {pg_host}")
    print(f"  POSTGRES_PORT: {pg_port}")
    print(f"  POSTGRES_USER: {pg_user}")
    print(f"  POSTGRES_PASSWORD: {'***' if pg_password else 'Não definido'}")
    print(f"  POSTGRES_DB: {pg_db}\n")
    
    try:
        conn = psycopg2.connect(
            host=pg_host,
            port=pg_port,
            user=pg_user,
            password=pg_password,
            dbname=pg_db
        )
        
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"✅ Conexão PostgreSQL bem-sucedida!")
        print(f"   Versão: {version[0]}\n")
        
        # Listar tabelas
        cursor.execute("""
        SELECT 
            table_name, 
            (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = t.table_name) as column_count
        FROM 
            information_schema.tables t
        WHERE 
            table_schema = 'public' 
            AND table_type = 'BASE TABLE'
        ORDER BY 
            table_name;
        """)
        
        tables = cursor.fetchall()
        if tables:
            table_data = [[table[0], table[1]] for table in tables]
            print("Tabelas encontradas no banco de dados:")
            print(tabulate(table_data, headers=["Nome da Tabela", "Número de Colunas"], tablefmt="grid"))
        else:
            print("Nenhuma tabela encontrada no banco de dados.")
        
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Erro na conexão PostgreSQL: {str(e)}\n")
        return False

def check_redis_connection():
    """Verifica a conexão com o Redis."""
    print("\n===== Teste de Conexão Redis =====\n")
    
    # Variáveis de ambiente
    redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    redis_host = os.environ.get('REDIS_HOST', 'localhost')
    redis_port = os.environ.get('REDIS_PORT', '6379')
    redis_db = os.environ.get('REDIS_DB', '0')
    redis_password = os.environ.get('REDIS_PASSWORD', '')
    
    print(f"Variáveis de ambiente encontradas:")
    print(f"  REDIS_URL: {redis_url}")
    print(f"  REDIS_HOST: {redis_host}")
    print(f"  REDIS_PORT: {redis_port}")
    print(f"  REDIS_DB: {redis_db}")
    print(f"  REDIS_PASSWORD: {'***' if redis_password else 'Não definido'}\n")
    
    # Tentar conexão via parâmetros individuais
    try:
        client = redis.Redis(
            host=redis_host,
            port=int(redis_port),
            db=int(redis_db),
            password=redis_password if redis_password else None,
            decode_responses=True,
            socket_timeout=5
        )
        client.ping()
        print(f"✅ Conexão Redis bem-sucedida via parâmetros: {redis_host}:{redis_port}/{redis_db}")
        
        # Testar operações básicas
        client.set('test_key', 'Teste de conexão bem-sucedido!')
        value = client.get('test_key')
        print(f"   Operação SET/GET: {value}\n")
        
        # Listar algumas chaves se existirem
        keys = client.keys("*")
        if keys:
            print(f"Chaves encontradas no Redis (até 10 primeiras):")
            for i, key in enumerate(keys[:10]):
                value = client.get(key)
                value_preview = str(value)[:50] + "..." if len(str(value)) > 50 else value
                print(f"  {key}: {value_preview}")
            if len(keys) > 10:
                print(f"  ... e mais {len(keys) - 10} chaves")
        else:
            print("Nenhuma chave encontrada no Redis.")
            
        return True
    except Exception as e:
        print(f"❌ Erro na conexão Redis via parâmetros: {str(e)}\n")
        
        # Se falhar via parâmetros, tentar via URL
        try:
            client = redis.from_url(redis_url, decode_responses=True)
            client.ping()
            print(f"✅ Conexão Redis bem-sucedida via URL: {redis_url}")
            return True
        except Exception as e:
            print(f"❌ Erro na conexão Redis via URL: {str(e)}\n")
            return False

def check_qdrant_connection():
    """Verifica a conexão com o Qdrant."""
    print("\n===== Teste de Conexão Qdrant =====\n")
    
    # Variável de ambiente
    qdrant_url = os.environ.get('QDRANT_URL', 'http://localhost:6333')
    
    print(f"Variável de ambiente encontrada:")
    print(f"  QDRANT_URL: {qdrant_url}\n")
    
    try:
        # Testar API REST do Qdrant
        response = requests.get(f"{qdrant_url}/collections", timeout=5)
        
        if response.status_code == 200:
            collections = response.json()
            print(f"✅ Conexão Qdrant bem-sucedida!")
            print(f"   Status: {response.status_code}")
            
            # Listar coleções
            if 'result' in collections and 'collections' in collections['result']:
                collections_list = collections['result']['collections']
                if collections_list:
                    print("\nColeções encontradas no Qdrant:")
                    for collection in collections_list:
                        print(f"  - {collection['name']}")
                else:
                    print("\nNenhuma coleção encontrada no Qdrant.")
            else:
                print("\nFormato de resposta do Qdrant inesperado:", collections)
                
            return True
        else:
            print(f"❌ Erro na conexão Qdrant: Status {response.status_code}")
            print(f"   Resposta: {response.text}\n")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro na conexão Qdrant: {str(e)}\n")
        return False

def main():
    """Função principal."""
    print("\n" + "=" * 80)
    print("VERIFICAÇÃO DE CONEXÃO COM SERVIÇOS")
    print("=" * 80)
    
    # Verificar conexões
    pg_success = check_postgres_connection()
    redis_success = check_redis_connection()
    qdrant_success = check_qdrant_connection()
    
    # Resumo
    print("\n" + "=" * 80)
    print("RESUMO DAS VERIFICAÇÕES")
    print("=" * 80)
    
    print(f"PostgreSQL: {'✅ Conectado' if pg_success else '❌ Falha na conexão'}")
    print(f"Redis: {'✅ Conectado' if redis_success else '❌ Falha na conexão'}")
    print(f"Qdrant: {'✅ Conectado' if qdrant_success else '❌ Falha na conexão'}")
    
    if pg_success and redis_success and qdrant_success:
        print("\n✅ Todas as conexões estão funcionando corretamente!")
    else:
        print("\n⚠️ Algumas conexões falharam. Verifique os detalhes acima.")

if __name__ == "__main__":
    main()
