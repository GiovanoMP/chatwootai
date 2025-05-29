# MCP-MongoDB para ChatwootAI

## Configuração Rápida

### Credenciais para o Módulo Company Services

Para que o módulo `company_services` do Odoo envie dados para o MongoDB, configure os seguintes parâmetros no Odoo:

| Parâmetro | Valor | Descrição |
|------------|-------|------------|
| `company_services.config_service_url` | `http://localhost:8003` | URL do webhook-mongo |
| `company_services.config_service_api_key` | `development-api-key` | Chave de API para autenticação |
| `company_services.account_id` | `account_1` | ID do tenant (deve ser único por empresa) |

Estas configurações podem ser definidas em Configurações > Parâmetros do Sistema no Odoo.

### Visualização de Coleções no MongoDB

Para visualizar as coleções e dados no MongoDB:

1. Acesse o **Mongo Express** em: http://localhost:8082
2. Credenciais: 
   - Usuário: `admin`
   - Senha: `express_password`
3. Selecione o banco de dados `config_service`
4. Navegue até a coleção `company_services` para ver os dados enviados pelo módulo

### Conexão de Agentes de IA ao MCP-MongoDB

Os agentes de IA podem se conectar ao MCP-MongoDB de duas formas:

#### 1. Usando CrewAI (Recomendado)

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

#### 2. Usando Chamadas HTTP Diretas

```python
import requests
import json

# Obter configuração da empresa
def get_company_config(tenant_id="account_1"):
    response = requests.post(
        "http://localhost:8001/tools/getCompanyConfig",
        headers={"Content-Type": "application/json"},
        data=json.dumps({"tenant_id": tenant_id})
    )
    return response.json()

# Exemplo de uso
company_data = get_company_config()
print(f"Nome da empresa: {company_data['modules']['company_info']['name']}")
print(f"Horário de funcionamento: {company_data['modules']['service_settings']['business_hours']['start_time']} - {company_data['modules']['service_settings']['business_hours']['end_time']}")
```

## Visão Geral

O MCP-MongoDB é um servidor que implementa uma API compatível com o protocolo MCP (Model Context Protocol) para fornecer acesso seguro e estruturado aos dados armazenados no MongoDB. Esta implementação foi especialmente adaptada para o projeto ChatwootAI, com suporte robusto para multi-tenant e medidas de segurança aprimoradas.

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

4. **Integração com ChatwootAI**:
   - Acesso aos dados de configuração da empresa
   - Suporte para múltiplos canais de comunicação
   - Contexto para agentes de IA baseado nas configurações do tenant
   - Compatibilidade com o módulo company_services do Odoo

## Arquitetura

O MCP-MongoDB atua como uma camada de abstração entre o MongoDB e os agentes de IA, permitindo que os dados do módulo company_services sejam utilizados como contexto:

```
┬────────────────┬    ┬──────────────┬    ┬──────────────┬
│ Odoo (company_services) │    │ Webhook-Mongo │    │   MongoDB    │
│                     │────►│              │────►│              │
┴────────────────┴    ┴──────────────┴    ┴──────────────┴
                                                      │
                                                      │
┬───────────┬    ┬───────────┬    ┬──────────────┬
│  Agentes IA │    │  CrewAI     │    │ MCP-MongoDB    │
│  (LLMs)     │◄───│ (Orquestrador)◄───│ (API REST)      │
┴───────────┴    ┴───────────┴    ┴──────────────┴
```

## Fluxo de Dados

1. O módulo `company_services` do Odoo envia dados para o webhook (`webhook-mongo`) quando o usuário clica no botão "Sincronizar com Sistema de IA"
2. O webhook armazena os dados na coleção `company_services` do MongoDB, indexados pelo `account_id`
3. O MCP-MongoDB fornece acesso a esses dados via API REST compatível com o protocolo MCP
4. Os agentes de IA consultam o MCP-MongoDB para obter contexto sobre a empresa
5. Os agentes utilizam esse contexto para personalizar suas respostas de acordo com as configurações da empresa

## Configuração

O servidor pode ser configurado através das seguintes variáveis de ambiente:

| Variável | Descrição | Valor Padrão |
|----------|-----------|--------------|
| `MONGODB_URI` | URI de conexão com o MongoDB | `mongodb://localhost:27017/config_service` |
| `PORT` | Porta para o servidor HTTP | `8000` |
| `MULTI_TENANT` | Ativar modo multi-tenant | `true` |
| `DEFAULT_TENANT` | ID do tenant padrão | `account_1` |
| `MAX_RESULTS` | Número máximo de resultados | `100` |
| `ALLOWED_COLLECTIONS` | Lista de coleções permitidas | `company_services,tenants,configurations` |

## Endpoints da API

### Endpoints de Recursos

- `GET /health`: Verificação de saúde do servidor
- `GET /resources`: Lista coleções disponíveis
- `GET /resources/:tenant_id/:collection`: Obtém esquema da coleção

### Endpoints de Ferramentas

- `GET /tools`: Lista ferramentas disponíveis
- `POST /tools/query`: Consulta documentos com filtros
- `POST /tools/aggregate`: Executa pipelines de agregação
- `POST /tools/getCompanyConfig`: Obtém configuração da empresa

## Uso com CrewAI

O MCP-MongoDB pode ser facilmente integrado com o CrewAI usando o `MCPServerAdapter` ou diretamente via API REST:

```python
from crewai import Agent, Task, Crew
from crewai_tools import MCPServerAdapter

# Conectar ao servidor MCP-MongoDB
with MCPServerAdapter({"url": "http://localhost:8001"}) as mongodb_tools:
    
    # Criar agente com ferramentas do MongoDB
    customer_service_agent = Agent(
        role="Especialista em Atendimento ao Cliente",
        goal="Fornecer informações precisas e úteis aos clientes",
        tools=mongodb_tools,
        verbose=True
    )
    
    # Criar e executar tarefa
    task = Task(
        description="Responder à consulta do cliente sobre horários de funcionamento",
        agent=customer_service_agent
    )
    
    crew = Crew(
        agents=[customer_service_agent],
        tasks=[task]
    )
    
    result = crew.kickoff()
```

## Instalação e Execução

### Pré-requisitos
- Docker e Docker Compose
- MongoDB configurado com usuário `config_user`
- Rede Docker `chatwoot-mongo-network`
- Webhook-Mongo em execução

### Instalação

1. Certifique-se de que o MongoDB está em execução:
```bash
docker ps | grep mongodb
```

2. Construa e inicie o MCP-MongoDB:
```bash
docker-compose -f docker-compose.mcp-mongodb.yml build
docker-compose -f docker-compose.mcp-mongodb.yml up -d
```

3. Verifique se o MCP-MongoDB está em execução:
```bash
docker ps | grep mcp-mongodb
```

4. Teste a conexão com o endpoint de saúde:
```bash
curl http://localhost:8001/health
```

## Segurança

Esta implementação inclui várias medidas de segurança:

1. **Isolamento de Tenant**: Dados de diferentes tenants são completamente isolados
2. **Sanitização de Dados**: Campos sensíveis (como `security_token`) são automaticamente removidos
3. **Validação de Parâmetros**: Todos os parâmetros são rigorosamente validados
4. **Limitação de Acesso**: Apenas coleções específicas são acessíveis
5. **Controle de Recursos**: Limites configuráveis para resultados e tempo de execução

## Testes

### Teste com o Módulo Company Services

1. No Odoo, acesse o módulo Company Services e configure as informações da empresa

2. Clique no botão "Sincronizar com Sistema de IA" para enviar os dados para o webhook

3. Verifique se os dados foram recebidos pelo MCP-MongoDB:
```bash
curl -X POST "http://localhost:8001/tools/getCompanyConfig" -H "Content-Type: application/json" -d '{"tenant_id": "account_1"}'
```

### Teste Manual com Curl

1. Listar ferramentas disponíveis:
```bash
curl http://localhost:8001/tools
```

2. Consultar documentos na coleção company_services:
```bash
curl -X POST "http://localhost:8001/tools/query" -H "Content-Type: application/json" -d '{"collection": "company_services", "tenant_id": "account_1"}'
```

## Solução de Problemas

### Problemas de Conexão com MongoDB
- Verifique se o MongoDB está em execução
- Confirme que o usuário `config_user` existe e tem as permissões corretas
- Verifique se ambos os contêineres estão na mesma rede Docker

### Erros de Autenticação
- Verifique as credenciais no `MONGODB_URI`
- Confirme que o banco de dados `config_service` existe

### Problemas de Acesso a Dados
- Verifique se a coleção está na lista `ALLOWED_COLLECTIONS`
- Confirme que os documentos têm o campo `tenant_id` correto
