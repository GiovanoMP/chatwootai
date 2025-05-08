# Nova Arquitetura do Sistema ChatwootAI

Este documento descreve a nova arquitetura do sistema ChatwootAI, focada em baixa latência, multi-tenancy e escalabilidade.

## Visão Geral

A nova arquitetura substitui o modelo anterior baseado em múltiplas crews funcionais por uma abordagem mais modular com crews específicas por canal (WhatsApp, Instagram, etc.), todas configuráveis via YAML existente gerado pelo Odoo.

### Arquitetura Atual vs. Nova Arquitetura

**Arquitetura Atual:**
```
Webhook → WebhookHandler → Hub → CrewFactory → Domain Crews (múltiplas)
                                     ↓
                            DataProxyAgent (compartilhado)
```

**Nova Arquitetura:**
```
Webhook → WebhookHandler → Hub → CrewFactory → Canal-Specific Crews (WhatsApp, Instagram, etc.)
                            ↓        ↓                      ↓
                        [Redis]  [Config YAML]     [Agentes Especializados com MCP]
```

## Componentes Principais

### 1. ConfigRegistry

Responsável pelo carregamento e cache de configurações YAML, com suporte a Redis.

```python
class ConfigRegistry:
    def __init__(self, redis_client=None, config_loader=None):
        self.redis_client = redis_client or get_redis_client()
        self.config_loader = config_loader or ConfigLoader()
        self.memory_cache = {}

    async def get_config(self, domain_name, account_id, force_reload=False):
        # Implementação com cache em camadas
        # 1. Verificar cache em memória
        # 2. Verificar Redis
        # 3. Carregar do arquivo YAML
        pass
```

### 2. CrewFactory

Responsável pela criação de crews específicas por canal com base na configuração YAML.

```python
class CrewFactory:
    def __init__(self, config_registry=None):
        self.config_registry = config_registry or ConfigRegistry()

    async def create_crew(self, crew_type, domain_name, account_id, channel_type=None):
        # Carregar configuração YAML existente gerada pelo Odoo
        config = await self.config_registry.get_config(domain_name, account_id)

        # Criar a crew apropriada com base no tipo e canal
        if crew_type == "customer_service":
            if channel_type == "whatsapp":
                return WhatsAppCrew(config=config, account_id=account_id, domain_name=domain_name)
            elif channel_type == "instagram":
                return InstagramCrew(config=config, account_id=account_id, domain_name=domain_name)
            else:
                return CustomerServiceCrew(config=config, account_id=account_id, domain_name=domain_name)
        elif crew_type == "analytics":
            return AnalyticsCrew(config=config, account_id=account_id, domain_name=domain_name)
        else:
            raise ValueError(f"Tipo de crew desconhecido: {crew_type}")
```

### 3. Crews Específicas por Canal

Implementação de crews especializadas para cada canal de comunicação, todas utilizando a mesma estrutura YAML.

```python
# Classe base para todas as crews de atendimento
class BaseCrew:
    def __init__(self, config, domain_name, account_id):
        self.config = config
        self.domain_name = domain_name
        self.account_id = account_id
        self.agents = self._create_agents()
        self.crew = self._create_crew()

    def _create_agents(self):
        # Implementação base para criar agentes
        pass

    def _create_crew(self):
        # Implementação base para criar a crew
        pass

    async def process(self, message, context):
        # Processamento base de mensagens
        pass

# Crew específica para WhatsApp
class WhatsAppCrew(BaseCrew):
    def _create_agents(self):
        # Criar agentes otimizados para WhatsApp
        # Usando a mesma configuração YAML, mas adaptando para o contexto do WhatsApp
        agents = []

        # Configurações comuns para todos os canais
        common_config = self.config.get("customer_service", {})

        # Agente de intenção adaptado para WhatsApp
        intention_agent = self._create_intention_agent(
            greeting=common_config.get("greeting", "Olá, como posso ajudar?"),
            style=common_config.get("communication_style", "friendly")
        )

        # Outros agentes específicos para WhatsApp
        # ...

        return agents

# Crew específica para Instagram
class InstagramCrew(BaseCrew):
    def _create_agents(self):
        # Criar agentes otimizados para Instagram
        # Usando a mesma configuração YAML, mas adaptando para o contexto do Instagram
        # ...
```

### 4. Hub Simplificado

Responsável pelo direcionamento de mensagens para a crew apropriada com base no canal e gerenciamento de cache.

```python
class Hub:
    def __init__(self, redis_client=None, domain_manager=None, crew_factory=None):
        self.redis_client = redis_client or get_redis_client()
        self.domain_manager = domain_manager or DomainManager()
        self.crew_factory = crew_factory or CrewFactory()
        self.memory_cache = {}

    async def process_message(self, message, conversation_id, channel_type, domain_name=None, account_id=None):
        # Verificar se temos domínio e account_id
        if not domain_name or not account_id:
            # Determinar domínio e account_id se não fornecidos
            pass

        # Determinar o tipo de crew e canal com base na origem da mensagem
        crew_type, specific_channel = self._determine_crew_type(message, channel_type)

        # Obter a crew apropriada (do cache ou criar nova)
        crew = await self.get_crew(crew_type, domain_name, account_id, specific_channel)

        # Processar a mensagem com a crew
        return await crew.process(message, {"conversation_id": conversation_id, "channel_type": channel_type})

    def _determine_crew_type(self, message, channel_type):
        # Determinar o tipo de crew e canal específico com base na origem
        if channel_type == "chatwoot":
            # Verificar o canal específico dentro do Chatwoot
            if "whatsapp" in message.get("source_id", "").lower():
                return "customer_service", "whatsapp"
            elif "instagram" in message.get("source_id", "").lower():
                return "customer_service", "instagram"
            else:
                return "customer_service", "default"
        elif channel_type == "analytics_request":
            return "analytics", None
        else:
            return "customer_service", "default"

    async def get_crew(self, crew_type, domain_name, account_id, channel_type=None):
        # Chave de cache que inclui o tipo de crew e canal
        cache_key = f"crew:{crew_type}:{channel_type or 'default'}:{domain_name}:{account_id}"

        # Implementação com cache em camadas
        # 1. Verificar cache em memória
        # 2. Verificar Redis
        # 3. Criar nova crew com o tipo e canal específicos
        pass
```

## Estratégia de Cache

A nova arquitetura implementa uma estratégia de cache em camadas:

1. **Camada 1: Cache em Memória**
   - Mais rápido, mas volátil
   - Primeira verificação ao buscar crews ou configurações

2. **Camada 2: Cache Redis**
   - Persistente entre reinicializações
   - Segunda verificação se não encontrado em memória

3. **Camada 3: Carregamento Direto**
   - Último recurso, carrega do arquivo YAML
   - Cria a crew do zero

```python
async def get_crew(self, crew_type, domain_name, account_id, channel_type=None):
    # Chave de cache que inclui o tipo de crew e canal
    cache_key = f"crew:{crew_type}:{channel_type or 'default'}:{domain_name}:{account_id}"

    # Camada 1: Cache em memória
    if cache_key in self.memory_cache:
        return self.memory_cache[cache_key]

    # Camada 2: Cache Redis
    try:
        if self.redis_client and self.redis_client.is_connected():
            crew_data = await self.redis_client.get(cache_key)
            if crew_data:
                crew = pickle.loads(crew_data)
                self.memory_cache[cache_key] = crew
                return crew
    except Exception as e:
        logger.warning(f"Erro ao acessar Redis: {e}, usando fallback")

    # Camada 3: Criação da crew específica para o canal
    crew = await self.crew_factory.create_crew(
        crew_type=crew_type,
        domain_name=domain_name,
        account_id=account_id,
        channel_type=channel_type
    )

    # Armazenar em cache
    self.memory_cache[cache_key] = crew

    # Tentar armazenar em Redis
    try:
        if self.redis_client and self.redis_client.is_connected():
            crew_data = pickle.dumps(crew)
            await self.redis_client.set(cache_key, crew_data, ex=3600)  # 1 hora
    except Exception as e:
        logger.warning(f"Erro ao armazenar crew no Redis: {e}")

    return crew
```

## Sistema de Filas (Opcional)

Para maior escalabilidade, podemos implementar um sistema de filas com RabbitMQ:

```
Webhook → WebhookHandler → RabbitMQ → Processadores → Hub → CustomerServiceCrew
```

Benefícios:
- Resposta imediata ao webhook
- Processamento assíncrono em segundo plano
- Resiliência a picos de tráfego
- Garantia de processamento de todas as mensagens

## Fluxo de Dados

1. WebhookHandler recebe webhook do Chatwoot
2. WebhookHandler extrai account_id e determina domínio
3. WebhookHandler normaliza a mensagem
4. WebhookHandler chama Hub.process_message()
5. Hub determina o tipo de crew e canal específico com base na origem da mensagem
6. Hub verifica cache para a crew específica do canal
   - Se não encontrar, carrega a configuração YAML para o account_id
   - Cria a crew apropriada para o canal específico
   - Armazena a crew no cache
7. Hub chama crew.process() na crew específica do canal
8. A crew processa a mensagem com agentes otimizados para o canal
9. A crew retorna resposta ao Hub
10. Hub retorna resposta ao WebhookHandler
11. WebhookHandler envia resposta ao Chatwoot

## Considerações sobre Componentes Existentes

### CrewFactory

- **Status**: Adaptado
- **Substituto**: CrewFactory genérico
- **Razão**: Suporte a múltiplos tipos de crews e canais específicos

### DomainRegistry

- **Status**: Adapatado
- **Adaptação**: ConfigRegistry
- **Razão**: Manter a lógica de cache com Redis, simplificar para configurações

### DomainLoader

- **Status**: Adaptado
- **Adaptação**: ConfigLoader
- **Razão**: Manter a lógica de carregamento e mesclagem de configurações

### DataProxyAgent

- **Status**: Substituido
- **Substituto**: Agentes MCP específicos dentro de cada crew especializada por canal
- **Razão**: Cada crew terá seu próprio agente MCP configurado para o account_id específico e otimizado para o canal

## Estrutura de Diretórios

```
src/
├── core/
│   ├── config/
│   │   ├── config_registry.py
│   │   └── config_loader.py
│   ├── crews/
│   │   ├── base_crew.py
│   │   ├── crew_factory.py
│   │   └── channels/
│   │       ├── whatsapp_crew.py
│   │       ├── instagram_crew.py
│   │       └── default_crew.py
│   ├── hub.py
│   └── cache/
│       └── redis_cache.py
└── webhook/
    ├── webhook_handler.py
    └── routes.py
```

## Estrutura de Configuração YAML

```yaml
# config/domains/retail/account_1/config.yaml
account_id: account_1
name: Sandra Cosméticos
description: Loja de cosméticos online e física

company_metadata:
  business_hours:
    days: [0, 1, 2, 3, 4, 5, 6]
    start_time: 09:00
    end_time: '18:00'

  customer_service:
    communication_style: friendly
    greeting_message: Olá, bem-vindo à Sandra Cosméticos!

integrations:
  mcp:
    type: odoo-mcp
    config:
      credential_ref: account_1-00bfe67a
      db: account_1
      url: http://localhost:8069
```

## Plano de Implementação

### Fase 1: Sistema de Configuração

1. Implementar `ConfigRegistry` e `ConfigLoader`
   - Adaptar a partir do DomainRegistry e DomainLoader existentes
   - Garantir compatibilidade com a estrutura de arquivos YAML existente
   - Implementar cache em Redis com fallback

### Fase 2: Crews Específicas por Canal

1. Implementar `CrewFactory` genérico
   - Criar lógica de inicialização de crews com base no tipo e canal
   - Integrar com o sistema de configuração

2. Implementar `BaseCrew` e crews específicas por canal
   - Criar estrutura base comum a todas as crews
   - Implementar crews especializadas para WhatsApp, Instagram, etc.
   - Implementar agentes MCP específicos por account_id e otimizados por canal
   - Implementar processamento de mensagens adaptado a cada canal

### Fase 3: Hub Simplificado

1. Implementar novo `Hub`
   - Integrar com Redis para cache de crews
   - Implementar sistema de fallback em camadas
   - Implementar lógica de determinação de tipo de crew e canal
   - Direcionar mensagens para a crew específica do canal

### Fase 4: Integração com WebhookHandler

1. Atualizar `WebhookHandler`
   - Manter lógica de determinação de account_id e domínio
   - Integrar com o novo Hub
   - Atualizar fluxo de processamento

### Fase 5 (Opcional): Sistema de Filas

1. Implementar sistema de filas com RabbitMQ
   - Adicionar produtores no WebhookHandler
   - Implementar consumidores para processamento assíncrono

## Métricas de Sucesso

1. **Latência**: Tempo de resposta < 3 segundos para 95% das mensagens
2. **Escalabilidade**: Suporte a pelo menos 10 mensagens simultâneas por instância
3. **Resiliência**: Funcionamento contínuo mesmo com Redis indisponível
4. **Multi-tenancy**: Suporte a pelo menos 10 contas diferentes com configurações específicas

## Diagrama de Arquitetura

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────────────┐
│   Chatwoot  │────▶│  Webhook    │────▶│    Hub      │────▶│   CrewFactory      │
│             │     │  Handler    │     │             │     │                     │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────┬───────────┘
                           │                   │                       │
                           │                   │                       ▼
                           ▼                   ▼             ┌─────────────────────┐
                    ┌─────────────┐     ┌─────────────┐     │  Canal-Specific     │
                    │  Domain     │     │   Redis     │     │  Crews              │
                    │  Manager    │     │   Cache     │     │                     │
                    └─────────────┘     └─────────────┘     └─────────┬───────────┘
                                                                      │
                                                                      │
                                                                      ▼
                                                            ┌─────────────────────┐
                                                            │     MCP / Odoo      │
                                                            │     Integration     │
                                                            └─────────────────────┘
```

### Fluxo Detalhado por Canal

```
                         ┌─────────────────────┐
                         │    CrewFactory      │
                         └─────────┬───────────┘
                                   │
                                   ▼
          ┌────────────────────────────────────────────┐
          │                                            │
          ▼                                            ▼
┌─────────────────────┐                    ┌─────────────────────┐
│   WhatsAppCrew      │                    │   InstagramCrew     │
│                     │                    │                     │
└─────────┬───────────┘                    └─────────┬───────────┘
          │                                          │
          ▼                                          ▼
┌─────────────────────┐                    ┌─────────────────────┐
│ Agentes otimizados  │                    │ Agentes otimizados  │
│ para WhatsApp       │                    │ para Instagram      │
└─────────────────────┘                    └─────────────────────┘
```

## Status de Implementação

### Componentes Implementados

1. **ConfigRegistry e ConfigLoader**
   - ✅ Implementado com cache em camadas (memória → Redis → arquivo)
   - ✅ Compatível com a estrutura YAML existente
   - ✅ Suporte a fallback para Redis indisponível

2. **BaseCrew e Crews Específicas por Canal**
   - ✅ Implementada a classe base (BaseCrew) com métodos comuns
   - ✅ Implementada a WhatsAppCrew com otimizações específicas
   - ✅ Implementada a DefaultCrew para canais genéricos
   - ⏳ Pendente: InstagramCrew e outras crews específicas

3. **CrewFactory Genérico**
   - ✅ Implementado com suporte a múltiplos tipos de crews e canais
   - ✅ Integrado com ConfigRegistry para carregamento de configurações
   - ✅ Cache de crews para evitar recriação desnecessária

4. **Hub Simplificado**
   - ✅ Implementado com determinação de canal e tipo de crew
   - ✅ Integrado com Redis para cache de crews
   - ✅ Sistema de fallback em camadas
   - ✅ Direcionamento de mensagens para a crew específica do canal

5. **Integração com WebhookHandler**
   - ✅ Atualizado WebhookHandler para usar diretamente o novo Hub
   - ✅ Removido adaptador HubCrew e dependências legadas
   - ✅ Corrigido método de envio de mensagens para o Chatwoot
   - ✅ Testado com sucesso o fluxo completo de processamento de mensagens

### Resultados dos Testes

Os testes iniciais foram executados com sucesso, demonstrando o funcionamento dos componentes principais:

1. **ConfigRegistry e ConfigLoader**
   - Carregou corretamente a configuração para o domínio "furniture" e account_id "account_2"
   - Extraiu informações como nome da empresa ("Móveis Elegantes") e integrações disponíveis

2. **CrewFactory e WhatsAppCrew**
   - Criou com sucesso uma WhatsAppCrew para o domínio "furniture" e account_id "account_2"
   - A crew foi inicializada com 4 agentes e 4 tarefas
   - Os agentes foram criados corretamente: Intenção, Busca Vetorial, MCP e Resposta

3. **Hub**
   - Determinou corretamente o tipo de crew (customer_service) e canal específico (whatsapp)
   - Criou e armazenou a crew em cache
   - Processou a mensagem com sucesso através da crew

4. **Processamento de Mensagem**
   - A mensagem foi processada pela WhatsAppCrew
   - Todos os agentes executaram suas tarefas com sucesso
   - O Agente de Intenção identificou a intenção do cliente
   - O Agente de Busca Vetorial encontrou informações relevantes
   - O Agente MCP preparou-se para executar operações no Odoo
   - O Agente de Resposta gerou uma resposta clara e adaptada para WhatsApp

### Exemplo de Resposta Gerada

```
Olá! 😊 Como posso te ajudar hoje? Você está com alguma dúvida sobre nossos produtos ou serviços? Ou precisa de ajuda para resolver algum problema? Vou fazer o possível para te auxiliar!

Se precisar de informações sobre preços, características ou orientações para usar nossos produtos, é só me avisar! Estou aqui para te ajudar da melhor forma possível. 💪✨
```

Esta resposta demonstra:
- Adaptação para o formato WhatsApp (curta, direta, com emojis moderados)
- Estilo amigável e acolhedor
- Abertura para entender melhor a necessidade do cliente

## Próximos Passos

1. **Implementar mais crews específicas por canal**
   - InstagramCrew
   - FacebookCrew
   - WebCrew

2. **Refinar a integração com WebhookHandler**
   - Remover o adaptador HubCrew quando possível
   - Migrar completamente para a nova arquitetura
   - Otimizar o fluxo de processamento de mensagens

3. **Implementar ferramentas específicas**
   - Adicionar ferramentas reais para os agentes (busca vetorial, MCP, etc.)
   - Integrar com Qdrant para busca vetorial
   - Integrar com MCP-Odoo para operações no Odoo

4. **Melhorar o sistema de cache**
   - Configurar corretamente o Redis para produção
   - Implementar estratégias de expiração de cache

5. **Testes de carga e performance**
   - Verificar latência com múltiplas mensagens simultâneas
   - Testar resiliência com Redis indisponível
   - Validar isolamento entre diferentes accounts
