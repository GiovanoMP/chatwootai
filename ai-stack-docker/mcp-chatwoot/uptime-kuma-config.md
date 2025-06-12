# Configuração de Monitoramento para MCP-Chatwoot

Este documento descreve como configurar o monitoramento do MCP-Chatwoot no Uptime Kuma.

## Configuração do Monitor

### 1. MCP-Chatwoot Health

- **Nome Amigável**: MCP Chatwoot Health
- **Tipo de Monitoramento**: HTTP
- **URL**: http://mcp-chatwoot:8004/health
- **Intervalo**: 60 segundos
- **Método**: GET
- **Condição de Sucesso**: Status Code 200 e resposta contendo `{"status":"healthy"}`
- **Verificação de Resposta**: Verificar se o JSON contém `"chatwoot_connection":"connected"`
- **Nota**: Use o nome do contêiner e porta interna (mcp-chatwoot:8004) quando monitorado de dentro da rede Docker; use localhost:8004 quando monitorado externamente

### 2. MCP-Chatwoot API

- **Nome Amigável**: MCP Chatwoot API
- **Tipo de Monitoramento**: TCP
- **Host**: mcp-chatwoot
- **Porta**: 8004
- **Intervalo**: 60 segundos
- **Condição de Sucesso**: Porta aberta e acessível
- **Nota**: Use o nome do contêiner (mcp-chatwoot) quando monitorado de dentro da rede Docker; use localhost quando monitorado externamente

## Verificação Manual

Para verificar manualmente se o MCP-Chatwoot está funcionando corretamente:

```bash
# Teste de saúde (de fora da rede Docker)
curl http://localhost:8004/health

# Teste de saúde (de dentro da rede Docker)
docker exec ai-uptime-kuma curl http://mcp-chatwoot:8004/health

# Verificar logs do contêiner
docker logs mcp-chatwoot

# Verificar se o serviço está em execução
docker ps | grep mcp-chatwoot
```

## Resolução de Problemas Comuns

1. **Erro de conexão com o Chatwoot**:
   - Verifique se o Chatwoot está acessível
   - Confirme se as variáveis de ambiente CHATWOOT_BASE_URL e CHATWOOT_ACCESS_TOKEN estão configuradas corretamente

2. **Serviço não inicia**:
   - Verifique os logs do contêiner: `docker logs mcp-chatwoot`
   - Confirme se todas as variáveis de ambiente necessárias estão configuradas

3. **Porta não está acessível**:
   - Verifique se o contêiner está em execução: `docker ps | grep mcp-chatwoot`
   - Confirme se a porta está mapeada corretamente no docker-compose.yml
