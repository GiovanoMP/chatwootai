#!/usr/bin/env python3
"""
Exemplo de integração entre CrewAI e múltiplos servidores MCP.

Este script demonstra como:
1. Conectar a múltiplos servidores MCP (MongoDB, Redis, Qdrant, Chatwoot)
2. Criar agentes CrewAI especializados com ferramentas específicas
3. Definir tarefas para os agentes executarem
4. Executar a crew e obter resultados

Certifique-se de que todos os servidores MCP estejam em execução:
- MCP-MongoDB na porta 8001
- MCP-Redis na porta 8002
- MCP-Qdrant na porta 8003
- MCP-Chatwoot na porta 8004
"""

import os
import json
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
from mongodb_adapter import MongoDBAdapter
from chatwoot_dynamic_adapter import ChatwootDynamicAdapter
from mcpadapt.core import MCPAdapt
from mcpadapt.crewai_adapter import CrewAIAdapter

# Carregar variáveis de ambiente
load_dotenv()

# Cores para saída no terminal
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"

def print_section(title):
    """Imprime um título de seção formatado"""
    print(f"\n{BLUE}{'=' * 60}{RESET}")
    print(f"{BLUE}== {title}{RESET}")
    print(f"{BLUE}{'=' * 60}{RESET}")

def main():
    print_section("CREW AI COM MÚLTIPLOS CONECTORES MCP")
    
    # Configurar URLs dos servidores MCP
    mongodb_url = os.getenv("MCP_MONGODB_URL", "http://localhost:8001")
    redis_url = os.getenv("MCP_REDIS_URL", "http://localhost:8002/sse")
    qdrant_url = os.getenv("MCP_QDRANT_URL", "http://localhost:8003/sse")
    chatwoot_url = os.getenv("MCP_CHATWOOT_URL", "http://localhost:8004")
    
    # Configurar tenant_id para MongoDB
    tenant_id = os.getenv("MONGODB_TENANT_ID", "account_1")
    
    print(f"{YELLOW}ℹ️ Conectando aos servidores MCP...{RESET}")
    
    # Inicializar adaptadores
    print(f"  - MongoDB: {mongodb_url}")
    mongodb_adapter = MongoDBAdapter(base_url=mongodb_url, tenant_id=tenant_id)
    
    print(f"  - Chatwoot: {chatwoot_url}")
    chatwoot_adapter = ChatwootDynamicAdapter(base_url=chatwoot_url)
    
    # Configurações para MCPAdapt (Redis e Qdrant)
    redis_config = {"url": redis_url, "timeout": 10}
    qdrant_config = {"url": qdrant_url, "timeout": 10}
    
    # Criar agentes com ferramentas específicas
    with MCPAdapt(redis_config, CrewAIAdapter()) as redis_tools, \
         MCPAdapt(qdrant_config, CrewAIAdapter()) as qdrant_tools:
        
        print(f"{GREEN}✅ Conectado a todos os servidores MCP!{RESET}")
        print(f"{YELLOW}ℹ️ Criando agentes especializados...{RESET}")
        
        # Agente especialista em banco de dados (MongoDB)
        db_agent = Agent(
            role="Especialista em Banco de Dados",
            goal="Gerenciar e consultar bancos de dados MongoDB",
            backstory="Um especialista em bancos de dados com anos de experiência em MongoDB. "
                     "Sabe como consultar e agregar dados de forma eficiente.",
            verbose=True,
            allow_delegation=True,
            tools=mongodb_adapter.tools
        )
        
        # Agente especialista em memória (Qdrant)
        memory_agent = Agent(
            role="Especialista em Memória Vetorial",
            goal="Armazenar e recuperar memórias usando vetores",
            backstory="Um especialista em sistemas de memória vetorial. "
                     "Sabe como armazenar e recuperar informações usando embeddings.",
            verbose=True,
            allow_delegation=True,
            tools=qdrant_tools
        )
        
        # Agente especialista em cache (Redis)
        cache_agent = Agent(
            role="Gerente de Cache",
            goal="Otimizar operações de cache usando Redis",
            backstory="Um especialista em sistemas de cache distribuído. "
                     "Sabe como armazenar, recuperar e gerenciar dados em cache.",
            verbose=True,
            allow_delegation=True,
            tools=redis_tools
        )
        
        # Agente especialista em atendimento (Chatwoot)
        support_agent = Agent(
            role="Especialista em Atendimento",
            goal="Gerenciar conversas e atender clientes via Chatwoot",
            backstory="Um especialista em atendimento ao cliente. "
                     "Sabe como gerenciar conversas, responder a clientes e criar contatos.",
            verbose=True,
            allow_delegation=True,
            tools=chatwoot_adapter.tools
        )
        
        print(f"{GREEN}✅ Agentes criados com sucesso!{RESET}")
        print(f"{YELLOW}ℹ️ Definindo tarefas...{RESET}")
        
        # Tarefa para o agente de banco de dados
        db_task = Task(
            description="Consultar informações de clientes no banco de dados MongoDB e "
                       "fornecer insights sobre os dados armazenados.",
            expected_output="Relatório com informações de clientes e insights",
            agent=db_agent
        )
        
        # Tarefa para o agente de memória
        memory_task = Task(
            description="Armazenar informações importantes sobre clientes como memórias vetoriais "
                       "e recuperar informações relevantes quando necessário.",
            expected_output="Confirmação de armazenamento e recuperação de memórias",
            agent=memory_agent
        )
        
        # Tarefa para o agente de cache
        cache_task = Task(
            description="Configurar um sistema de cache para armazenar temporariamente "
                       "informações frequentemente acessadas e gerenciar sua expiração.",
            expected_output="Relatório de configuração do cache e estatísticas de uso",
            agent=cache_agent
        )
        
        # Tarefa para o agente de atendimento
        support_task = Task(
            description="Listar conversas ativas no Chatwoot, verificar detalhes de uma conversa "
                       "específica e enviar uma resposta para um cliente.",
            expected_output="Relatório de atendimento ao cliente",
            agent=support_agent
        )
        
        print(f"{GREEN}✅ Tarefas definidas com sucesso!{RESET}")
        print(f"{YELLOW}ℹ️ Criando e executando a crew...{RESET}")
        
        # Criar a crew com todos os agentes
        crew = Crew(
            agents=[db_agent, memory_agent, cache_agent, support_agent],
            tasks=[db_task, memory_task, cache_task, support_task],
            verbose=2,
            process=Process.sequential  # Executar tarefas sequencialmente
        )
        
        # Executar a crew
        result = crew.kickoff()
        
        print(f"{GREEN}✅ Crew executada com sucesso!{RESET}")
        print(f"{YELLOW}ℹ️ Resultado final:{RESET}")
        print(result)

if __name__ == "__main__":
    main()
