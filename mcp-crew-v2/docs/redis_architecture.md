# Arquitetura Redis no MCP-Crew

Este documento descreve a arquitetura e uso do Redis no MCP-Crew, incluindo a separação entre o Redis interno do MCP-Crew e o MCP-Redis.

## Visão Geral

O Redis é utilizado em múltiplas camadas no ecossistema MCP:

1. **Redis do MCP-Crew**: Redis dedicado para cache interno, gerenciamento de contexto e estado do sistema MCP-Crew.
2. **MCP-Redis**: Um MCP que expõe operações Redis como ferramentas para agentes.

É importante manter uma clara separação entre esses dois usos do Redis para garantir segurança, isolamento e manutenibilidade.

## Redis do MCP-Crew

### Propósito

O Redis do MCP-Crew é um componente interno dedicado para:

- Cache de sistema (descoberta de ferramentas, resultados de consultas)
- Armazenamento de contexto de conversas
- Cache de embeddings
- Gerenciamento de estado temporário
- Isolamento multi-tenant

### Configuração

O Redis do MCP-Crew é executado em um contêiner Docker dedicado:

- **Host**: `mcp-crew-redis`
- **Porta**: `6379`
- **Rede**: `ai-docker`

### Estrutura de Chaves

Todas as chaves seguem o formato:

```
mcp-crew:{tenant_id}:{data_type}:{identifier}
```

Onde:
- `tenant_id`: ID do tenant para isolamento multi-tenant
- `data_type`: Tipo de dado (tool_discovery, conversation_context, query_result, embedding, etc.)
- `identifier`: Identificador específico para o item

### TTLs por Tipo de Dado

| Tipo de Dado | TTL Padrão | Descrição |
|--------------|------------|-----------|
| tool_discovery | 4 horas | Cache de ferramentas descobertas |
| conversation_context | 48 horas | Contexto de conversas |
| query_result | 1 hora | Resultados de consultas |
| embedding | 24 horas | Cache de embeddings |
| knowledge | 7 dias | Conhecimento persistente |
| event | 1 hora | Eventos temporários |

## MCP-Redis

### Propósito

O MCP-Redis é um MCP que expõe operações Redis como ferramentas para agentes, permitindo:

- Manipulação de listas, conjuntos, hashes
- Operações pub/sub
- Armazenamento e recuperação de dados específicos de agentes

### Separação do Redis do MCP-Crew

O MCP-Redis é logicamente separado do Redis do MCP-Crew:

1. **Separação de Responsabilidades**:
   - Redis do MCP-Crew: Cache interno e estado do sistema
   - MCP-Redis: Ferramenta para agentes

2. **Separação de Instâncias**:
   - Redis do MCP-Crew: Instância dedicada
   - MCP-Redis: Pode usar sua própria instância Redis

3. **Separação de Keyspace**:
   - Redis do MCP-Crew: Prefixo `mcp-crew:`
   - MCP-Redis: Prefixo definido pelo MCP-Redis

## Implementação no MCP-Crew

### RedisManager

O MCP-Crew implementa uma classe `RedisManager` para gerenciar todas as interações com o Redis interno:

- Conexão com Redis
- Particionamento por tenant
- Circuit breakers para proteção contra falhas
- TTLs configuráveis por tipo de dado
- Métodos específicos para diferentes tipos de dados

### Uso em Componentes do MCP-Crew

O `RedisManager` é utilizado em vários componentes do MCP-Crew:

1. **Descoberta de Ferramentas**:
   - Cache de ferramentas descobertas por MCP
   - Redução de chamadas repetidas para MCPs

2. **Gerenciamento de Contexto**:
   - Armazenamento de contexto de conversas
   - Persistência entre chamadas de agentes

3. **Cache de Consultas**:
   - Armazenamento de resultados de consultas frequentes
   - Redução de carga em sistemas externos

4. **Cache de Embeddings**:
   - Armazenamento de embeddings para textos frequentes
   - Redução de chamadas para modelos de embedding

## Boas Práticas

1. **Sempre use o RedisManager** para interagir com o Redis do MCP-Crew
2. **Sempre inclua o tenant_id** para garantir isolamento multi-tenant
3. **Respeite os TTLs recomendados** para cada tipo de dado
4. **Não armazene dados sensíveis** no Redis sem criptografia
5. **Monitore o uso de memória** para evitar problemas de performance

## Diagrama de Arquitetura

```
+----------------------------------+      +----------------------------------+
|           MCP-Crew               |      |           Agentes                |
|                                  |      |                                  |
|  +---------------------------+   |      |                                  |
|  |      RedisManager         |   |      |                                  |
|  +---------------------------+   |      |                                  |
|            |                     |      |            |                     |
|            v                     |      |            v                     |
|  +---------------------------+   |      |  +---------------------------+   |
|  |    Redis do MCP-Crew      |   |      |  |        MCP-Redis          |   |
|  | (Cache interno, contexto) |   |      |  | (Ferramenta para agentes) |   |
|  +---------------------------+   |      |  +---------------------------+   |
|                                  |      |                                  |
+----------------------------------+      +----------------------------------+
```

## Conclusão

A separação clara entre o Redis do MCP-Crew e o MCP-Redis é essencial para manter a segurança, isolamento e manutenibilidade do sistema. O Redis do MCP-Crew é um componente interno dedicado para cache e estado do sistema, enquanto o MCP-Redis é uma ferramenta para agentes.
