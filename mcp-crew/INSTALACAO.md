# Instalação e Configuração do Stack AI

Este documento descreve a instalação e configuração do stack AI, que inclui vários serviços MCP (Model Context Protocol) e suas dependências.

## Serviços Disponíveis

### 1. MongoDB
- **Serviço**: MongoDB 6.0
- **Porta**: 27017
- **Container**: ai-mongodb
- **Volumes**: mongodb_data

### 2. Mongo Express
- **Serviço**: Interface web para MongoDB
- **URL**: http://localhost:8082
- **Credenciais**: admin/admin_password
- **Container**: ai-mongo-express

### 3. Qdrant
- **Serviço**: Banco de dados vetorial
- **URL API**: http://localhost:6333
- **URL Dashboard**: http://localhost:6333/dashboard
- **Container**: ai-qdrant
- **Volumes**: qdrant_data
- **Portas**: 
  - 6333: REST API e Dashboard
  - 6334: gRPC API

### 4. MCP-MongoDB
- **Serviço**: Servidor MCP para MongoDB
- **URL**: http://localhost:8001
- **Container**: mcp-mongodb
- **Dependências**: MongoDB

### 5. MCP-Qdrant
- **Serviço**: Servidor MCP para Qdrant
- **URL**: http://localhost:8002
- **Container**: mcp-qdrant
- **Dependências**: Qdrant

### 6. Redis
- **Serviço**: Cache e mensageria
- **Porta**: 6379
- **Container**: ai-redis
- **Volumes**: redis_data

## Instalação

1. Clone o repositório:
\`\`\`bash
git clone <repository_url>
cd ai_stack
\`\`\`

2. Inicie os serviços:
\`\`\`bash
docker-compose -f docker-compose.ai-stack.yml up -d
\`\`\`

3. Verifique o status dos serviços:
\`\`\`bash
docker-compose -f docker-compose.ai-stack.yml ps
\`\`\`

## Verificação de Conectividade

### MongoDB
- MongoDB está acessível via Mongo Express: http://localhost:8082
- MCP-MongoDB está conectado ao MongoDB através da rede ai_network
- Teste a conexão: \`curl http://localhost:8001/health\`

### Qdrant
- Qdrant está acessível via Dashboard: http://localhost:6333/dashboard
- MCP-Qdrant está conectado ao Qdrant através da rede ai_network
- Teste a conexão: \`curl http://localhost:8002/health\`

## Redes Docker

Todos os serviços estão na mesma rede Docker chamada \`ai_network\`, permitindo comunicação entre eles usando os nomes dos containers como hostnames.

## Volumes

- \`mongodb_data\`: Dados persistentes do MongoDB
- \`qdrant_data\`: Dados persistentes do Qdrant
- \`redis_data\`: Dados persistentes do Redis

## Healthchecks

Os serviços possuem healthchecks configurados para garantir sua disponibilidade:
- MongoDB: Verifica conexão na porta 27017
- Qdrant: Verifica endpoint /healthz
- Redis: Verifica comando PING
- MCP-MongoDB: Verifica endpoint /health
- MCP-Qdrant: Verifica endpoint /health

**Nota**: Mesmo que o status do healthcheck apareça como "starting", os serviços podem estar funcionando corretamente. Verifique diretamente as URLs/endpoints para confirmar a disponibilidade.
