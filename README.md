# ChatwootAI - Sistema Multi-Agentes Modular para Atendimento Omnichannel

## Visão Geral

O ChatwootAI é uma plataforma avançada e altamente adaptável que integra Chatwoot, CrewAI, Odoo e tecnologias de banco de dados vetorial para criar um sistema inteligente de atendimento ao cliente em múltiplos canais. A solução utiliza agentes de IA especializados para automatizar interações, consultar regras de negócio, fornecer recomendações personalizadas e gerar insights analíticos, com uma arquitetura modular que permite fácil adaptação a diferentes modelos de negócio B2C, como cosméticos, saúde, varejo e serviços.

### Objetivos do Projeto

- Criar um hub central de comunicação para todos os canais (WhatsApp, Instagram, Facebook, etc.)
- Implementar agentes de IA especializados para diferentes funções (vendas, suporte, agendamento)
- Integrar com o Odoo para acesso a regras de negócio e dados empresariais
- Utilizar tecnologias de banco de dados vetorial para consultas semânticas eficientes
- Otimizar o desempenho com sistema de cache em dois níveis
- Proporcionar uma arquitetura modular e adaptável para diferentes domínios de negócio
- Facilitar a extensão e personalização através de um sistema de plugins
- Implementar estratégias de otimização de custos para uso eficiente de APIs de IA

## Arquitetura Hierárquica Hub-and-Spoke

O sistema utiliza uma arquitetura hierárquica baseada no modelo hub-and-spoke, permitindo especialização, coordenação eficiente e escalabilidade. Esta arquitetura é fundamental para o funcionamento do sistema, garantindo roteamento direto, coordenação centralizada, componentes desacoplados, design escalável e operação resiliente.

> **Documentação Detalhada**: Para uma explicação completa da arquitetura Hub-and-Spoke, incluindo princípios, componentes, fluxo de dados e otimizações, consulte nossa [documentação detalhada](docs/hub_and_spoke_architecture.md).

```
┌───────────────────────────────────────────────────────────────────────────┐
│                        CAMADA DE ENTRADA (SPOKES)                          │
├───────────┬───────────┬───────────┬───────────┬───────────┬───────────────┤
│  Crew     │  Crew     │  Crew     │  Crew     │  Crew     │  Crew         │
│ WhatsApp  │ Instagram │ Facebook  │  Email    │  Shopee   │  Outros Canais│
└─────┬─────┴─────┬─────┴─────┬─────┴─────┬─────┴─────┬─────┴───────┬───────┘
      │           │           │           │           │             │
      │           │           │           │           │             │
      ▼           ▼           ▼           ▼           ▼             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        CAMADA DE HUB CENTRAL                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│                              CHATWOOT                                   │
│                                                                         │
└───────────────────────────────────┬─────────────────────────────────────┘
                                    │
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      CAMADA DE PROCESSAMENTO                             │
├────────────────────┬────────────────────┬────────────────────┬──────────┤
│  Crew de     │  │  Crew de    │  │  Crew de     │  │  Crew           │    
│   Vendas     │  │  Suporte    │  │ Agendamento  │  │  Analítica      │    
└──────┬───────┘  └──────┬──────┘  └───────┬──────┘  └────────┬────────┘    
       │                  │                 │                   │             
       └──────────────────┼─────────────────┼───────────────────┘             
                          │                 │                                 
                          ▼                 ▼                                 
┌─────────────────────────────────────────────────────────────────────────┐
│                       CAMADA DE INTEGRAÇÃO                               │
├─────────────────┬─────────────────┬──────────────────┬──────────────────┤
│                 │                 │                  │                  │
│      ODOO       │     QDRANT      │      REDIS       │   OUTROS APIs    │
│                 │                 │                  │                  │
└─────────────────┴─────────────────┴──────────────────┴──────────────────┘
```

## Componentes Principais

### 1. Chatwoot

Chatwoot serve como o hub central de comunicação, gerenciando mensagens de múltiplos canais:

- **WhatsApp**: Integração via Evolution API
- **Instagram e Facebook**: Integração nativa do Chatwoot
- **Email**: Integração nativa do Chatwoot
- **Canais de Marketplace**: Shopee, Mercado Livre, Amazon, etc.

### 2. CrewAI

CrewAI orquestra agentes de IA especializados para processar mensagens e gerar respostas:

- **Agentes de Canal**: Monitoram e processam mensagens de canais específicos
- **Agentes Funcionais**: Especializados em funções como vendas, suporte e agendamento
- **Agentes de Hub**: Coordenam outros agentes e gerenciam o fluxo de informações

### 3. Odoo (ou outro ERP)

Odoo gerencia as regras de negócio, produtos, clientes e outros dados empresariais:

- **Catálogo de Produtos**: Informações detalhadas sobre produtos e serviços
- **Clientes**: Dados de clientes, histórico de compras e preferências
- **Regras de Negócio**: Políticas de preços, descontos, estoque, etc.

### 4. Qdrant (Banco de Dados Vetorial)

Qdrant armazena embeddings de regras de negócio para consultas semânticas eficientes:

- **Embeddings de Regras**: Representações vetoriais de políticas e procedimentos
- **Consultas Semânticas**: Busca de regras relevantes para uma determinada situação
- **Atualização Automática**: Sincronização com regras do Odoo

### 5. Redis (Cache)

Redis implementa um sistema de cache em dois níveis para otimizar consultas frequentes:

- **Cache L1**: Memória local para consultas muito frequentes
- **Cache L2**: Redis para consultas menos frequentes e compartilhamento entre instâncias

## Integração com a API do Chatwoot

O ChatwootAI implementa uma integração robusta com a API do Chatwoot para monitorar e responder a conversas em tempo real. Esta integração é composta pelos seguintes componentes:

### 1. Cliente da API do Chatwoot

O cliente da API do Chatwoot (`ChatwootClient`) fornece uma interface completa para interagir com todas as funcionalidades do Chatwoot:

- **Gerenciamento de Conversas**: Buscar, atualizar e resolver conversas
- **Mensagens**: Enviar e receber mensagens
- **Contatos**: Criar e atualizar informações de contatos
- **Inboxes**: Gerenciar diferentes canais de comunicação
- **Agentes e Equipes**: Atribuir conversas a agentes específicos

### 2. Manipulador de Webhooks

O `ChatwootWebhookHandler` processa eventos em tempo real enviados pelo Chatwoot:

- **Novas Mensagens**: Processa mensagens recebidas de clientes
- **Novas Conversas**: Inicializa o contexto para novas conversas
- **Mudanças de Status**: Reage a alterações no status das conversas



### 4. Manipulador de Respostas

O `ChatwootResponseHandler` facilita o envio de respostas para conversas:

- **Envio de Mensagens**: Envia respostas para conversas
- **Gerenciamento de Status**: Marca conversas como resolvidas
- **Atribuição**: Atribui conversas a agentes específicos
- **Etiquetas**: Adiciona etiquetas para classificação e organização

### 5. Integração com o Sistema de Contexto CRM

A integração com o Chatwoot se conecta ao serviço de contexto CRM para:

- **Armazenamento de Histórico**: Salva o histórico de conversas para referência futura
- **Contexto do Cliente**: Mantém informações sobre o cliente durante a conversa
- **Personalização**: Permite respostas personalizadas com base no histórico e perfil do cliente

### Exemplo de Uso

O sistema inclui um exemplo completo de integração com o Chatwoot que demonstra como:

1. Configurar o cliente da API do Chatwoot
2. Iniciar o monitor de conversas
3. Processar mensagens recebidas
4. Armazenar contexto no CRM
5. Enviar respostas personalizadas

Para executar o exemplo de integração, utilize o script `run_chatwoot_integration.sh` após configurar as variáveis de ambiente necessárias no arquivo `.env` (baseado no modelo `.env.chatwoot.example`).

## Adaptabilidade para Diferentes Modelos de Negócio

O ChatwootAI foi projetado com uma arquitetura modular que permite fácil adaptação para diferentes modelos de negócio B2C. Esta adaptabilidade é alcançada através dos seguintes componentes:

### 1. Sistema de Domínios de Negócio

O sistema utiliza arquivos YAML de configuração para definir regras, produtos, serviços e comportamentos específicos de cada domínio de negócio:

```
src/config/business_domains/
├── cosmetics.yaml     # Configuração para empresas de cosméticos
├── healthcare.yaml    # Configuração para clínicas e consultórios
├── retail.yaml        # Configuração para varejo
└── services.yaml      # Configuração para empresas de serviços
```

### 2. Agentes Adaptáveis

Os agentes são projetados para adaptar seu comportamento com base no domínio de negócio ativo:

- **SalesAgent**: Especializado em vendas, produtos e promoções
- **SupportAgent**: Especializado em suporte, dúvidas e problemas
- **SchedulingAgent**: Especializado em agendamentos e horários disponíveis

### 3. Sistema de Plugins

Um sistema modular de plugins permite estender as funcionalidades para necessidades específicas de cada domínio:

```
src/plugins/
├── base/                  # Classes base para todos os plugins
├── cosmetics/             # Plugins específicos para cosméticos
│   ├── product_recommendation.py
│   └── treatment_scheduler.py
├── healthcare/            # Plugins específicos para saúde
├── retail/                # Plugins específicos para varejo
└── plugin_manager.py      # Gerenciador central de plugins
```

### 4. Integração com Odoo

Integração direta com o sistema Odoo via API:

```
src/api/erp/
└── odoo/                  # Implementação para Odoo
    ├── client.py            # Cliente para API do Odoo
    └── conversation_context.py # Extensão para contexto de conversa
```

Durante o desenvolvimento, utilizamos uma simulação do Odoo com PostgreSQL em Docker (`src/api/odoo_simulation.py`).

### 5. Ferramenta de Criação de Domínios

Um script auxiliar facilita a criação de novos domínios de negócio:

```bash
python scripts/create_new_domain.py --name "education" --description "Configuração para instituições de ensino"
```

## Estratégias de Otimização de Custos

O ChatwootAI implementa diversas estratégias para otimizar o uso de APIs de IA e reduzir custos operacionais:

### 1. Otimização de Embeddings

O serviço de embeddings foi projetado para minimizar o consumo de tokens e reduzir chamadas à API da OpenAI:

- **Cache Redis**: Armazena embeddings já gerados para evitar chamadas repetidas à API
- **Processamento em Lote**: Agrupa múltiplas solicitações em uma única chamada de API
- **Pré-processamento de Texto**: Otimiza textos antes de gerar embeddings para reduzir tokens
- **Monitoramento de Uso**: Acompanha o consumo de tokens e estima custos para gestão eficiente

### 2. Sistema de Cache em Dois Níveis

Implementamos um sistema de cache em dois níveis para reduzir consultas repetidas:

- **Cache L1**: Memória local para consultas frequentes e dados temporais
- **Cache L2**: Redis para consultas menos frequentes e compartilhamento entre instâncias

### 3. Sincronização Inteligente

A sincronização entre PostgreSQL e Qdrant é otimizada para reduzir operações desnecessárias:

- **Sincronização Seletiva**: Atualiza apenas os registros que foram modificados
- **Sincronização Periódica**: Permite configurar intervalos de sincronização completa
- **Detecção de Mudanças**: Utiliza triggers do PostgreSQL para identificar alterações em tempo real

## Fluxo de Trabalho

1. Uma mensagem é recebida em um canal (WhatsApp, Instagram, etc.) e gerenciada pelo Chatwoot
2. O CrewAI Service recebe a notificação da nova mensagem via webhook do Chatwoot
3. O CrewAI Service analisa a mensagem e determina qual agente deve processá-la
4. O agente consulta o cache Redis para informações relevantes (regras, dados do cliente)
5. Se necessário, o agente realiza consultas semânticas no Qdrant para regras de negócio específicas
6. Para informações adicionais sobre clientes ou produtos, o agente consulta o Odoo via API
7. O agente processa a mensagem com o contexto completo e gera uma resposta
8. A resposta é enviada de volta ao Chatwoot, que a encaminha para o canal original
9. Informações relevantes da interação são armazenadas em cache para uso futuro

## Roadmap

- [x] Configuração inicial do projeto
- [x] Implementação da estrutura modular para adaptabilidade
- [x] Configuração do ambiente de simulação (PostgreSQL, Qdrant, Redis)
- [x] Implementação do cliente API do Chatwoot
- [x] Desenvolvimento da API de simulação do ERP (baseada em Odoo)
- [x] Criação de dados de exemplo para empresa de cosméticos
- [x] Implementação de embeddings com Ada 2 para regras de negócio
- [x] Integração com webhook do Chatwoot
- [x] Implementação do sistema de cache em dois níveis
- [ ] Desenvolvimento dos agentes básicos com CrewAI (usando GPT-4o Mini)
- [ ] Testes com canal WhatsApp
- [ ] Expansão para outros canais

## Status Atual do Projeto (Atualizado em 17/03/2025)

### Infraestrutura

- **Docker**: Todos os serviços estão configurados e funcionando corretamente no ambiente Docker
- **PostgreSQL** (`chatwootai_postgres`): Banco de dados configurado com tabelas para produtos, serviços, clientes, pedidos e regras de negócio
- **Qdrant** (`chatwootai_qdrant`): Banco de dados vetorial configurado com coleções para produtos e regras de negócio
- **Redis** (`chatwootai_redis`): Serviço de cache configurado e funcionando
- **API de Simulação do Odoo** (`chatwootai_odoo_simulation`): Serviço FastAPI funcionando na porta 8000

### Integração com Chatwoot

- **Conexão com API**: Configurada e testada com sucesso
- **Cliente API do Chatwoot**: Implementado e configurado com o token de acesso
- **Webhook**: Implementado localmente (não como serviço Docker), executado via terminal
- **Autenticação**: Configurada com token de API válido

### Próximos Passos

1. Implementar o webhook como serviço Docker para completar a integração com o Chatwoot
2. Finalizar a implementação dos agentes básicos com CrewAI
3. Realizar testes de integração completa com o canal WhatsApp
4. Expandir para outros canais (Instagram, Facebook, Email)

## Configuração

### 1. Pré-requisitos

- Docker e Docker Compose
- Python 3.10+
- Conta no Chatwoot
- Conta na OpenAI (para GPT-4o Mini e Ada 2)

### 2. Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto com as seguintes variáveis:

```
# Chatwoot
CHATWOOT_API_URL=https://seu-chatwoot.com/api/v1
CHATWOOT_API_KEY=seu-api-key

# OpenAI
OPENAI_API_KEY=sua-api-key

# Redis
REDIS_HOST=redis
REDIS_PORT=6379

# Qdrant
QDRANT_URL=http://qdrant:6333

# Odoo
ODOO_API_URL=http://odoo:8069
ODOO_API_KEY=seu-api-key
```

- Obtenha uma API Key do Chatwoot nas configurações do seu perfil
- Obtenha uma API Key da OpenAI

### 3. Configuração do CrewAI Service

```yaml
services:
  crewai_service:
    image: python:3.10-slim
    volumes:
      - crewai_data:/app/data
      - ./src:/app/src
    env_file:
      - .env
    command: python -m src.main
    depends_on:
      - redis
      - qdrant
      - odoo_simulation

  redis:
    image: redis:alpine
    volumes:
      - redis_data:/data

  qdrant:
    image: qdrant/qdrant
    volumes:
      - qdrant_data:/qdrant/storage

  odoo_simulation:
    build:
      context: ./src/api/odoo_simulation
    volumes:
      - odoo_sim_data:/app/data
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@postgres:5432/odoo_sim

  postgres:
    image: postgres:13
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_USER=postgres
      - POSTGRES_DB=odoo_sim

volumes:
  crewai_data:
  redis_data:
  qdrant_data:
  odoo_sim_data:
  postgres_data:
```

## Uso

### 1. Iniciar os Serviços

```bash
docker-compose up -d
```

### 2. Configurar o Webhook no Chatwoot

Configure um webhook no Chatwoot para enviar notificações de novas mensagens para o CrewAI Service:

- URL: `http://seu-servidor:8000/webhook`
- Eventos: `message_created`, `conversation_created`

### 3. Testar com um Canal

- Configure um canal no Chatwoot (ex: WhatsApp via Evolution API)
- Envie uma mensagem de teste
- Verifique os logs do CrewAI Service para confirmar o processamento

## Estrutura de Diretórios

```
chatwoot-ai/
├── docker-compose.yml
├── .env
├── README.md
├── docs/
│   ├── architecture.md
│   ├── api.md
│   └── domains/
│       ├── cosmetics.md
│       ├── healthcare.md
│       └── retail.md
├── scripts/
│   ├── create_new_domain.py
│   └── setup_environment.sh
├── config/                      # Arquivos de configuração
│   ├── .env                   # Variáveis de ambiente principais
│   ├── .env.chatwoot.example  # Exemplo de configuração do Chatwoot
│   ├── docker-compose.yml     # Configuração do Docker Compose
│   ├── docker-stack.yml       # Configuração do Docker Stack
│   ├── docker-swarm.yml       # Configuração do Docker Swarm
│   ├── Dockerfile             # Dockerfile principal
│   └── Dockerfile.api         # Dockerfile para a API
├── docs/                      # Documentação
│   ├── index.md               # Índice da documentação
│   ├── webhook_integration.md # Documentação da integração de webhook
│   ├── busca_hibrida.md       # Documentação da busca híbrida
│   └── archive/               # Documentação arquivada
├── scripts/                   # Scripts utilitários
│   ├── webhook/               # Scripts relacionados a webhook
│   ├── development/           # Scripts de desenvolvimento
│   ├── deployment/            # Scripts de implantação
│   └── utils/                 # Scripts utilitários diversos
├── src/                       # Código-fonte principal
│   ├── main.py
│   ├── agents/                # Agentes de IA
│   │   ├── channel_agents.py
│   │   ├── functional_agents.py
│   │   └── adaptable/
│   │       ├── adaptable_agent.py
│   │       ├── sales_agent.py
│   │       ├── support_agent.py
│   │       └── scheduling_agent.py
│   ├── api/                   # Integrações de API
│   │   ├── chatwoot_client.py
│   │   ├── webhook_server.py
│   │   ├── erp/
│   │   │   └── odoo/
│   │   │       ├── client.py
│   │   │       └── conversation_context.py
│   │   └── odoo_simulation.py
│   ├── config/                # Configurações e domínios de negócio
│   │   ├── config.py
│   │   └── business_domains/
│   │       ├── cosmetics.yaml
│   │       ├── healthcare.yaml
│   │       └── retail.yaml
│   ├── core/                  # Componentes principais
│   │   ├── hub.py             # Agentes do hub central (orquestrador, gerenciador de contexto, integração)
│   │   ├── cache/
│   │   │   ├── cache_manager.py
│   │   │   └── redis_client.py
│   │   └── domain/
│   │       ├── domain_loader.py
│   │       └── domain_manager.py
│   ├── plugins/               # Sistema de plugins
│   │   ├── base/
│   │   │   ├── base_plugin.py
│   │   │   └── plugin_interface.py
│   │   ├── plugin_manager.py
│   │   └── cosmetics/
│   │       ├── product_recommendation.py
│   │       └── treatment_scheduler.py
│   └── tools/                 # Ferramentas utilitárias
│       ├── vector_tools.py
│       └── nlp_tools.py
├── webhook/                   # Implementações de webhook
│   ├── simple_webhook.py      # Implementação atual do servidor webhook
│   └── README.md              # Documentação do webhook
```

## Exemplos de Agentes

### Agente de Vendas

```python
class SalesAgent(AdaptableAgent):
    """Agente especializado em vendas e recomendação de produtos"""
    
    def get_agent_type(self) -> str:
        return "sales"
    
    def process_product_inquiry(self, product_query: str, customer_id: str = None) -> Dict[str, Any]:
        """Processa uma consulta sobre produtos"""
        # Implementação adaptável ao domínio de negócio
```

### Agente de Suporte

```python
class SupportAgent(AdaptableAgent):
    """Agente especializado em suporte e resolução de problemas"""
    
    def get_agent_type(self) -> str:
        return "support"
    
    def process_support_query(self, query: str, customer_id: str = None) -> Dict[str, Any]:
        """Processa uma consulta de suporte"""
        # Implementação adaptável ao domínio de negócio
```

### Agente de Agendamento

```python
class SchedulingAgent(AdaptableAgent):
    """Agente especializado em agendamentos e horários"""
    
    def get_agent_type(self) -> str:
        return "scheduling"
    
    def get_available_slots(self, service_id: str, date_from: str = None, date_to: str = None) -> List[Dict[str, Any]]:
        """Obtém os horários disponíveis para um serviço"""
        # Implementação adaptável ao domínio de negócio
```

## Sistema de Memória Compartilhada

```python
class SharedMemory:
    """Sistema de memória compartilhada entre crews"""
    def __init__(self, redis_client):
        self.redis = redis_client
    
    def store(self, key, value, ttl=3600):
        """Armazena um valor na memória compartilhada"""
        self.redis.set(key, json.dumps(value), ex=ttl)
    
    def retrieve(self, key):
        """Recupera um valor da memória compartilhada"""
        value = self.redis.get(key)
        return json.loads(value) if value else None
```

## Estrutura do Projeto

O projeto está organizado da seguinte forma:

- **config/**: Contém arquivos de configuração, incluindo variáveis de ambiente, Dockerfiles e arquivos de configuração do Docker.
- **docs/**: Contém a documentação do projeto, incluindo a documentação da integração de webhook e da busca híbrida.
- **scripts/**: Contém scripts utilitários para desenvolvimento, implantação e manutenção.
- **src/**: Contém o código-fonte principal do projeto, incluindo agentes, API, configurações e ferramentas.
- **webhook/**: Contém implementações de webhook para integração com o Chatwoot.

## Guia de Início Rápido

### Requisitos

- Docker e Docker Compose
- Python 3.9+
- Chatwoot instalado e configurado

### Instalação

1. Clone o repositório
2. Configure as variáveis de ambiente em `config/.env`
3. Execute o script de configuração do ambiente de desenvolvimento:

```bash
bash scripts/development/setup_dev_environment.sh
```

4. Inicie o serviço com Docker Compose:

```bash
docker-compose -f config/docker-compose.yml up -d
```

### Configuração do Webhook

Para configurar a integração de webhook com o Chatwoot, siga as instruções em [docs/webhook_integration.md](docs/webhook_integration.md).

## Contribuição

Contribuições são bem-vindas! Por favor, siga estas etapas:

1. Fork o repositório
2. Crie um branch para sua feature (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova feature'`)
4. Push para o branch (`git push origin feature/nova-feature`)
5. Crie um Pull Request

## Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo LICENSE para detalhes.

## Contato

Para mais informações, entre em contato através de [email@exemplo.com](mailto:email@exemplo.com).
