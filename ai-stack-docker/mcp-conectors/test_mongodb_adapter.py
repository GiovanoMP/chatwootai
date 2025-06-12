#!/usr/bin/env python3
"""
Teste do adaptador personalizado para MCP-MongoDB com CrewAI
"""

import sys
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()
from mongodb_adapter import MongoDBAdapter
from crewai import Agent, Task, Crew, Process

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

def test_adapter_connection():
    """Testa a conexão do adaptador com o MCP-MongoDB"""
    print_info("Testando conexão com MCP-MongoDB via adaptador personalizado...")
    
    try:
        # Criar adaptador usando URL do arquivo .env ou padrão
        mcp_mongodb_url = os.getenv("MCP_MONGODB_URL", "http://localhost:8001")
        tenant_id = os.getenv("TENANT_ID", "account_1")
        adapter = MongoDBAdapter(base_url=mcp_mongodb_url, tenant_id=tenant_id)
        
        # Verificar saúde
        health = adapter.check_health()
        print_success(f"Servidor MCP-MongoDB está saudável: {health}")
        
        # Obter ferramentas
        tools = adapter.tools
        print_success(f"Ferramentas descobertas: {len(tools)}")
        
        # Listar ferramentas
        print_info("Ferramentas disponíveis:")
        for i, tool in enumerate(tools):
            print(f"  {i+1}. {tool.name}")
            print(f"     {tool.description.split('Parâmetros:')[0].strip()}")
        
        return True, tools
    except Exception as e:
        print_error(f"Erro ao conectar com MCP-MongoDB: {e}")
        return False, None

def test_with_crewai(tools):
    """Testa o uso do adaptador com CrewAI"""
    print_info("Testando integração com CrewAI...")
    
    try:
        # Criar um agente simples com as ferramentas do MCP-MongoDB
        agent = Agent(
            role="Analista de Dados",
            goal="Analisar dados da empresa",
            backstory="Você é um analista de dados especializado em consultas MongoDB.",
            verbose=True,
            tools=tools
        )
        
        # Criar uma tarefa simples
        task = Task(
            description=(
                "Verifique se é possível consultar a coleção 'company_services' "
                "usando a ferramenta 'query' do MCP-MongoDB. "
                "Não execute a consulta, apenas verifique se a ferramenta está disponível."
            ),
            agent=agent
        )
        
        # Criar e executar a crew
        crew = Crew(
            agents=[agent],
            tasks=[task],
            verbose=2,
            process=Process.sequential
        )
        
        print_info("Executando tarefa com CrewAI...")
        result = crew.kickoff()
        
        print_success("Tarefa concluída com sucesso!")
        print_info("Resultado:")
        print(result)
        
        return True
    except Exception as e:
        print_error(f"Erro ao testar com CrewAI: {e}")
        return False

def main():
    print(f"{BLUE}{'=' * 60}{RESET}")
    print(f"{BLUE}== TESTE DO ADAPTADOR PERSONALIZADO PARA MCP-MONGODB{RESET}")
    print(f"{BLUE}{'=' * 60}{RESET}")
    
    # Testar conexão do adaptador
    success, tools = test_adapter_connection()
    if not success:
        print_error("Falha na conexão do adaptador. Verifique se o MCP-MongoDB está em execução.")
        return False
    
    print(f"{BLUE}{'=' * 60}{RESET}")
    
    # Testar com CrewAI
    if tools:
        print_info("Deseja testar a integração com CrewAI? (s/n)")
        choice = input().strip().lower()
        
        if choice == 's':
            success = test_with_crewai(tools)
            if not success:
                print_error("Falha no teste com CrewAI.")
                return False
        else:
            print_info("Teste com CrewAI ignorado.")
    
    print(f"{BLUE}{'=' * 60}{RESET}")
    print_success("Teste do adaptador personalizado concluído com sucesso!")
    print_info("O adaptador está pronto para ser usado com CrewAI.")
    print_info("Para usar em seu código:")
    print("""
from mongodb_adapter import MongoDBAdapter

# Criar adaptador
adapter = MongoDBAdapter(base_url="http://localhost:8001")

# Obter ferramentas
mongodb_tools = adapter.tools

# Criar agente com as ferramentas
agent = Agent(
    role="Seu Agente",
    goal="Objetivo do Agente",
    tools=mongodb_tools
)
    """)
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print_warning("\nTeste interrompido pelo usuário.")
        sys.exit(130)
