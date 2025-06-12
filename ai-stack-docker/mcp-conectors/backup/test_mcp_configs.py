#!/usr/bin/env python3
"""
Teste de diferentes configurações para o MCPServerAdapter
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

def print_warning(message):
    print(f"{YELLOW}⚠️ {message}{RESET}")

def test_direct_http():
    """Testa a conexão direta via HTTP com o MCP-MongoDB"""
    print_info("Verificando conexão HTTP direta com MCP-MongoDB...")
    
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
        
        return True
    except Exception as e:
        print_error(f"Erro na conexão HTTP direta: {e}")
        return False

def test_config(config, name):
    """Testa uma configuração específica do MCPServerAdapter"""
    print_info(f"Testando configuração: {name}")
    print_info(f"Parâmetros: {json.dumps(config)}")
    
    try:
        # Criar adaptador com timeout reduzido para falhar mais rápido
        adapter = MCPServerAdapter(config)
        
        # Tentar obter ferramentas
        tools = adapter.tools
        
        # Verificar se obteve ferramentas
        tool_count = len(tools)
        print_success(f"Conexão estabelecida! Ferramentas descobertas: {tool_count}")
        
        # Listar ferramentas
        if tool_count > 0:
            for i, tool in enumerate(tools):
                print(f"  {i+1}. {tool.name}: {tool.description}")
        
        # Fechar adaptador
        adapter.stop()
        return True
    except Exception as e:
        print_error(f"Falha na configuração {name}: {e}")
        return False

def main():
    print(f"{BLUE}{'=' * 60}{RESET}")
    print(f"{BLUE}== TESTE DE CONFIGURAÇÕES PARA MCP-MONGODB{RESET}")
    print(f"{BLUE}{'=' * 60}{RESET}")
    
    # Verificar conexão direta
    if not test_direct_http():
        print_error("Falha na conexão direta. Verifique se o MCP-MongoDB está em execução.")
        return False
    
    print(f"{BLUE}{'=' * 60}{RESET}")
    
    # Lista de configurações a serem testadas
    configs = [
        {
            "name": "URL Base",
            "config": {"url": "http://localhost:8001"}
        },
        {
            "name": "URL Base com Timeout",
            "config": {"url": "http://localhost:8001", "timeout": 5}
        },
        {
            "name": "URL com /tools",
            "config": {"url": "http://localhost:8001/tools"}
        },
        {
            "name": "Transporte HTTP",
            "config": {"url": "http://localhost:8001", "transport": "http"}
        },
        {
            "name": "Transporte Streamable-HTTP",
            "config": {"url": "http://localhost:8001", "transport": "streamable-http"}
        },
        {
            "name": "Transporte REST",
            "config": {"url": "http://localhost:8001", "transport": "rest"}
        }
    ]
    
    # Testar cada configuração
    results = {}
    for config_info in configs:
        name = config_info["name"]
        config = config_info["config"]
        
        print(f"{BLUE}{'=' * 40}{RESET}")
        success = test_config(config, name)
        results[name] = success
        
        if success:
            print_success(f"Configuração '{name}' funcionou!")
            # Se encontrou uma configuração que funciona, podemos parar
            break
        else:
            print_warning(f"Configuração '{name}' falhou. Tentando próxima...")
    
    # Resumo
    print(f"{BLUE}{'=' * 60}{RESET}")
    print(f"{BLUE}== RESUMO DOS TESTES{RESET}")
    print(f"{BLUE}{'=' * 60}{RESET}")
    
    success_found = False
    for name, success in results.items():
        status = f"{GREEN}✅ SUCESSO{RESET}" if success else f"{RED}❌ FALHA{RESET}"
        print(f"{name}: {status}")
        if success:
            success_found = True
    
    if success_found:
        print_success("Pelo menos uma configuração funcionou! Use-a para integrar com CrewAI.")
    else:
        print_error("Nenhuma configuração funcionou. Considere as seguintes opções:")
        print_info("1. Verifique se o MCP-MongoDB suporta o protocolo MCP esperado pelo CrewAI")
        print_info("2. Considere implementar um adaptador personalizado")
        print_info("3. Use as ferramentas do MCP-MongoDB diretamente via API REST")
    
    return success_found

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print_warning("\nTeste interrompido pelo usuário.")
        sys.exit(130)
