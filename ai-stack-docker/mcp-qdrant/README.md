# MCP-Qdrant na AI Stack

Este diretório contém a configuração do MCP-Qdrant, um servidor MCP (Model Context Protocol) oficial que se integra com o banco de dados vetorial Qdrant para fornecer capacidades de busca semântica e armazenamento de informações para agentes CrewAI.

## Características Específicas

- **Transporte SSE**: Diferente de outros servidores MCP, o MCP-Qdrant está configurado para usar o transporte SSE (Server-Sent Events) em vez de HTTP tradicional.
- **Endpoint Principal**: `/sse` (não possui endpoints `/health` ou `/resources` tradicionais)
- **Porta**: 8000 (interna) / 8003 (externa)
- **Modelo de Embeddings**: `sentence-transformers/all-MiniLM-L6-v2`
- **Coleção Qdrant**: `ai_memories`

## Arquitetura

O MCP-Qdrant é construído a partir do código-fonte oficial clonado em `/home/giovano/Projetos/ai_stack/mcp-qdrant` e dockerizado neste diretório. Ele se conecta ao serviço Qdrant (`ai-qdrant`) na porta 6333 para armazenar e recuperar informações vetoriais.

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   CrewAI    │────▶│ MCP-Qdrant  │────▶│   Qdrant    │
│   Agentes   │     │ (SSE:8003)  │     │ (HTTP:6333) │
└─────────────┘     └─────────────┘     └─────────────┘
```

## Configuração

O MCP-Qdrant é configurado através de variáveis de ambiente no `docker-compose.yml`:

```yaml
environment:
  - QDRANT_URL=http://ai-qdrant:6333
  - COLLECTION_NAME=ai_memories
  - EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
  - FASTMCP_PORT=8000
  - FASTMCP_HOST=0.0.0.0
command: ["uvx", "mcp-server-qdrant", "--transport", "sse"]
```

## Monitoramento

Devido à natureza do transporte SSE, o monitoramento do MCP-Qdrant é diferente dos outros serviços:

1. **Monitoramento TCP** (recomendado):
   - Host: `mcp-qdrant` (interno) ou `localhost` (externo)
   - Porta: 8000 (interno) ou 8003 (externo)

2. **Verificação Manual**:
   ```bash
   # Verificar se o servidor está rodando
   docker logs mcp-qdrant | grep "Uvicorn running"
   
   # Verificar conexão com Qdrant
   docker logs mcp-qdrant | grep "Connecting to Qdrant"
   
   # Verificar se a porta está acessível
   nc -zv localhost 8003
   ```

3. **Verificação do Endpoint SSE**:
   ```bash
   curl -I http://localhost:8003/sse
   ```
   Deve retornar status 200 OK e content-type: text/event-stream

## Integração com CrewAI

Para integrar o MCP-Qdrant com agentes CrewAI, use o `MCPServerAdapter` apontando para o endpoint SSE:

```python
from crewai.tools.mcp_server_adapter import MCPServerAdapter

# Configuração do adaptador MCP para o Qdrant
mcp_qdrant = MCPServerAdapter(server_url="http://localhost:8003/sse")

# Listar recursos disponíveis
resources = mcp_qdrant.list_resources()

# Armazenar informação
store_result = mcp_qdrant.invoke_tool(
    "qdrant-store",
    {
        "information": "Informação a ser armazenada",
        "metadata": {"source": "exemplo"},
        "collection_name": "ai_memories"
    }
)

# Buscar informação
find_result = mcp_qdrant.invoke_tool(
    "qdrant-find",
    {
        "query": "consulta semântica",
        "collection_name": "ai_memories"
    }
)
```

## Ferramentas Disponíveis

O MCP-Qdrant fornece duas ferramentas principais:

1. **qdrant-store**: Armazena informações com embeddings vetoriais
   - Parâmetros: `information` (texto), `metadata` (objeto), `collection_name` (opcional)

2. **qdrant-find**: Busca informações semanticamente similares
   - Parâmetros: `query` (texto), `collection_name` (opcional)

## Solução de Problemas

Se o MCP-Qdrant não estiver respondendo:

1. Verifique se o container está em execução: `docker ps | grep mcp-qdrant`
2. Verifique os logs: `docker logs mcp-qdrant`
3. Confirme que o Qdrant está acessível: `curl http://localhost:6333/collections`
4. Reinicie o serviço: `cd /home/giovano/Projetos/ai_stack/ai-stack-docker/mcp-qdrant && docker-compose down && docker-compose up -d`

## Notas Importantes

- O MCP-Qdrant depende do serviço Qdrant estar em execução e acessível
- O healthcheck do Docker pode mostrar o container como "unhealthy" mesmo quando está funcionando corretamente, devido à natureza do transporte SSE
- Para testes de integração, sempre verifique a conectividade TCP antes de tentar usar o adaptador CrewAI
