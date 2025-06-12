# Integração MCP com CrewAI

Este repositório contém implementações para integrar servidores MCP (Model Context Protocol) com o framework CrewAI, permitindo que agentes de IA utilizem ferramentas expostas por diferentes serviços.

## Visão Geral

O projeto oferece quatro soluções de integração:

1. **MCPAdapt para MCP-Redis e MCP-Qdrant**: Integração moderna usando o pacote `mcpadapt` para servidores que suportam SSE
2. **MCP-MongoDB**: Adaptador personalizado para conexão via REST
3. **MCP-Chatwoot**: Adaptador dinâmico para integração com o Chatwoot via MCP
4. **MCPServerAdapter (Legado)**: Integração antiga usando o adaptador nativo do CrewAI (não mais recomendado)

Todas as soluções permitem que agentes CrewAI descubram e utilizem ferramentas expostas pelos servidores MCP de forma transparente.

## Requisitos

- Python 3.8+
- CrewAI 0.28.0+
- MCPAdapt (para MCP-Redis e MCP-Qdrant): `pip install mcpadapt[crewai]`
- Servidores MCP em execução:
  - MCP-Redis na porta 8002 (SSE)
  - MCP-MongoDB na porta 8001 (REST)
  - MCP-Qdrant na porta 8003 (SSE)
  - MCP-Chatwoot na porta 8004 (SSE/REST)
- Variáveis de ambiente configuradas no arquivo `.env`

## Configuração

1. Clone este repositório
2. Crie um ambiente virtual: `python -m venv venv`
3. Ative o ambiente: `source venv/bin/activate`
4. Instale as dependências: `pip install crewai requests python-dotenv mcpadapt[crewai]`
5. Configure o arquivo `.env` com suas credenciais:

```
OPENAI_API_KEY=sua_chave_aqui
MCP_MONGODB_URL=http://localhost:8001
MCP_REDIS_URL=http://localhost:8002/sse
MCP_QDRANT_URL=http://localhost:8003/sse
MCP_CHATWOOT_URL=http://localhost:8004/sse
QDRANT_COLLECTION=memories
MONGODB_TENANT_ID=account_1
CHATWOOT_ACCOUNT_ID=1
```

## Soluções de Integração

### 1. MCPAdapt para MCP-Redis e MCP-Qdrant (Recomendado)

O MCPAdapt é uma biblioteca moderna que facilita a integração de servidores MCP com diversos frameworks de agentes, incluindo CrewAI. É especialmente eficaz para servidores que usam transporte SSE:

```python
from mcpadapt.core import MCPAdapt
from mcpadapt.crewai_adapter import CrewAIAdapter
from crewai import Agent, Task, Crew

# Configuração para conexão SSE
sse_config = {
    "url": "http://localhost:8002/sse",  # Para MCP-Redis
    "timeout": 10,  # Timeout em segundos
}

# Conectar ao MCP-Redis
with MCPAdapt(sse_config, CrewAIAdapter()) as tools:
    # Criar agente com as ferramentas
    agent = Agent(
        role="Especialista em Redis",
        goal="Gerenciar dados em cache",
        tools=tools  # Todas as ferramentas do MCP-Redis
    )
```

**Características principais:**
- Suporta mais de 650 servidores MCP
- Integração padronizada com diversos frameworks (CrewAI, Langchain, etc.)
- Gerenciamento automático do ciclo de vida do MCP
- Suporte a operações síncronas e assíncronas
- Compatível com múltiplos MCPs simultâneos

### 2. MCP-MongoDB com Adaptador Personalizado

Como o MCP-MongoDB usa REST em vez de SSE, criamos um adaptador personalizado que se conecta via HTTP e descobre ferramentas dinamicamente:

```python
from mongodb_adapter import MongoDBAdapter

# Conectar ao MCP-MongoDB via REST
adapter = MongoDBAdapter(base_url="http://localhost:8001", tenant_id="account_1")

# Obter ferramentas como objetos Tool do CrewAI
mongodb_tools = adapter.tools

# Criar agente com as ferramentas do MongoDB
mongodb_agent = Agent(
    role="Especialista em MongoDB",
    goal="Gerenciar dados no MongoDB",
    tools=mongodb_tools
)
```

**Características principais:**
- Usa o transporte REST (HTTP padrão)
- Implementação personalizada para servidores que não suportam SSE
- Suporte a multi-tenant com isolamento por `tenant_id`
- Descoberta dinâmica de ferramentas via endpoint REST

### 3. MCP-Chatwoot com Adaptador Dinâmico

O MCP-Chatwoot utiliza um adaptador dinâmico que descobre ferramentas automaticamente via endpoint REST `/tools` e as converte em objetos Tool do CrewAI:

```python
from chatwoot_dynamic_adapter import ChatwootDynamicAdapter

# Conectar ao MCP-Chatwoot
adapter = ChatwootDynamicAdapter(base_url="http://localhost:8004")

# Obter ferramentas como objetos Tool do CrewAI
chatwoot_tools = adapter.tools

# Criar agente com as ferramentas do Chatwoot
chatwoot_agent = Agent(
    role="Especialista em Atendimento",
    goal="Gerenciar conversas no Chatwoot",
    tools=chatwoot_tools
)
```

**Características principais:**
- Suporta transporte SSE para eventos em tempo real
- Descoberta dinâmica de ferramentas via endpoint REST `/tools`
- Integração completa com a API do Chatwoot
- Conversão automática de ferramentas para o formato CrewAI

### 4. MCPServerAdapter (Legado - Não Recomendado)

O adaptador nativo do CrewAI (`MCPServerAdapter`) está obsoleto e não é mais recomendado:

```python
from crewai_adapters.tools import MCPToolsAdapter
from crewai_adapters.types import AdapterConfig

# Configuração para conexão SSE
config = AdapterConfig(
    mcp_url="http://localhost:8002/sse",
    tools=["collection", "transport"]  # Configuração obrigatória
)

# Conectar ao MCP-Redis
adapter = MCPToolsAdapter(config=config)
tools = adapter.get_all_tools()
```

**Problemas conhecidos:**
- Documentação desatualizada
- Erros de configuração frequentes
- Incompatibilidade com versões recentes do CrewAI

## Arquivos Importantes

- `mongodb_adapter.py`: Implementação do adaptador personalizado para MCP-MongoDB
- `chatwoot_dynamic_adapter.py`: Implementação do adaptador dinâmico para MCP-Chatwoot
- `test_mongodb_adapter.py`: Script para testar a conexão com MCP-MongoDB
- `test_chatwoot_dynamic.py`: Script para testar a conexão com MCP-Chatwoot
- `test_mcpadapt_redis.py`: Script para testar a conexão com MCP-Redis usando MCPAdapt
- `test_mcpadapt_qdrant.py`: Script para testar a conexão com MCP-Qdrant usando MCPAdapt
- `mongodb_agent_example.py`: Exemplo de uso do MCP-MongoDB com CrewAI
- `chatwoot_agent_example.py`: Exemplo de uso do MCP-Chatwoot com CrewAI
- `MCP_BEST_PRACTICES.md`: Guia de boas práticas para servidores MCP e adaptadores

## Testes

Para testar a conexão com o MCP-MongoDB (usando adaptador personalizado):

```bash
python test_mongodb_adapter.py
```

Para testar a conexão com o MCP-Chatwoot (usando adaptador dinâmico):

```bash
python test_chatwoot_dynamic.py
```

Para testar a conexão com o MCP-Redis (usando MCPAdapt):

```bash
python test_mcpadapt_redis.py
```

Para testar a conexão com o MCP-Qdrant (usando MCPAdapt):

```bash
python test_mcpadapt_qdrant.py
```

## Arquitetura MCP

O protocolo MCP (Model Context Protocol) permite que servidores exponham ferramentas para serem utilizadas por agentes de IA. Existem diferentes tipos de transporte no protocolo MCP:

1. **SSE (Server-Sent Events)**: Implementado pelo MCP-Redis, permite streaming de eventos do servidor para o cliente
2. **HTTP/REST**: Implementado pelo MCP-MongoDB, baseado em requisições HTTP padrão
3. **streamable-http**: Uma variante do HTTP que suporta streaming
4. **STDIO**: Para comunicação local via entrada/saída padrão

## Extensibilidade

O padrão de adaptador personalizado implementado para o MongoDB pode ser facilmente adaptado para outros serviços MCP que não suportem SSE. Basta seguir a mesma estrutura:

1. Criar uma classe adaptadora que se conecte aos endpoints REST do serviço
2. Implementar métodos para descobrir ferramentas disponíveis
3. Converter as ferramentas em objetos `Tool` do CrewAI
4. Disponibilizar as ferramentas para os agentes

## Próximos Passos

- Criar um adaptador personalizado para MCPAdapt que suporte REST para MCP-MongoDB
- Implementar caching para melhorar a performance
- Desenvolver exemplos de uso com múltiplos MCPs simultâneos
- Explorar recursos avançados do MCPAdapt como operações assíncronas
- Criar exemplos mais complexos de uso com múltiplos agentes
- Padronizar a descoberta dinâmica de ferramentas em todos os adaptadores
- Implementar JSON-RPC completo para o MCP-Chatwoot
