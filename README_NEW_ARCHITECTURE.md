# Nova Arquitetura do Sistema ChatwootAI

## Visão Geral

O ChatwootAI é um sistema avançado de atendimento ao cliente e integração com ERPs que combina:

1. **Chatwoot** como hub central de mensagens para atendimento ao cliente
2. **CrewAI** como framework para orquestração de agentes inteligentes
3. **MCP (Model Context Protocol)** como camada de abstração para comunicação com diferentes ERPs
4. **Qdrant** como banco de dados vetorial para busca semântica
5. **Redis** como cache distribuído, persistência de crews e gerenciamento de estado

O sistema é projetado para ser **multi-tenant**, adaptando-se a diferentes domínios de negócio (móveis, cosméticos, saúde, etc.) através de configurações YAML, com foco no **account_id** como identificador principal.

## Princípios Arquiteturais Fundamentais

1. **Foco no Account_ID**: O account_id é o identificador principal, com o domínio sendo apenas uma organização de pastas
2. **Simplificação do Fluxo**: Direcionamento direto para crews específicas com base na origem da mensagem
3. **Acesso a Dados via MCP**: Substituição do DataServiceHub por integração direta com MCP-Odoo
4. **Configuração por Account_ID**: Cada account_id possui dois arquivos YAML: config.yaml (configurações) e credentials.yaml (credenciais)
5. **Processamento Paralelo**: Agentes dentro de cada crew trabalham em paralelo para reduzir latência
6. **Persistência e Cache com Redis**: Utilização do Redis para persistência de crews, cache de consultas e otimização de desempenho
7. **Busca Híbrida**: Combinação de busca semântica (Qdrant) e relacional (Odoo) para resultados precisos e atualizados
8. **Separação de Responsabilidades**: Interfaces claras entre componentes para facilitar manutenção e extensão

## Arquitetura do Sistema

```
┌─────────────┐     ┌───────────────────────────────────────────────────┐
│             │     │                                                   │
│  Cliente    │────►│                 Servidor Unificado               │
│  (Chatwoot) │     │                    (main.py)                     │
│             │     │                                                   │
└─────────────┘     │  ┌───────────────┐          ┌───────────────┐    │
                    │  │               │          │               │    │
┌─────────────┐     │  │   Webhook     │          │   API REST    │    │
│             │     │  │   Handler     │          │   (Odoo)      │    │
│  Módulo     │────►│  │ (/webhook)    │          │ (/api/v1)     │    │
│  Odoo       │     │  │               │          │               │    │
│             │     │  └───────┬───────┘          └───────┬───────┘    │
└─────────────┘     └──────────┼──────────────────────────┼────────────┘
                               │                          │
                               │                          │
                               ▼                          ▼
                    ┌───────────────┐
                    │               │
                    │     Hub       │────────► Direcionamento direto para
                    │   (hub.py)    │          crews específicas com base
                    │               │          na origem da mensagem
                    └───────┬───────┘
                            │
                            │
                            ▼
                    ┌───────────────────────────────────────────┐
                    │                                           │
                    │           Customer Service Crew           │
                    │                                           │
                    │  ┌─────────────┐  ┌─────────────────┐    │
                    │  │ Agente de   │  │ Agente de       │    │
                    │  │ Intenção    │  │ Vendas          │    │
                    │  └─────────────┘  └─────────────────┘    │
                    │                                           │
                    │  ┌─────────────┐  ┌─────────────────┐    │
                    │  │ Agente de   │  │ Agente de       │    │
                    │  │ Suporte     │  │ Agendamento     │    │
                    │  └─────────────┘  └─────────────────┘    │
                    │                                           │
                    │  ┌─────────────┐  ┌─────────────────┐    │
                    │  │ Agente de   │  │ Agente          │    │
                    │  │ Dados       │  │ Finalizador     │    │
                    │  └─────────────┘  └─────────────────┘    │
                    │                                           │
                    └───────────────────┬───────────────────────┘
                                        │
                                        │
                                        ▼
                    ┌───────────────┐     ┌─────────────┐
                    │               │     │             │
                    │   MCP-Odoo    │────►│    Odoo     │
                    │               │     │    ERP      │
                    │               │     │             │
                    └───────┬───────┘     └─────────────┘
                            │
                            │
                            ▼
                    ┌───────────────┐     ┌─────────────┐
                    │               │     │             │
                    │   Serviço de  │────►│   Qdrant    │
                    │  Vetorização  │     │             │
                    │               │     │             │
                    └───────────────┘     └─────────────┘
```

## Componentes Principais

### 1. Pontos de Entrada

1. **Servidor Unificado (`main.py`)**
   - Ponto de entrada principal do sistema
   - Unifica o webhook do Chatwoot e a API Odoo em um único servidor
   - Direciona requisições para os componentes apropriados com base nos prefixos de rota
   - Implementa middlewares e eventos compartilhados
   - Fornece uma interface única para todos os serviços

2. **Webhook Handler (`src/webhook/webhook_handler.py`)**
   - Processa webhooks do Chatwoot para atendimento ao cliente
   - Processa eventos de sincronização de credenciais do módulo `ai_credentials_manager`
   - Extrai metadados (account_id, conversation_id, etc.)
   - Direciona para o Hub para processamento

3. **API REST para Odoo (`odoo_api/modules/*/routes.py`)**
   - Processa requisições dos módulos Odoo
   - Extrai metadados (account_id, action, etc.)
   - Direciona para o processamento apropriado

### 2. Hub Simplificado (`src/core/hub.py`)

- **Responsabilidade**: Identificar o account_id/domínio e direcionar para a crew apropriada
- **Nova Abordagem**: Direcionamento direto para crews específicas com base na origem da mensagem
- **Funcionalidades**:
  - Validar o account_id contra os YAMLs existentes
  - Carregar configurações específicas do account_id
  - Direcionar a mensagem diretamente para a crew apropriada (ex: mensagens do Chatwoot vão para customer_service_crew)
  - Obter ou criar a crew apropriada
  - Gerenciar o ciclo de vida das conversações

### 3. Customer Service Crew

A nova abordagem centraliza o processamento em uma única crew para atendimento ao cliente, com agentes especializados trabalhando em paralelo:

- **Agente de Identificação de Intenção**: Analisa a mensagem e identifica a intenção do usuário
- **Agentes Funcionais**: Especialistas em diferentes áreas (vendas, suporte, agendamento, regras de negócio)
- **Agente de Dados**: Especializado em operações com dados, acessando o MCP-Odoo
- **Agente Finalizador**: Agrega as informações e envia a resposta diretamente ao usuário

Cada agente tem suas próprias ferramentas de acesso ao banco vetorial Qdrant para extrair informações relevantes ao momento do atendimento.

### 4. MCP-Odoo (`@mcp-odoo/`)

- **Responsabilidade**: Fornecer interface padronizada para o Odoo
- **Componentes**:
  - **OdooClient**: Cliente para comunicação com o Odoo via XML-RPC
  - **FastMCP Server**: Servidor que expõe ferramentas para interação com o Odoo
- **Funcionalidades**:
  - Expor métodos para consultar produtos, clientes, vendas, etc.
  - Implementar operações de negócio específicas do Odoo
  - Abstrair a complexidade do Odoo para os agentes de IA
  - Gerenciar conexões com o Odoo
  - Fornecer ferramentas para vendas, calendário, produtos, clientes, estoque, preços e pagamentos

### 5. Serviço de Vetorização

- **Responsabilidade**: Gerenciar embeddings e busca semântica
- **Funcionalidades**:
  - Gerar embeddings para descrições de produtos e regras de negócio
  - Armazenar embeddings no Qdrant
  - Fornecer busca semântica para produtos e regras
  - Implementar busca híbrida (BM42 ou BM25)
  - Manter persistência de regras de negócio para busca semântica

## Configuração via YAML

A nova abordagem utiliza dois arquivos YAML separados para cada account_id:

### 1. `config.yaml`

Cada cliente terá seus proprios arquivos yaml com a principal diferenciação o account_id. O arquivo de config.yaml contem configurações gerais, informações da empresa e comportamento dos agentes:

```yaml
account_id: account_1
company_metadata:
  business_hours:
    days: [0, 1, 2, 3, 4, 5, 6]
    end_time: '18:00'
    has_lunch_break: true
    lunch_break_end: '13:00'
    lunch_break_start: '12:00'
    start_time: 09:00
  company_info:
    business_area: retail
    company_name: Sandra Cosméticos
    description: Testando 123
  customer_service:
    communication_style: friendly
    emoji_usage: moderate
    greeting_message: Olá, testando 123
integrations:
  facebook:
    access_token_ref: fb_token_account_1
    app_id: '12345678910'
    app_secret_ref: fb_secret_account_1
  mcp:
    config:
      credential_ref: account_1-00bfe67a
      db: account_1
      url: http://localhost:8069
      username: giovano@sprintia.com.br
    type: odoo-mcp
  qdrant:
    collection: business_rules_account_1
  redis:
    prefix: account_1
name: Sandra Cosméticos
```

### 2. `credentials.yaml`

Contém credenciais sensíveis, armazenadas de forma criptografada:

```yaml
account_id: account_1
credentials:
  account_1-00bfe67a: ENC:Z0FBQUFBQm9DdEdFZHh0cXN0cXVHQXRfUEVNQ3FBY1BuaVpROUFyM2dEMnV2MlJDbDNMQUhuZnhZeUREU28zczQ4M3haS2pMRnR0bThoN1FabUp3NHRBSC1XN3dYWWN2blE9PQ==
  fb_secret_account_1: ENC:Z0FBQUFBQm9DdEdFbjM4M1AyQXMyZ0x2cjcyUHExRVpkS19TVUkzVENoOE8zalBzNXBfZnBzVXJKcnVjOFN5b1YtcTA2UHFCalNfcjA0OHVGVm11b28zRnh6bkpTLWdiREE9PQ==
  fb_token_account_1: ENC:Z0FBQUFBQm9DdEdFeE1iSFp6UDVEVmh4aXdvWWsyNGpTLUtRdHhheVdTeEFGTmo3X25OSmtQdXBCYThWUUVvdGRQY1VpR18xNmp6Sm9rLXk3ZzdHSUZTakpzNU5PRXduaVE9PQ==
```

## Fluxos de Trabalho

### 1. Atendimento ao Cliente (Chatwoot → Sistema)

1. **Entrada da Mensagem e Identificação do Account_ID**
   - Cliente envia mensagem pelo WhatsApp ou outro canal
   - Chatwoot recebe a mensagem e a encaminha via webhook para o sistema
   - O webhook_handler processa a requisição e extrai o account_id

2. **Processamento pelo Hub Simplificado**
   - A mensagem é encaminhada para o Hub
   - O Hub identifica que a mensagem vem do Chatwoot e a direciona diretamente para a customer_service_crew
   - O Hub carrega a configuração do account_id do arquivo config.yaml
   - O Hub obtém ou cria a customer_service_crew (usando cache Redis se disponível)

3. **Processamento pela Customer Service Crew**
   - O agente de identificação de intenção analisa a mensagem
   - Os agentes funcionais relevantes (vendas, suporte, etc.) são acionados em paralelo
   - O agente de dados acessa o MCP-Odoo para obter informações relevantes
   - Os agentes realizam busca semântica no Qdrant para encontrar regras de negócio relevantes
   - O agente finalizador agrega as informações e gera uma resposta personalizada

4. **Retorno da Resposta**
   - O agente finalizador envia a resposta diretamente ao Chatwoot
   - O Chatwoot entrega a resposta ao cliente via canal original

### 2. Integração com MCP (Model Context Protocol)

O MCP é um protocolo aberto que padroniza como aplicações de IA interagem com dados e serviços externos:

1. **Acesso a Dados via MCP-Odoo**
   - Os agentes na customer_service_crew acessam dados do Odoo através do MCP-Odoo
   - O MCP-Odoo traduz as solicitações em chamadas XML-RPC para o Odoo
   - Os resultados são retornados em um formato padronizado para os agentes

2. **Vantagens do MCP**
   - Interface padronizada para diferentes ERPs
   - Abstração da complexidade dos sistemas externos
   - Facilidade de integração com novos sistemas
   - Redução do acoplamento entre componentes

## Busca Híbrida

O sistema implementa uma estratégia de busca híbrida, combinando:

1. **Busca Vetorial Densa** (Qdrant): Encontra produtos com base na similaridade semântica
2. **Busca Vetorial Esparsa** (BM25) ou BM42: Encontra produtos com base em correspondência de palavras-chave
3. **Busca Relacional** (Odoo): Verifica disponibilidade, preço e outras informações estruturadas

Esta abordagem oferece resultados mais precisos e relevantes, combinando o melhor da busca semântica e da busca por palavras-chave.

## Otimizações de Performance

Para reduzir a latência e melhorar a experiência do usuário, o sistema implementa:

1. **Processamento Paralelo**: Agentes dentro da crew trabalham em paralelo
2. **Cache com Redis**: Armazena resultados de consultas frequentes, embeddings e configurações
3. **Resposta Direta**: O agente finalizador envia a resposta diretamente ao usuário
4. **Simplificação do Fluxo**: Direcionamento direto para a crew apropriada com base na origem da mensagem

## Mapeamento de Canais e Multi-Tenancy

### Configuração de Empresas via Odoo

A nova arquitetura permite a configuração completa de novas empresas (tenants) diretamente através do módulo Odoo, sem necessidade de intervenção manual nos arquivos do sistema de IA:

1. **Módulo `ai_credentials_manager`**
   - Gerencia credenciais e configurações para cada tenant
   - Permite criar e configurar novos tenants (account_id) diretamente pela interface do Odoo
   - Sincroniza automaticamente as configurações com o sistema de IA via webhook

2. **Mapeamento de Canais do Chatwoot**
   - Novo recurso que mapeia IDs de conta e caixa de entrada do Chatwoot para account_id interno e domínio
   - Configurado diretamente na interface do Odoo
   - Permite que diferentes contas/caixas de entrada do Chatwoot sejam mapeadas para diferentes tenants

3. **Fluxo de Criação de Novo Tenant**
   1. Administrador cria nova credencial no módulo `ai_credentials_manager` com um account_id único (ex: "account_2")
   2. Configura os detalhes da empresa, credenciais e preferências
   3. Configura o mapeamento de canais para associar IDs do Chatwoot ao novo account_id
   4. Clica em "Sincronizar com Sistema de IA"
   5. O sistema automaticamente:
      - Cria os arquivos YAML de configuração e credenciais
      - Atualiza o arquivo de mapeamento de canais
      - Configura as coleções no Qdrant
      - Prepara o Redis para o novo tenant

### Fluxo de Processamento de Mensagens

Quando uma mensagem chega do Chatwoot, o sistema:

1. **Identificação do Tenant**
   - Extrai o account_id e inbox_id do webhook do Chatwoot
   - Consulta o arquivo `chatwoot_mapping.yaml` para determinar:
     - O domínio associado (ex: "retail", "healthcare")
     - O account_id interno (ex: "account_1", "account_2")

2. **Carregamento de Configuração**
   - Carrega os arquivos YAML específicos do tenant:
     - `config/domains/[domain]/[account_id]/config.yaml`
     - `config/domains/[domain]/[account_id]/credentials.yaml`

3. **Direcionamento para Crew**
   - Direciona a mensagem para a customer_service_crew podendo ser WHatsAppapropriada
   - Fornece o contexto completo: domínio, account_id, configurações e credenciais

4. **Processamento e Resposta**
   - A crew processa a mensagem no contexto do tenant específico
   - Acessa dados específicos do tenant via MCP-Odoo
   - Retorna a resposta ao Chatwoot

Este fluxo garante completo isolamento entre tenants, permitindo que o sistema atenda múltiplas empresas simultaneamente, cada uma com suas próprias configurações, regras de negócio e dados.

## Estado Atual e Próximos Passos

### Componentes Implementados

- [x] Módulo `business_rules`: Vetorização de regras de negócio
- [x] Módulo `ai_credentials_manager`: Gerenciamento de credenciais
- [x] Configuração via YAML: Arquivos config.yaml e credentials.yaml
- [x] MCP-Odoo: Camada de abstração para o Odoo
- [x] Mapeamento de Canais: Associação de IDs do Chatwoot a account_id interno e domínio

### Próximos Passos

1. **Implementar a Customer Service Crew**
   - Desenvolver os agentes especializados (intenção, vendas, suporte, etc.)
   - Implementar o processamento paralelo
   - Integrar com o MCP-Odoo
   - Resolver o erro atual na criação da crew: `expected str, bytes or os.PathLike object, not NoneType`

2. **Implementar Segurança do Webhook**
   - Adicionar validação de assinatura HMAC para webhooks do Chatwoot
   - Implementar verificação de token para todas as requisições
   - Adicionar rate limiting para prevenir abusos

3. **Simplificar o Hub**
   - Remover a lógica de análise de intenção
   - Implementar o direcionamento direto para crews específicas
   - Otimizar o carregamento de configurações

4. **Otimizar a Busca Híbrida**
   - Definir a abordagem final (BM42 ou BM25)
   - Implementar cache de resultados
   - Otimizar a combinação de resultados

5. **Expandir o MCP-Odoo**
   - Adicionar mais ferramentas para interação com o Odoo
   - Implementar cache de resultados
   - Otimizar o desempenho das consultas
