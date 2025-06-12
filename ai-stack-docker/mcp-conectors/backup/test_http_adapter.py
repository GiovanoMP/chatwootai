#!/usr/bin/env python3
"""
Teste simplificado para conexão com o MCP-MongoDB usando transporte HTTP
"""

import sys
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

def test_direct_http():
    """Testa a conexão direta via HTTP com o MCP-MongoDB"""
    print_info("Testando conexão HTTP direta com MCP-MongoDB...")
    
    try:
        # Verificar endpoint de saúde
        health_response = requests.get("http://localhost:8001/health")
        health_response.raise_for_status()
        health_data = health_response.json()
        print_success(f"Endpoint de saúde respondeu: {health_data}")
        
        # Verificar endpoint de ferramentas
        tools_response = requests.get("http://localhost:8001/tools")
        tools_response.raise_for_status()
        tools_data = tools_response.json()
        print_success(f"Endpoint de ferramentas respondeu com {len(tools_data['tools'])} ferramentas")
        
        # Listar ferramentas
        print_info("Ferramentas disponíveis:")
        for i, tool in enumerate(tools_data['tools']):
            print(f"  {i+1}. {tool['name']}: {tool['description']}")
            
        return True
    except Exception as e:
        print_error(f"Erro na conexão HTTP direta: {e}")
        return False

def test_mcp_adapter():
    """Testa o MCPServerAdapter com o MCP-MongoDB"""
    print_info("Testando MCPServerAdapter com MCP-MongoDB...")
    
    try:
        # Configuração para o MCP-MongoDB
        mongodb_config = {
            "url": "http://localhost:8001",
            "transport": "streamable-http"  # Usar o transporte streamable-http
        }
        print_info(f"Configuração: {mongodb_config}")
        
        # Tenta conectar ao MCP-MongoDB
        adapter = MCPServerAdapter(mongodb_config)
        mongodb_tools = adapter.tools
        
        tool_count = len(mongodb_tools)
        print_success(f"Conexão estabelecida com MCPServerAdapter!")
        print_success(f"Ferramentas descobertas via MCPServerAdapter: {tool_count}")
        
        # Lista as ferramentas disponíveis
        if tool_count > 0:
            print_info("Ferramentas disponíveis via MCPServerAdapter:")
            for i, tool in enumerate(mongodb_tools):
                print(f"  {i+1}. {tool.name}: {tool.description}")
        
        # Fechar o adaptador
        adapter.stop()
        return True
    except Exception as e:
        print_error(f"Erro ao conectar via MCPServerAdapter: {e}")
        print_info("Detalhes do erro para diagnóstico:")
        import traceback
        traceback.print_exc()
        return False

def main():
    print(f"{BLUE}{'=' * 50}{RESET}")
    print(f"{BLUE}== TESTE DE CONEXÃO COM MCP-MONGODB{RESET}")
    print(f"{BLUE}{'=' * 50}{RESET}")
    
    # Testar conexão HTTP direta
    http_success = test_direct_http()
    
    print(f"{BLUE}{'=' * 50}{RESET}")
    
    # Testar MCPServerAdapter
    adapter_success = test_mcp_adapter()
    
    # Resumo
    print(f"{BLUE}{'=' * 50}{RESET}")
    print(f"{BLUE}== RESUMO{RESET}")
    print(f"{BLUE}{'=' * 50}{RESET}")
    
    if http_success:
        print_success("Conexão HTTP direta com MCP-MongoDB funciona corretamente!")
    else:
        print_error("Falha na conexão HTTP direta com MCP-MongoDB")
    
    if adapter_success:
        print_success("MCPServerAdapter conectou com sucesso ao MCP-MongoDB!")
    else:
        print_error("Falha na conexão via MCPServerAdapter")
        print_info("Sugestões para resolver o problema:")
        print_info("1. Verifique se o MCPServerAdapter suporta transporte HTTP")
        print_info("2. Verifique se as versões do MCP e crewai-tools são compatíveis")
        print_info("3. Considere implementar um adaptador personalizado para o MCP-MongoDB")
    
    return http_success and adapter_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
