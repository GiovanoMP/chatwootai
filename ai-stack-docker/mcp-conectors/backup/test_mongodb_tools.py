#!/usr/bin/env python3
"""
Teste para conexão com o MCP-MongoDB usando a configuração correta
"""

import sys
import json
import requests
from crewai_tools import MCPServerAdapter

# Cores para saída no terminal
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"

def print_success(message):
    print(f"{GREEN}✅ {message}{RESET}")

def print_error(message):
    print(f"{RED}❌ {message}{RESET}")

def print_info(message):
    print(f"{BLUE}ℹ️ {message}{RESET}")

def check_mongodb_health():
    """Verifica se o MCP-MongoDB está saudável"""
    try:
        response = requests.get("http://localhost:8001/health")
        response.raise_for_status()
        health_data = response.json()
        print_success(f"MCP-MongoDB está saudável: {json.dumps(health_data)}")
        return True
    except Exception as e:
        print_error(f"Erro ao verificar saúde do MCP-MongoDB: {e}")
        return False

def check_mongodb_tools():
    """Verifica as ferramentas disponíveis no MCP-MongoDB"""
    try:
        response = requests.get("http://localhost:8001/tools")
        response.raise_for_status()
        tools_data = response.json()
        print_success(f"MCP-MongoDB tem {len(tools_data['tools'])} ferramentas disponíveis")
        
        print_info("Ferramentas disponíveis:")
        for i, tool in enumerate(tools_data['tools']):
            print(f"  {i+1}. {tool['name']}: {tool['description']}")
        
        return tools_data
    except Exception as e:
        print_error(f"Erro ao verificar ferramentas do MCP-MongoDB: {e}")
        return None

def test_mcp_adapter():
    """Testa o MCPServerAdapter com o MCP-MongoDB"""
    print_info("Testando MCPServerAdapter com MCP-MongoDB...")
    
    try:
        # Configuração para o MCP-MongoDB
        # Tentando com o endpoint /sse que é o padrão esperado pelo MCPServerAdapter
        mongodb_url = "http://localhost:8001/sse"
        print_info(f"Tentando conectar ao MCP-MongoDB em: {mongodb_url}")
        
        # Tenta conectar ao MCP-MongoDB
        with MCPServerAdapter({"url": mongodb_url}) as mongodb_tools:
            tool_count = len(mongodb_tools)
            print_success(f"Conexão estabelecida com MCPServerAdapter!")
            print_success(f"Ferramentas descobertas via MCPServerAdapter: {tool_count}")
            
            # Lista as ferramentas disponíveis
            if tool_count > 0:
                print_info("Ferramentas disponíveis via MCPServerAdapter:")
                for i, tool in enumerate(mongodb_tools):
                    print(f"  {i+1}. {tool.name}: {tool.description}")
            
            return True
    except Exception as e:
        print_error(f"Erro ao conectar via MCPServerAdapter: {e}")
        print_info("O MCP-MongoDB pode não estar configurado para suportar o protocolo SSE no endpoint /sse")
        print_info("Você pode precisar usar endpoints REST diretamente para acessar as ferramentas")
        return False

def main():
    print(f"{BLUE}{'=' * 50}{RESET}")
    print(f"{BLUE}== TESTE DETALHADO DO MCP-MONGODB{RESET}")
    print(f"{BLUE}{'=' * 50}{RESET}")
    
    # Verifica saúde do MCP-MongoDB
    if not check_mongodb_health():
        print_error("MCP-MongoDB não está saudável. Verifique se o serviço está em execução.")
        return False
    
    # Verifica ferramentas disponíveis
    tools_data = check_mongodb_tools()
    if not tools_data:
        print_error("Não foi possível obter as ferramentas do MCP-MongoDB.")
        return False
    
    # Testa MCPServerAdapter
    adapter_success = test_mcp_adapter()
    
    # Resumo
    print(f"{BLUE}{'=' * 50}{RESET}")
    print(f"{BLUE}== RESUMO{RESET}")
    print(f"{BLUE}{'=' * 50}{RESET}")
    
    if adapter_success:
        print_success("MCPServerAdapter conectou com sucesso ao MCP-MongoDB!")
    else:
        print_info("Para usar as ferramentas do MCP-MongoDB com CrewAI, você pode:")
        print_info("1. Configurar o MCP-MongoDB para suportar SSE no endpoint /sse")
        print_info("2. Implementar um adaptador personalizado que use os endpoints REST")
        print_info("3. Usar as ferramentas diretamente via API REST")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
