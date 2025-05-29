# MCP-Qdrant para ChatwootAI

## Configuração Rápida

### Credenciais para Módulos de Vetorização

Para que os módulos do Odoo enviem dados para o Qdrant, configure os seguintes parâmetros no Odoo:

| Parâmetro | Valor | Descrição |
|------------|-------|------------|
| `semantic_product_description.qdrant_url` | `http://localhost:8002` | URL do MCP-Qdrant |
| `semantic_product_description.qdrant_api_key` | `development-api-key` | Chave de API para autenticação |
| `semantic_product_description.account_id` | `account_1` | ID do tenant (deve ser único por empresa) |

Estas configurações podem ser definidas em Configurações > Parâmetros do Sistema no Odoo.

### Visualização de Coleções no Qdrant

Para visualizar as coleções e dados no Qdrant:

1. Acesse a **Interface Web do Qdrant** em: http://localhost:6333/dashboard
2. Navegue até a seção "Collections" para ver as coleções vetoriais
3. As coleções são prefixadas com o ID do tenant (ex: `account_1_products`)

### Conexão de Agentes de IA ao MCP-Qdrant

Os agentes de IA podem se conectar ao MCP-Qdrant de duas formas:

#### 1. Usando CrewAI (Recomendado)

```python
from crewai import Agent, Task, Crew
from crewai_tools import MCPServerAdapter

# Conectar ao servidor MCP-Qdrant
with MCPServerAdapter({"url": "http://localhost:8002"}) as qdrant_tools:
    
    # Criar agente com ferramentas do Qdrant
    agent = Agent(
        role="Especialista em Produtos",
        goal="Fornecer informações precisas sobre produtos",
        tools=qdrant_tools,
        verbose=True
    )
    
    # Usar o agente para buscar produtos similares
    task = Task(
        description="Encontrar produtos similares baseado em descrição semântica",
        agent=agent
    )
    
    crew = Crew(agents=[agent], tasks=[task])
    result = crew.kickoff()
```

#### 2. Usando Chamadas HTTP Diretas

```python
import requests
import json

# Buscar produtos similares
def search_similar_products(query, tenant_id="account_1", limit=5):
    response = requests.post(
        "http://localhost:8002/tools/searchSimilarProducts",
        headers={"Content-Type": "application/json"},
        data=json.dumps({
            "query": query,
            "tenant_id": tenant_id,
            "limit": limit
        })
    )
    return response.json()

# Exemplo de uso
similar_products = search_similar_products("smartphone com câmera de alta resolução")
for product in similar_products:
    print(f"Nome: {product['name']}, Similaridade: {product['similarity']:.2f}")
```

## Visão Geral

O MCP-Qdrant é um servidor que implementa uma API compatível com o protocolo MCP (Model Context Protocol) para fornecer acesso seguro e estruturado às coleções vetoriais armazenadas no Qdrant. Esta implementação foi especialmente adaptada para o projeto ChatwootAI, com suporte robusto para multi-tenant e medidas de segurança aprimoradas.

## Características Principais

1. **Suporte Multi-tenant**:
   - Isolamento completo de dados entre diferentes tenants
   - Prefixo automático de coleções com `tenant_id` (ex: `account_1_products`)
   - Configuração de tenant padrão via variável de ambiente

2. **Segurança Aprimorada**:
   - Limitação de coleções acessíveis (whitelist)
   - Validação rigorosa de parâmetros
   - Limites de resultados configuráveis

3. **Ferramentas Específicas**:
   - `searchSimilarProducts`: Busca produtos similares por descrição semântica
   - `searchSimilarRules`: Busca regras de negócio similares por descrição
   - `addVectors`: Adiciona ou atualiza vetores em uma coleção
   - `createCollection`: Cria uma nova coleção vetorial
   - `listCollections`: Lista coleções disponíveis para um tenant

4. **Integração com ChatwootAI**:
   - Acesso às coleções vetoriais de produtos, regras e procedimentos
   - Suporte para busca semântica em múltiplos contextos
   - Vetorização automática de conteúdo relevante

## Arquitetura

O MCP-Qdrant atua como uma camada de abstração entre o Qdrant e os agentes de IA, permitindo que as coleções vetoriais sejam utilizadas para busca semântica:

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│   Agentes IA    │────▶│   MCP-Qdrant    │────▶│     Qdrant      │
│   (CrewAI)      │     │  (API REST MCP) │     │ (Vector Store)  │
│                 │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        ▲                        ▲                      ▲
        │                        │                      │
        │                        │                      │
┌───────┴───────────────────────┴──────────────────────┴───────┐
│                                                               │
│                        Módulos Odoo                           │
│  (semantic_product_description, business_rules2, etc.)        │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

## Fluxo de Dados

1. Os módulos Odoo (como `semantic_product_description`) geram embeddings para conteúdo relevante
2. Os embeddings são enviados para o Qdrant através do MCP-Qdrant, organizados em coleções por tenant
3. Os agentes de IA consultam o MCP-Qdrant para realizar buscas semânticas
4. O MCP-Qdrant traduz as consultas para operações no Qdrant e retorna os resultados

## Variáveis de Ambiente

| Variável | Descrição | Valor Padrão |
|----------|-----------|--------------|
| `QDRANT_URL` | URL do servidor Qdrant | `http://chatwoot-qdrant:6333` |
| `QDRANT_API_KEY` | Chave de API do Qdrant (se configurada) | `""` |
| `MULTI_TENANT` | Habilitar suporte multi-tenant | `true` |
| `DEFAULT_TENANT` | ID do tenant padrão | `account_1` |
| `MAX_RESULTS` | Número máximo de resultados | `20` |
| `ALLOWED_COLLECTIONS` | Lista de coleções permitidas | `products,business_rules,support_procedures,interactions` |
| `PORT` | Porta do servidor | `8000` |

## Endpoints da API

### Endpoints de Recursos

- `GET /health`: Verificação de saúde do servidor
- `GET /resources`: Lista coleções disponíveis
- `GET /resources/:tenant_id/:collection`: Obtém metadados da coleção

### Endpoints de Ferramentas

- `GET /tools`: Lista ferramentas disponíveis
- `POST /tools/searchSimilarProducts`: Busca produtos similares
- `POST /tools/searchSimilarRules`: Busca regras de negócio similares
- `POST /tools/addVectors`: Adiciona ou atualiza vetores
- `POST /tools/createCollection`: Cria uma nova coleção
- `POST /tools/listCollections`: Lista coleções disponíveis

## Uso com CrewAI

O MCP-Qdrant pode ser facilmente integrado com o CrewAI usando o `MCPServerAdapter`:

```python
from crewai import Agent, Task, Crew
from crewai_tools import MCPServerAdapter

# Conectar ao servidor MCP-Qdrant
with MCPServerAdapter({"url": "http://localhost:8002"}) as qdrant_tools:
    
    # Criar agente especializado em produtos
    product_specialist = Agent(
        role="Especialista em Produtos",
        goal="Fornecer informações precisas sobre produtos",
        tools=qdrant_tools,
        verbose=True
    )
    
    # Criar e executar tarefa de busca semântica
    task = Task(
        description="Encontrar produtos similares a 'smartphone com câmera profissional'",
        agent=product_specialist
    )
    
    crew = Crew(
        agents=[product_specialist],
        tasks=[task]
    )
    
    result = crew.kickoff()
```

## Instalação e Execução

### Pré-requisitos
- Docker e Docker Compose
- Qdrant configurado e em execução
- Rede Docker `chatwoot-network`

### Instalação

1. Certifique-se de que o Qdrant está em execução:
```bash
docker ps | grep qdrant
```

2. Construa e inicie o MCP-Qdrant:
```bash
docker-compose -f docker-compose.mcp-qdrant.yml build
docker-compose -f docker-compose.mcp-qdrant.yml up -d
```

3. Verifique se o MCP-Qdrant está em execução:
```bash
docker ps | grep mcp-qdrant
```

4. Teste a conexão com o endpoint de saúde:
```bash
curl http://localhost:8002/health
```

## Segurança

Esta implementação inclui várias medidas de segurança:

1. **Isolamento de Tenant**: Dados de diferentes tenants são completamente isolados
2. **Validação de Parâmetros**: Todos os parâmetros são rigorosamente validados
3. **Limitação de Acesso**: Apenas coleções específicas são acessíveis
4. **Controle de Recursos**: Limites configuráveis para resultados e tempo de execução

## Testes

### Teste com o Módulo semantic_product_description

1. No Odoo, acesse o módulo semantic_product_description e configure as descrições semânticas dos produtos

2. Verifique se os vetores foram adicionados ao Qdrant:
```bash
curl -X POST "http://localhost:8002/tools/listCollections" -H "Content-Type: application/json" -d '{"tenant_id": "account_1"}'
```

### Teste Manual com Curl

1. Listar ferramentas disponíveis:
```bash
curl http://localhost:8002/tools
```

2. Buscar produtos similares:
```bash
curl -X POST "http://localhost:8002/tools/searchSimilarProducts" -H "Content-Type: application/json" -d '{"query": "smartphone com câmera de alta resolução", "tenant_id": "account_1", "limit": 5}'
```

## Solução de Problemas

### Problemas de Conexão com Qdrant
- Verifique se o Qdrant está em execução
- Confirme que o MCP-Qdrant e o Qdrant estão na mesma rede Docker
- Verifique as variáveis de ambiente no arquivo docker-compose

### Erros de Autenticação
- Verifique a chave de API do Qdrant (se configurada)
- Confirme que o MCP-Qdrant tem permissão para acessar o Qdrant

### Problemas de Acesso a Coleções
- Verifique se a coleção está na lista `ALLOWED_COLLECTIONS`
- Confirme que as coleções têm o prefixo de tenant correto
