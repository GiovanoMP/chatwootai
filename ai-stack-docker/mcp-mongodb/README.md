# MCP-MongoDB para ChatwootAI

Este diretório contém a configuração do serviço MCP-MongoDB para o projeto ChatwootAI, fornecendo uma interface MCP (Model Context Protocol) para acesso aos dados armazenados no MongoDB.

## Informações de Acesso

- **URL de acesso**: http://localhost:8001
- **Endpoint de saúde**: http://localhost:8001/health
- **Endpoint de recursos**: http://localhost:8001/resources

## Inicialização

### Pré-requisitos

Antes de iniciar o MCP-MongoDB, certifique-se de que:

1. O serviço MongoDB está em execução
2. A rede ai-stack existe

### Inicialização com Docker Compose

```bash
# Navegue até o diretório do MCP-MongoDB
cd /home/giovano/Projetos/ai_stack/ai-stack/mcp-mongodb

# Verifique se a rede ai-stack existe
cd ..
./network.sh
cd mcp-mongodb

# Inicie o MCP-MongoDB
docker-compose up -d
```

## Parando o serviço

Para parar o serviço MCP-MongoDB:

```bash
# Navegue até o diretório do MCP-MongoDB
cd /home/giovano/Projetos/ai_stack/ai-stack/mcp-mongodb

# Pare o serviço
docker-compose down
```

## Reiniciando o serviço

Para reiniciar o serviço MCP-MongoDB:

```bash
# Navegue até o diretório do MCP-MongoDB
cd /home/giovano/Projetos/ai_stack/ai-stack/mcp-mongodb

# Pare e inicie o serviço
docker-compose down
docker-compose up -d
```

## Características Principais

1. **Suporte Multi-tenant**:
   - Isolamento completo de dados entre diferentes tenants
   - Filtragem automática por `tenant_id` em todas as operações
   - Configuração de tenant padrão via variável de ambiente

2. **Segurança Aprimorada**:
   - Limitação de coleções acessíveis (whitelist)
   - Remoção automática de campos sensíveis (password, security_token)
   - Limites de resultados configuráveis
   - Validação rigorosa de parâmetros

3. **Ferramentas Específicas**:
   - `query`: Consulta documentos com filtros por tenant
   - `aggregate`: Executa pipelines de agregação com segurança
   - `getCompanyConfig`: Obtém configuração da empresa para um tenant específico

## Integração com Agentes de IA

Os agentes de IA podem se conectar ao MCP-MongoDB usando o CrewAI:

```python
from crewai import Agent, Task, Crew
from crewai_tools import MCPServerAdapter

# Conectar ao servidor MCP-MongoDB
with MCPServerAdapter({"url": "http://localhost:8001"}) as mongodb_tools:
    
    # Criar agente com ferramentas do MongoDB
    agent = Agent(
        role="Especialista em Atendimento ao Cliente",
        goal="Fornecer informações precisas sobre a empresa",
        tools=mongodb_tools,
        verbose=True
    )
    
    # Usar o agente para acessar dados da empresa
    task = Task(
        description="Obter informações da empresa e responder ao cliente",
        agent=agent
    )
    
    crew = Crew(agents=[agent], tasks=[task])
    result = crew.kickoff()
```

## Nota Importante

Este serviço depende do código fonte presente no diretório `/home/giovano/Projetos/ai_stack/mcp-mongodb`. O docker-compose.yml está configurado para fazer o build a partir desse diretório.
