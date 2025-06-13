# Componentes Redis MCP-Crew v2

Este documento descreve os componentes Redis implementados no sistema MCP-Crew v2.

## Visão Geral

Todos os componentes utilizam o `RedisManager` existente, aproveitando suas funcionalidades:
- Isolamento multi-tenant
- Circuit breaker para resiliência
- Fallback para cache local
- TTLs configuráveis por tipo de dado

## Componentes Implementados

### 1. Sistema de Eventos (`event_system.py`)

**Propósito**: Comunicação assíncrona entre componentes do sistema.

**Funcionalidades**:
- Publicação de eventos em streams Redis
- Assinatura de eventos com callbacks
- Processamento em background
- Priorização de eventos

**Benefícios**:
- Desacoplamento entre componentes
- Comunicação assíncrona
- Registro de eventos para auditoria

### 2. Cache de Embeddings (`embedding_cache.py`)

**Propósito**: Armazenar e recuperar vetores de embedding para evitar recálculos.

**Funcionalidades**:
- Armazenamento de embeddings com hash do texto original
- Operações em lote para eficiência
- Limpeza de embeddings por padrão

**Benefícios**:
- Redução de carga em modelos de IA
- Menor latência em operações semânticas
- Economia de recursos computacionais

### 3. Gerenciamento de Sessão (`session_manager.py`)

**Propósito**: Manter estado de sessões de usuário.

**Funcionalidades**:
- Criação e recuperação de sessões
- Atualização de dados de sessão
- Listagem de sessões por usuário
- Limpeza automática de sessões expiradas

**Benefícios**:
- Persistência de estado entre requisições
- Controle de acesso simplificado
- Gerenciamento eficiente de recursos

### 4. Filas de Tarefas (`task_queue.py`)

**Propósito**: Processamento assíncrono de tarefas.

**Funcionalidades**:
- Enfileiramento de tarefas com prioridades
- Workers em background para processamento
- Retry automático em caso de falhas
- Armazenamento de resultados

**Benefícios**:
- Processamento assíncrono de operações demoradas
- Balanceamento de carga
- Resiliência a falhas temporárias

### 5. Rate Limiting (`rate_limiter.py`)

**Propósito**: Controlar frequência de requisições por tenant.

**Funcionalidades**:
- Verificação de limites por operação
- Contadores genéricos com TTL
- Janelas de tempo configuráveis

**Benefícios**:
- Proteção contra sobrecarga
- Uso justo de recursos entre tenants
- Prevenção de abusos

## Adaptabilidade

Os componentes foram projetados para serem adaptáveis a mudanças:

- **Configuração**: TTLs, limites e intervalos são parametrizáveis
- **Extensibilidade**: Enums de tipos e prioridades podem ser expandidos
- **Callbacks**: Handlers personalizáveis para eventos e tarefas
- **Isolamento**: Separação por tenant para configurações específicas

## Testes

Cada componente possui um arquivo de teste correspondente:
- `test_event_system.py`
- `test_embedding_cache.py`
- `test_session_manager.py`
- `test_task_queue.py`
- `test_rate_limiter.py`

Os testes validam as funcionalidades básicas e comportamentos esperados de cada componente.
