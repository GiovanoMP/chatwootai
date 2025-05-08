# Fluxo de Integração para Implementação de Crews

Este documento descreve o fluxo atual do sistema e como a nova implementação de crews deve se integrar ao código existente.

## Fluxo Atual do Sistema

### 1. Recebimento de Mensagens (Webhook)

O fluxo começa quando uma mensagem é recebida pelo webhook do Chatwoot:

```
[Chatwoot] → [Webhook Handler] → [Hub] → [Crew] → [Resposta para Chatwoot]
```

**Arquivos relevantes:**
- `src/webhook/routes.py`: Define as rotas do webhook
- `src/webhook/webhook_handler.py`: Processa as mensagens recebidas
- `src/webhook/init.py`: Inicializa o sistema de webhook

### 2. Processamento pelo Webhook Handler

O `webhook_handler.py` é responsável por:
1. Extrair informações da mensagem (account_id, conversation_id, etc.)
2. Determinar o domínio e account_id interno com base no mapeamento
3. Encaminhar a mensagem para o Hub

**Trecho relevante em `webhook_handler.py`:**
```python
# Encaminhar mensagem para processamento pelo Hub
logger.info("Encaminhando mensagem para processamento pelo Hub")
response = await self.hub.process_message(
    message=content,
    channel_type="whatsapp",
    account_id=account_id,
    domain_name=domain_name,
    internal_account_id=internal_account_id,
    conversation_id=conversation_id,
    metadata=metadata
)
```

### 3. Direcionamento pelo Hub

O Hub (`src/core/hub.py`) é responsável por:
1. Determinar o tipo de crew com base no canal
2. Obter ou criar a crew apropriada
3. Encaminhar a mensagem para a crew

**Trecho relevante em `hub.py`:**
```python
async def process_message(self, message, channel_type, account_id, domain_name, internal_account_id, conversation_id=None, metadata=None):
    # Determinar o tipo de crew com base no canal
    crew_type = "customer_service"
    
    # Obter ou criar a crew apropriada
    crew = await self.get_or_create_crew(
        crew_type=crew_type,
        channel_type=channel_type,
        domain_name=domain_name,
        account_id=internal_account_id
    )
    
    # Processar a mensagem com a crew
    return await crew.process_message(
        message=message,
        conversation_id=conversation_id,
        metadata=metadata
    )
```

### 4. Criação da Crew

O método `get_or_create_crew` do Hub verifica se a crew já existe em cache (Redis ou memória) e, se não, cria uma nova usando o `CrewFactory`:

```python
async def get_or_create_crew(self, crew_type, channel_type, domain_name, account_id):
    # Gerar chave de cache
    cache_key = f"crew:{crew_type}:{channel_type}:{domain_name}:{account_id}"
    
    # Verificar cache em memória
    if cache_key in self.memory_cache:
        return self.memory_cache[cache_key]
    
    # Verificar cache no Redis
    if self.redis_async:
        try:
            # Tentar obter do Redis
            # ...
        except Exception as e:
            logger.warning(f"Erro ao acessar Redis para crew {cache_key}: {e}")
    
    # Se não encontrou, criar nova crew
    crew = await self.crew_factory.create_crew(
        crew_type=crew_type,
        domain_name=domain_name,
        account_id=account_id,
        channel_type=channel_type
    )
    
    # Armazenar em cache
    self.memory_cache[cache_key] = crew
    
    # Armazenar no Redis
    if self.redis_async:
        try:
            # Armazenar no Redis
            # ...
        except Exception as e:
            logger.warning(f"Erro ao armazenar crew no Redis: {e}")
    
    return crew
```

### 5. Criação da Crew pelo CrewFactory

O `CrewFactory` (`src/core/crews/crew_factory.py`) é responsável por criar a crew apropriada com base no tipo de canal:

```python
async def create_crew(self, crew_type, domain_name, account_id, channel_type=None):
    # Carregar configuração
    config = await self.config_registry.get_config(domain_name, account_id)
    
    # Criar crew com base no canal
    if channel_type == "whatsapp":
        from src.core.crews.channels.whatsapp_crew import WhatsAppCrew
        crew = WhatsAppCrew(domain_name, account_id, config)
    elif channel_type == "facebook":
        # ...
    else:
        # Crew padrão
        # ...
    
    return crew
```

### 6. Processamento pela Crew

A crew atual (`src/core/crews/channels/whatsapp_crew.py`) processa a mensagem e retorna uma resposta:

```python
async def process_message(self, message, conversation_id=None, metadata=None):
    # Processar a mensagem
    # ...
    
    # Retornar resposta
    return {
        "content": response,
        "status": "success",
        "metadata": {
            "crew_type": self.__class__.__name__,
            "domain_name": self.domain_name,
            "account_id": self.account_id
        },
        "channel": "whatsapp",
        "routing": {
            "crew_type": "customer_service",
            "channel_type": "whatsapp",
            "domain_name": self.domain_name,
            "account_id": self.account_id
        }
    }
```

### 7. Envio da Resposta

O `webhook_handler.py` recebe a resposta da crew e a envia de volta para o Chatwoot:

```python
# Enviar resposta para o Chatwoot
if response and response.get("content"):
    await self._send_response_to_chatwoot(
        account_id=account_id,
        conversation_id=conversation_id,
        content=response["content"]
    )
```

## Integração da Nova Implementação

Para integrar a nova implementação de crews ao fluxo existente, siga estas diretrizes:

### 1. Manter a Interface da Crew

A nova implementação da `WhatsAppCrew` deve manter a mesma interface pública:

```python
class WhatsAppCrew(BaseCrew):
    def __init__(self, domain_name, account_id, config):
        super().__init__(domain_name, account_id, config)
        # Inicializar agentes e tarefas
    
    async def process_message(self, message, conversation_id=None, metadata=None):
        # Implementar processamento com os 4 agentes
        # Retornar resposta no mesmo formato que a implementação atual
```

### 2. Estrutura de Retorno

A resposta deve seguir o mesmo formato:

```python
{
    "content": "Texto da resposta",
    "status": "success",
    "metadata": {
        "crew_type": "WhatsAppCrew",
        "domain_name": domain_name,
        "account_id": account_id
    },
    "channel": "whatsapp",
    "routing": {
        "crew_type": "customer_service",
        "channel_type": "whatsapp",
        "domain_name": domain_name,
        "account_id": account_id
    }
}
```

### 3. Localização do Arquivo

Mantenha o arquivo da crew no mesmo local:
- `src/core/crews/channels/whatsapp_crew.py`

### 4. Implementação dos Agentes

Os 4 agentes devem ser implementados como classes separadas:
- `src/core/crews/agents/intention_agent.py`
- `src/core/crews/agents/vector_search_agent.py`
- `src/core/crews/agents/mcp_agent.py`
- `src/core/crews/agents/response_agent.py`

### 5. Processamento Paralelo

Implemente o processamento paralelo usando `asyncio.gather()`:

```python
async def process_message(self, message, conversation_id=None, metadata=None):
    # Executar o agente de intenção primeiro
    intention_result = await self.intention_agent.execute(message)
    
    # Executar os outros agentes em paralelo
    vector_search_task = asyncio.create_task(
        self.vector_search_agent.execute(message, intention_result)
    )
    mcp_task = asyncio.create_task(
        self.mcp_agent.execute(message, intention_result)
    )
    
    # Aguardar resultados
    vector_search_result, mcp_result = await asyncio.gather(
        vector_search_task, mcp_task
    )
    
    # Gerar resposta final
    response = await self.response_agent.execute(
        message, intention_result, vector_search_result, mcp_result
    )
    
    # Retornar no formato esperado
    return {
        "content": response,
        "status": "success",
        "metadata": {
            "crew_type": self.__class__.__name__,
            "domain_name": self.domain_name,
            "account_id": self.account_id
        },
        "channel": "whatsapp",
        "routing": {
            "crew_type": "customer_service",
            "channel_type": "whatsapp",
            "domain_name": self.domain_name,
            "account_id": self.account_id
        }
    }
```

## Pontos de Atenção

1. **Não modifique** os arquivos `hub.py` e `webhook_handler.py` a menos que seja absolutamente necessário
2. **Mantenha compatibilidade** com o formato de resposta atual
3. **Implemente logging detalhado** para facilitar diagnóstico
4. **Trate erros** para garantir que falhas em um agente não comprometam todo o fluxo
5. **Use o Redis** para cache quando apropriado
6. **Acesse configurações** através do objeto `config` passado no construtor

Seguindo estas diretrizes, a nova implementação da WhatsApp Crew se integrará perfeitamente ao fluxo existente, mantendo a compatibilidade com o restante do sistema.
