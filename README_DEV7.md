# Implementação de Crews Especializadas - Guia de Referência

Este documento detalha a arquitetura e implementação de crews especializadas no sistema ChatwootAI, começando pela WhatsApp Crew. Serve como referência para o desenvolvimento atual e futuras crews, alinhado com a nova arquitetura do sistema.

## 1. Visão Geral da Arquitetura

A arquitetura de crews especializadas segue o padrão CrewAI com adaptações para nosso sistema multi-tenant, focando em crews específicas por canal:

```
src/
└── core/
    ├── config/
    │   ├── config_registry.py
    │   └── config_loader.py
    ├── crews/
    │   ├── base_crew.py
    │   ├── crew_factory.py
    │   └── channels/
    │       ├── whatsapp_crew/
    │       │   ├── agents/
    │       │   │   ├── __init__.py
    │       │   │   ├── intention_agent.py
    │       │   │   ├── business_rules_agent.py
    │       │   │   ├── scheduling_rules_agent.py
    │       │   │   ├── support_documents_agent.py
    │       │   │   ├── product_info_agent.py
    │       │   │   ├── delivery_rules_agent.py
    │       │   │   ├── mcp_agent.py
    │       │   │   └── response_agent.py
    │       │   ├── tools/
    │       │   │   ├── __init__.py
    │       │   │   ├── qdrant_base_tool.py
    │       │   │   ├── business_rules_tool.py
    │       │   │   ├── scheduling_rules_tool.py
    │       │   │   ├── support_documents_tool.py
    │       │   │   ├── product_info_tool.py
    │       │   │   ├── delivery_rules_tool.py
    │       │   │   ├── mcp_odoo_tool.py
    │       │   │   └── redis_cache_tool.py
    │       │   ├── __init__.py
    │       │   └── whatsapp_crew.py
    │       ├── instagram_crew/
    │       └── default_crew/
    ├── hub.py
    └── cache/
        └── redis_cache.py
```

### 1.1. Fluxo de Processamento

```
[Chatwoot Webhook] ---> [WebhookHandler] ---> [Hub] ---> [CrewFactory] ---> [WhatsApp Crew]
                                                                                |--> [Intent Agent]
                                                                                |--> [Business Rules Agent]
                                                                                |--> [Scheduling Rules Agent]
                                                                                |--> [Support Docs Agent]
                                                                                |--> [Product Info Agent]
                                                                                |--> [Delivery Rules Agent]
                                                                                |--> [MCP Executor Agent]
                                                                                ---> [Response Aggregator] ---> [Resposta ao cliente]
```

### 1.2. Estratégia de Delegação e Processamento Paralelo

1. O Intention Identifier sempre é o primeiro a executar
2. Dependendo da intenção detectada, as tarefas são delegadas aos agentes relevantes em paralelo
3. Os agentes especializados executam suas tarefas simultaneamente, reduzindo o tempo total de processamento
4. O Response Aggregator finaliza o atendimento com base nos resultados dos outros agentes

### 1.3. Integração com o Sistema

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────────────┐
│   Chatwoot  │────▶│  Webhook    │────▶│    Hub      │────▶│   CrewFactory      │
│             │     │  Handler    │     │             │     │                     │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────┬───────────┘
                           │                   │                       │
                           │                   │                       ▼
                           ▼                   ▼             ┌─────────────────────┐
                    ┌─────────────┐     ┌─────────────┐     │  Canal-Specific     │
                    │  Config     │     │   Redis     │     │  Crews              │
                    │  Registry   │     │   Cache     │     │                     │
                    └─────────────┘     └─────────────┘     └─────────┬───────────┘
                                                                      │
                                                                      │
                                                                      ▼
                                                            ┌─────────────────────┐
                                                            │     MCP / Odoo      │
                                                            │     Integration     │
                                                            └─────────────────────┘
```

## 2. Configuração via YAML

### 2.1. Estrutura do YAML

Mantemos a estrutura atual dos arquivos YAML em `config/domains/[domain]/[account_id]/config.yaml`, mas adicionamos uma nova seção `enabled_collections`:

```yaml
account_id: account_1
company_metadata:
  # ... configurações existentes
customer_service:
  # ... configurações existentes
# Nova seção para coleções habilitadas
enabled_collections:
  - business_rules
  - support_documents
  - product_info
  - delivery_rules
integrations:
  # ... configurações existentes
```

### 2.2. Adaptação do Módulo Odoo

O módulo Odoo `ai_credentials_manager` deve ser adaptado para incluir campos que permitam configurar quais coleções estão habilitadas para cada tenant:

- Adicionar campos booleanos para cada coleção possível
- Modificar o método de geração de YAML para incluir a seção `enabled_collections`
- Atualizar a interface de usuário para permitir a configuração dessas coleções

## 3. Implementação dos Agentes

### 3.1. Agentes Especializados

| Agente | Descrição | Coleção Qdrant |
|--------|-----------|----------------|
| intention_identifier_agent | Identifica a intenção do cliente | N/A |
| business_rules_agent | Consulta regras de negócio | business_rules |
| scheduling_rules_agent | Consulta regras de agendamento | scheduling_rules |
| support_documents_agent | Busca documentos de suporte | support_documents |
| product_info_agent | Consulta produtos e preços | product_info |
| delivery_rules_agent | Consulta regras de entrega | delivery_rules |
| mcp_executor_agent | Executa ações no Odoo | N/A |
| response_aggregator_agent | Gera resposta final | N/A |

### 3.2. Criação Dinâmica de Agentes

Os agentes são criados dinamicamente com base nas coleções habilitadas no YAML:

```python
def _initialize_agents(self) -> Dict[str, Agent]:
    agents = {}

    # Agente de intenção (sempre presente)
    agents["intention"] = create_intention_agent(self.config)

    # Agentes de coleções vetoriais (criados apenas se a coleção estiver habilitada)
    if "business_rules" in self.enabled_collections:
        agents["business_rules"] = create_business_rules_agent(
            self.config,
            tools=[self.tools["business_rules"], self.tools["redis_cache"]]
        )

    # ... outros agentes

    return agents
```

## 4. Ferramentas Especializadas (Tools)

### 4.1. Ferramenta Base para Qdrant

```python
class QdrantBaseTool(BaseTool):
    def __init__(self, collection_name: str, account_id: str):
        self.collection_name = f"{collection_name}_{account_id}"
        self.account_id = account_id
        self.client = QdrantClient(host="localhost", port=6333)

        super().__init__(
            name=f"{collection_name}_lookup",
            description=f"Consulta informações na coleção {collection_name}"
        )

    def _search(self, query: str, limit: int = 5, filter_conditions: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        # Implementação da busca vetorial
        # ...
```

### 4.2. Ferramentas Específicas

Cada coleção tem sua própria ferramenta especializada:

```python
class BusinessRulesQdrantTool(QdrantBaseTool):
    def __init__(self, account_id: str):
        super().__init__(
            collection_name="business_rules",
            account_id=account_id,
            description="Consulta regras de negócio vetorizadas"
        )

    def _run(self, query: str, rule_type: Optional[str] = None) -> str:
        # Implementação específica para regras de negócio
        # ...
```

### 4.3. Ferramenta MCP Odoo

```python
class MCPOdooTool(BaseTool):
    def __init__(self, account_id: str, config: Dict[str, Any]):
        self.account_id = account_id
        self.config = config

        # Extrair configurações do MCP
        mcp_config = config.get("integrations", {}).get("mcp", {}).get("config", {})
        self.mcp_url = mcp_config.get("url", "http://localhost:8000")

        super().__init__(
            name="mcp_odoo",
            description="Executa operações no sistema Odoo através da camada MCP"
        )

    def _run(self, action: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        # Implementação da chamada ao MCP-Odoo
        # ...
```

### 4.4. Ferramenta Redis Cache

```python
class RedisCacheTool(BaseTool):
    def __init__(self, account_id: str):
        self.account_id = account_id
        self.prefix = f"{account_id}:"
        self.redis = redis.Redis(host="localhost", port=6379, db=0)

        super().__init__(
            name="redis_cache",
            description="Armazena e recupera dados em cache no Redis"
        )

    def _run(self, action: str, key: str, value: Optional[Union[str, Dict[str, Any]]] = None, expire: int = 3600) -> Dict[str, Any]:
        # Implementação das operações de cache
        # ...
```

## 5. Processamento Paralelo e Técnicas Avançadas

### 5.1. Configuração das Tarefas com Dependências

As tarefas são configuradas para execução paralela utilizando o padrão `depends_on` para definir dependências entre tarefas:

```python
def _initialize_tasks(self) -> Dict[str, Task]:
    tasks = {}

    # Tarefa de intenção (sempre executada primeiro)
    tasks["intention"] = Task(
        description="Identifique a intenção do cliente na mensagem",
        expected_output="Classificação da intenção do cliente",
        agent=self.agents["intention"],
        async_execution=False  # Esta tarefa deve ser executada primeiro
    )

    # Tarefas de coleções vetoriais (executadas em paralelo)
    if "business_rules" in self.enabled_collections:
        tasks["business_rules"] = Task(
            description="Consulte regras de negócio relevantes",
            expected_output="Regras de negócio aplicáveis",
            agent=self.agents["business_rules"],
            async_execution=True,  # Execução paralela
            depends_on=[tasks["intention"]]  # Usa depends_on em vez de context
        )

    # ... outras tarefas

    return tasks
```

### 5.2. Configuração da Crew com Processamento Assíncrono

A crew é configurada para processamento paralelo utilizando padrões assíncronos:

```python
async def _initialize_crew(self) -> Crew:
    # Obter lista de agentes e tarefas
    agent_list = list(self.agents.values())
    task_list = list(self.tasks.values())

    # Criar a crew com processamento paralelo
    crew = Crew(
        agents=agent_list,
        tasks=task_list,
        process=Process.parallel,  # Processamento paralelo
        verbose=True,
        memory=True,  # Habilitar memória compartilhada
        cache=self.redis_client  # Usar Redis para cache
    )

    return crew
```

### 5.3. Implementação de Timeout e Fallback

Implementamos timeout para tarefas longas e mecanismos de fallback para garantir respostas rápidas:

```python
async def execute_task_with_timeout(self, task_name: str, inputs: Dict[str, Any], timeout: int = 10) -> Dict[str, Any]:
    """Executa uma tarefa com timeout e fallback."""
    try:
        # Tentar executar a tarefa com timeout
        result = await asyncio.wait_for(
            self.tasks[task_name].execute(inputs),
            timeout=timeout
        )
        return result
    except asyncio.TimeoutError:
        logger.warning(f"Timeout ao executar tarefa {task_name}, usando fallback")
        # Implementar lógica de fallback
        return self._task_fallback(task_name, inputs)
    except Exception as e:
        logger.error(f"Erro ao executar tarefa {task_name}: {str(e)}")
        return self._task_fallback(task_name, inputs)

def _task_fallback(self, task_name: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Implementa fallback para tarefas que falharam ou atingiram timeout."""
    # Fallbacks específicos por tipo de tarefa
    if task_name == "business_rules":
        return {"result": "Não foi possível consultar as regras de negócio no momento."}
    elif task_name == "product_info":
        return {"result": "Informações sobre produtos não disponíveis no momento."}
    # Fallback genérico
    return {"result": "Não foi possível completar esta parte da tarefa."}
```

### 5.4. Pré-processamento de Mensagens com Redis

Implementamos pré-processamento de mensagens utilizando Redis para armazenar contexto:

```python
async def preprocess_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
    """Pré-processa a mensagem antes de enviá-la para a crew."""
    # Extrair informações básicas
    conversation_id = message.get("conversation_id")
    sender_id = message.get("sender_id")
    content = message.get("content", "")

    # Chave para o contexto da conversa
    context_key = f"{self.account_id}:conversation:{conversation_id}:context"

    # Verificar se já temos contexto para esta conversa
    context = await self.redis_client.get(context_key)
    if context:
        context = json.loads(context)
    else:
        context = {"history": [], "metadata": {}}

    # Atualizar histórico
    context["history"].append({
        "role": "user",
        "content": content,
        "timestamp": time.time()
    })

    # Limitar tamanho do histórico
    if len(context["history"]) > 10:
        context["history"] = context["history"][-10:]

    # Salvar contexto atualizado
    await self.redis_client.set(context_key, json.dumps(context), ex=3600)  # 1 hora

    # Adicionar contexto à mensagem
    message["context"] = context

    return message
```

### 5.5. Integração com OpenTelemetry para Métricas

Implementamos integração com OpenTelemetry para monitoramento de performance:

```python
from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import ConsoleMetricExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource

# Configurar provedor de métricas
resource = Resource(attributes={SERVICE_NAME: "whatsapp-crew"})
metric_provider = MeterProvider(resource=resource)
metrics.set_meter_provider(metric_provider)
meter = metrics.get_meter("whatsapp_crew_metrics")

# Criar métricas
task_duration = meter.create_histogram(
    name="task_duration",
    description="Duração da execução de tarefas",
    unit="s",
)

crew_duration = meter.create_histogram(
    name="crew_duration",
    description="Duração total da execução da crew",
    unit="s",
)

# Exemplo de uso
async def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
    start_time = time.time()

    # Processar mensagem
    result = await self._process_message_internal(message)

    # Registrar duração
    duration = time.time() - start_time
    crew_duration.record(duration, {"account_id": self.account_id, "domain": self.domain_name})

    return result
```

## 6. Uso Avançado do Redis

### 6.1. Memória Compartilhada

O Redis é usado como memória compartilhada entre os agentes:

```python
# Exemplo de uso do Redis para compartilhar contexto entre agentes
def share_context(self, key: str, value: Any) -> None:
    """Compartilha contexto entre agentes via Redis."""
    prefixed_key = f"{self.account_id}:context:{key}"
    self.redis.set(prefixed_key, json.dumps(value), ex=3600)

def get_shared_context(self, key: str) -> Any:
    """Obtém contexto compartilhado entre agentes via Redis."""
    prefixed_key = f"{self.account_id}:context:{key}"
    value = self.redis.get(prefixed_key)
    if value:
        return json.loads(value)
    return None
```

### 6.2. Cache de Embeddings

O Redis é usado para cache de embeddings, melhorando a performance:

```python
def get_embedding(self, text: str) -> List[float]:
    """Obtém embedding para um texto, usando cache Redis."""
    # Gerar chave de cache
    cache_key = f"{self.account_id}:embedding:{hashlib.md5(text.encode()).hexdigest()}"

    # Verificar cache
    cached = self.redis.get(cache_key)
    if cached:
        return json.loads(cached)

    # Gerar embedding
    embedding = self._generate_embedding(text)

    # Armazenar em cache
    self.redis.set(cache_key, json.dumps(embedding), ex=86400)  # 24 horas

    return embedding
```

### 6.3. Histórico de Conversas

O Redis armazena o histórico de conversas para contexto:

```python
def save_conversation_history(self, conversation_id: str, message: Dict[str, Any]) -> None:
    """Salva mensagem no histórico da conversa."""
    key = f"{self.account_id}:conversation:{conversation_id}:history"

    # Obter histórico atual
    history = self.redis.lrange(key, 0, -1)
    history = [json.loads(h) for h in history]

    # Adicionar nova mensagem
    history.append(message)

    # Limitar tamanho do histórico
    if len(history) > 10:
        history = history[-10:]

    # Salvar histórico atualizado
    self.redis.delete(key)
    for msg in history:
        self.redis.rpush(key, json.dumps(msg))

    # Definir expiração
    self.redis.expire(key, 86400)  # 24 horas
```

## 7. Implementação da WhatsApp Crew

### 7.1. Método `process_message` com Assincronicidade

```python
async def process_message(self, message: Dict[str, Any], conversation_id: str = None, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Processa uma mensagem do WhatsApp de forma assíncrona.

    Args:
        message: Mensagem a ser processada
        conversation_id: ID da conversa
        metadata: Metadados adicionais

    Returns:
        Resultado do processamento
    """
    try:
        start_time = time.time()
        logger.info(f"Processando mensagem para {self.domain_name}/{self.account_id}")

        # Pré-processar mensagem para adicionar contexto
        processed_message = await self.preprocess_message(message)

        # Preparar input para a crew
        crew_input = {
            "message": processed_message.get("content", ""),
            "sender_id": processed_message.get("sender_id", ""),
            "conversation_id": conversation_id,
            "context": processed_message.get("context", {}),
            "metadata": metadata or {},
            "account_id": self.account_id,
            "domain_name": self.domain_name
        }

        # Executar a crew com timeout
        try:
            result = await asyncio.wait_for(
                self.crew.kickoff(inputs=crew_input),
                timeout=25  # 25 segundos de timeout máximo
            )
        except asyncio.TimeoutError:
            logger.warning(f"Timeout ao processar mensagem para {self.domain_name}/{self.account_id}")
            # Fallback para timeout
            result = "Estou processando sua solicitação, mas está demorando mais do que o esperado. Poderia reformular sua pergunta de forma mais simples?"

        # Registrar métricas de performance
        duration = time.time() - start_time
        crew_duration.record(duration, {
            "account_id": self.account_id,
            "domain": self.domain_name,
            "success": True
        })

        # Salvar resposta no histórico da conversa
        await self.save_conversation_history(conversation_id, {
            "role": "assistant",
            "content": result,
            "timestamp": time.time()
        })

        # Processar resultado
        response = {
            "content": result,
            "status": "success",
            "metadata": {
                "crew_type": "WhatsAppCrew",
                "domain_name": self.domain_name,
                "account_id": self.account_id,
                "processing_time": duration
            },
            "channel": "whatsapp",
            "routing": {
                "crew_type": "customer_service",
                "channel_type": "whatsapp",
                "domain_name": self.domain_name,
                "account_id": self.account_id
            }
        }

        return response

    except Exception as e:
        # Registrar erro nas métricas
        duration = time.time() - start_time
        crew_duration.record(duration, {
            "account_id": self.account_id,
            "domain": self.domain_name,
            "success": False
        })

        logger.error(f"Erro ao processar mensagem: {str(e)}", exc_info=True)
        return {
            "content": f"Desculpe, ocorreu um erro ao processar sua mensagem. Nossa equipe foi notificada e estamos trabalhando para resolver o problema.",
            "status": "error",
            "metadata": {
                "crew_type": "WhatsAppCrew",
                "domain_name": self.domain_name,
                "account_id": self.account_id,
                "error": str(e)
            },
            "channel": "whatsapp"
        }
```

### 7.2. Integração com o Hub

```python
# No arquivo hub.py
async def process_message(self, message: Dict[str, Any], conversation_id: str, channel_type: str, domain_name: str = None, account_id: str = None) -> Dict[str, Any]:
    """
    Processa uma mensagem através da crew apropriada.

    Args:
        message: Mensagem a ser processada
        conversation_id: ID da conversa
        channel_type: Tipo de canal (whatsapp, instagram, etc.)
        domain_name: Nome do domínio
        account_id: ID da conta

    Returns:
        Resposta processada
    """
    # Determinar domínio e account_id se não fornecidos
    if not domain_name or not account_id:
        mapping = await self.get_account_mapping(message)
        domain_name = mapping.get("domain_name")
        account_id = mapping.get("account_id")

    # Determinar o tipo de crew e canal específico
    crew_type, specific_channel = self._determine_crew_type(message, channel_type)

    # Obter a crew apropriada (do cache ou criar nova)
    crew = await self.get_crew(crew_type, domain_name, account_id, specific_channel)

    # Processar a mensagem com a crew
    return await crew.process_message(
        message=message,
        conversation_id=conversation_id,
        metadata={"channel_type": channel_type}
    )
```

## 8. Próximos Passos e Melhorias Futuras

### 8.1. Melhorias Técnicas

1. **Validação de Schema YAML**: Implementar validação de schema usando Pydantic para garantir integridade dos dados de configuração
2. **Monitoramento Avançado**: Expandir a integração com OpenTelemetry para monitoramento completo do sistema
3. **Otimização de Cache Redis**: Implementar estratégias avançadas de cache para reduzir latência
4. **Sistema de Filas com RabbitMQ**: Implementar processamento assíncrono com filas para maior escalabilidade
5. **Containerização**: Preparar a arquitetura para execução em contêineres Docker com orquestração

### 8.2. Expansão de Funcionalidades

1. **Crews para Outros Canais**: Implementar crews especializadas para Instagram, Facebook e Web
2. **Agentes Especializados Adicionais**: Desenvolver agentes para análise de sentimento, detecção de idioma e personalização
3. **Integração com Sistemas Externos**: Expandir além do Odoo para outros ERPs e CRMs
4. **Suporte a Múltiplos Idiomas**: Implementar detecção automática de idioma e respostas multilíngues
5. **Processamento de Mídia**: Adicionar suporte para análise de imagens, áudio e vídeo enviados pelos clientes

### 8.3. Melhorias de Experiência do Usuário

1. **Interface de Administração**: Criar dashboard para visualizar e gerenciar crews em tempo real
2. **Ferramentas de Diagnóstico**: Implementar ferramentas para depuração e análise de problemas
3. **Simulador de Conversas**: Criar ambiente de teste para simular interações com diferentes crews
4. **Análise de Conversas**: Implementar ferramentas para análise de qualidade das respostas
5. **Feedback Loop**: Criar mecanismos para incorporar feedback dos usuários na melhoria contínua dos agentes

## 9. Logging e Observabilidade

### 9.1. Estrutura de Logs

Implementamos logs estruturados para facilitar o diagnóstico:

```python
import logging
import json
from typing import Dict, Any

class StructuredLogger:
    """Logger estruturado para crews."""

    def __init__(self, name: str, account_id: str, domain_name: str):
        self.logger = logging.getLogger(name)
        self.account_id = account_id
        self.domain_name = domain_name

    def _format_extra(self, extra: Dict[str, Any]) -> Dict[str, Any]:
        """Formata informações extras para o log."""
        return {
            "account_id": self.account_id,
            "domain_name": self.domain_name,
            **extra
        }

    def info(self, message: str, extra: Dict[str, Any] = None):
        """Registra mensagem de informação."""
        self.logger.info(message, extra=self._format_extra(extra or {}))

    def error(self, message: str, extra: Dict[str, Any] = None):
        """Registra mensagem de erro."""
        self.logger.error(message, extra=self._format_extra(extra or {}))

    def warning(self, message: str, extra: Dict[str, Any] = None):
        """Registra mensagem de aviso."""
        self.logger.warning(message, extra=self._format_extra(extra or {}))

    def debug(self, message: str, extra: Dict[str, Any] = None):
        """Registra mensagem de debug."""
        self.logger.debug(message, extra=self._format_extra(extra or {}))
```

### 9.2. Métricas de Performance

Coletamos métricas de performance para monitorar o desempenho:

```python
class PerformanceMetrics:
    """Métricas de performance para crews."""

    def __init__(self, account_id: str, redis_client):
        self.account_id = account_id
        self.redis = redis_client
        self.prefix = f"{account_id}:metrics:"

    def record_agent_execution(self, agent_name: str, execution_time: float):
        """Registra tempo de execução de um agente."""
        key = f"{self.prefix}agent:{agent_name}:execution_time"
        self.redis.lpush(key, execution_time)
        self.redis.ltrim(key, 0, 99)  # Manter apenas os últimos 100 registros

    def record_task_execution(self, task_name: str, execution_time: float):
        """Registra tempo de execução de uma tarefa."""
        key = f"{self.prefix}task:{task_name}:execution_time"
        self.redis.lpush(key, execution_time)
        self.redis.ltrim(key, 0, 99)  # Manter apenas os últimos 100 registros

    def record_crew_execution(self, execution_time: float):
        """Registra tempo de execução total da crew."""
        key = f"{self.prefix}crew:execution_time"
        self.redis.lpush(key, execution_time)
        self.redis.ltrim(key, 0, 99)  # Manter apenas os últimos 100 registros

    def get_agent_avg_execution_time(self, agent_name: str) -> float:
        """Obtém tempo médio de execução de um agente."""
        key = f"{self.prefix}agent:{agent_name}:execution_time"
        times = self.redis.lrange(key, 0, -1)
        if not times:
            return 0
        return sum(float(t) for t in times) / len(times)

    def get_task_avg_execution_time(self, task_name: str) -> float:
        """Obtém tempo médio de execução de uma tarefa."""
        key = f"{self.prefix}task:{task_name}:execution_time"
        times = self.redis.lrange(key, 0, -1)
        if not times:
            return 0
        return sum(float(t) for t in times) / len(times)

    def get_crew_avg_execution_time(self) -> float:
        """Obtém tempo médio de execução total da crew."""
        key = f"{self.prefix}crew:execution_time"
        times = self.redis.lrange(key, 0, -1)
        if not times:
            return 0
        return sum(float(t) for t in times) / len(times)
```

## 10. Testes

### 10.1. Testes Unitários

Implementamos testes unitários para cada componente:

```python
# tests/test_whatsapp_crew.py
import unittest
from unittest.mock import MagicMock, patch
from src.core.crews.whatsapp_crew.whatsapp_crew import WhatsAppCrew

class TestWhatsAppCrew(unittest.TestCase):
    def setUp(self):
        # Mock do ConfigLoader
        self.config_loader_mock = MagicMock()
        self.config_loader_mock.load_config.return_value = {
            "account_id": "account_1",
            "enabled_collections": ["business_rules", "product_info"],
            "customer_service": {
                "communication_style": "friendly",
                "emoji_usage": "moderate",
                "greeting_message": "Olá! Como posso ajudar?"
            },
            "integrations": {
                "mcp": {
                    "config": {
                        "url": "http://localhost:8000",
                        "db": "account_1"
                    }
                }
            }
        }

        # Patch do ConfigLoader
        self.config_loader_patch = patch("src.core.crews.whatsapp_crew.whatsapp_crew.ConfigLoader")
        self.config_loader_mock_class = self.config_loader_patch.start()
        self.config_loader_mock_class.return_value = self.config_loader_mock

        # Inicializar WhatsAppCrew
        self.crew = WhatsAppCrew("retail", "account_1")

    def tearDown(self):
        self.config_loader_patch.stop()

    def test_initialize_tools(self):
        """Testa a inicialização das ferramentas."""
        tools = self.crew.tools

        # Verificar se as ferramentas esperadas foram criadas
        self.assertIn("redis_cache", tools)
        self.assertIn("business_rules", tools)
        self.assertIn("product_info", tools)
        self.assertIn("mcp_odoo", tools)

        # Verificar se as ferramentas não habilitadas não foram criadas
        self.assertNotIn("scheduling_rules", tools)
        self.assertNotIn("support_documents", tools)
        self.assertNotIn("delivery_rules", tools)

    def test_initialize_agents(self):
        """Testa a inicialização dos agentes."""
        agents = self.crew.agents

        # Verificar se os agentes esperados foram criados
        self.assertIn("intention", agents)
        self.assertIn("business_rules", agents)
        self.assertIn("product_info", agents)
        self.assertIn("mcp", agents)
        self.assertIn("response", agents)

        # Verificar se os agentes não habilitados não foram criados
        self.assertNotIn("scheduling_rules", agents)
        self.assertNotIn("support_documents", agents)
        self.assertNotIn("delivery_rules", agents)

    def test_process_message(self):
        """Testa o processamento de mensagem."""
        # Mock da crew
        self.crew.crew = MagicMock()
        self.crew.crew.kickoff.return_value = "Resposta de teste"

        # Processar mensagem
        message = {"content": "Olá, gostaria de saber sobre os produtos"}
        result = self.crew.process_message(message, "conv123")

        # Verificar resultado
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["content"], "Resposta de teste")
        self.assertEqual(result["channel"], "whatsapp")
        self.assertEqual(result["metadata"]["account_id"], "account_1")
```

### 10.2. Testes de Integração

Implementamos testes de integração para verificar o fluxo completo:

```python
# tests/integration/test_whatsapp_crew_integration.py
import asyncio
import unittest
from src.core.crews.whatsapp_crew.whatsapp_crew import WhatsAppCrew

class TestWhatsAppCrewIntegration(unittest.TestCase):
    async def setUp(self):
        # Inicializar WhatsAppCrew com configuração real
        self.crew = WhatsAppCrew("retail", "account_1")

    async def test_full_flow(self):
        """Testa o fluxo completo de processamento de mensagem."""
        # Mensagem de teste
        message = {
            "content": "Qual é a política de devolução para produtos eletrônicos?",
            "sender_id": "user123"
        }

        # Processar mensagem
        result = await self.crew.process_message(message, "conv123")

        # Verificar resultado
        self.assertEqual(result["status"], "success")
        self.assertIsNotNone(result["content"])
        self.assertEqual(result["channel"], "whatsapp")

        # Verificar se a resposta contém informações relevantes
        self.assertIn("devolução", result["content"].lower())
        self.assertIn("eletrônicos", result["content"].lower())
```

## 11. Técnicas Avançadas de Implementação CrewAI

### 11.1. Uso de `depends_on` em vez de `context`

O CrewAI oferece duas formas de definir dependências entre tarefas: `context` e `depends_on`. Recomendamos o uso de `depends_on` por ser mais explícito e oferecer melhor controle:

```python
# Forma recomendada (depends_on)
task_b = Task(
    description="Tarefa B que depende da Tarefa A",
    expected_output="Resultado da Tarefa B",
    agent=agent_b,
    depends_on=[task_a]  # Dependência explícita
)

# Forma antiga (context)
task_b = Task(
    description="Tarefa B que depende da Tarefa A",
    expected_output="Resultado da Tarefa B",
    agent=agent_b,
    context=[task_a]  # Menos explícito
)
```

### 11.2. Padrão Async/Await com Asyncio

Implementamos o padrão async/await para melhorar a performance e responsividade:

```python
async def process_tasks(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Processa múltiplas tarefas em paralelo."""
    # Criar tarefas assíncronas
    tasks = []
    for task_name in self.parallel_tasks:
        if task_name in self.tasks:
            tasks.append(self.execute_task_with_timeout(task_name, inputs))

    # Executar tarefas em paralelo
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Processar resultados
    processed_results = {}
    for task_name, result in zip(self.parallel_tasks, results):
        if isinstance(result, Exception):
            # Lidar com exceção
            processed_results[task_name] = self._task_fallback(task_name, inputs)
        else:
            processed_results[task_name] = result

    return processed_results
```

### 11.3. Tratamento de Timeout com asyncio.wait_for

Implementamos timeout para evitar que tarefas lentas bloqueiem o sistema:

```python
async def execute_task_with_timeout(self, task_name: str, inputs: Dict[str, Any], timeout: int = 10) -> Dict[str, Any]:
    """Executa uma tarefa com timeout."""
    try:
        return await asyncio.wait_for(
            self.tasks[task_name].execute(inputs),
            timeout=timeout
        )
    except asyncio.TimeoutError:
        logger.warning(f"Timeout ao executar tarefa {task_name}")
        return self._task_fallback(task_name, inputs)
```

### 11.4. Melhor Tratamento de Erros com Fallback

Implementamos estratégias de fallback para garantir resiliência:

```python
def _task_fallback(self, task_name: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Implementa fallback para tarefas que falharam."""
    # Verificar cache para resultados anteriores
    cache_key = f"{self.account_id}:fallback:{task_name}:{hash(json.dumps(inputs))}"
    cached_result = self.redis_client.get(cache_key)

    if cached_result:
        return json.loads(cached_result)

    # Fallback específico por tipo de tarefa
    if task_name == "business_rules":
        result = {"result": "Não foi possível consultar as regras de negócio no momento."}
    else:
        result = {"result": "Não foi possível completar esta parte da tarefa."}

    # Armazenar em cache para uso futuro
    self.redis_client.set(cache_key, json.dumps(result), ex=3600)

    return result
```

### 11.5. Pré-processamento de Mensagens com Contexto Redis

Implementamos pré-processamento para enriquecer as mensagens com contexto:

```python
async def preprocess_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
    """Pré-processa a mensagem antes de enviá-la para a crew."""
    # Extrair informações básicas
    conversation_id = message.get("conversation_id")

    # Obter histórico da conversa do Redis
    history_key = f"{self.account_id}:conversation:{conversation_id}:history"
    history = await self.redis_client.lrange(history_key, 0, -1)
    history = [json.loads(h) for h in history]

    # Adicionar histórico à mensagem
    message["context"] = {"history": history}

    return message
```

### 11.6. Integração com OpenTelemetry para Métricas

Implementamos métricas para monitoramento de performance:

```python
# Configurar métricas
meter = metrics.get_meter("whatsapp_crew_metrics")
task_duration = meter.create_histogram("task_duration", unit="s")
crew_duration = meter.create_histogram("crew_duration", unit="s")

# Registrar métricas
async def execute_task(self, task_name: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
    start_time = time.time()
    result = await self.tasks[task_name].execute(inputs)
    duration = time.time() - start_time

    # Registrar duração
    task_duration.record(duration, {
        "task_name": task_name,
        "account_id": self.account_id
    })

    return result
```

## 12. Machine Learning para Otimização e Funções Avançadas

Esta seção detalha a implementação de Machine Learning para otimização de rotas de agentes e sua expansão para funções avançadas, estabelecendo a base para um sistema de estado da arte.

### 12.1. ML para Otimização de Rotas de Agentes

#### 12.1.1. Visão Geral

O sistema implementará Machine Learning para prever quais agentes terão maior probabilidade de resolver determinadas consultas, otimizando a seleção de agentes com base no histórico de interações similares.

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Mensagem   │────▶│  Intention  │────▶│  ML Routing │────▶│  Agentes    │
│  do Cliente │     │  Agent      │     │  Agent      │     │  Relevantes │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
                                              │
                                              ▼
                                        ┌─────────────┐
                                        │  Histórico  │
                                        │  de Dados   │
                                        └─────────────┘
```

#### 12.1.2. Implementação do Agente de Roteamento ML

```python
class MLRoutingAgent(Agent):
    def __init__(self, account_id: str, redis_client):
        self.account_id = account_id
        self.redis = redis_client
        self.model = self._load_model()

        super().__init__(
            name="ml_routing_agent",
            description="Determina quais agentes têm maior probabilidade de resolver a consulta"
        )

    def _load_model(self):
        # Carregar modelo do Redis ou criar um novo se não existir
        model_key = f"{self.account_id}:ml_routing_model"
        model_data = self.redis.get(model_key)
        if model_data:
            return pickle.loads(model_data)
        else:
            # Criar modelo inicial simples
            return self._create_initial_model()

    def _create_initial_model(self):
        # Implementar modelo inicial baseado em regras simples
        # Será substituído por ML quando houver dados suficientes
        return SimpleRoutingModel()

    def _run(self, query: str, intent: str, metadata: Dict[str, Any]) -> Dict[str, float]:
        # Extrair features
        features = self._extract_features(query, intent, metadata)

        # Prever probabilidades
        agent_probabilities = self.model.predict_proba(features)

        # Registrar para treinamento futuro
        self._log_prediction(query, intent, agent_probabilities)

        return agent_probabilities

    def _extract_features(self, query: str, intent: str, metadata: Dict[str, Any]):
        # Extrair features para o modelo
        # Exemplo: embeddings da consulta, one-hot encoding da intenção, etc.
        embedding = get_embedding(query)
        intent_vector = self._encode_intent(intent)
        metadata_features = self._extract_metadata_features(metadata)

        return {
            "embedding": embedding,
            "intent_vector": intent_vector,
            "metadata_features": metadata_features
        }

    def _log_prediction(self, query: str, intent: str, probabilities: Dict[str, float]):
        # Registrar predição para treinamento futuro
        log_key = f"{self.account_id}:ml_routing_logs"
        log_entry = {
            "query": query,
            "intent": intent,
            "probabilities": probabilities,
            "timestamp": time.time()
        }
        self.redis.lpush(log_key, json.dumps(log_entry))
        self.redis.ltrim(log_key, 0, 9999)  # Manter últimos 10000 registros
```

#### 12.1.3. Integração com o Fluxo de Tarefas

```python
def _initialize_tasks(self) -> Dict[str, Task]:
    tasks = {}

    # Tarefa de intenção (sempre executada primeiro)
    tasks["intention"] = Task(
        description="Identifique a intenção do cliente na mensagem",
        expected_output="Classificação da intenção do cliente",
        agent=self.agents["intention"],
        async_execution=False
    )

    # Nova tarefa de roteamento ML
    tasks["ml_routing"] = Task(
        description="Determine quais agentes têm maior probabilidade de resolver a consulta",
        expected_output="Probabilidades para cada agente",
        agent=self.agents["ml_routing"],
        async_execution=False,
        depends_on=[tasks["intention"]]
    )

    # Tarefas de agentes especializados (agora condicionais com base no ML)
    for collection in self.enabled_collections:
        if collection in self.agents:
            tasks[collection] = Task(
                description=f"Execute a tarefa de {collection}",
                expected_output=f"Resultado da consulta a {collection}",
                agent=self.agents[collection],
                async_execution=True,
                depends_on=[tasks["ml_routing"]],
                condition=lambda inputs, collection=collection:
                    inputs.get("ml_routing_result", {}).get(collection, 0) > 0.3  # Threshold configurável
            )

    # Tarefa de resposta (sempre executada por último)
    tasks["response"] = Task(
        description="Gere a resposta final com base nos resultados dos outros agentes",
        expected_output="Resposta final para o cliente",
        agent=self.agents["response"],
        async_execution=False,
        depends_on=[task for name, task in tasks.items() if name not in ["intention", "ml_routing", "response"]]
    )

    return tasks
```

#### 12.1.4. Coleta de Feedback para Aprendizado Contínuo

```python
class FeedbackCollector:
    def __init__(self, account_id: str, redis_client):
        self.account_id = account_id
        self.redis = redis_client

    def record_agent_success(self, agent_name: str, query: str, intent: str, success_score: float):
        """Registra o sucesso de um agente para uma consulta específica."""
        key = f"{self.account_id}:agent_success:{agent_name}"
        entry = {
            "query": query,
            "intent": intent,
            "success_score": success_score,
            "timestamp": time.time()
        }
        self.redis.lpush(key, json.dumps(entry))
        self.redis.ltrim(key, 0, 999)  # Manter últimos 1000 registros

    def record_response_feedback(self, conversation_id: str, response: str, feedback_score: float):
        """Registra feedback sobre a resposta final."""
        key = f"{self.account_id}:response_feedback"
        entry = {
            "conversation_id": conversation_id,
            "response": response,
            "feedback_score": feedback_score,
            "timestamp": time.time()
        }
        self.redis.lpush(key, json.dumps(entry))
        self.redis.ltrim(key, 0, 999)  # Manter últimos 1000 registros
```

### 12.2. Expansão para Funções Avançadas

O framework de ML para otimização de rotas pode ser expandido para suportar funções avançadas, transformando o sistema em uma plataforma de inteligência de negócios.

#### 12.2.1. Análise de Dados

```python
class DataAnalysisAgent(Agent):
    def __init__(self, account_id: str, redis_client, mcp_client):
        self.account_id = account_id
        self.redis = redis_client
        self.mcp = mcp_client
        self.model = self._load_model("data_analysis")

        super().__init__(
            name="data_analysis_agent",
            description="Analisa dados de negócio para extrair insights"
        )

    def _run(self, query_type: str, time_range: Dict, metrics: List[str]) -> Dict:
        # Extrair dados relevantes do MCP/Odoo
        raw_data = self.mcp.get_business_data(metrics, time_range)

        # Aplicar modelo de análise
        insights = self.model.analyze(raw_data, query_type)

        # Gerar visualizações se necessário
        visualizations = self._generate_visualizations(raw_data, insights)

        return {
            "insights": insights,
            "visualizations": visualizations,
            "confidence": self.model.get_confidence()
        }

    def _generate_visualizations(self, data, insights):
        """Gera visualizações baseadas nos dados e insights."""
        visualizations = {}

        # Exemplo: gerar gráfico de tendência de vendas
        if "sales_trend" in insights:
            visualizations["sales_trend"] = {
                "type": "line_chart",
                "data": self._prepare_chart_data(data, "sales_trend"),
                "title": "Tendência de Vendas",
                "x_label": "Data",
                "y_label": "Vendas (R$)"
            }

        # Exemplo: gerar gráfico de distribuição de produtos
        if "product_distribution" in insights:
            visualizations["product_distribution"] = {
                "type": "pie_chart",
                "data": self._prepare_chart_data(data, "product_distribution"),
                "title": "Distribuição de Vendas por Produto"
            }

        return visualizations
```

**Exemplo de Uso:**
```python
# Analisar dados de vendas dos últimos 30 dias
result = data_analysis_agent.run(
    query_type="sales_performance",
    time_range={"start": "2023-05-01", "end": "2023-05-30"},
    metrics=["daily_sales", "product_performance", "customer_segments"]
)

# Resultado
{
    "insights": [
        "As vendas aumentaram 15% em relação ao mês anterior",
        "O produto 'Smartphone X' teve o maior crescimento (32%)",
        "Clientes do segmento 'Premium' aumentaram suas compras em 24%"
    ],
    "visualizations": {
        "sales_trend": {...},  # Dados para gráfico de linha
        "product_distribution": {...}  # Dados para gráfico de pizza
    }
}
```

#### 12.2.2. Análise de Redes Sociais

```python
class SocialMediaAnalysisAgent(Agent):
    def __init__(self, account_id: str, redis_client):
        self.account_id = account_id
        self.redis = redis_client
        self.sentiment_model = self._load_model("sentiment_analysis")
        self.trend_model = self._load_model("trend_detection")

        super().__init__(
            name="social_media_analysis_agent",
            description="Analisa menções em redes sociais e identifica tendências"
        )

    def _run(self, social_data: Dict, analysis_type: str) -> Dict:
        if analysis_type == "sentiment":
            # Análise de sentimento em menções da marca
            results = self.sentiment_model.analyze(social_data["mentions"])

        elif analysis_type == "trends":
            # Detecção de tendências relacionadas
            results = self.trend_model.detect(social_data["industry_posts"])

        # Armazenar resultados para treinamento contínuo
        self._store_analysis_results(analysis_type, social_data, results)

        return results

    def _store_analysis_results(self, analysis_type, data, results):
        """Armazena resultados para treinamento futuro."""
        key = f"{self.account_id}:social_analysis:{analysis_type}"
        entry = {
            "data_sample": self._get_data_sample(data),  # Amostra dos dados para referência
            "results": results,
            "timestamp": time.time()
        }
        self.redis.lpush(key, json.dumps(entry))
        self.redis.ltrim(key, 0, 499)  # Manter últimos 500 registros
```

**Exemplo de Uso:**
```python
# Analisar sentimento das menções à marca nas últimas 24 horas
result = social_media_agent.run(
    social_data={
        "mentions": [
            {"text": "Adorei o novo produto da @marca!", "platform": "twitter", "timestamp": "2023-05-30T14:23:00Z"},
            {"text": "Péssimo atendimento da @marca hoje", "platform": "twitter", "timestamp": "2023-05-30T15:45:00Z"},
            # ... mais menções
        ]
    },
    analysis_type="sentiment"
)

# Resultado
{
    "overall_sentiment": 0.65,  # 0 a 1, onde 1 é totalmente positivo
    "sentiment_distribution": {
        "positive": 0.7,
        "neutral": 0.2,
        "negative": 0.1
    },
    "key_topics": {
        "produto": {"sentiment": 0.8, "count": 15},
        "atendimento": {"sentiment": 0.3, "count": 8},
        "preço": {"sentiment": 0.6, "count": 5}
    },
    "trending_mentions": [
        {"text": "Adorei o novo produto da @marca!", "engagement": 120, "sentiment": 0.9},
        # ... mais menções em destaque
    ]
}
```

#### 12.2.3. Análise de Tendências de Produtos

```python
class ProductTrendAgent(Agent):
    def __init__(self, account_id: str, redis_client, mcp_client):
        self.account_id = account_id
        self.redis = redis_client
        self.mcp = mcp_client
        self.recommendation_model = self._load_model("product_recommendation")
        self.trend_model = self._load_model("product_trend")

        super().__init__(
            name="product_trend_agent",
            description="Analisa tendências de produtos e gera recomendações"
        )

    def _run(self, customer_id: str = None, product_category: str = None) -> Dict:
        # Obter catálogo de produtos do cliente
        products = self.mcp.get_products(self.account_id)

        # Obter histórico de vendas
        sales_history = self.mcp.get_sales_history(self.account_id, days=90)

        if customer_id:
            # Recomendações personalizadas para cliente específico
            customer_history = self.mcp.get_customer_history(customer_id)
            recommendations = self.recommendation_model.recommend(
                customer_history, products, top_n=5
            )
            return {"recommendations": recommendations}

        elif product_category:
            # Análise de tendências para categoria específica
            category_trends = self.trend_model.analyze_category(
                product_category, sales_history, products
            )
            return {"category_trends": category_trends}

        else:
            # Tendências gerais de produtos
            general_trends = self.trend_model.analyze_general(
                sales_history, products
            )
            return {"general_trends": general_trends}

    def _load_model(self, model_type):
        """Carrega modelo específico do Redis ou cria novo."""
        model_key = f"{self.account_id}:{model_type}_model"
        model_data = self.redis.get(model_key)

        if model_data:
            return pickle.loads(model_data)
        else:
            # Criar modelo inicial
            if model_type == "product_recommendation":
                return CollaborativeFilteringModel()
            elif model_type == "product_trend":
                return ProductTrendModel()
```

**Exemplo de Uso:**
```python
# Analisar tendências gerais de produtos
result = product_trend_agent.run()

# Resultado
{
    "general_trends": {
        "rising_products": [
            {"id": "P123", "name": "Smartphone X", "growth_rate": 0.32, "confidence": 0.85},
            {"id": "P456", "name": "Fone Bluetooth Y", "growth_rate": 0.28, "confidence": 0.82},
            # ... mais produtos em ascensão
        ],
        "declining_products": [
            {"id": "P789", "name": "Tablet Z", "decline_rate": 0.15, "confidence": 0.75},
            # ... mais produtos em declínio
        ],
        "seasonal_patterns": [
            {"category": "Eletrônicos", "peak_months": ["Novembro", "Dezembro"], "confidence": 0.9},
            # ... mais padrões sazonais
        ],
        "cross_selling_opportunities": [
            {"product1": "P123", "product2": "P456", "correlation": 0.75, "confidence": 0.8},
            # ... mais oportunidades de cross-selling
        ]
    }
}
```

### 12.3. Arquitetura Integrada para ML Avançado

A implementação de ML para otimização de rotas e funções avançadas requer uma arquitetura integrada:

```
┌─────────────────────────────────────────────────────────────┐
│                   Interface de Usuário                       │
└───────────────────────────────┬─────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────┐
│                      API de Serviços                         │
└───────────────────────────────┬─────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────┐
│                    Orquestrador de Crews                     │
│                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ WhatsApp    │  │ Instagram   │  │ Analytics           │  │
│  │ Crew        │  │ Crew        │  │ Crew                │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└───────────────────────────────┬─────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────┐
│                   ML Service Layer                           │
│                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ Routing     │  │ Analytics   │  │ Recommendation      │  │
│  │ Models      │  │ Models      │  │ Models              │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└───────────────────────────────┬─────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────┐
│                   Data Service Layer                         │
│                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ Redis       │  │ Qdrant      │  │ Time Series DB      │  │
│  │ Cache       │  │ Vector DB   │  │ (para análises)     │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└───────────────────────────────┬─────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────┐
│                   Integration Layer                          │
│                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ MCP/Odoo    │  │ Social Media│  │ External APIs       │  │
│  │ Connector   │  │ Connectors  │  │ (mercado, clima)    │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 12.4. Plano de Implementação em Fases

A implementação deve seguir uma abordagem em fases para minimizar riscos e maximizar o valor:

#### Fase 1: Coleta de Dados e Infraestrutura Básica
- Implementar coleta de métricas detalhadas sobre o desempenho de cada agente
- Armazenar no Redis o histórico de consultas, agentes acionados e resultados
- Estabelecer a infraestrutura básica de ML (pipelines de dados, armazenamento, etc.)

#### Fase 2: ML para Otimização de Rotas
- Implementar o MLRoutingAgent com um modelo simples baseado em regras
- Integrar com o fluxo de tarefas existente
- Implementar mecanismos de feedback para aprendizado contínuo

#### Fase 3: Expansão para Análise de Dados
- Implementar o DataAnalysisAgent para análise básica de dados de negócio
- Integrar com o MCP/Odoo para acesso a dados relevantes
- Desenvolver visualizações básicas para insights

#### Fase 4: Expansão para Redes Sociais e Tendências de Produtos
- Implementar o SocialMediaAnalysisAgent para análise de sentimento e tendências
- Implementar o ProductTrendAgent para análise de tendências de produtos
- Integrar com fontes de dados externas relevantes

#### Fase 5: Integração Completa e Otimização
- Integrar todos os componentes em uma plataforma coesa
- Otimizar modelos com base em dados reais
- Implementar dashboards e interfaces para visualização de insights

### 12.5. Considerações Técnicas

#### 12.5.1. Escolha de Modelos

Para cada função, recomendamos começar com modelos mais simples e evoluir conforme necessário:

1. **Roteamento de Agentes**:
   - Inicial: Modelo baseado em regras + TF-IDF
   - Intermediário: Random Forest ou Gradient Boosting
   - Avançado: Modelos de embedding + classificação

2. **Análise de Dados**:
   - Inicial: Estatísticas descritivas + regras de detecção de anomalias
   - Intermediário: Modelos de séries temporais (ARIMA, Prophet)
   - Avançado: Redes neurais para previsão e detecção de padrões

3. **Análise de Redes Sociais**:
   - Inicial: Análise de sentimento baseada em léxico
   - Intermediário: Classificadores de texto (SVM, Naive Bayes)
   - Avançado: Modelos de linguagem pré-treinados fine-tuned

4. **Tendências de Produtos**:
   - Inicial: Filtros colaborativos simples
   - Intermediário: Matrix Factorization
   - Avançado: Modelos híbridos (conteúdo + colaborativo)

#### 12.5.2. Armazenamento e Processamento de Dados

1. **Redis**:
   - Armazenar modelos serializados
   - Cache de resultados de inferência
   - Armazenar métricas de performance

2. **Qdrant**:
   - Armazenar embeddings de consultas
   - Busca semântica para casos similares
   - Armazenar representações vetoriais de produtos

3. **Time Series DB** (opcional):
   - Armazenar dados históricos para análise
   - Suportar consultas eficientes em séries temporais
   - Facilitar a detecção de tendências e padrões

#### 12.5.3. Considerações de Performance

1. **Latência**:
   - Implementar cache de inferência para consultas similares
   - Utilizar modelos mais leves para inferência em tempo real
   - Pré-calcular insights comuns em background jobs

2. **Escalabilidade**:
   - Separar treinamento (batch) de inferência (tempo real)
   - Utilizar processamento assíncrono para análises complexas
   - Implementar filas para processamento de tarefas intensivas

### 12.6. Métricas de Sucesso

Para avaliar o sucesso da implementação de ML, devemos monitorar:

1. **Métricas de Performance**:
   - Tempo médio de resposta
   - Utilização de recursos (CPU, memória)
   - Throughput (consultas processadas por minuto)

2. **Métricas de Qualidade**:
   - Precisão do roteamento de agentes
   - Relevância dos insights gerados
   - Satisfação do usuário com as respostas

3. **Métricas de Negócio**:
   - Redução no tempo de atendimento
   - Aumento na satisfação do cliente
   - Conversão de insights em ações de negócio

## 13. Referências

- [Documentação CrewAI](https://docs.crewai.com/)
- [Padrões Assíncronos em Python](https://docs.python.org/3/library/asyncio.html)
- [Documentação Qdrant](https://qdrant.tech/documentation/)
- [Documentação Redis](https://redis.io/documentation/)
- [Documentação FastAPI](https://fastapi.tiangolo.com/)
- [Documentação OpenAI](https://platform.openai.com/docs/)
- [OpenTelemetry para Python](https://opentelemetry.io/docs/instrumentation/python/)
- [RabbitMQ para Python](https://www.rabbitmq.com/tutorials/tutorial-one-python.html)
- [Pydantic para Validação](https://docs.pydantic.dev/)
- [Scikit-learn para ML](https://scikit-learn.org/stable/)
- [PyTorch para Deep Learning](https://pytorch.org/docs/stable/index.html)
- [Pandas para Análise de Dados](https://pandas.pydata.org/docs/)
- [NLTK para Processamento de Linguagem Natural](https://www.nltk.org/)
