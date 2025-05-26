# Documentação da Infraestrutura Atual

## Contêineres Docker Ativos

| Container ID | Imagem | Portas | Status | Nome |
|--------------|--------|--------|--------|------|
| cc2e1dd45ebd | odoo:16 | 8069:8069 | Em execução | odoo16-odoo-1 |
| 39c172100636 | postgres:13 | 5433:5432 | Em execução | odoo16-db-1 |
| 50f05e506f1c | vectorization-service:latest | 8004:8004 | Em execução | vectorization-service |
| 786f73e50c8c | mongo:6.0-focal | 27017:27017 | Em execução | chatwoot-mongodb |
| 25de87111b01 | mongo-express:latest | 8082:8081 | Em execução | chatwoot-mongo-express |
| 97275264eb61 | mongo-config-service-webhook-mongo | 8003:8003 | Em execução | chatwoot-webhook-mongo |
| 5382ac7d6701 | portainer/portainer-ce | 9000:9000 | Em execução | portainer |
| chatwoot-redis | redis:6.2-alpine | 6379:6379 | Em execução | chatwoot-redis |

## Contêineres Docker Parados

| Container ID | Imagem | Status | Nome |
|--------------|--------|--------|------|
| b6e051857b7b | qdrant/qdrant | Parado | qdrant |

## Redes Docker

| Network ID | Nome | Driver | Escopo | Uso |
|------------|------|--------|--------|-----|
| 0ad5cb1efb92 | bridge | bridge | local | Rede padrão do Docker |
| d67d4d0763f2 | chatwoot-mongo-network | bridge | local | Rede para MongoDB e serviços relacionados |
| a9c74bea30e3 | chatwoot-network | bridge | local | **Rede principal** para comunicação entre serviços |
| c1dcd3f0d24c | odoo16_default | bridge | local | Rede para Odoo e PostgreSQL |
| 15ad96088415 | odoo16_odoo-network | bridge | local | Rede adicional do Odoo |

## Volumes Docker Relevantes

| Driver | Nome do Volume | Uso |
|--------|----------------|-----|
| local | chatwoot-mongodb-data | Dados do MongoDB para Chatwoot |
| local | chatwoot-redis-data | Dados do Redis para Chatwoot |
| local | odoo16_odoo-db-data | Dados do PostgreSQL para Odoo |
| local | odoo16_odoo-web-data | Dados web do Odoo |
| local | portainer_data | Dados do Portainer |
| local | redis_data | Dados do Redis reinstalado |

## Configuração Docker Compose Planejada

O arquivo `docker-compose.yml` define os seguintes serviços:

### Serviços MCP

| Serviço | Porta | Dependências | Descrição |
|---------|-------|--------------|-----------|
| mcp-odoo | 8000 | redis | Interface MCP para Odoo ERP |
| mcp-mongodb | 8001 | redis, mongodb | Interface MCP para MongoDB |
| mcp-qdrant | 8002 | redis, qdrant | Interface MCP para Qdrant |

### Serviços de Infraestrutura

| Serviço | Porta | Volumes | Descrição |
|---------|-------|---------|-----------|
| redis | 6379 | redis-data | Cache e comunicação entre serviços |
| mongodb | 27017 | mongodb-data | Armazenamento de configurações |
| qdrant | 6333, 6334 | qdrant-data | Armazenamento vetorial |

### Serviços de Aplicação

| Serviço | Porta | Dependências | Descrição |
|---------|-------|--------------|-----------|
| crewai-api | 8003 | mcp-odoo, mcp-mongodb, mcp-qdrant, redis | API para orquestração de crews |

## Mapeamento de Portas

| Porta | Serviço | Descrição |
|-------|---------|-----------|
| 8000 | mcp-odoo | Interface MCP para Odoo |
| 8001 | mcp-mongodb | Interface MCP para MongoDB |
| 8002 | mcp-qdrant | Interface MCP para Qdrant |
| 8003 | crewai-api | API de orquestração |
| 8004 | vectorization-service | Serviço de vetorização (existente) |
| 8069 | odoo | Odoo ERP (existente) |
| 8082 | mongo-express | Interface web para MongoDB (existente) |
| 6379 | redis | Cache e mensageria |
| 6333, 6334 | qdrant | Armazenamento vetorial |
| 27017 | mongodb | Banco de dados de configurações |
| 9000 | portainer | Gerenciamento de contêineres (existente) |

## Serviços Reinstalados

### MongoDB

- **Contêiner**: chatwoot-mongodb
- **Imagem**: mongo:6.0-focal
- **Porta**: 27017
- **Credenciais**: 
  - Admin: admin / chatwoot_mongodb_password
  - Aplicação: config_user / config_password
- **Banco de dados**: config_service
- **Rede**: chatwoot-mongo-network
- **Volume**: chatwoot-mongodb-data
- **Interface Web**: Mongo Express (http://localhost:8082)

### Redis

- **Contêiner**: chatwoot-redis
- **Imagem**: redis:6.2-alpine
- **Porta**: 6379
- **Senha**: redispassword
- **Rede**: chatwoot-network
- **Volume**: redis_data
- **Configuração**: AOF habilitado para persistência

## Configuração Multi-tenant

- Arquivo `.env` configurado com suporte a múltiplos tenants
- Tenant padrão: account_1
- Estrutura preparada para adicionar novos tenants no futuro

## Observações

1. **Serviços Existentes**: Odoo, MongoDB, Redis, e serviço de vetorização estão em execução.

2. **Serviços Planejados**: O docker-compose.yml define serviços MCP que ainda precisam ser implementados.

3. **Conflitos de Porta**: 
   - O serviço chatwoot-webhook-mongo já está usando a porta 8003, que é a mesma planejada para o crewai-api.
   - Será necessário ajustar o mapeamento de portas para evitar conflitos.

4. **Serviços Parados**:
   - O contêiner Qdrant está parado, mas é necessário para o funcionamento do mcp-qdrant.

5. **Organização do Projeto**:
   - Removido diretório legado redis-installation
   - Mantidos apenas componentes essenciais para a arquitetura atual

## Próximos Passos

1. **Resolver Conflitos de Porta**: Ajustar o mapeamento de portas para evitar conflitos.
2. **Iniciar Qdrant**: Reiniciar o Qdrant que é necessário para o funcionamento do sistema.
3. **Implementar MCPs**: Prosseguir com a análise e implementação dos servidores MCP.
4. **Integrar Rede Única**: Garantir que todos os serviços estejam na mesma rede Docker para facilitar a comunicação.
