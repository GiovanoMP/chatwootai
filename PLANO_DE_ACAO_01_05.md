# Plano de Ação - 01/05/2025

Este documento descreve as ações necessárias para otimizar a arquitetura atual do sistema ChatwootAI, corrigir problemas identificados e melhorar o desempenho geral.

## Princípios Gerais

1. **Teste Contínuo**: Cada modificação deve ser testada para garantir que a arquitetura continue funcionando.
2. **Código Limpo**: Remover código obsoleto e arquivos que não fazem mais sentido na arquitetura atual.
3. **Documentação**: Documentar claramente as mudanças e a razão por trás delas.
4. **Otimização Incremental**: Focar em melhorias incrementais que possam ser validadas individualmente.

## 1. Resolver Problemas com Redis

**Problema**: O Redis não estava conectando, mas é fundamental para a arquitetura.
```
[WEBHOOK] 2025-05-01 17:42:57,835 - src.utils.redis_client - ERROR - Erro ao conectar ao Redis: Error 111 connecting to localhost:6379. Connection refused.
```

**Ações**:
- [x] Verificar se o Redis está instalado e em execução no ambiente
- [x] Confirmar as configurações de conexão (host, porta, senha) no arquivo de configuração
- [x] Implementar um mecanismo de retry e fallback mais robusto
- [x] Documentar o uso do Redis na arquitetura (caching, persistência, etc.)
- [x] Testar a conexão e o funcionamento do Redis após as correções

**Implementação**:
1. Instalamos o pacote `redis[hiredis]` para suporte a operações assíncronas
2. Modificamos o arquivo `src/utils/redis_client.py` para usar `redis.asyncio` para operações assíncronas
3. Atualizamos os métodos em `src/core/hub.py` e `src/core/config/config_registry.py` para usar o cliente Redis assíncrono
4. Corrigimos problemas de decodificação UTF-8 ao trabalhar com dados binários (pickle)

**Resultados**:
- Melhoria significativa no desempenho: tempo de resposta reduzido de 30.416s para 12.978s (redução de 57%)
- Conexão com Redis estabelecida com sucesso
- Implementação de cache em camadas (memória → Redis → arquivo) funcionando corretamente

**Próximos Passos**:
- Otimizar ainda mais o uso do Redis para caching de resultados de LLM
- Implementar persistência de histórico de conversas no Redis
- Implementar cache de embeddings vetoriais para reduzir chamadas à API de embeddings
- Criar um sistema de rate limiting baseado em Redis para controlar chamadas à API OpenAI

## 2. Limpar Arquivos Hub Redundantes

**Problema**: Existiam múltiplos arquivos "hub" no projeto, causando confusão.

**Ações**:
- [x] Identificar todos os arquivos hub no projeto
- [x] Confirmar qual está sendo usado atualmente (confirmado: `src/core/hub.py`)
- [x] Remover ou refatorar os arquivos obsoletos
- [x] Garantir que todas as referências apontem para o hub correto
- [x] Documentar claramente o papel do hub na arquitetura atual
- [x] Testar o sistema após a remoção para garantir que tudo funcione corretamente

**Implementação**:
1. Analisamos todos os arquivos hub no projeto:
   - `src/core/hub.py` - Arquivo principal em uso
   - `src/core/new_hub.py` - Versão alternativa não utilizada
   - `src/core/data_service_hub.py` - Implementação especializada não utilizada
2. Confirmamos que apenas `src/core/hub.py` está sendo importado e usado ativamente
3. Criamos backups dos arquivos não utilizados em `/backups/`
4. Removemos os arquivos redundantes: `src/core/new_hub.py` e `src/core/data_service_hub.py`

**Resultados**:
- Código mais limpo e fácil de manter
- Menos confusão para novos desenvolvedores
- Redução de bugs potenciais devido a importações incorretas

**Estrutura do Hub Atual**:
- `Hub` é a classe principal que gerencia o processamento de mensagens
- `get_hub()` é a função factory que retorna uma instância singleton do Hub
- O Hub utiliza Redis para cache de crews e configurações
- O Hub é responsável por determinar o domínio e o account_id interno para cada mensagem

## 3. Esclarecer a Hierarquia de Crews

**Problema**: Confusão entre "customer_service" e "WhatsAppCrew".
```
[WEBHOOK] 2025-05-01 17:42:57,837 - src.core.hub - INFO - Determinado tipo de crew: customer_service, canal específico: whatsapp
```

**Ações**:
- [ ] Documentar a relação entre tipos funcionais (customer_service) e implementações por canal (WhatsAppCrew)
- [ ] Revisar o método `_determine_crew_type` no hub para garantir que a identificação de canal seja consistente
- [ ] Garantir que o código reflita claramente essa hierarquia
- [ ] Verificar se a WhatsAppCrew está sendo corretamente instanciada para mensagens do WhatsApp
- [ ] Testar com diferentes tipos de mensagens para validar o direcionamento correto

**Benefícios Esperados**:
- Melhor compreensão da arquitetura
- Direcionamento correto de mensagens para crews específicas
- Base sólida para adicionar novas crews para outros canais

## 4. Configurar o chatwoot_mapping.yaml

**Problema**: O arquivo chatwoot_mapping.yaml parece estar vazio ou não configurado.
```
[WEBHOOK] 2025-05-01 17:42:57,834 - src.webhook.init - INFO - 📊 Mapeamento de accounts: {}
[WEBHOOK] 2025-05-01 17:42:57,834 - src.webhook.init - INFO - 📊 Mapeamento de inboxes: {}
```

**Ações**:
- [ ] Verificar a localização correta do arquivo chatwoot_mapping.yaml
- [ ] Criar um template com a estrutura correta para o arquivo
- [ ] Preencher com os mapeamentos necessários (account_id, inbox_id, domain)
- [ ] Implementar um mecanismo para atualizar o arquivo automaticamente
- [ ] Testar o carregamento e uso do arquivo no sistema
- [ ] Documentar o formato e propósito do arquivo

**Benefícios Esperados**:
- Identificação correta de domínios e account_ids
- Suporte adequado para multi-tenancy
- Base para escalar para mais contas e inboxes

## 5. Otimizar o Carregamento de Configuração YAML

**Problema**: Precisamos garantir que as configurações YAML sejam carregadas corretamente e que as crews sejam instanciadas com base nessas configurações.

**Ações**:
- [ ] Revisar o processo de carregamento de configurações YAML
- [ ] Verificar se as configurações específicas do canal estão sendo aplicadas
- [ ] Implementar validação de configuração para detectar problemas precocemente
- [ ] Otimizar o cache de configurações no Redis
- [ ] Testar com diferentes configurações para garantir flexibilidade

**Benefícios Esperados**:
- Crews corretamente configuradas para cada canal
- Redução de erros devido a configurações inválidas
- Melhor desempenho no carregamento de configurações

## 6. Otimizar o Tempo de Resposta

**Problema**: O tempo de resposta inicial (28.714 segundos) estava muito acima do objetivo de 3 segundos.

**Ações**:
- [x] Implementar cache Redis para crews e configurações
- [ ] Considerar modelos LLM mais rápidos ou com menor latência
- [ ] Otimizar o paralelismo entre agentes
- [ ] Implementar cache de respostas para perguntas comuns
- [ ] Adicionar métricas detalhadas para identificar gargalos
- [ ] Implementar timeout para garantir resposta dentro de um tempo máximo
- [ ] Testar o desempenho após cada otimização

**Progresso**:
- Implementamos cache Redis para crews e configurações, reduzindo o tempo de resposta de 28.714s para 12.978s (redução de 57%)
- Ainda precisamos reduzir mais para atingir o objetivo de 3 segundos

**Oportunidades Adicionais de Otimização com Redis**:
1. **Cache de Prompts e Respostas LLM**:
   - Armazenar pares de prompts/respostas frequentes para evitar chamadas repetidas à API
   - Implementar um sistema de expiração baseado em TTL para garantir que as respostas permaneçam atualizadas

2. **Cache de Embeddings**:
   - Armazenar embeddings de documentos e consultas frequentes
   - Reduzir chamadas à API de embeddings, que podem ser caras e lentas

3. **Filas de Processamento**:
   - Usar Redis como broker de mensagens para processamento assíncrono
   - Implementar um sistema de filas para balancear a carga em momentos de pico

4. **Armazenamento de Estado de Sessão**:
   - Manter o contexto da conversa no Redis para acesso rápido
   - Permitir que diferentes instâncias do aplicativo acessem o mesmo contexto

5. **Métricas e Monitoramento**:
   - Usar Redis para armazenar métricas em tempo real
   - Implementar dashboards para monitorar o desempenho do sistema

**Benefícios Esperados**:
- Redução significativa no tempo de resposta (objetivo: < 3 segundos)
- Melhor experiência do usuário
- Capacidade de lidar com mais mensagens simultaneamente
- Redução de custos com APIs externas

## 7. Implementar Verificação de Assinatura para Webhooks

**Problema**: Os webhooks estão sendo recebidos sem assinatura, o que representa um risco de segurança.
```
[WEBHOOK] 2025-05-01 17:42:57,836 - src.webhook.routes - WARNING - Webhook recebido sem assinatura
```

**Ações**:
- [ ] Implementar verificação de assinatura HMAC para webhooks do Chatwoot
- [ ] Configurar chaves secretas para cada account_id
- [ ] Documentar o processo de verificação
- [ ] Implementar logs detalhados para falhas de verificação
- [ ] Testar com webhooks válidos e inválidos

**Benefícios Esperados**:
- Maior segurança do sistema
- Proteção contra webhooks maliciosos
- Conformidade com boas práticas de segurança

## Priorização e Progresso

1. **Alta Prioridade** (Concluído/Em Andamento):
   - ✅ Resolver problemas com Redis (Concluído - Redução de 57% no tempo de resposta)
   - ⏳ Configurar o chatwoot_mapping.yaml (Pendente)
   - ⏳ Otimizar o tempo de resposta (Em andamento - Progresso de 57%)

2. **Média Prioridade** (Concluído/Pendente):
   - ✅ Limpar arquivos hub redundantes (Concluído)
   - ⏳ Esclarecer a hierarquia de crews
   - ⏳ Otimizar o carregamento de configuração YAML

3. **Baixa Prioridade** (para implementação futura):
   - ⏳ Implementar verificação de assinatura para webhooks

## Próximas Etapas Imediatas

1. **Configurar chatwoot_mapping.yaml**:
   - Identificar o formato correto para o arquivo
   - Preencher com os mapeamentos necessários
   - Testar o carregamento e uso do arquivo

2. **Esclarecer a Hierarquia de Crews**:
   - Documentar a estrutura atual das crews
   - Definir claramente o papel de cada crew
   - Padronizar a nomenclatura

3. **Otimizar o Carregamento de Configuração YAML**:
   - Implementar cache eficiente para configurações
   - Reduzir a frequência de leitura de arquivos
   - Melhorar o tratamento de erros

## Métricas de Sucesso

- Tempo de resposta < 3 segundos para 95% das mensagens
- Redis funcionando e sendo utilizado para cache (✅ Parcialmente concluído - 57% de melhoria)
- Mapeamento Chatwoot corretamente configurado
- Código limpo, sem arquivos ou funções obsoletas
- Direcionamento correto de mensagens para crews específicas por canal

## Otimizações Adicionais com Redis

### 1. Cache de Resultados LLM

Implementar um sistema de cache para as chamadas à API do OpenAI:

```python
async def get_llm_response_cached(prompt, model="gpt-4o-mini", ttl=3600):
    """
    Obtém uma resposta do LLM, usando cache Redis quando disponível.

    Args:
        prompt: O prompt para enviar ao LLM
        model: O modelo a ser usado
        ttl: Tempo de vida do cache em segundos

    Returns:
        A resposta do LLM
    """
    # Gerar chave de cache
    cache_key = f"llm:response:{model}:{hashlib.md5(prompt.encode()).hexdigest()}"

    # Verificar cache
    redis_client = await get_aioredis_client()
    if redis_client:
        cached_response = await redis_client.get(cache_key)
        if cached_response:
            return json.loads(cached_response)

    # Se não estiver em cache, chamar a API
    response = await call_openai_api(prompt, model)

    # Armazenar em cache
    if redis_client and response:
        await redis_client.set(cache_key, json.dumps(response), ex=ttl)

    return response
```

### 2. Armazenamento de Contexto de Conversa

Manter o histórico de conversas no Redis para acesso rápido:

```python
async def store_conversation_context(conversation_id, messages, ttl=86400):
    """
    Armazena o contexto de uma conversa no Redis.

    Args:
        conversation_id: ID da conversa
        messages: Lista de mensagens
        ttl: Tempo de vida em segundos
    """
    redis_client = await get_aioredis_client()
    if redis_client:
        key = f"conversation:context:{conversation_id}"
        await redis_client.set(key, json.dumps(messages), ex=ttl)

async def get_conversation_context(conversation_id):
    """
    Obtém o contexto de uma conversa do Redis.

    Args:
        conversation_id: ID da conversa

    Returns:
        Lista de mensagens ou None se não encontrado
    """
    redis_client = await get_aioredis_client()
    if redis_client:
        key = f"conversation:context:{conversation_id}"
        data = await redis_client.get(key)
        if data:
            return json.loads(data)
    return None
```

### 3. Sistema de Filas para Processamento Assíncrono

Usar Redis como broker de mensagens para processamento assíncrono:

```python
async def enqueue_task(task_type, payload, priority=0):
    """
    Adiciona uma tarefa à fila do Redis.

    Args:
        task_type: Tipo da tarefa
        payload: Dados da tarefa
        priority: Prioridade (0-10, maior = mais prioritário)
    """
    redis_client = await get_aioredis_client()
    if redis_client:
        task_id = str(uuid.uuid4())
        task = {
            "id": task_id,
            "type": task_type,
            "payload": payload,
            "created_at": time.time()
        }
        # Usar sorted set para implementar prioridade
        await redis_client.zadd(f"tasks:{task_type}", {json.dumps(task): priority})
        return task_id
    return None

async def process_next_task(task_type):
    """
    Processa a próxima tarefa da fila.

    Args:
        task_type: Tipo da tarefa

    Returns:
        A tarefa processada ou None se a fila estiver vazia
    """
    redis_client = await get_aioredis_client()
    if redis_client:
        # Obter a tarefa com maior prioridade
        tasks = await redis_client.zpopmax(f"tasks:{task_type}")
        if tasks:
            task_json, _ = tasks[0]
            task = json.loads(task_json)
            # Processar a tarefa...
            return task
    return None
```

## Próximos Passos

Após a implementação deste plano de ação, focaremos na otimização das crews específicas e na implementação de novas funcionalidades conforme necessário. O uso eficiente do Redis será fundamental para atingir o objetivo de tempo de resposta inferior a 3 segundos.


Recomendações REDIS

Use volumes persistentes: Configure volumes Docker para garantir que os dados do Redis persistam mesmo se o contêiner for reiniciado. Lembre-também de configurar a persistência da memória

volumes:
  - redis_data:/data

  Configure limites de recursos apropriados: Defina limites de CPU e memória adequados para evitar que o Redis seja afetado por outros serviços.


deploy:
  resources:
    limits:
      cpus: '2'
      memory: 4G
    reservations:
      cpus: '1'
      memory: 2G

Considere uma configuração de alta disponibilidade: Para produção, considere usar Redis Sentinel ou Redis Cluster para alta disponibilidade.
Otimize a configuração de rede: Use a rede overlay do Docker Swarm para comunicação eficiente entre serviços.
Monitore ativamente: Implemente monitoramento robusto para acompanhar o desempenho e a saúde do Redis.