#!/usr/bin/env python3
"""
Exemplo de integração entre CrewAI e MCP-Redis usando o MCPServerAdapter.

Este script demonstra como:
1. Conectar ao MCP-Redis usando o MCPServerAdapter
2. Criar um agente CrewAI com as ferramentas do Redis
3. Definir tarefas para o agente executar
4. Executar a crew e obter resultados

Certifique-se de que o MCP-Redis esteja em execução na porta 8002.
"""

import os
from crewai import Agent, Task, Crew
from crewai_tools import MCPServerAdapter

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

def main():
    """Função principal"""
    print_section("EXEMPLO DE INTEGRAÇÃO CREWAI COM MCP-REDIS")
    
    # URL do MCP-Redis
    redis_url = "http://localhost:8002/sse"
    print(f"{YELLOW}Conectando ao MCP-Redis em: {redis_url}{RESET}")
    
    # Conectar ao MCP-Redis usando o MCPServerAdapter
    with MCPServerAdapter({"url": redis_url}) as redis_tools:
        print(f"{GREEN}Conectado ao MCP-Redis! Ferramentas disponíveis: {len(redis_tools)}{RESET}")
        
        # Criar um agente CrewAI com as ferramentas do Redis
        redis_agent = Agent(
            role="Especialista em Redis",
            goal="Gerenciar dados em cache e demonstrar operações Redis",
            backstory="""Você é um especialista em Redis com anos de experiência.
            Sua missão é demonstrar como o Redis pode ser usado para armazenar
            e recuperar dados de forma eficiente.""",
            verbose=True,
            allow_delegation=False,
            tools=redis_tools
        )
        
        # Definir tarefas para o agente
        tasks = [
            Task(
                description="""
                Demonstre o uso do Redis para armazenar e recuperar dados:
                
                1. Armazene uma string com a chave 'chatwootai:demo:greeting' e valor 'Olá do ChatwootAI!'
                2. Recupere e mostre o valor armazenado
                3. Defina um tempo de expiração de 1 hora para esta chave
                4. Verifique se a chave existe
                5. Armazene um hash com informações sobre o projeto ChatwootAI
                6. Recupere e mostre as informações do hash
                
                Explique cada operação de forma clara e didática.
                """,
                agent=redis_agent,
                expected_output="Um relatório detalhado demonstrando as operações Redis realizadas"
            )
        ]
        
        # Criar e executar a crew
        crew = Crew(
            agents=[redis_agent],
            tasks=tasks,
            verbose=2
        )
        
        print(f"{YELLOW}Executando a crew...{RESET}")
        result = crew.kickoff()
        
        # Mostrar resultado
        print_section("RESULTADO")
        print(result)

if __name__ == "__main__":
    main()
