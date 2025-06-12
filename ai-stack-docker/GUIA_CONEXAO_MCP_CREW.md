# Guia de Conexão MCP-Crew para ChatwootAI

Este documento serve como guia para conectar agentes de IA usando o framework CrewAI aos diversos serviços MCP (Model Context Protocol) do ChatwootAI.

## Configuração Geral do MCPServerAdapter

Para todos os MCPs, a conexão básica é feita usando o `MCPServerAdapter` do CrewAI:

```python
from crewai import Agent, Task, Crew
from crewai_tools import MCPServerAdapter

# Exemplo de conexão com um MCP
with MCPServerAdapter({"url": "http://localhost:8001"}) as mcp_tools:
    
    # Criar agente com ferramentas do MCP
    agent = Agent(
        role="Especialista em Dados",
        goal="Analisar informações da empresa",
        tools=mcp_tools,
        verbose=True
    )
    
    # Criar tarefa para o agente
    task = Task(
        description="Obter informações da empresa para o tenant account_1",
        agent=agent
    )
    
    # Executar a tarefa
    crew = Crew(agents=[agent], tasks=[task])
    result = crew.kickoff()
```

## Conexão com MCPs Específicos

### 1. MCP-MongoDB

**URLs de Acesso:**
- **Interno (dentro da rede Docker)**: `http://mcp-mongodb:8000`
- **Externo (fora da rede Docker)**: `http://localhost:8001`

**Tenant ID Padrão:** `account_1`

**Recursos Disponíveis:**
- `company_services` - Configurações de serviços da empresa
- `tenants` - Informações sobre tenants
- `configurations` - Configurações gerais

**Endpoint de Recursos:** `http://localhost:8001/resources`

**Exemplo de Uso:**

```python
# Conexão com MCP-MongoDB
with MCPServerAdapter({"url": "http://localhost:8001"}) as mongodb_tools:
    
    # As ferramentas são descobertas automaticamente
    # Exemplos de ferramentas disponíveis:
    # - query_company_services
    # - query_tenants
    # - query_configurations
    # - aggregate_company_services
    # - etc.
    
    agent = Agent(
        role="Analista de Configurações",
        goal="Gerenciar configurações da empresa",
        tools=mongodb_tools,
        verbose=True
    )
```

**Operações Disponíveis:**
- `query` - Consulta documentos com filtros
- `aggregate` - Executa pipelines de agregação
- `getCompanyConfig` - Obtém configuração específica da empresa

### 2. MCP-Redis

**URLs de Acesso:**
- **Interno (dentro da rede Docker)**: `http://mcp-redis:8000`
- **Externo (fora da rede Docker)**: `http://localhost:8002`

**Endpoint de Saúde:** `http://localhost:8080/health` (porta separada para healthcheck)

**Ferramentas Disponíveis:**
- Ferramentas para manipulação de strings, hashes, listas, sets, sorted sets
- Ferramentas para pub/sub, streams e JSON
- Ferramentas para gerenciamento do servidor e consultas

**Exemplo de Uso:**

```python
# Conexão com MCP-Redis
with MCPServerAdapter({"url": "http://localhost:8002"}) as redis_tools:
    
    # As ferramentas são descobertas automaticamente
    # Exemplos de ferramentas disponíveis:
    # - string_get
    # - string_set
    # - hash_hget
    # - list_lpush
    # - etc.
    
    agent = Agent(
        role="Gerenciador de Cache",
        goal="Otimizar o acesso a dados frequentemente utilizados",
        tools=redis_tools,
        verbose=True
    )
```

**Nota:** O MCP-Redis não expõe um endpoint HTTP `/resources` como o MCP-MongoDB. As ferramentas são descobertas automaticamente pelo MCPServerAdapter quando os agentes se conectam diretamente ao servidor MCP.

## Conexão com Múltiplos MCPs

Para conectar um agente a múltiplos MCPs, combine as ferramentas:

```python
# Conexão com múltiplos MCPs
with MCPServerAdapter({"url": "http://localhost:8001"}) as mongodb_tools, \
     MCPServerAdapter({"url": "http://localhost:8002"}) as redis_tools, \
     MCPServerAdapter({"url": "http://localhost:8003"}) as chatwoot_tools:
    
    # Combinar ferramentas de diferentes MCPs
    all_tools = mongodb_tools + redis_tools + chatwoot_tools
    
    agent = Agent(
        role="Super Agente",
        goal="Acessar dados de múltiplos sistemas",
        tools=all_tools,
        verbose=True
    )
```

## Descoberta Automática de Ferramentas

O `MCPServerAdapter` descobre automaticamente as ferramentas disponíveis em cada MCP. Não é necessário definir manualmente as ferramentas para cada agente.

**Nota Importante:** Os diferentes MCPs implementam a descoberta de ferramentas de formas diferentes:

- **MCP-MongoDB** expõe um endpoint HTTP `/resources` que pode ser consultado diretamente:
  ```bash
  # Para MCP-MongoDB
  curl http://localhost:8001/resources
  ```

- **MCP-Redis** não expõe um endpoint HTTP `/resources`. As ferramentas são descobertas automaticamente pelo MCPServerAdapter quando os agentes se conectam diretamente ao servidor MCP.

## Considerações sobre Multi-tenant

Quando trabalhando com múltiplos tenants:

1. O MCP-MongoDB filtra automaticamente os dados pelo tenant atual
2. O tenant padrão é definido pela variável de ambiente `DEFAULT_TENANT`
3. Para acessar dados de um tenant específico, use o parâmetro `tenant_id` nas consultas

```python
# Exemplo de consulta para um tenant específico
result = agent.tools.query_company_services(
    filter={"service_name": "email"},
    tenant_id="account_2"  # Sobrescreve o tenant padrão
)
```

## Segurança e Boas Práticas

1. **Nunca** exponha os MCPs diretamente à internet sem autenticação adequada
2. Use a rede Docker `ai-stack` para comunicação interna entre serviços
3. Implemente rate limiting para evitar sobrecarga dos MCPs
4. Monitore o uso dos MCPs usando o Uptime Kuma conforme o GUIA_MONITORAMENTO.md
