#!/usr/bin/env python3
"""
Script para verificar o status dos serviços do ChatwootAI
Independente dos healthchecks do Docker

Este script verifica a saúde de todos os serviços do ChatwootAI,
incluindo serviços de infraestrutura e MCPs.
"""

import requests
import json
import socket
import time
import os
import sys
import redis
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from dotenv import load_dotenv

def check_http_service(name, url, path="/health", timeout=5):
    """Verifica um serviço HTTP"""
    try:
        full_url = f"{url.rstrip('/')}{path}"
        print(f"Verificando {name} em {full_url}...")
        response = requests.get(full_url, timeout=timeout)
        if response.status_code < 400:
            print(f"\u2705 {name}: OK (status {response.status_code})")
            return {"status": "healthy", "code": response.status_code}
        else:
            print(f"\u274c {name}: FALHA (status {response.status_code})")
            return {"status": "error", "error": f"HTTP status {response.status_code}"}
    except Exception as e:
        print(f"\u274c {name}: ERRO ({str(e)})")
        return {"status": "error", "error": str(e)}

def check_redis(host="localhost", port=6379, password=None):
    """Verifica conexão com Redis"""
    try:
        print(f"Verificando Redis em {host}:{port}...")
        r = redis.Redis(host=host, port=port, password=password, socket_connect_timeout=5)
        if r.ping():
            info = r.info()
            print(f"✅ Redis: OK (versão {info.get('redis_version')})")
            return {"status": "up", "version": info.get('redis_version')}
        else:
            print("❌ Redis: FALHA (ping falhou)")
            return {"status": "down", "error": "Ping falhou"}
    except Exception as e:
        print(f"❌ Redis: ERRO ({str(e)})")
        return {"status": "error", "error": str(e)}

def check_mongodb(uri="mongodb://localhost:27017/"):
    """Verifica conexão com MongoDB"""
    try:
        print(f"Verificando MongoDB em {uri}...")
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        client.admin.command('ismaster')
        server_info = client.server_info()
        print(f"✅ MongoDB: OK (versão {server_info.get('version')})")
        return {"status": "up", "version": server_info.get('version')}
    except ConnectionFailure as e:
        print(f"❌ MongoDB: FALHA ({str(e)})")
        return {"status": "down", "error": str(e)}
    except Exception as e:
        print(f"❌ MongoDB: ERRO ({str(e)})")
        return {"status": "error", "error": str(e)}

def check_socket(host, port, service_name, timeout=5):
    """Verifica se uma porta está aberta"""
    try:
        print(f"Verificando {service_name} em {host}:{port}...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            print(f"✅ {service_name}: OK (porta aberta)")
            return {"status": "up", "details": "Porta aberta"}
        else:
            print(f"❌ {service_name}: FALHA (porta fechada)")
            return {"status": "down", "error": f"Porta fechada (erro {result})"}
    except Exception as e:
        print(f"❌ {service_name}: ERRO ({str(e)})")
        return {"status": "error", "error": str(e)}

def load_env_vars():
    """Carrega variáveis de ambiente do arquivo .env"""
    try:
        # Carregar variáveis do arquivo .env na raiz do projeto
        dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
        load_dotenv(dotenv_path)
        print(f"Variáveis de ambiente carregadas de {dotenv_path}")
        return True
    except Exception as e:
        print(f"Erro ao carregar variáveis de ambiente: {e}")
        return False

def main():
    """Função principal"""
    results = {}
    
    # Carregar variáveis de ambiente do arquivo .env centralizado
    load_env_vars()
    redis_password = os.getenv('REDIS_PASSWORD', '')
    mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017')
    qdrant_url = os.getenv('QDRANT_URL', 'http://localhost:6333')
    
    print(f"\n=== Verificando serviços do ChatwootAI ===\n")
    print(f"Data e hora: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Verificar serviços básicos
    print("\n[1/3] Verificando serviços de infraestrutura...")
    results["redis"] = check_redis(host="localhost", port=6379, password=redis_password)
    results["mongodb"] = check_mongodb(mongodb_uri.replace('ai-mongodb', 'localhost'))
    results["qdrant"] = check_http_service("Qdrant", qdrant_url.replace('ai-qdrant', 'localhost'), path="/healthz")
    
    # Verificar MCPs existentes
    print("\n[2/3] Verificando serviços MCP...")
    # Nota: O MCP-Odoo ainda não foi implementado, então não está incluído
    results["mcp-postgres"] = check_http_service("MCP-Postgres", "http://localhost:8005")
    
    # Verificar serviço de monitoramento
    print("\n[3/3] Verificando serviço de monitoramento...")
    results["uptime-kuma"] = check_http_service("Uptime Kuma", "http://localhost:3001", path="/")
    
    
    # Exibir resumo
    print("\n=== Resumo dos Serviços ===\n")
    healthy = 0
    unhealthy = 0
    
    for service, result in results.items():
        status = result.get("status", "error")
        if status == "healthy":
            healthy += 1
        else:
            unhealthy += 1
    
    print(f"Serviços saudáveis: {healthy}")
    print(f"Serviços com problemas: {unhealthy}")
    
    if unhealthy > 0:
        print("\nServiços com problemas:")
        for service, result in results.items():
            if result.get("status", "error") != "healthy":
                error = result.get("error", "Erro desconhecido")
                print(f"  - {service}: {error}")
    
    # Sugestões para configuração no Uptime Kuma
    print("\n=== Configurações para Uptime Kuma ===\n")
    print("Acesse o Uptime Kuma em: http://localhost:3001")
    print("Configure os seguintes monitores:")
    
    # Serviços de infraestrutura
    print("\n1. Serviços de Infraestrutura:")
    print("  - Redis: TCP em ai-redis:6379 (com senha)")
    print("  - MongoDB: TCP em ai-mongodb:27017")
    print("  - Qdrant: HTTP em http://ai-qdrant:6333/healthz")
    
    # Serviços MCP
    print("\n2. Serviços MCP:")
    print("  - MCP-Postgres: HTTP em http://mcp-postgres:8000/health")
    
    # Nota sobre serviços futuros
    print("\n3. Serviços a serem adicionados futuramente:")
    print("  - MCP-Odoo: Quando implementado")
    print("  - MCP-MongoDB: Quando implementado")
    print("  - MCP-Qdrant: Quando implementado")
    print("  - MCP-Redis: Quando implementado")
    
    # Salvar resultados em JSON se solicitado
    if '--json' in sys.argv:
        output_file = 'service_status.json'
        with open(output_file, 'w') as f:
            json.dump({
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'services': results,
                'summary': {
                    'healthy': healthy,
                    'unhealthy': unhealthy,
                    'total': healthy + unhealthy
                }
            }, f, indent=2)
        print(f"\nResultados salvos em {output_file}")

if __name__ == "__main__":
    main()
