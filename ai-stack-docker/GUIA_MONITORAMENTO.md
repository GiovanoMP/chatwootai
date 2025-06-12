# Guia de Monitoramento - ChatwootAI

Este documento serve como guia para configurar o monitoramento dos serviços do ChatwootAI usando o Uptime Kuma.

## Serviços para Monitoramento

### 1. Portainer
- **Nome Amigável**: Portainer
- **Tipo de Monitoramento**: HTTP
- **URL**: http://ai-portainer:9000
- **Intervalo**: 60 segundos
- **Método**: GET
- **Condição de Sucesso**: Status Code 200
- **Nota**: Use o nome do contêiner (ai-portainer:9000) quando monitorado de dentro da rede Docker; use localhost:9000 quando monitorado externamente

### 2. MongoDB
- **Nome Amigável**: MongoDB
- **Tipo de Monitoramento**: TCP
- **Host**: ai-mongodb
- **Porta**: 27017
- **Intervalo**: 60 segundos
- **Condição de Sucesso**: Conexão TCP estabelecida
- **Nota**: Use o nome do contêiner (ai-mongodb) quando monitorado de dentro da rede Docker; use localhost quando monitorado externamente

### 3. Mongo Express
- **Nome Amigável**: Mongo Express
- **Tipo de Monitoramento**: HTTP
- **URL**: http://ai-mongo-express:8081
- **Intervalo**: 60 segundos
- **Método**: GET
- **Autenticação**: Basic Auth
  - **Usuário**: admin
  - **Senha**: express_password
- **Condição de Sucesso**: Status Code 200
- **Nota**: Use o nome do contêiner e porta interna (ai-mongo-express:8081) quando monitorado de dentro da rede Docker; use localhost:8082 quando monitorado externamente

### 4. MCP-MongoDB
- **Nome Amigável**: MCP MongoDB
- **Tipo de Monitoramento**: HTTP
- **URL**: http://mcp-mongodb:8000/health
- **Intervalo**: 60 segundos
- **Método**: GET
- **Condição de Sucesso**: Status Code 200 e resposta contendo `{"status":"healthy"}`
- **Verificação de Resposta**: Verificar se o JSON contém `"mongodb":"connected"`
- **Nota**: Use o nome do contêiner e porta interna (mcp-mongodb:8000) quando monitorado de dentro da rede Docker; use localhost:8001 quando monitorado externamente

### 5. MCP-MongoDB Resources
- **Nome Amigável**: MCP MongoDB Resources
- **Tipo de Monitoramento**: HTTP
- **URL**: http://mcp-mongodb:8000/resources
- **Intervalo**: 120 segundos
- **Método**: GET
- **Condição de Sucesso**: Status Code 200 e resposta contendo `"resources"`
- **Verificação de Resposta**: Verificar se o JSON contém pelo menos uma coleção
- **Nota**: Use o nome do contêiner e porta interna (mcp-mongodb:8000) quando monitorado de dentro da rede Docker; use localhost:8001 quando monitorado externamente

### 6. Redis
- **Nome Amigável**: Redis
- **Tipo de Monitoramento**: TCP
- **Host**: ai-redis
- **Porta**: 6379
- **Intervalo**: 60 segundos
- **Condição de Sucesso**: Conexão TCP estabelecida
- **Nota**: Use o nome do contêiner (ai-redis) quando monitorado de dentro da rede Docker; use localhost quando monitorado externamente

### 7. Redis Commander
- **Nome Amigável**: Redis Commander
- **Tipo de Monitoramento**: HTTP
- **URL**: http://ai-redis-commander:8081
- **Intervalo**: 60 segundos
- **Método**: GET
- **Autenticação**: Basic Auth
  - **Usuário**: admin
  - **Senha**: admin_password
- **Condição de Sucesso**: Status Code 200
- **Nota**: Use o nome do contêiner e porta interna (ai-redis-commander:8081) quando monitorado de dentro da rede Docker; use localhost:8083 quando monitorado externamente

### 8. MCP-Redis Health
- **Nome Amigável**: MCP Redis Health
- **Tipo de Monitoramento**: HTTP
- **URL**: http://mcp-redis:8080/health
- **Intervalo**: 60 segundos
- **Método**: GET
- **Condição de Sucesso**: Status Code 200 e resposta contendo `"status":"running"`
- **Verificação de Resposta**: Verificar se o JSON contém `"redis_connection":"connected"`
- **Nota**: Use o nome do contêiner e porta interna (mcp-redis:8080) quando monitorado de dentro da rede Docker; use localhost:8080 quando monitorado externamente

### 9. MCP-Redis 
- **Nome Amigável**: MCP Redis
- **Tipo de Monitoramento**: TCP
- **Host**: mcp-redis
- **Porta**: 8000
- **Intervalo**: 60 segundos
- **Condição de Sucesso**: Conexão TCP estabelecida
- **Nota**: O MCP-Redis não expõe um endpoint HTTP `/resources` como o MCP-MongoDB. A verificação de conectividade TCP é a melhor forma de monitorar se o serviço está disponível para os agentes. Use o nome do contêiner e porta interna (mcp-redis:8000) quando monitorado de dentro da rede Docker; use localhost:8002 quando monitorado externamente

### 10. Qdrant
- **Nome Amigável**: Qdrant
- **Tipo de Monitoramento**: HTTP
- **URL**: http://ai-qdrant:6333/healthz
- **Intervalo**: 60 segundos
- **Método**: GET
- **Condição de Sucesso**: Status Code 200 e resposta contendo `healthz check passed`
- **Nota**: Use o nome do contêiner (ai-qdrant:6333) quando monitorado de dentro da rede Docker; use localhost:6333 quando monitorado externamente

### 11. Qdrant Collections
- **Nome Amigável**: Qdrant Collections
- **Tipo de Monitoramento**: HTTP
- **URL**: http://ai-qdrant:6333/collections
- **Intervalo**: 120 segundos
- **Método**: GET
- **Condição de Sucesso**: Status Code 200
- **Verificação de Resposta**: Verificar se o JSON contém `"result"`
- **Nota**: Use o nome do contêiner (ai-qdrant:6333) quando monitorado de dentro da rede Docker; use localhost:6333 quando monitorado externamente

### 12. MCP-Qdrant 
- **Nome Amigável**: MCP Qdrant 
- **Tipo de Monitoramento**: TCP
- **Host**: mcp-qdrant
- **Porta**: 8000
- **Intervalo**: 60 segundos
- **Condição de Sucesso**: Porta aberta e acessível
- **Nota**: O MCP-Qdrant usa o transporte SSE (Server-Sent Events) e não expõe endpoints tradicionais como /health ou /resources, portanto o monitoramento TCP é mais confiável. Use o nome do contêiner e porta interna (mcp-qdrant:8000) quando monitorado de dentro da rede Docker; use localhost:8003 quando monitorado externamente.

### 13. MCP-Qdrant Logs
- **Verificação Manual**: Para verificar se o MCP-Qdrant está funcionando corretamente, execute o seguinte comando:
  ```bash
  docker logs mcp-qdrant | grep "Uvicorn running"
  ```
- **Resultado Esperado**: Deve mostrar a mensagem "Uvicorn running on http://0.0.0.0:8000"
- **Verificação de Conexão com Qdrant**: Para verificar se o MCP-Qdrant está conectado ao Qdrant, execute:
  ```bash
  docker logs mcp-qdrant | grep "Connecting to Qdrant"
  ```
- **Resultado Esperado**: Deve mostrar a mensagem "Connecting to Qdrant at http://ai-qdrant:6333"
- **Verificação de Porta**: Para verificar se a porta está aberta e acessível:
  ```bash
  nc -zv localhost 8003
  ```
- **Resultado Esperado**: "Connection to localhost (127.0.0.1) 8003 port [tcp/*] succeeded!"

### 14. MCP-Chatwoot
- **Nome Amigável**: MCP Chatwoot
- **Tipo de Monitoramento**: HTTP
- **URL**: http://mcp-chatwoot:8004/health
- **Intervalo**: 60 segundos
- **Método**: GET
- **Condição de Sucesso**: Status Code 200 e resposta contendo `{"status":"healthy"}`
- **Verificação de Resposta**: Verificar se o JSON contém `"tools_count"` com valor maior que 0
- **Nota**: Use o nome do contêiner e porta interna (mcp-chatwoot:8004) quando monitorado de dentro da rede Docker; use localhost:8004 quando monitorado externamente

### 15. MCP-Chatwoot Logs
- **Verificação Manual**: Para verificar se o MCP-Chatwoot está funcionando corretamente, execute o seguinte comando:
  ```bash
  docker logs mcp-chatwoot | grep "Uvicorn running"
  ```
- **Resultado Esperado**: Deve mostrar a mensagem "Uvicorn running on http://0.0.0.0:8004 (Press CTRL+C to quit)"
- **Verificação de Configuração**: Para verificar se o MCP-Chatwoot está configurado corretamente, execute:
  ```bash
  docker logs mcp-chatwoot | grep "MCP-Chatwoot iniciado com sucesso"
  ```
- **Resultado Esperado**: Deve mostrar a mensagem "MCP-Chatwoot iniciado com sucesso"
- **Verificação de Porta**: Para verificar se a porta está aberta e acessível:
  ```bash
  nc -zv localhost 8004
  ```
- **Resultado Esperado**: "Connection to localhost (127.0.0.1) 8004 port [tcp/*] succeeded!"

## Configuração no Uptime Kuma

1. Acesse o Uptime Kuma em http://localhost:3001
2. Faça login com suas credenciais
3. Clique em "+ Monitor" para adicionar um novo monitor
4. Preencha os campos conforme as especificações acima para cada serviço
5. Configure notificações se desejar ser alertado sobre problemas

## Problemas Conhecidos com Healthchecks do Docker

O Docker às vezes reporta serviços como "unhealthy" mesmo quando estão funcionando corretamente. Isso pode ocorrer devido a:

1. **Tempo de inicialização**: Alguns serviços demoram mais para inicializar completamente do que o tempo configurado no healthcheck
2. **Configurações de autenticação**: Serviços com autenticação podem falhar no healthcheck se as credenciais não forem fornecidas corretamente
3. **Dependências**: Um serviço pode depender de outro que ainda não está totalmente inicializado

Por esses motivos, o Uptime Kuma é uma ferramenta mais confiável para monitoramento de longo prazo, pois:

- Permite configuração mais detalhada dos checks
- Suporta autenticação nas verificações HTTP
- Fornece histórico de disponibilidade e tempo de resposta
- Oferece notificações configuráveis

## Verificação Manual de Serviços

Para verificar manualmente se um serviço está funcionando corretamente:

### MongoDB
```bash
# Teste de conexão TCP (de fora da rede Docker)
nc -zv localhost 27017

# Teste de conexão TCP (de dentro da rede Docker)
docker exec ai-uptime-kuma nc -zv ai-mongodb 27017

# Teste de autenticação (requer mongo shell, de fora da rede Docker)
mongosh --host localhost --port 27017 -u admin -p admin_password --authenticationDatabase admin

# Teste de autenticação (de dentro da rede Docker)
docker exec ai-uptime-kuma mongosh --host ai-mongodb --port 27017 -u admin -p admin_password --authenticationDatabase admin
```

### Mongo Express
```bash
# Teste HTTP com autenticação (de fora da rede Docker)
curl -u admin:express_password http://localhost:8082

# Teste HTTP com autenticação (de dentro da rede Docker)
docker exec ai-uptime-kuma curl -u admin:express_password http://ai-mongo-express:8081
```

### Portainer
```bash
# Teste HTTP simples (de fora da rede Docker)
curl -I http://localhost:9000

# Teste HTTP simples (de dentro da rede Docker)
docker exec ai-uptime-kuma curl -I http://ai-portainer:9000
```

### MCP-Chatwoot
```bash
# Teste HTTP simples (de fora da rede Docker)
curl http://localhost:8004/health

# Teste HTTP simples (de dentro da rede Docker)
docker exec ai-uptime-kuma curl http://mcp-chatwoot:8004/health

# Verificar logs do serviço
docker logs mcp-chatwoot --tail 20

# Verificar se o serviço está em execução
docker ps | grep mcp-chatwoot
```

### Qdrant
```bash
# Teste de saúde (de fora da rede Docker)
curl http://localhost:6333/healthz

# Teste de saúde (de dentro da rede Docker)
docker exec ai-uptime-kuma curl http://ai-qdrant:6333/healthz

# Listar coleções (de fora da rede Docker)
curl http://localhost:6333/collections

# Listar coleções (de dentro da rede Docker)
docker exec ai-uptime-kuma curl http://ai-qdrant:6333/collections
```

### MCP-Qdrant
```bash
# Teste de saúde (de fora da rede Docker)
curl http://localhost:8003/health

# Teste de saúde (de dentro da rede Docker)
docker exec ai-uptime-kuma curl http://mcp-qdrant:8000/health

# Listar recursos disponíveis (de fora da rede Docker)
curl http://localhost:8003/resources

# Listar recursos disponíveis (de dentro da rede Docker)
docker exec ai-uptime-kuma curl http://mcp-qdrant:8000/resources
```
