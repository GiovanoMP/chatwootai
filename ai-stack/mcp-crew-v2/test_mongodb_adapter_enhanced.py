#!/usr/bin/env python3
"""
Script de teste para o MongoDB Adapter aprimorado.

Este script testa a integração entre o MongoDB Adapter personalizado e o CrewAI,
verificando a conexão, descoberta de ferramentas e execução de tarefas.
"""

import sys
import time
import json
import requests
import logging
from typing import List, Dict, Any, Optional

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("MongoDBAdapterTest")

# Importar MongoDB Adapter
try:
    from mongodb_adapter_final import MongoDBAdapter, MongoDBTool
    logger.info("MongoDB Adapter importado com sucesso")
except ImportError as e:
    logger.error(f"Erro ao importar MongoDB Adapter: {e}")
    logger.error("Verifique se o arquivo mongodb_adapter_final.py está no mesmo diretório")
    sys.exit(1)

# Tentar importar CrewAI
try:
    from crewai import Agent, Task, Crew
    logger.info("CrewAI importado com sucesso")
except ImportError as e:
    logger.error(f"Erro ao importar CrewAI: {e}")
    logger.error("Instale o CrewAI com: pip install crewai")
    sys.exit(1)

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

def test_mongodb_health(base_url: str, timeout: int = 5) -> bool:
    """
    Testa a conexão com o servidor MCP-MongoDB.
    
    Args:
        base_url: URL base do servidor MCP-MongoDB
        timeout: Timeout para a requisição em segundos
        
    Returns:
        bool: True se o servidor estiver saudável, False caso contrário
    """
    print_info(f"Verificando saúde do MCP-MongoDB em {base_url}/health")
    
    try:
        response = requests.get(f"{base_url}/health", timeout=timeout)
        response.raise_for_status()
        health_data = response.json()
        
        print_success(f"MCP-MongoDB está saudável: {json.dumps(health_data, indent=2)}")
        return True
    except Exception as e:
        print_error(f"Erro ao verificar saúde do MCP-MongoDB: {e}")
        return False

def test_mongodb_tools(base_url: str, timeout: int = 5) -> bool:
    """
    Testa a listagem de ferramentas do MCP-MongoDB.
    
    Args:
        base_url: URL base do servidor MCP-MongoDB
        timeout: Timeout para a requisição em segundos
        
    Returns:
        bool: True se conseguir listar as ferramentas, False caso contrário
    """
    print_info(f"Listando ferramentas do MCP-MongoDB em {base_url}/tools")
    
    try:
        response = requests.get(f"{base_url}/tools", timeout=timeout)
        response.raise_for_status()
        tools_data = response.json()
        
        # Verificar formato da resposta
        if isinstance(tools_data, list):
            tools = tools_data
        elif isinstance(tools_data, dict) and "tools" in tools_data:
            tools = tools_data["tools"]
        else:
            print_error(f"Formato de resposta inesperado: {tools_data}")
            return False
        
        print_success(f"Encontradas {len(tools)} ferramentas:")
        for i, tool in enumerate(tools):
            print(f"  {i+1}. {tool['name']}: {tool['description']}")
        
        return True
    except Exception as e:
        print_error(f"Erro ao listar ferramentas do MCP-MongoDB: {e}")
        return False

def test_mongodb_adapter(base_url: str, tenant_id: Optional[str] = None) -> bool:
    """
    Testa o MongoDB Adapter.
    
    Args:
        base_url: URL base do servidor MCP-MongoDB
        tenant_id: ID do tenant para operações multi-tenant
        
    Returns:
        bool: True se o adaptador funcionar corretamente, False caso contrário
    """
    print_section("TESTE DO MONGODB ADAPTER")
    print_info(f"Inicializando MongoDB Adapter com URL: {base_url}, Tenant: {tenant_id}")
    
    try:
        # Inicializar adaptador
        adapter = MongoDBAdapter(base_url=base_url, tenant_id=tenant_id)
        
        # Verificar saúde
        print_info("Verificando saúde via adaptador...")
        health = adapter.check_health()
        print_success(f"Saúde do servidor: {health}")
        
        # Obter ferramentas
        print_info("Obtendo ferramentas via adaptador...")
        tools = adapter.tools
        print_success(f"Ferramentas encontradas: {len(tools)}")
        
        # Listar ferramentas
        for i, tool in enumerate(tools):
            desc = tool.description.split('Parâmetros:')[0].strip() if 'Parâmetros:' in tool.description else tool.description
            print(f"  {i+1}. {tool.name}: {desc}")
        
        return True
    except Exception as e:
        print_error(f"Erro ao testar MongoDB Adapter: {e}")
        return False

def test_crewai_integration(base_url: str, tenant_id: Optional[str] = None) -> bool:
    """
    Testa a integração do MongoDB Adapter com o CrewAI.
    
    Args:
        base_url: URL base do servidor MCP-MongoDB
        tenant_id: ID do tenant para operações multi-tenant
        
    Returns:
        bool: True se a integração funcionar corretamente, False caso contrário
    """
    print_section("TESTE DE INTEGRAÇÃO COM CREWAI")
    print_info(f"Testando integração com CrewAI usando MongoDB Adapter")
    
    try:
        # Criar adaptador e obter ferramentas
        adapter = MongoDBAdapter(base_url=base_url, tenant_id=tenant_id)
        mongodb_tools = adapter.tools
        
        if not mongodb_tools:
            print_error("Nenhuma ferramenta disponível para teste")
            return False
        
        print_success(f"Ferramentas disponíveis para o agente: {len(mongodb_tools)}")
        
        # Criar agente com as ferramentas do MCP-MongoDB
        agent = Agent(
            role="Analista de MongoDB",
            goal="Consultar dados no MongoDB",
            backstory="Especialista em análise de dados com MongoDB",
            tools=mongodb_tools,
            verbose=True
        )
        
        # Criar tarefa simples para testar as ferramentas
        task = Task(
            description="Liste as ferramentas disponíveis e explique como usá-las",
            agent=agent,
            expected_output="Uma lista detalhada das ferramentas disponíveis e como usá-las"
        )
        
        # Criar crew
        crew = Crew(
            agents=[agent],
            tasks=[task],
            verbose=True
        )
        
        print_info("Executando tarefa com CrewAI...")
        print_warning("Este processo pode levar alguns minutos...")
        
        # Executar crew
        result = crew.kickoff()
        
        print_success("Tarefa concluída com sucesso!")
        print_info("Resultado:")
        print(result)
        
        return True
    except Exception as e:
        print_error(f"Erro na integração com CrewAI: {e}")
        return False

def main():
    print_section("TESTE DO MONGODB ADAPTER PARA CREWAI")
    
    # Configurações
    base_url = "http://localhost:8001"
    tenant_id = "account_1"  # Opcional, pode ser None
    
    # Verificar conexão direta com MCP-MongoDB
    if not test_mongodb_health(base_url):
        print_error("Falha na verificação de saúde do MCP-MongoDB")
        print_warning("Verifique se o servidor MCP-MongoDB está em execução")
        return False
    
    # Verificar ferramentas disponíveis
    if not test_mongodb_tools(base_url):
        print_error("Falha na listagem de ferramentas do MCP-MongoDB")
        return False
    
    # Testar MongoDB Adapter
    if not test_mongodb_adapter(base_url, tenant_id):
        print_error("Falha no teste do MongoDB Adapter")
        return False
    
    # Perguntar se deseja testar integração com CrewAI
    print_info("\nDeseja testar a integração com CrewAI? (s/n)")
    print_warning("Isso pode levar alguns minutos e requer uma chave de API OpenAI configurada")
    choice = input().strip().lower()
    
    if choice == 's':
        if not test_crewai_integration(base_url, tenant_id):
            print_error("Falha no teste de integração com CrewAI")
            return False
    
    print_section("RESUMO DOS TESTES")
    print_success("Todos os testes foram concluídos com sucesso!")
    print_info("O MongoDB Adapter está funcionando corretamente")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print_warning("\nTeste interrompido pelo usuário")
        sys.exit(130)
