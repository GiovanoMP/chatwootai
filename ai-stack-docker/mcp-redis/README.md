# MCP-Redis para ChatwootAI

Este diretório contém a configuração do serviço MCP-Redis para o projeto ChatwootAI, fornecendo uma interface MCP (Model Context Protocol) para acesso aos dados armazenados no Redis.

## Informações de Acesso

- **URL de acesso**: http://localhost:8002
- **Endpoint de saúde**: http://localhost:8080/health
- **Nota sobre recursos**: O MCP-Redis não expõe um endpoint HTTP `/resources` como o MCP-MongoDB. As ferramentas são descobertas automaticamente pelo MCPServerAdapter quando os agentes se conectam diretamente ao servidor MCP na porta 8002.

## Inicialização

### Pré-requisitos

Antes de iniciar o MCP-Redis, certifique-se de que:

1. O serviço Redis está em execução
2. A rede ai-stack existe

### Inicialização com Docker Compose

```bash
# Navegue até o diretório do MCP-Redis
cd /home/giovano/Projetos/ai_stack/ai-stack/mcp-redis

# Verifique se a rede ai-stack existe
cd ..
./network.sh
cd mcp-redis

# Inicie o MCP-Redis
docker-compose up -d
```

## Parando o serviço

Para parar o serviço MCP-Redis:

```bash
# Navegue até o diretório do MCP-Redis
cd /home/giovano/Projetos/ai_stack/ai-stack/mcp-redis

# Pare o serviço
docker-compose down
```

## Reiniciando o serviço

Para reiniciar o serviço MCP-Redis:

```bash
# Navegue até o diretório do MCP-Redis
cd /home/giovano/Projetos/ai_stack/ai-stack/mcp-redis

# Pare e inicie o serviço
docker-compose down
docker-compose up -d
```

## Características Principais

1. **Gerenciamento de Cache**:
   - Armazenamento e recuperação de dados em cache
   - Definição de tempo de expiração (TTL)
   - Invalidação seletiva de cache

2. **Filas e Pub/Sub**:
   - Implementação de filas para processamento assíncrono
   - Sistema de publicação/assinatura para eventos em tempo real
   - Gerenciamento de mensagens com prioridade

3. **Ferramentas Específicas**:
   - `get`: Recupera valores por chave
   - `set`: Define valores com chave e TTL opcional
   - `publish`: Publica mensagens em canais
   - `subscribe`: Assina canais para receber mensagens

## Integração com Agentes de IA

Os agentes de IA podem se conectar ao MCP-Redis usando o CrewAI:

```python
from crewai import Agent, Task, Crew
from crewai_tools import MCPServerAdapter

# Conectar ao servidor MCP-Redis
with MCPServerAdapter({"url": "http://localhost:8002"}) as redis_tools:
    
    # Criar agente com ferramentas do Redis
    agent = Agent(
        role="Gerenciador de Cache",
        goal="Otimizar o acesso a dados frequentemente utilizados",
        tools=redis_tools,
        verbose=True
    )
    
    # Usar o agente para gerenciar cache
    task = Task(
        description="Armazenar e recuperar dados de configuração em cache",
        agent=agent
    )
    
    crew = Crew(agents=[agent], tasks=[task])
    result = crew.kickoff()
```

## Nota Importante

Este serviço depende do código fonte presente no diretório `/home/giovano/Projetos/ai_stack/mcp-redis-official`. O docker-compose.yml está configurado para fazer o build a partir desse diretório.
