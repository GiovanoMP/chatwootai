# MCP-Crew v2 - Otimização do Redis

## Visão Geral

Este documento serve como guia para o próximo desenvolvedor que continuará o trabalho de unificação e otimização do uso do Redis no MCP-Crew v2. Ele contém informações sobre o que já foi implementado, o que ainda precisa ser feito, e diretrizes para garantir consistência no desenvolvimento.

## O que já foi implementado

### 1. Unificação do RedisManager

- Implementamos um RedisManager robusto que é usado globalmente no sistema
- Configuramos circuit breaker, fallback local e TTLs otimizados
- Atualizamos a configuração padrão para conexão local com Redis CREW (localhost:6380)
- Implementamos isolamento multi-tenant via `tenant_id` (account_id)

### 2. TTLs Otimizados

- Implementamos TTLs específicos para diferentes tipos de dados:
  - **Ferramentas descobertas**: TTLs específicos por MCP (MongoDB: 8h, Redis: 4h, Chatwoot: 2h, Qdrant: 4h)
  - **Contexto de conversação**: TTLs baseados na importância (Alta: 7 dias, Média: 3 dias, Baixa: 1 dia)
  - **Conhecimento compartilhado**: TTLs específicos por tipo de conhecimento (Produto: 30 dias, Mercado: 3 dias, etc.)

### 3. Unificação do Sistema de Conhecimento

- Unificamos os sistemas duplicados `knowledge_manager.py` e `knowledge_sharing.py`
- Mantivemos apenas o `knowledge_manager.py` que já usava o RedisManager robusto
- Atualizamos todas as referências nos arquivos do projeto

### 4. Testes e Validação

- Executamos testes de conexão, operações básicas e isolamento multi-tenant
- Confirmamos que o sistema de descoberta de ferramentas via conectores MCP está funcionando corretamente
- Verificamos que o RedisManager está operacional no contexto real

## O que ainda precisa ser implementado

### 1. Sistema de Eventos

Implementar um sistema de eventos usando Redis Streams para comunicação assíncrona entre componentes:

- Criar classes `Event`, `EventType` e `EventPriority`
- Implementar métodos para publicar e assinar eventos
- Configurar TTLs específicos para diferentes tipos de eventos
- Implementar consumer threads para processamento assíncrono

### 2. Cache de Embeddings

Implementar um sistema para armazenar embeddings de documentos e consultas:

- Criar métodos para armazenar e recuperar vetores de embedding
- Configurar TTLs específicos para diferentes tipos de embeddings
- Otimizar o armazenamento de grandes vetores no Redis

### 3. Gerenciamento de Sessão

Implementar um sistema para manter o estado da sessão do usuário:

- Criar métodos para armazenar e recuperar dados de sessão
- Configurar TTLs curtos para dados de sessão
- Implementar limpeza automática de sessões expiradas

### 4. Filas de Tarefas

Implementar um sistema de filas para processamento assíncrono de tarefas:

- Criar métodos para enfileirar e processar tarefas
- Implementar prioridades e retry de tarefas
- Configurar workers para processamento distribuído

### 5. Rate Limiting

Implementar um sistema para limitar o número de requisições por tenant:

- Criar métodos para verificar e incrementar contadores de requisições
- Configurar limites específicos por tipo de operação
- Implementar expiração automática de contadores

## Diretrizes de Implementação

### Uso do RedisManager

Sempre use o RedisManager robusto para interagir com o Redis:

```python
# Exemplo de uso do RedisManager
from src.redis_manager.redis_manager import redis_manager, DataType

# Para armazenar dados
redis_manager.set(
    tenant_id="account123",
    data_type=DataType.KNOWLEDGE,
    identifier="topic:id123",
    value=data_dict,
    ttl=86400  # 24 horas
)

# Para recuperar dados
data = redis_manager.get(
    tenant_id="account123",
    data_type=DataType.KNOWLEDGE,
    identifier="topic:id123"
)
```

### TTLs Otimizados

Sempre use TTLs específicos para diferentes tipos de dados:

- Dados que mudam frequentemente: TTLs curtos (minutos a horas)
- Dados que mudam ocasionalmente: TTLs médios (horas a dias)
- Dados que mudam raramente: TTLs longos (dias a semanas)

### Isolamento Multi-tenant

Sempre use o `tenant_id` (account_id) para garantir isolamento entre tenants:

- Todas as chaves no Redis devem incluir o tenant_id
- Nunca compartilhe dados entre tenants sem uma razão específica

### Fallback Local

O RedisManager já implementa fallback local para resiliência:

- Em caso de falha do Redis, os dados são armazenados localmente
- Quando o Redis volta a funcionar, os dados são sincronizados

### Testes

Sempre escreva testes para novas funcionalidades:

- Teste o comportamento normal
- Teste o comportamento em caso de falha do Redis
- Teste o isolamento multi-tenant

## Variáveis de Ambiente

As seguintes variáveis de ambiente são usadas para configurar o Redis:

- `REDIS_CREW_HOST` (default: `localhost`)
- `REDIS_CREW_PORT` (default: `6380`)
- `REDIS_CREW_DB` (default: `0`)
- `REDIS_CREW_PASSWORD` (default: `None`)
- `REDIS_CREW_PREFIX` (default: `mcp-crew:`)
- `REDIS_CREW_POOL_SIZE` (default: `10`)
- `REDIS_CIRCUIT_BREAKER_THRESHOLD` (default: `5`)
- `REDIS_CIRCUIT_BREAKER_TIMEOUT` (default: `60`)

## Documentação

Ao implementar novas funcionalidades, atualize o arquivo `evolucao_projeto.md` com:

- Descrição da funcionalidade implementada
- Decisões de design importantes
- Exemplos de uso
- Considerações de desempenho e segurança

## Próximos Passos Recomendados

1. Comece implementando o Sistema de Eventos, pois ele será usado por outros componentes
2. Em seguida, implemente o Cache de Embeddings para otimizar pesquisas semânticas
3. Depois, implemente o Gerenciamento de Sessão para manter o estado do usuário
4. Em seguida, implemente as Filas de Tarefas para processamento assíncrono
5. Por fim, implemente o Rate Limiting para proteger o sistema contra sobrecarga

## Contato

Se tiver dúvidas ou precisar de ajuda, entre em contato com a equipe de desenvolvimento.

---

**Lembre-se**: O objetivo principal é garantir um sistema robusto, resiliente e eficiente que aproveite ao máximo os recursos do Redis para o MCP-Crew v2.
