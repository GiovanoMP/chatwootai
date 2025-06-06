#!/usr/bin/env python3
"""
Teste de importação e funcionalidade básica do MCPServerAdapter do CrewAI
para conexão com servidores MCP (MongoDB e Redis).

Este script verifica:
1. Se o MCPServerAdapter pode ser importado
2. Se é possível conectar aos servidores MCP existentes
3. Se as ferramentas são descobertas corretamente
"""

import os
import sys
from typing import List, Dict, Any

# Cores para saída no terminal
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"

def print_success(message: str) -> None:
    """Imprime mensagem de sucesso em verde"""
    print(f"{GREEN}✅ {message}{RESET}")

def print_warning(message: str) -> None:
    """Imprime aviso em amarelo"""
    print(f"{YELLOW}⚠️ {message}{RESET}")

def print_error(message: str) -> None:
    """Imprime erro em vermelho"""
    print(f"{RED}❌ {message}{RESET}")

def print_info(message: str) -> None:
    """Imprime informação em azul"""
    print(f"{BLUE}ℹ️ {message}{RESET}")

def print_section(title: str) -> None:
    """Imprime título de seção"""
    print(f"\n{BLUE}{'=' * 50}{RESET}")
    print(f"{BLUE}== {title}{RESET}")
    print(f"{BLUE}{'=' * 50}{RESET}\n")

def test_imports() -> bool:
    """Testa se as importações necessárias funcionam"""
    print_section("TESTE DE IMPORTAÇÕES")
    
    try:
        from crewai_tools import MCPServerAdapter
        print_success("MCPServerAdapter importado com sucesso!")
        
        from crewai import Agent, Task, Crew
        print_success("CrewAI (Agent, Task, Crew) importado com sucesso!")
        
        return True
    except ImportError as e:
        print_error(f"Erro na importação: {e}")
        print_warning("Tente instalar as dependências com: pip install crewai-tools[mcp]")
        return False

def test_mcp_mongodb_connection() -> bool:
    """Testa conexão com o MCP-MongoDB"""
    print_section("TESTE DE CONEXÃO COM MCP-MONGODB")
    
    try:
        from crewai_tools import MCPServerAdapter
        
        # URL do MCP-MongoDB com transporte streamable-http
        # O MCP-MongoDB usa endpoints REST com streaming
        mongodb_url = "http://localhost:8001"
        print_info(f"Tentando conectar ao MCP-MongoDB em: {mongodb_url}")
        print_info("Usando transporte streamable-http para MCP-MongoDB")
        
        # Tenta conectar ao MCP-MongoDB com transporte streamable-http
        with MCPServerAdapter({"url": mongodb_url, "transport": "streamable-http"}) as mongodb_tools:
            tool_count = len(mongodb_tools)
            print_success(f"Conexão estabelecida com MCP-MongoDB!")
            print_success(f"Ferramentas descobertas: {tool_count}")
            
            # Lista as ferramentas disponíveis
            print_info("Ferramentas disponíveis:")
            for i, tool in enumerate(mongodb_tools):
                print(f"  {i+1}. {tool.name}: {tool.description}")
            
            return True
    except Exception as e:
        print_error(f"Erro ao conectar ao MCP-MongoDB: {e}")
        return False

def test_mcp_redis_connection() -> bool:
    """Testa conexão com o MCP-Redis"""
    print_section("TESTE DE CONEXÃO COM MCP-REDIS")
    
    try:
        from crewai_tools import MCPServerAdapter
        
        # URL do MCP-Redis (ajuste conforme necessário)
        redis_url = "http://localhost:8002/sse"
        print_info(f"Tentando conectar ao MCP-Redis em: {redis_url}")
        
        # Tenta conectar ao MCP-Redis
        with MCPServerAdapter({"url": redis_url}) as redis_tools:
            tool_count = len(redis_tools)
            print_success(f"Conexão estabelecida com MCP-Redis!")
            print_success(f"Ferramentas descobertas: {tool_count}")
            
            # Lista as ferramentas disponíveis
            print_info("Ferramentas disponíveis:")
            for i, tool in enumerate(redis_tools):
                print(f"  {i+1}. {tool.name}: {tool.description}")
            
            return True
    except Exception as e:
        print_error(f"Erro ao conectar ao MCP-Redis: {e}")
        return False

def main() -> None:
    """Função principal"""
    print_section("TESTE DO MCP ADAPTER DO CREWAI")
    print_info("Este script verifica a disponibilidade e funcionalidade do MCPServerAdapter")
    
    # Testa importações
    if not test_imports():
        print_error("Falha nos testes de importação. Abortando.")
        sys.exit(1)
    
    # Testa conexão com MCP-MongoDB
    mongodb_ok = test_mcp_mongodb_connection()
    
    # Testa conexão com MCP-Redis
    redis_ok = test_mcp_redis_connection()
    
    # Resumo
    print_section("RESUMO DOS TESTES")
    if mongodb_ok:
        print_success("MCP-MongoDB: Conexão bem-sucedida")
    else:
        print_error("MCP-MongoDB: Falha na conexão")
        
    if redis_ok:
        print_success("MCP-Redis: Conexão bem-sucedida")
    else:
        print_error("MCP-Redis: Falha na conexão")
    
    if mongodb_ok and redis_ok:
        print_success("Todos os testes passaram! O MCPServerAdapter está funcionando corretamente.")
    elif mongodb_ok or redis_ok:
        print_warning("Alguns testes passaram. Verifique os erros acima.")
    else:
        print_error("Todos os testes falharam. Verifique se os servidores MCP estão em execução.")

if __name__ == "__main__":
    main()
