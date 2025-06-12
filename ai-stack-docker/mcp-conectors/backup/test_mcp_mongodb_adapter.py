#!/usr/bin/env python3
"""
Teste de integração entre CrewAI e MCP-MongoDB usando o MCPServerAdapter padrão.

Este script tenta diferentes configurações para conectar ao MCP-MongoDB:
1. Conexão direta com URL base
2. Conexão com URL base e transporte streamable-http
3. Conexão com URL específica para endpoint de ferramentas
"""

import sys
import requests
from crewai_tools import MCPServerAdapter
from crewai import Agent, Task, Crew

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

def print_section(title):
    print(f"\n{BLUE}{'=' * 60}{RESET}")
    print(f"{BLUE}== {title}{RESET}")
    print(f"{BLUE}{'=' * 60}{RESET}\n")

def verify_mcp_health(url):
    """Verifica se o MCP-MongoDB está acessível e saudável"""
    try:
        base_url = url.split("/")[0] + "//" + url.split("/")[2]
        health_url = f"{base_url}/health"
        print_info(f"Verificando saúde do MCP em: {health_url}")
        
        response = requests.get(health_url, timeout=5)
        response.raise_for_status()
        health_data = response.json()
        
        print_success(f"MCP está saudável: {health_data}")
        return True, health_data
    except Exception as e:
        print_error(f"Erro ao verificar saúde do MCP: {e}")
        return False, None

def test_mcp_connection(config, config_name):
    """Testa uma configuração específica do MCPServerAdapter"""
    print_section(f"TESTANDO CONFIGURAÇÃO: {config_name}")
    print_info(f"Configuração: {config}")
    
    adapter = None
    try:
        # Criar adaptador com a configuração especificada
        adapter = MCPServerAdapter(config)
        
        # Tentar obter ferramentas
        tools = adapter.tools
        tool_count = len(tools)
        
        print_success(f"Conexão estabelecida! Ferramentas descobertas: {tool_count}")
        
        # Listar ferramentas
        if tool_count > 0:
            print_info("Ferramentas disponíveis:")
            for i, tool in enumerate(tools):
                print(f"  {i+1}. {tool.name}: {tool.description}")
        
        return True, tools
    except Exception as e:
        print_error(f"Erro na conexão: {e}")
        return False, None
    finally:
        if adapter:
            try:
                adapter.stop()
            except:
                pass

def main():
    print_section("TESTE DE INTEGRAÇÃO CREWAI COM MCP-MONGODB")
    
    # URL base do MCP-MongoDB
    base_url = "http://localhost:8001"
    
    # Verificar saúde do MCP-MongoDB
    health_ok, _ = verify_mcp_health(base_url)
    if not health_ok:
        print_error("MCP-MongoDB não está acessível. Verifique se o serviço está em execução.")
        return False
    
    # Lista de configurações para testar
    configs = [
        {
            "name": "URL Base",
            "config": {"url": base_url}
        },
        {
            "name": "URL Base com Timeout Estendido",
            "config": {"url": base_url, "timeout": 60}
        },
        {
            "name": "URL Base com Transporte Streamable-HTTP",
            "config": {"url": base_url, "transport": "streamable-http"}
        },
        {
            "name": "URL Base com Transporte Streamable-HTTP e Timeout",
            "config": {"url": base_url, "transport": "streamable-http", "timeout": 60}
        },
        {
            "name": "URL Base com Tenant ID",
            "config": {"url": f"{base_url}?tenant=account_1"}
        },
        {
            "name": "URL de Ferramentas",
            "config": {"url": f"{base_url}/tools"}
        }
    ]
    
    # Testar cada configuração
    successful_configs = []
    
    for config_info in configs:
        success, tools = test_mcp_connection(config_info["config"], config_info["name"])
        if success:
            successful_configs.append((config_info["name"], config_info["config"], tools))
    
    # Resumo dos resultados
    print_section("RESUMO DOS RESULTADOS")
    
    if successful_configs:
        print_success(f"{len(successful_configs)} configurações bem-sucedidas:")
        for name, config, tools in successful_configs:
            print(f"  - {name}: {len(tools)} ferramentas")
        
        # Perguntar se deseja testar com CrewAI
        print_info("\nDeseja testar uma configuração bem-sucedida com CrewAI? (s/n)")
        choice = input().strip().lower()
        
        if choice == 's':
            # Usar a primeira configuração bem-sucedida
            name, config, tools = successful_configs[0]
            print_info(f"Testando CrewAI com configuração: {name}")
            
            try:
                # Criar agente com as ferramentas
                agent = Agent(
                    role="Analista de MongoDB",
                    goal="Consultar dados no MongoDB",
                    backstory="Especialista em análise de dados com MongoDB",
                    tools=tools,
                    verbose=True
                )
                
                # Criar tarefa
                task = Task(
                    description="Verifique quais ferramentas estão disponíveis e como usá-las",
                    agent=agent,
                    expected_output="Lista de ferramentas disponíveis e exemplos de uso"
                )
                
                # Criar e executar crew
                crew = Crew(
                    agents=[agent],
                    tasks=[task],
                    verbose=True
                )
                
                print_info("Executando tarefa com CrewAI...")
                result = crew.kickoff()
                
                print_success("Tarefa concluída com sucesso!")
                print_info("Resultado:")
                print(result)
                
            except Exception as e:
                print_error(f"Erro ao testar com CrewAI: {e}")
    else:
        print_error("Nenhuma configuração foi bem-sucedida.")
        print_warning("Será necessário implementar um adaptador personalizado.")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print_warning("\nTeste interrompido pelo usuário.")
        sys.exit(130)
