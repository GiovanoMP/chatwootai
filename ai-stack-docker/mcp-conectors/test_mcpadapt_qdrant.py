#!/usr/bin/env python3
"""
Teste de conexão com MCP-Qdrant usando MCPAdapt.
Este script verifica a conexão e lista as ferramentas disponíveis.
"""

import os
import sys
from dotenv import load_dotenv
from mcpadapt.core import MCPAdapt
from mcpadapt.crewai_adapter import CrewAIAdapter

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# Cores para saída no terminal
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"

def print_info(message):
    """Imprime mensagem informativa"""
    print(f"{YELLOW}ℹ️ {message}{RESET}")

def print_success(message):
    """Imprime mensagem de sucesso"""
    print(f"{GREEN}✅ {message}{RESET}")

def print_error(message):
    """Imprime mensagem de erro"""
    print(f"{RED}❌ {message}{RESET}")

def print_section(title):
    """Imprime título de seção"""
    print(f"{BLUE}{'=' * 60}{RESET}")
    print(f"{BLUE}== {title}{RESET}")
    print(f"{BLUE}{'=' * 60}{RESET}")

def test_qdrant_connection():
    """Testa a conexão com o MCP-Qdrant usando o MCPAdapt"""
    print_section("TESTE DE CONEXÃO COM MCP-QDRANT USANDO MCPADAPT")
    
    # URL do MCP-Qdrant com transporte SSE
    qdrant_url = os.getenv("MCP_QDRANT_URL", "http://localhost:8003/sse")
    collection_name = os.getenv("QDRANT_COLLECTION", "memories")
    print_info(f"Tentando conectar ao MCP-Qdrant em: {qdrant_url}")
    print_info(f"Coleção configurada: {collection_name}")
    
    try:
        # Configuração para conexão SSE
        sse_config = {
            "url": qdrant_url,
            "timeout": 10,  # Timeout em segundos
        }
        
        # Tenta conectar ao MCP-Qdrant usando MCPAdapt
        with MCPAdapt(sse_config, CrewAIAdapter()) as tools:
            tool_count = len(tools)
            print_success(f"Conexão estabelecida com MCP-Qdrant!")
            print_success(f"Ferramentas descobertas: {tool_count}")
            
            # Listar ferramentas disponíveis
            print_info("Ferramentas disponíveis:")
            for i, tool in enumerate(tools, 1):
                print(f"  {i}. {tool.name}")
                print(f"     Descrição: {tool.description}")
                
                # Mostrar detalhes dos parâmetros
                try:
                    schema = tool.args_schema.schema()
                    if 'properties' in schema:
                        print(f"     Parâmetros:")
                        for param_name, param_info in schema['properties'].items():
                            param_type = param_info.get('type', 'any')
                            param_desc = param_info.get('description', 'Sem descrição')
                            print(f"       - {param_name} ({param_type}): {param_desc}")
                except Exception as e:
                    print(f"     Erro ao obter parâmetros: {e}")
                print("")
        
        return True
    except Exception as e:
        print_error(f"Erro ao conectar ao MCP-Qdrant: {str(e)}")
        return False

def main():
    """Função principal"""
    print_section("TESTE DE CONEXÃO MCP-QDRANT COM MCPADAPT")
    
    # Testar conexão com MCP-Qdrant
    success = test_qdrant_connection()
    
    print_section("RESULTADO")
    if success:
        print_success("Conexão bem-sucedida com MCP-Qdrant usando MCPAdapt!")
        print_info("O MCPAdapt está pronto para ser usado com CrewAI.")
        print_info("Para usar em seu código:")
        print("""
from mcpadapt.core import MCPAdapt
from mcpadapt.crewai_adapter import CrewAIAdapter
from crewai import Agent, Task, Crew

# Configuração para conexão SSE
sse_config = {
    "url": "http://localhost:8003/sse",
    "timeout": 10,  # Timeout em segundos
}

# Conectar ao MCP-Qdrant
with MCPAdapt(sse_config, CrewAIAdapter()) as tools:
    # Criar agente com as ferramentas
    agent = Agent(
        role="Seu Agente",
        goal="Objetivo do Agente",
        tools=tools  # Todas as ferramentas do MCP-Qdrant
    )
    
    # Criar tarefa
    task = Task(
        description="Descrição da tarefa",
        expected_output="Saída esperada",
        agent=agent
    )
    
    # Criar e executar o crew
    crew = Crew(
        agents=[agent],
        tasks=[task],
        verbose=True
    )
    result = crew.kickoff()
        """)
    else:
        print_error("Falha na conexão com MCP-Qdrant.")
        print_info("Verifique se o servidor MCP-Qdrant está em execução na porta 8003.")
        print_info("Certifique-se de que o endpoint SSE está disponível em /sse.")
        print_info("Verifique se o MCP-Qdrant está configurado para usar transporte SSE com o comando 'uvx mcp-server-qdrant --transport sse'.")
        print_info("Lembre-se que o MCP-Qdrant não expõe endpoints HTTP tradicionais, apenas SSE.")
        return False
    
    return True

if __name__ == "__main__":
    main()
