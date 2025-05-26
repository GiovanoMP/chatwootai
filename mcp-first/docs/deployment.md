# Guia de Implantação da Arquitetura MCP First

## Visão Geral

Este guia fornece instruções detalhadas para implantar a arquitetura MCP First em ambientes de desenvolvimento, teste e produção. A arquitetura é composta por vários componentes interconectados através do Model Context Protocol (MCP).

## Pré-requisitos

Antes de iniciar a implantação, certifique-se de que você tem:

1. Docker e Docker Compose instalados
2. Acesso a um servidor Odoo (pode ser local ou remoto)
3. Acesso a um servidor Chatwoot (pode ser local ou remoto)
4. Python 3.8+ instalado para desenvolvimento local

## Estrutura de Implantação

A arquitetura MCP First é implantada como um conjunto de serviços Docker interconectados:

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   MCP-Odoo      │     │   MCP-Qdrant    │     │  MCP-Chatwoot   │
│   (Container)   │     │   (Container)   │     │   (Container)   │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                      ┌──────────┴──────────┐
                      │  MCP-Orchestrator   │
                      │    (Container)      │
                      └──────────┬──────────┘
                                 │
                      ┌──────────┴──────────┐
                      │      CrewAI         │
                      │    (Container)      │
                      └──────────┬──────────┘
                                 │
                      ┌──────────┴──────────┐
                      │       Redis         │
                      │    (Container)      │
                      └─────────────────────┘
```

## Etapas de Implantação

### 1. Configurar Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto com as seguintes variáveis:

```
# Configurações gerais
ENVIRONMENT=development  # development, staging, production

# Configurações do Odoo
ODOO_URL=http://localhost:8069
ODOO_DB=odoo
ODOO_USERNAME=admin
ODOO_PASSWORD=admin

# Configurações do Qdrant
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=your_qdrant_api_key

# Configurações do Chatwoot
CHATWOOT_URL=http://localhost:3000
CHATWOOT_API_KEY=your_chatwoot_api_key

# Configurações do Redis
REDIS_URL=redis://localhost:6379
REDIS_PASSWORD=your_redis_password

# Configurações do CrewAI
OPENAI_API_KEY=your_openai_api_key
```

### 2. Configurar Docker Compose

Crie um arquivo `docker-compose.yml` na raiz do projeto:

```yaml
version: '3.8'

services:
  # MCP-Odoo
  mcp-odoo:
    build:
      context: ./src/mcp-odoo
    ports:
      - "8000:8000"
    environment:
      - ODOO_URL=${ODOO_URL}
      - ODOO_DB=${ODOO_DB}
      - ODOO_USERNAME=${ODOO_USERNAME}
      - ODOO_PASSWORD=${ODOO_PASSWORD}
      - ENVIRONMENT=${ENVIRONMENT}
    volumes:
      - ./src/mcp-odoo:/app
    depends_on:
      - redis
    restart: unless-stopped

  # MCP-Qdrant
  mcp-qdrant:
    build:
      context: ./src/mcp-qdrant
    ports:
      - "8001:8000"
    environment:
      - QDRANT_URL=${QDRANT_URL}
      - QDRANT_API_KEY=${QDRANT_API_KEY}
      - ENVIRONMENT=${ENVIRONMENT}
    volumes:
      - ./src/mcp-qdrant:/app
    depends_on:
      - redis
    restart: unless-stopped

  # MCP-Chatwoot
  mcp-chatwoot:
    build:
      context: ./src/mcp-chatwoot
    ports:
      - "8002:8000"
    environment:
      - CHATWOOT_URL=${CHATWOOT_URL}
      - CHATWOOT_API_KEY=${CHATWOOT_API_KEY}
      - ENVIRONMENT=${ENVIRONMENT}
    volumes:
      - ./src/mcp-chatwoot:/app
    depends_on:
      - redis
    restart: unless-stopped

  # MCP-Orchestrator
  mcp-orchestrator:
    build:
      context: ./src/mcp-orchestrator
    ports:
      - "8003:8000"
    environment:
      - MCP_ODOO_URL=http://mcp-odoo:8000
      - MCP_QDRANT_URL=http://mcp-qdrant:8000
      - MCP_CHATWOOT_URL=http://mcp-chatwoot:8000
      - REDIS_URL=${REDIS_URL}
      - REDIS_PASSWORD=${REDIS_PASSWORD}
      - ENVIRONMENT=${ENVIRONMENT}
    volumes:
      - ./src/mcp-orchestrator:/app
    depends_on:
      - mcp-odoo
      - mcp-qdrant
      - mcp-chatwoot
      - redis
    restart: unless-stopped

  # CrewAI
  crewai:
    build:
      context: ./src/crewai
    ports:
      - "8004:8000"
    environment:
      - MCP_ORCHESTRATOR_URL=http://mcp-orchestrator:8000
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - REDIS_URL=${REDIS_URL}
      - REDIS_PASSWORD=${REDIS_PASSWORD}
      - ENVIRONMENT=${ENVIRONMENT}
    volumes:
      - ./src/crewai:/app
    depends_on:
      - mcp-orchestrator
      - redis
    restart: unless-stopped

  # Redis
  redis:
    image: redis:6.2-alpine
    ports:
      - "6379:6379"
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis-data:/data
    restart: unless-stopped

volumes:
  redis-data:
```

### 3. Preparar Estrutura de Diretórios

```bash
mkdir -p src/mcp-odoo
mkdir -p src/mcp-qdrant
mkdir -p src/mcp-chatwoot
mkdir -p src/mcp-orchestrator
mkdir -p src/crewai
mkdir -p examples/whatsapp-flow
mkdir -p examples/product-search
mkdir -p examples/order-creation
```

### 4. Implementar Servidores MCP

#### MCP-Odoo

Crie um Dockerfile em `src/mcp-odoo/Dockerfile`:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
```

Crie um arquivo `src/mcp-odoo/requirements.txt`:

```
fastmcp>=0.1.0
pydantic>=1.8.2
requests>=2.26.0
xmlrpc>=0.9.0
```

Crie um arquivo `src/mcp-odoo/main.py`:

```python
import os
import xmlrpc.client
import json
from fastmcp import FastMCP, mcp
from typing import List, Dict, Any, Optional

# Inicializar o servidor MCP
app = FastMCP(title="MCP-Odoo")

# Configurar a conexão com o Odoo
ODOO_URL = os.environ.get("ODOO_URL", "http://localhost:8069")
ODOO_DB = os.environ.get("ODOO_DB", "odoo")
ODOO_USERNAME = os.environ.get("ODOO_USERNAME", "admin")
ODOO_PASSWORD = os.environ.get("ODOO_PASSWORD", "admin")

# Função para conectar ao Odoo
def get_odoo_client():
    common = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/common")
    uid = common.authenticate(ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD, {})
    models = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/object")
    return models, uid

# Implementar ferramentas (tools)
@mcp.tool("search_records")
def search_records(model: str, domain: List, fields: Optional[List[str]] = None, limit: Optional[int] = None) -> Dict[str, Any]:
    """
    Busca registros em qualquer modelo Odoo.
    
    Args:
        model: Nome do modelo Odoo (ex: 'res.partner')
        domain: Domínio de busca (ex: [['is_company', '=', True]])
        fields: Campos a serem retornados (opcional)
        limit: Número máximo de registros a serem retornados (opcional)
        
    Returns:
        Lista de registros encontrados
    """
    models, uid = get_odoo_client()
    
    try:
        records = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            model, 'search_read',
            [domain],
            {'fields': fields, 'limit': limit}
        )
        return {"success": True, "records": records}
    except Exception as e:
        return {"success": False, "error": str(e)}

# Implementar recursos (resources)
@mcp.resource("odoo://models")
def get_models() -> str:
    """
    Obtém a lista de modelos disponíveis no Odoo.
    
    Returns:
        Lista de modelos em formato JSON
    """
    models, uid = get_odoo_client()
    
    try:
        model_list = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'ir.model', 'search_read',
            [[]], {'fields': ['model', 'name']}
        )
        return json.dumps(model_list)
    except Exception as e:
        return json.dumps({"error": str(e)})

# Iniciar o servidor
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
```

Implemente os outros servidores MCP de forma semelhante (MCP-Qdrant, MCP-Chatwoot, MCP-Orchestrator).

### 5. Implementar CrewAI

Crie um Dockerfile em `src/crewai/Dockerfile`:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
```

Crie um arquivo `src/crewai/requirements.txt`:

```
fastapi>=0.68.0
uvicorn>=0.15.0
crewai>=0.1.0
mcp-client>=0.1.0
redis>=4.0.0
```

Crie um arquivo `src/crewai/main.py` com a implementação das crews.

### 6. Iniciar os Serviços

```bash
# Construir e iniciar todos os serviços
docker-compose up -d

# Verificar se todos os serviços estão em execução
docker-compose ps

# Verificar logs de um serviço específico
docker-compose logs -f mcp-odoo
```

## Implantação em Ambiente de Produção

### 1. Configurações de Segurança

Para ambientes de produção, adicione as seguintes configurações de segurança:

1. **SSL/TLS**: Configure HTTPS para todos os serviços expostos externamente.
2. **Autenticação**: Implemente autenticação JWT para todos os serviços MCP.
3. **Rede**: Utilize uma rede Docker isolada para comunicação interna entre serviços.
4. **Secrets**: Utilize Docker Secrets ou Kubernetes Secrets para armazenar credenciais.

### 2. Escalabilidade

Para garantir escalabilidade em produção:

1. **Replicação**: Configure múltiplas réplicas de cada serviço.
2. **Balanceamento de Carga**: Utilize um balanceador de carga para distribuir requisições.
3. **Cache Distribuído**: Configure o Redis em modo cluster para cache distribuído.
4. **Monitoramento**: Implemente métricas e alertas para monitorar o desempenho.

### 3. Implantação em Kubernetes

Para ambientes de produção em grande escala, considere utilizar Kubernetes:

1. Converta o `docker-compose.yml` em manifestos Kubernetes.
2. Utilize Helm para gerenciar a implantação.
3. Configure HorizontalPodAutoscaler para escalar automaticamente com base na carga.
4. Implemente probes de liveness e readiness para garantir disponibilidade.

## Monitoramento e Manutenção

### 1. Monitoramento

Implemente monitoramento para todos os componentes:

1. **Métricas**: Utilize Prometheus para coletar métricas de desempenho.
2. **Visualização**: Utilize Grafana para visualizar métricas.
3. **Logs**: Utilize ELK Stack (Elasticsearch, Logstash, Kibana) para centralizar logs.
4. **Alertas**: Configure alertas para notificar sobre problemas.

### 2. Backup e Recuperação

Implemente estratégias de backup e recuperação:

1. **Backup Automático**: Configure backups automáticos para todos os dados.
2. **Retenção**: Defina políticas de retenção de backups.
3. **Recuperação**: Teste regularmente procedimentos de recuperação.
4. **Disaster Recovery**: Implemente um plano de recuperação de desastres.

### 3. Atualizações

Implemente um processo de atualização seguro:

1. **Versionamento**: Utilize versionamento semântico para todos os componentes.
2. **Canary Releases**: Implemente lançamentos canário para testar atualizações.
3. **Rollback**: Garanta que todas as atualizações possam ser revertidas facilmente.
4. **Testes Automatizados**: Execute testes automatizados antes de implantar atualizações.

## Solução de Problemas

### 1. Verificar Logs

```bash
# Verificar logs de um serviço específico
docker-compose logs -f mcp-odoo

# Verificar logs de todos os serviços
docker-compose logs -f
```

### 2. Verificar Conectividade

```bash
# Verificar se o MCP-Odoo está acessível
curl -X POST http://localhost:8000/tools/list -H "Content-Type: application/json" -d '{}'

# Verificar se o MCP-Orchestrator pode se comunicar com o MCP-Odoo
docker-compose exec mcp-orchestrator curl -X POST http://mcp-odoo:8000/tools/list -H "Content-Type: application/json" -d '{}'
```

### 3. Reiniciar Serviços

```bash
# Reiniciar um serviço específico
docker-compose restart mcp-odoo

# Reiniciar todos os serviços
docker-compose restart
```

### 4. Problemas Comuns e Soluções

1. **Erro de Conexão com o Odoo**: Verifique se o Odoo está acessível e se as credenciais estão corretas.
2. **Erro de Conexão com o Qdrant**: Verifique se o Qdrant está acessível e se a API Key está correta.
3. **Erro de Conexão com o Chatwoot**: Verifique se o Chatwoot está acessível e se a API Key está correta.
4. **Erro de Conexão com o Redis**: Verifique se o Redis está acessível e se a senha está correta.
5. **Erro de Autenticação**: Verifique se as credenciais estão corretas e se o token JWT é válido.

## Conclusão

Seguindo este guia, você pode implantar a arquitetura MCP First em ambientes de desenvolvimento, teste e produção. A arquitetura é modular e escalável, permitindo que você adicione novos componentes e expanda para outros contextos conforme necessário.

Para mais informações sobre a arquitetura MCP First, consulte os outros documentos na pasta `docs/`.
