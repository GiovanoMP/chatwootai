# MongoDB MCP Server Oficial

Este diretório contém a configuração do MongoDB MCP Server oficial para integração com o projeto ChatwootAI.

## Sobre o MongoDB MCP Server

O MongoDB MCP Server é um servidor que implementa o Model Context Protocol (MCP) para permitir que LLMs e agentes de IA interajam com bancos de dados MongoDB. Este servidor possibilita:

- Exploração de esquemas de coleções
- Execução de pipelines de agregação
- Análise de planos de execução
- Acesso seguro e controlado aos dados

## Configuração

O servidor está configurado para:

1. Conectar-se ao MongoDB existente na rede `ai-stack`
2. Expor a API MCP na porta 8001
3. Limitar o acesso às coleções específicas definidas em `ALLOWED_COLLECTIONS`
4. Limitar o número máximo de resultados para 100 documentos

## Como Iniciar

Para iniciar o servidor MCP-MongoDB oficial:

```bash
cd /home/giovano/Projetos/ai_stack/ai-stack/mcp-mongodb-official
docker-compose up -d
```

## Como Verificar o Status

```bash
docker ps | grep mcp-mongodb-official
```

## Como Testar a Conexão

Para testar a conexão com o MCP-MongoDB oficial:

```bash
curl http://localhost:8001/health
```

## Integração com CrewAI

Para integrar o MCP-MongoDB oficial com o CrewAI, use o seguinte código:

```python
from crewai_tools import MCPServerAdapter

# Conectar ao MCP-MongoDB
with MCPServerAdapter({"url": "http://localhost:8001/sse"}) as mongodb_tools:
    # Usar as ferramentas do MongoDB
    print(f"Ferramentas disponíveis: {len(mongodb_tools)}")
    for tool in mongodb_tools:
        print(f"- {tool.name}: {tool.description}")
```

## Documentação Oficial

- [GitHub do MongoDB MCP Server](https://github.com/mongodb-js/mongodb-mcp-server)
- [Anúncio do MongoDB MCP Server](https://www.mongodb.com/blog/post/announcing-mongodb-mcp-server)
