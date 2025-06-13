# Evolução do Projeto MCP-Crew v2

Este documento registra as principais evoluções e modificações realizadas no projeto MCP-Crew v2, bem como os próximos passos planejados.

## Unificação do Redis (Junho 2025)

### Contexto e Objetivos

O sistema MCP-Crew v2 utiliza Redis para cache, gerenciamento de contexto e estado. Identificamos a necessidade de unificar e aprimorar a implementação do RedisManager para:

1. Utilizar a instância Redis CREW (porta 6380) para cache interno do sistema
2. Garantir isolamento multi-tenant através de particionamento por account_id
3. Implementar mecanismos de resiliência (circuit breaker e fallback local)
4. Separar claramente o uso do Redis entre o sistema interno e os agentes AI

### Análise da Situação Anterior

Identificamos duas implementações do RedisManager:

1. Uma implementação robusta em `src/redis_manager/redis_manager.py` com recursos avançados
2. Uma implementação mais simples em `src/config/config.py` com funcionalidades básicas

O sistema estava usando a implementação mais simples para cache interno, enquanto a implementação robusta não estava sendo utilizada globalmente.

### Modificações Realizadas

#### 1. Aprimoramento do RedisManager (`src/redis_manager/redis_manager.py`)

- Adicionado suporte a variáveis de ambiente para configuração
- Implementado fallback para cache local quando o Redis não está disponível
- Adicionada verificação de conexão no início
- Melhorado o circuit breaker com configurações via variáveis de ambiente
- Criada instância global `redis_manager` para uso em todo o sistema

#### 2. Atualização do `src/config/config.py`

- Removida a implementação simplificada do RedisManager
- Adicionada importação do RedisManager robusto
- Adicionadas funções utilitárias para trabalhar com o RedisManager

#### 3. Adaptação do `src/core/knowledge_manager.py` e `src/core/mcp_tool_discovery.py`

- Modificado para usar o RedisManager robusto com particionamento por tenant
- Atualizado para usar os tipos de dados definidos em DataType
- Mantida a compatibilidade com o cache local
- Implementados TTLs específicos por tipo de conhecimento e por MCP

#### 4. Unificação dos Sistemas de Conhecimento

- Identificados dois sistemas duplicados: `knowledge_manager.py` e `knowledge_sharing.py`
- Mantido apenas o `knowledge_manager.py` que já usava o RedisManager robusto
- Removido o `knowledge_sharing.py` para evitar duplicação e confusão
- Atualizadas todas as referências nos arquivos do projeto

### Variáveis de Ambiente

As seguintes variáveis de ambiente foram introduzidas/utilizadas:

- `REDIS_CREW_HOST` (default: `localhost` em desenvolvimento, `redis-crew` em produção)
- `REDIS_CREW_PORT` (default: `6380`)
- `REDIS_CREW_DB` (default: `0`)
- `REDIS_CREW_PASSWORD` (opcional)
- `REDIS_CREW_PREFIX` (default: `mcp-crew`)
- `REDIS_CREW_POOL_SIZE` (default: `10`)
- `REDIS_CIRCUIT_BREAKER_THRESHOLD` (default: `5`)
- `REDIS_CIRCUIT_BREAKER_TIMEOUT` (default: `30` segundos)

### Testes Realizados

Foram implementados testes para verificar:

1. Conexão com o Redis
2. Operações básicas (set/get/delete/exists)
3. Isolamento multi-tenant
4. Fallback para cache local

Todos os testes foram executados com sucesso, confirmando que o RedisManager está funcionando corretamente.

### Benefícios Obtidos

- **Resiliência**: O sistema agora tem fallback para cache local quando o Redis não está disponível
- **Monitoramento**: Estatísticas aprimoradas para monitorar o uso do Redis
- **Isolamento Multi-tenant**: Garantido através do particionamento por account_id
- **Performance**: Cache local para reduzir latência e proteger contra falhas do Redis
- **Manutenibilidade**: Código mais limpo e consistente com uma única implementação

## Próximos Passos

### Curto Prazo

1. **Sistema de Eventos**: Implementar um sistema de eventos usando Redis Streams para comunicação assíncrona entre componentes
   - Criar classes `Event`, `EventType` e `EventPriority`
   - Implementar métodos para publicar e assinar eventos
   - Configurar TTLs específicos para diferentes tipos de eventos

2. **Cache de Embeddings**: Implementar um sistema para armazenar embeddings de documentos e consultas
   - Criar métodos para armazenar e recuperar vetores de embedding
   - Configurar TTLs específicos para diferentes tipos de embeddings
   - Otimizar o armazenamento de grandes vetores no Redis

3. **Gerenciamento de Sessão**: Implementar um sistema para manter o estado da sessão do usuário
   - Criar métodos para armazenar e recuperar dados de sessão
   - Configurar TTLs curtos para dados de sessão
   - Implementar limpeza automática de sessões expiradas

4. **Filas de Tarefas**: Implementar um sistema de filas para processamento assíncrono de tarefas
   - Criar métodos para enfileirar e processar tarefas
   - Implementar prioridades e retry de tarefas
   - Configurar workers para processamento distribuído

5. **Rate Limiting**: Implementar um sistema para limitar o número de requisições por tenant
   - Criar métodos para verificar e incrementar contadores de requisições
   - Configurar limites específicos por tipo de operação
   - Implementar expiração automática de contadores

### Médio Prazo

1. **Monitoramento**: Implementar monitoramento e alertas baseados nas métricas do RedisManager (hit ratio, latência, estado do circuit breaker)

2. **Testes de Resiliência**: Testar o comportamento do sistema em cenários de indisponibilidade do Redis para validar o fallback e o circuit breaker

3. **Documentação**: Documentar padrões de uso do Redis, políticas de TTL e estrutura de chaves multi-tenant para referência dos desenvolvedores

4. **Otimização de Cache**: Analisar e otimizar o uso de cache com base em métricas de hit/miss

5. **Segurança**: Revisar e implementar melhores práticas de segurança para o Redis (controle de acesso, gerenciamento de credenciais)

### Longo Prazo

1. **Integração MCP-Redis**: Planejar a integração com MCP-Redis quando ferramentas específicas para agentes forem necessárias
2. **Escalabilidade**: Avaliar a necessidade de sharding ou clustering do Redis para suportar maior escala
3. **Migração de Dados**: Desenvolver estratégias para migração de dados entre versões do sistema

## Conclusão

A unificação do RedisManager representa um passo importante na evolução do MCP-Crew v2, melhorando a confiabilidade, manutenibilidade e desempenho do sistema. O uso consistente do Redis CREW para cache interno, com isolamento multi-tenant e mecanismos de resiliência, proporciona uma base sólida para o crescimento contínuo do sistema.
