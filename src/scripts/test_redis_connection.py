#!/usr/bin/env python3
"""
Script para testar a conexão com o Redis.
"""

import os
import sys
import redis
from pathlib import Path

# Carregar variáveis de ambiente do arquivo .env
try:
    from dotenv import load_dotenv
    # Carregar variáveis de ambiente do arquivo .env no diretório raiz do projeto
    dotenv_path = Path(__file__).resolve().parents[2] / '.env'
    load_dotenv(dotenv_path)
    print(f"Carregando variáveis de ambiente de: {dotenv_path}")
except ImportError:
    print("Pacote python-dotenv não instalado. Variáveis de ambiente não serão carregadas do arquivo .env")

def test_redis_connection():
    """Testa a conexão com o Redis usando diferentes abordagens."""
    print("\n===== Teste de Conexão Redis =====\n")
    
    # Verificar variáveis de ambiente
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
    
    # Teste 1: Conexão via URL
    print("Teste 1: Tentando conectar via URL...")
    try:
        client = redis.from_url(redis_url, decode_responses=True)
        client.ping()
        print(f"✅ Conexão bem-sucedida via URL: {redis_url}\n")
        
        # Testar operações básicas
        client.set('test_key', 'test_value')
        value = client.get('test_key')
        print(f"Operação SET/GET: {value}\n")
    except Exception as e:
        print(f"❌ Erro na conexão via URL: {str(e)}\n")
    
    # Teste 2: Conexão via parâmetros individuais
    print("Teste 2: Tentando conectar via parâmetros individuais...")
    try:
        client = redis.Redis(
            host=redis_host,
            port=int(redis_port),
            db=int(redis_db),
            password=redis_password if redis_password else None,
            decode_responses=True
        )
        client.ping()
        print(f"✅ Conexão bem-sucedida via parâmetros: {redis_host}:{redis_port}/{redis_db}\n")
        
        # Testar operações básicas
        client.set('test_key2', 'test_value2')
        value = client.get('test_key2')
        print(f"Operação SET/GET: {value}\n")
    except Exception as e:
        print(f"❌ Erro na conexão via parâmetros: {str(e)}\n")
    
    # Teste 3: Tentar conexão direta com IP do container Docker
    print("Teste 3: Tentando conectar diretamente com IP do container Docker...")
    
    # Testar diferentes IPs comuns em redes Docker
    ips_to_try = [
        '172.24.0.3',  # IP atual do container
        '172.24.0.5',  # IP que estava sendo usado
        '172.17.0.1',  # IP gateway padrão da rede bridge
        '127.0.0.1'    # localhost
    ]
    
    for ip in ips_to_try:
        print(f"Testando conexão com IP: {ip}")
        try:
            client = redis.Redis(
                host=ip,
                port=6379,
                db=0,
                socket_timeout=5,
                decode_responses=True
            )
            client.ping()
            print(f"✅ Conexão bem-sucedida com IP: {ip}\n")
            
            # Testar operações básicas
            test_key = f"test_key_{ip.replace('.', '_')}"
            client.set(test_key, f"test_value_{ip}")
            value = client.get(test_key)
            print(f"Operação SET/GET: {value}\n")
            break
        except Exception as e:
            print(f"❌ Erro na conexão com IP {ip}: {str(e)}\n")

def main():
    """Função principal."""
    test_redis_connection()

if __name__ == "__main__":
    main()
