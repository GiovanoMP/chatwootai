# Guia Resumido de Implementações Redis no MCP-Crew v2

## Componentes Implementados

### 1. RedisManager (Base)
- **Função**: Gerencia todas as interações com Redis
- **Como usar**: `from src.redis_manager.redis_manager import redis_manager, DataType`
- **Configuração**: Via variáveis de ambiente (REDIS_CREW_HOST, REDIS_CREW_PORT, etc.)

### 2. Sistema de Eventos (`event_system.py`)
- **Função**: Comunicação assíncrona entre componentes via Redis Streams
- **Como usar**:
```python
# Publicar evento
event_mgr = EventManager(tenant_id="account123")
event = Event(EventType.SYSTEM, {"message": "teste"})
event_mgr.publish(event, "stream_name")

# Assinar eventos
def callback(event):
    print(f"Evento recebido: {event.data}")
event_mgr.subscribe("stream_name", callback)
```
- **Dicas**: Sempre converta dicionários para JSON antes de publicar

### 3. Cache de Embeddings (`embedding_cache.py`)
- **Função**: Armazena vetores de embedding para evitar recálculos
- **Como usar**:
```python
cache = EmbeddingCache(tenant_id="account123")
cache.store("texto_exemplo", [0.1, 0.2, 0.3])
vector = cache.retrieve("texto_exemplo")
```
- **Dicas**: Use batch_store/batch_retrieve para operações em lote

### 4. Gerenciamento de Sessão (`session_manager.py`)
- **Função**: Mantém dados de sessão de usuários
- **Como usar**:
```python
session_mgr = SessionManager(tenant_id="account123")
session_id = session_mgr.create_session("user123", {"preferences": {"theme": "dark"}})
session = session_mgr.get_session(session_id)
session_mgr.cleanup_expired_sessions()
```
- **Dicas**: Configure TTL apropriado baseado na importância da sessão

### 5. Filas de Tarefas (`task_queue.py`)
- **Função**: Processamento assíncrono de tarefas com prioridades
- **Como usar**:
```python
queue = TaskQueue(tenant_id="account123", queue_name="default")
task_id = queue.enqueue("process_data", {"user_id": "123"}, priority=TaskPriority.HIGH)
queue.start_worker(task_handler_function)
```
- **Dicas**: Use prioridades para tarefas críticas e configure retry para resiliência

### 6. Rate Limiting (`rate_limiter.py`)
- **Função**: Controla frequência de requisições por tenant
- **Como usar**:
```python
limiter = RateLimiter(tenant_id="account123")
allowed = limiter.check_limit("api_calls", max_requests=100, window_seconds=60)
if allowed:
    # processar requisição
```
- **Dicas**: Configure janelas e limites apropriados por tipo de operação

## Integração com o Sistema

- Todos os componentes usam o RedisManager global para isolamento multi-tenant
- Configuração centralizada via DataType para TTLs específicos
- Suporte automático para circuit breaker e fallback local

## Adaptação e Extensão

- Para adicionar novos tipos de eventos: Expanda o enum EventType
- Para novas prioridades: Adicione ao enum apropriado (EventPriority, TaskPriority)
- Para novos tipos de dados: Adicione ao enum DataType com TTL apropriado

## Considerações de Desempenho

- Use batch operations quando possível
- Configure TTLs apropriados para cada tipo de dado
- Monitore o uso de memória do Redis
