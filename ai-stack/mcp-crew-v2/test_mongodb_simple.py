#!/usr/bin/env python3
"""
Teste simplificado para conexão com o MCP-MongoDB
"""

import sys
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

def main():
    print(f"{BLUE}Testando conexão com MCP-MongoDB...{RESET}")
    
    try:
        # URL do MCP-MongoDB
        mongodb_url = "http://localhost:8001"
        print_info(f"Tentando conectar ao MCP-MongoDB em: {mongodb_url}")
        
        # Tenta conectar ao MCP-MongoDB
        with MCPServerAdapter({"url": mongodb_url}) as mongodb_tools:
            tool_count = len(mongodb_tools)
            print_success(f"Conexão estabelecida com MCP-MongoDB!")
            print_success(f"Ferramentas descobertas: {tool_count}")
            
            # Lista as ferramentas disponíveis
            print_info("Ferramentas disponíveis:")
            for i, tool in enumerate(mongodb_tools):
                print(f"  {i+1}. {tool.name}: {tool.description}")
                
    except Exception as e:
        print_error(f"Erro ao conectar ao MCP-MongoDB: {e}")
        return False
        
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
