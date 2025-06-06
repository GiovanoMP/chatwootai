#!/usr/bin/env python3
"""
Exemplo de integração entre CrewAI e MCP-MongoDB usando o MongoDBAdapter personalizado.

Este script demonstra como:
1. Conectar ao MCP-MongoDB usando o MongoDBAdapter
2. Criar um agente CrewAI com as ferramentas do MongoDB
3. Definir tarefas para o agente executar
4. Executar a crew e obter resultados

Certifique-se de que o MCP-MongoDB esteja em execução na porta 8001.
"""

import os
import json
from crewai import Agent, Task, Crew
from mongodb_adapter import MongoDBAdapter

# Cores para saída no terminal
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"

def print_section(title):
    """Imprime título de seção"""
    print(f"\n{BLUE}{'=' * 50}{RESET}")
    print(f"{BLUE}== {title}{RESET}")
    print(f"{BLUE}{'=' * 50}{RESET}\n")

def print_info(message):
    """Imprime mensagem informativa"""
    print(f"{YELLOW}{message}{RESET}")

def print_success(message):
    """Imprime mensagem de sucesso"""
    print(f"{GREEN}{message}{RESET}")

def print_error(message):
    """Imprime mensagem de erro"""
    print(f"{RED}{message}{RESET}")

def main():
    """Função principal"""
    print_section("EXEMPLO DE INTEGRAÇÃO CREWAI COM MCP-MONGODB")
    
    # URL do MCP-MongoDB
    mongodb_url = "http://localhost:8001"
    tenant_id = "account_1"
    print_info(f"Conectando ao MCP-MongoDB em: {mongodb_url}")
    
    try:
        # Criar o adaptador MongoDB
        adapter = MongoDBAdapter(base_url=mongodb_url, tenant_id=tenant_id)
        
        # Verificar saúde do servidor
        health_info = adapter.check_health()
        print_success(f"Status do MCP-MongoDB: {json.dumps(health_info, indent=2)}")
        
        # Obter ferramentas
        mongodb_tools = adapter.tools
        print_success(f"Conectado ao MCP-MongoDB! Ferramentas disponíveis: {len(mongodb_tools)}")
        
        # Listar ferramentas disponíveis
        print_info("Ferramentas disponíveis:")
        for i, tool in enumerate(mongodb_tools):
            print(f"  {i+1}. {tool.name}")
        
        # Criar um agente CrewAI com as ferramentas do MongoDB
        mongodb_agent = Agent(
            role="Especialista em MongoDB",
            goal="Consultar e analisar dados do MongoDB",
            backstory="""Você é um especialista em MongoDB com anos de experiência.
            Sua missão é demonstrar como o MongoDB pode ser usado para consultar
            e analisar dados de forma eficiente.""",
            verbose=True,
            allow_delegation=False,
            tools=mongodb_tools
        )
        
        # Definir tarefas para o agente
        tasks = [
            Task(
                description="""
                Demonstre o uso do MongoDB para consultar dados:
                
                1. Use a ferramenta 'query' para buscar documentos na coleção 'company_services'
                2. Analise os resultados e explique os campos principais
                3. Use a ferramenta 'aggregate' para fazer uma agregação simples na coleção 'company_services'
                4. Use a ferramenta 'getCompanyConfig' para obter configurações da empresa
                
                Explique cada operação de forma clara e didática.
                
                Observações:
                - Sempre inclua o parâmetro 'tenant_id' com valor 'account_1'
                - Para a ferramenta 'query', use o parâmetro 'filter' como um objeto JSON vazio ({}) para buscar todos os documentos
                - Para a ferramenta 'aggregate', use o parâmetro 'pipeline' como um array com um estágio $match vazio ([{"$match": {}}])
                """,
                agent=mongodb_agent,
                expected_output="Um relatório detalhado demonstrando as consultas MongoDB realizadas"
            )
        ]
        
        # Criar e executar a crew
        crew = Crew(
            agents=[mongodb_agent],
            tasks=tasks,
            verbose=True
        )
        
        print_info("Executando a crew...")
        result = crew.kickoff()
        
        # Mostrar resultado
        print_section("RESULTADO")
        print(result)
        
    except Exception as e:
        print_error(f"Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
