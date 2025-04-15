# Arquitetura do Sistema ChatwootAI

## Visão Geral

O ChatwootAI é um sistema avançado de atendimento ao cliente e integração com ERPs que combina:

1. **Chatwoot** como hub central de mensagens para atendimento ao cliente
2. **CrewAI** como framework para orquestração de agentes inteligentes
3. **MCP (Multi-Client Protocol)** como camada de abstração para comunicação com diferentes ERPs
4. **Qdrant** como banco de dados vetorial para busca semântica
5. **Redis** como cache distribuído, persistência de crews e gerenciamento de estado

O sistema é projetado para ser **multi-tenant**, adaptando-se dinamicamente a diferentes domínios de negócio (móveis, cosméticos, saúde, etc.) através de configurações YAML, com foco no **account_id** como identificador principal.

Uma característica fundamental do sistema é sua **flexibilidade de integração com ERPs**, podendo funcionar tanto como um ERP completo (com Odoo) quanto como uma plataforma que se integra a ERPs existentes dos clientes.

## Princípios Arquiteturais Fundamentais

1. **Foco no Account_ID**: O account_id é o identificador principal, com o domínio sendo apenas uma organização de pastas
2. **Simplificação do Fluxo**: Arquitetura hub-and-spoke com o Hub como orquestrador central
3. **Centralização do Acesso a Dados**: Todo acesso a dados passa obrigatoriamente pelo DataProxyAgent
4. **Conexão Direta com ERPs**: Utilização do MCP (Model Context Protocol) para acesso padronizado aos ERPs
5. **Configuração por Account_ID**: Cada account_id possui seu próprio arquivo YAML com todas as configurações necessárias
6. **Múltiplas Crews Especializadas**: Cada account_id pode ter múltiplas crews para diferentes funções (atendimento, produtos, marketing) ainda precisamos definir como o sistema identificará as diferentes crews. Meu palpite é que integremos ao webhook_handler metodos de identificação de crews e que o hub.py direcione à crew correta com base nos metadados recebidos
7. **Persistência e Cache com Redis**: Utilização do Redis para persistência de crews, cache de consultas e otimização de desempenho
8. **Busca Híbrida (BM42)**: Combinação de busca semântica (Qdrant) e relacional (Odoo) para resultados precisos e atualizados
9. **Separação de Responsabilidades**: Interfaces claras entre componentes para facilitar manutenção e extensão

## Arquitetura do Sistema

```
┌─────────────┐     ┌───────────────┐     ┌───────────────┐     ┌─────────────────┐
│             │     │               │     │               │     │                 │
│  Cliente    │────►│   Webhook     │────►│     Hub       │────►│  Customer       │
│  (Chatwoot) │     │   Handler     │     │               │     │  Service Crew   │
│             │     │               │     │               │     │                 │
└─────────────┘     └───────────────┘     └───────┬───────┘     └─────────────────┘
                                                  │
┌─────────────┐     ┌───────────────┐             │             ┌─────────────────┐
│             │     │               │             │             │                 │
│  Módulo     │────►│   API REST    │─────────────┼────────────►│  Product        │
│  Odoo       │     │   (Entrada)   │             │             │  Management Crew│
│             │     │               │             │             │                 │
└─────────────┘     └───────────────┘             │             └─────────────────┘
                                                  │
                                                  │             ┌─────────────────┐
                                                  │             │                 │
                                                  └────────────►│  Social Media   │
                                                                │  Crew           │
                                                                │                 │
                                                                └─────────────────┘
                                                                        │
                    ┌───────────────┐     ┌─────────────┐               │
                    │               │     │             │               │
                    │  DataProxy    │◄───►│  MCP-Odoo   │◄──────────────┘
                    │  Agent        │     │  (Saída)    │
                    │               │     │             │
                    └───────┬───────┘     └──────┬──────┘
                            │                    │
                            │                    │
                            ▼                    ▼
┌───────────────┐    ┌───────────────┐     ┌─────────────┐
│               │    │               │     │             │
│   RabbitMQ    │◄──►│   Serviço de  │     │    Odoo     │
│   Message     │    │  Vetorização  │     │    ERP      │
│   Queue       │    │  (OpenAI API) │     │             │
└───────────────┘    └───────┬───────┘     └─────────────┘
                             │
                             ▼
                    ┌───────────────┐
                    │    Qdrant     │
                    │  Busca Híbrida│
                    │  (Densa+Esparsa)│
                    └───────────────┘
```

### Componentes Principais

#### 1. Pontos de Entrada

1. **Webhook Handler (`src/webhook/webhook_handler.py`)**
   - Processa webhooks do Chatwoot para atendimento ao cliente
   - Processa eventos de sincronização de credenciais do módulo `ai_credentials_manager`
   - Extrai metadados (account_id, conversation_id, etc.)
   - Direciona para o Hub para processamento

2. **API REST para Odoo (`odoo_api/main.py`)**
   - Processa requisições dos módulos Odoo
   - Extrai metadados (account_id, action, etc.)
   - Direciona para o processamento apropriado
   - Processa requisições do módulo Odoo
   - Extrai metadados (account_id, action, etc.)
   - Direciona para o Hub para processamento

#### 2. Hub Central (`src/core/hub.py`)

- **Responsabilidade**: Identificar o account_id/domínio e direcionar para a crew apropriada
- **Funcionalidades**:
  - Validar o account_id contra os YAMLs existentes
  - Carregar configurações específicas do account_id
  - Determinar qual crew deve processar a requisição
  - Obter ou criar a crew apropriada (a geração de crew ocorre apenas na primeira execução do sistema, pós isso, as configurações são salvas em REDIS)
  - Direcionar a requisição para processamento
  - Gerenciar o ciclo de vida das conversações
  - Centralizar o acesso aos serviços de dados através do DataProxyAgent

#### 3. Crews Especializadas

Cada account_id pode ter múltiplas crews especializadas para diferentes funções:

1. **Customer Service Crew**
   - Processa mensagens de clientes via Chatwoot
   - Responde a perguntas sobre produtos, pedidos, etc.
   - Gerencia o fluxo de conversação com clientes

2. **Product Management Crew** Ainda não implementado
   - Gerencia descrições de produtos através do módulo `semantic_product_description`
   - Sincroniza produtos com o banco de dados vetorial usando o módulo `product_ai_mass_management`
   - Processa buscas semânticas de produtos com o sistema híbrido BM42
   - Gera descrições otimizadas para produtos usando agentes especializados

3. **Social Media Crew** Ainda não implementado
   - Gera conteúdo para redes sociais
   - Analisa engajamento em redes sociais
   - Gerencia campanhas de marketing

4. **Marketplace Crew** Ainda não implementado
   - Gerencia integração com marketplaces (Mercado Livre, etc.)
   - Sincroniza produtos com marketplaces
   - Processa pedidos de marketplaces

5. **Analytics Crew** Ainda não implementado
   - Analisa dados de vendas, clientes, etc.
   - Gera relatórios e insights
   - Fornece recomendações baseadas em dados

#### 4. DataProxyAgent (`src/core/data_proxy_agent.py`)

- **Responsabilidade**: Centralizar o acesso a dados de diferentes fontes
- **Funcionalidades**:
  - Interface unificada para acesso a dados
  - Adaptação de consultas ao account_id ativo
  - Roteamento para o MCP apropriado - a principio, apenas o mcp do Odoo
  - Formatação e filtragem de resultados

#### 5. MCP-Odoo (`src/mcp_odoo/`)

- **Responsabilidade**: Fornecer interface padronizada para o Odoo
- **Componentes**:
  - **OdooClient (`odoo_client.py`)**: Cliente para comunicação com o Odoo via XML-RPC
  - **FastMCP Server (`server.py`)**: Servidor que expor ferramentas para interação com o Odoo
- **Funcionalidades**:
  - Expor métodos para consultar produtos, clientes, vendas, etc.
  - Implementar operações de negócio específicas do Odoo
  - Abstrair a complexidade do Odoo para os agentes de IA
  - Gerenciar conexões com o Odoo
  - Fornecer ferramentas para vendas, calendário, produtos, clientes, estoque, preços e pagamentos
- **Integração com DataProxyAgent**:
  - O DataProxyAgent usa o MCP-Odoo para acessar dados do Odoo
  - Fornece uma interface consistente para os agentes de IA
  - Centraliza o acesso a dados, implementando cache e otimizações

#### 6. Serviço de Vetorização (`odoo_api/services/vector_service.py`)

- **Responsabilidade**: Gerenciar embeddings e busca semântica
- **Funcionalidades**:
  - Gerar embeddings para descrições de produtos e regras de negócio
  - Armazenar embeddings no Qdrant
  - Fornecer busca semântica para produtos e regras
  - Implementar busca híbrida (BM42)
  - Manter persistência de regras de negócio para busca semântica

##### Integração com OpenAI

O serviço de vetorização utiliza a API da OpenAI para gerar embeddings de alta qualidade:

- **Modelos Utilizados**:
  - **GPT4o-mini**: Para o agente de embedding, oferecendo instruções detalhadas sobre como gerar descrições
  - **Modelo de Embedding da OpenAI**: Para geração de vetores densos de forma eficiente

- **Agentes de Embedding Especializados**:
  - Cada módulo (business_rules, product_ai_mass_management, semantic_product_description) possui seu próprio agente de embedding especializado e estão em odoo_api/embbeding_agents
  - Os agentes são treinados para extrair informações relevantes para cada domínio específico

- **Otimização de Custos**:
  - Cache de embeddings para evitar geração repetida
  - Processamento em lote para reduzir o número de chamadas à API
  - Reutilização de embeddings quando possível

- **Fluxo de Processamento**:
  1. Dados brutos são extraídos do Odoo (produtos, regras, etc.)
  2. O agente de embedding processa os dados e gera descrições otimizadas
  3. As descrições são convertidas em vetores usando o modelo de embedding
  4. Os vetores são armazenados no Qdrant com metadados relevantes
  5. O sistema de busca híbrida combina busca vetorial e relacional

#### 7. Gerenciamento de Domínios (`src/core/domain/`)

- **Responsabilidade**: Gerenciar configurações de domínios e account_ids
- **Funcionalidades**:
  - Carregamento de configurações YAML
  - Mapeamento de account_ids para domínios
  - Validação de configurações
  - Cache de configurações com Redis

#### 8. Agentes de Embedding (`odoo_api/embedding_agents/`)

- **Responsabilidade**: Gerar descrições otimizadas e embeddings para diferentes tipos de dados
- **Componentes**:
  - **business_rules_agent.py**: Especializado em processar regras de negócio
  - **product_description_agent.py**: Especializado em gerar descrições de produtos
  - **product_mass_agent.py**: Especializado em processamento em lote de produtos
- **Funcionalidades**:
  - Recebem dados brutos dos módulos Odoo
  - Aplicam instruções específicas para cada tipo de conteúdo
  - Geram descrições otimizadas para busca semântica
  - Interagem com o serviço de vetorização para gerar embeddings
  - Implementam cache para evitar processamento redundante
- **Fluxo de Trabalho**:
  1. Módulo Odoo envia dados para a API REST
  2. API direciona para o agente de embedding apropriado
  3. Agente processa os dados e gera descrições otimizadas
  4. Serviço de vetorização converte descrições em embeddings
  5. Embeddings são armazenados no Qdrant com metadados relevantes

#### 9. Gerenciamento de Credenciais

- **Responsabilidade**: Gerenciar credenciais de forma segura para integrações externas
- **Componentes**:
  - **Módulo Odoo `ai_credentials_manager`**: Armazena e gerencia credenciais no Odoo
  - **Webhook de Credenciais**: Implementado no `webhook_handler.py`, recebe e processa credenciais do módulo Odoo
  - **Sistema de Referências**: Armazena apenas referências a credenciais sensíveis nos arquivos YAML
  - **API de Credenciais**: Endpoint seguro para recuperar credenciais usando referências
- **Funcionalidades**:
  - Armazenamento seguro de credenciais sensíveis (senhas, tokens, chaves de API)
  - Sincronização de credenciais entre o Odoo e o sistema de IA
  - Verificação de token para autenticação de requisições
  - Mesclagem inteligente de configurações para preservar estrutura existente
  - Gerenciamento centralizado de credenciais para todas as integrações (Odoo, Facebook, Instagram, Mercado Livre, etc.)
  - Registro detalhado de todos os acessos às credenciais para auditoria
  - Criptografia de campos sensíveis no banco de dados Odoo
- **Fluxo de Dados**:
  1. Credenciais são configuradas no módulo Odoo `ai_credentials_manager`
  2. O módulo envia as credenciais para o webhook com um token de autenticação
  3. O webhook verifica o token e processa as credenciais
  4. Credenciais sensíveis são substituídas por referências no arquivo YAML
  5. Agentes de IA usam as referências para solicitar credenciais reais quando necessário

##### Sistema de Referências para Credenciais

O sistema implementa uma abordagem de segurança que evita o armazenamento de credenciais sensíveis diretamente nos arquivos de configuração. Esta abordagem é implementada pelo módulo `ai_credentials_manager` e pelo webhook handler:

```yaml
# Exemplo de configuração com referências
integrations:
  mcp:
    type: "odoo-mcp"
    config:
      url: "http://localhost:8069"
      db: "account_1"
      username: "admin"
      credential_ref: "a1b2c3d4-e5f6-g7h8-i9j0"  # Referência, não a senha real
  facebook:
    app_id: "123456789"
    app_secret_ref: "fb_secret_account_1"  # Referência, não o segredo real
    access_token_ref: "fb_token_account_1"  # Referência, não o token real
```

As credenciais reais são armazenadas em um arquivo separado (`credentials.yaml`) que não é versionado:

```yaml
account_1:
  a1b2c3d4-e5f6-g7h8-i9j0: "senha_real_do_odoo"
  fb_secret_account_1: "segredo_real_do_facebook"
  fb_token_account_1: "token_real_do_facebook"
```

##### Integração com Módulos Odoo

Os módulos Odoo (`business_rules`, `semantic_product_description` e `product_ai_mass_management`) foram atualizados para usar o `ai_credentials_manager` para obter credenciais de forma segura:

1. Verificam se o módulo `ai_credentials_manager` está instalado
2. Obtêm credenciais do módulo se disponível
3. Usam fallback para parâmetros do sistema se o módulo não estiver disponível
4. Registram todos os acessos às credenciais para auditoria

##### Implementação de Segurança no Módulo ai_credentials_manager

O módulo `ai_credentials_manager` implementa várias camadas de segurança:

1. **Acesso Restrito**: Apenas administradores do sistema têm acesso ao módulo
2. **Criptografia de Dados**: Campos sensíveis como senhas e tokens são armazenados criptografados
3. **Auditoria Completa**: Todas as operações são registradas em logs detalhados
4. **Verificação de Token**: Todas as requisições de sincronização são autenticadas com token
5. **Mesclagem Inteligente**: Preserva a estrutura existente dos arquivos YAML durante atualizações

O módulo também suporta integrações com múltiplas plataformas externas:

- **Redes Sociais**: Facebook, Instagram, Twitter
- **Marketplaces**: Mercado Livre, Amazon, Shopee
- **Serviços de Mensagens**: WhatsApp Business, Telegram

## Fluxos de Trabalho

### 1. Atendimento ao Cliente (Chatwoot → Sistema)

1. **Entrada da Mensagem e Identificação do Account_ID**
   - Cliente envia mensagem pelo WhatsApp ou outro canal
   - Chatwoot recebe a mensagem e a encaminha via webhook para o sistema
   - O `webhook_handler.py` processa a requisição e extrai o account_id
   - O account_id é usado para determinar qual configuração usar

2. **Processamento pelo Hub**
   - A mensagem é encaminhada para o `HubCrew`
   - O `HubCrew` carrega a configuração do account_id
   - O `HubCrew` determina que a mensagem deve ser processada pela Customer Service Crew
   - O `HubCrew` obtém ou cria a Customer Service Crew (usando cache Redis se disponível)

3. **Processamento pela Customer Service Crew**
   - A Customer Service Crew processa a mensagem
   - Os agentes da crew consultam dados via DataProxyAgent
   - O DataProxyAgent direciona as consultas para o MCP-Odoo
   - O MCP-Odoo consulta o Odoo e retorna os resultados
   - Os agentes realizam busca semântica de regras de negócio relevantes para a consulta
   - O sistema consulta o Qdrant para encontrar regras semanticamente similares à consulta
   - A Customer Service Crew gera uma resposta personalizada (considerando domínio, histórico e regras de negócio)

4. **Retorno da Resposta**
   - A resposta é enviada de volta ao `HubCrew`
   - O `HubCrew` a encaminha para o Chatwoot através do webhook_handler
   - O Chatwoot entrega a resposta ao cliente via canal original

### Otimizações no Fluxo de Processamento

O sistema implementa várias otimizações para melhorar o desempenho e a eficiência:

1. **Cache de Crews com Redis**
   - Crews são serializadas e armazenadas no Redis após a primeira criação
   - Requisições subsequentes recuperam a crew do cache, evitando o custo de inicialização
   - Reduz significativamente o tempo de resposta e o consumo de tokens

2. **Determinação Eficiente de Domínio**
   - O webhook_handler implementa uma hierarquia de fontes para determinar o domínio:
     * Primeiro verifica o mapeamento via account_id
     * Depois verifica o mapeamento via inbox_id
     * Por último, consulta a API do Chatwoot para metadados adicionais
   - Resultados são cacheados para evitar consultas repetidas

3. **Processamento Assíncrono**
   - O webhook_handler utiliza processamento assíncrono (async/await) para melhorar a capacidade de resposta
   - Permite que o sistema continue processando outras requisições enquanto aguarda respostas de serviços externos

4. **Centralização de Acesso a Dados**
   - Todo acesso a dados passa pelo DataProxyAgent, que implementa cache e otimizações
   - Evita consultas redundantes e reduz a carga nos sistemas externos

### 2. Geração de Descrição de Produto (Odoo → Sistema)

1. **Módulo Odoo envia requisição para a API REST**
   ```json
   {
     "metadata": {
       "source": "odoo",
       "account_id": "account_2",
       "action": "generate_description"
     },
     "params": {
       "product_id": 123
     }
   }
   ```

2. **Processamento pela API REST**
   - A API REST extrai o account_id e a ação
   - A requisição é encaminhada para o `HubCrew`

3. **Processamento pelo Hub**
   - O `HubCrew` carrega a configuração do account_id
   - O `HubCrew` determina que a requisição deve ser processada pelo Product Management Crew? Não sabemos disso
   - O `HubCrew` obtém ou cria a Product Management Crew??

4. **Processamento pela Product Management Crew**
   - A Product Management Crew processa a requisição
   - O agente de geração de conteúdo consulta metadados do produto via DataProxyAgent
   - O DataProxyAgent direciona a consulta para o MCP-Odoo
   - O MCP-Odoo consulta o Odoo e retorna os metadados
   - O agente de geração de conteúdo gera uma descrição para o produto

5. **Retorno da Resposta**
   - A descrição é enviada de volta ao `HubCrew`
   - O `HubCrew` a encaminha para a API REST
   - A API REST retorna a descrição para o módulo Odoo

### 3. Sincronização de Produto com Qdrant (Odoo → Sistema)

1. **Módulo Odoo envia requisição para a API REST**
   ```json
   {
     "metadata": {
       "source": "odoo",
       "account_id": "account_2",
       "action": "sync_product"
     },
     "params": {
       "product_id": 123,
       "description": "Descrição do produto..."
     }
   }
   ```

2. **Processamento pela API REST** no caso do modulo do modulo semantic_product_description
   - A API REST extrai o account_id e a ação
   - A requisição é encaminhada para o `HubCrew`

3. **Processamento pelo Hub**
   - O `HubCrew` carrega a configuração do account_id
   - O `HubCrew` determina que a requisição deve ser processada pela Product Management Crew
   - O `HubCrew` obtém ou cria a Product Management Crew

4. **Processamento pela Product Management Crew**
   - A Product Management Crew processa a requisição
   - O agente de sincronização consulta metadados adicionais do produto via DataProxyAgent
   - O DataProxyAgent direciona a consulta para o MCP-Odoo
   - O MCP-Odoo consulta o Odoo e retorna os metadados
   - O agente de sincronização envia a descrição e metadados para o Serviço de Vetorização
   - O Serviço de Vetorização gera embeddings e armazena no Qdrant

5. **Retorno da Resposta**
   - O ID do vetor é enviado de volta ao `HubCrew`
   - O `HubCrew` o encaminha para a API REST
   - A API REST retorna o ID do vetor para o módulo Odoo

## Configuração do Sistema

### Estrutura de Configuração

A estrutura de configuração foi atualizada para suportar múltiplas crews por account_id, permitindo maior flexibilidade e especialização:

```
/config
  /account_mapping.yaml    # Mapeamento de account_ids para domínios
  /credentials.yaml        # Armazena credenciais reais (não versionado)
  /domains
    /furniture             # Domínio (apenas uma organização de pastas)
      /account_1           # Diretório para o account_id 1
        /config.yaml       # Configuração geral para o account_id 1
        /support_crew.yaml # Configuração da crew de suporte
        /analytics_crew.yaml # Configuração da crew de analytics
      /account_2           # Diretório para o account_id 2
        /config.yaml       # Configuração geral para o account_id 2
        /support_crew.yaml # Configuração da crew de suporte
    /cosmetics             # Outro domínio
      /account_3           # Diretório para o account_id 3
        /config.yaml       # Configuração geral para o account_id 3
        /support_crew.yaml # Configuração da crew de suporte
        /sales_crew.yaml   # Configuração da crew de vendas
```

Esta estrutura permite:

1. **Configuração Granular**: Cada crew tem seu próprio arquivo de configuração
2. **Escalabilidade**: Novas crews podem ser adicionadas sem modificar configurações existentes
3. **Organização Clara**: Separação lógica por domínio e account_id
4. **Segurança Aprimorada**: Credenciais sensíveis são armazenadas separadamente



### Exemplo de Configuração de Account_ID com CrewAI

```yaml
# config/furniture/account_2.yaml
account_id: account_2
name: "Cliente Exemplo"
domain: "furniture"

# Configuração de Crews com CrewAI
crews:
  customer_service:
    enabled: true
    name: "Customer Service Crew"
    description: "Crew especializada em atendimento ao cliente"
    agents:
      - name: "customer_support_agent"
        role: "Agente de Suporte ao Cliente"
        goal: "Fornecer suporte excepcional aos clientes, respondendo perguntas e resolvendo problemas"
        backstory: "Especialista em atendimento ao cliente com amplo conhecimento sobre os produtos da empresa"
        verbose: true
        tools:
          - "product_search_tool"
          - "order_status_tool"
      - name: "sales_agent"
        role: "Agente de Vendas"
        goal: "Ajudar clientes a encontrar os produtos ideais e finalizar vendas"
        backstory: "Especialista em vendas com conhecimento detalhado sobre os produtos e suas características"
        verbose: true
        tools:
          - "product_search_tool"
          - "price_calculator_tool"

  product_management:
    enabled: true
    name: "Product Management Crew"
    description: "Crew especializada em gerenciamento de produtos"
    agents:
      - name: "content_generator"
        role: "Gerador de Conteúdo"
        goal: "Criar descrições atraentes e informativas para produtos"
        backstory: "Especialista em marketing de conteúdo com habilidade para destacar características de produtos"
        verbose: true
        tools:
          - "product_metadata_tool"
          - "content_generation_tool"
      - name: "product_syncer"
        role: "Sincronizador de Produtos"
        goal: "Garantir que os dados de produtos estejam sincronizados entre sistemas"
        backstory: "Especialista em integração de dados com foco em consistência e precisão"
        verbose: true
        tools:
          - "vector_db_tool"
          - "odoo_sync_tool"

  social_media:
    enabled: false
    name: "Social Media Crew"
    description: "Crew especializada em gerenciamento de redes sociais"
    agents:
      - name: "instagram_content_creator"
        role: "Criador de Conteúdo para Instagram"
        goal: "Criar conteúdo envolvente para o Instagram que promova produtos e aumente o engajamento"
        backstory: "Especialista em marketing digital com foco em conteúdo visual e storytelling"
        verbose: true
        tools:
          - "content_generation_tool"
          - "image_suggestion_tool"

# Configuração de Integrações
integrations:
  mcp:
    type: "odoo-mcp"
    config:
      url: "http://localhost:8069"
      db: "account_2"
      username: "admin"
      credential_ref: "a1b2c3d4-e5f6-g7h8-i9j0"  # Referência, não a senha real

  chatwoot:
    enabled: true
    config:
      account_id: "chatwoot_account_123"
      webhook_secret_ref: "chatwoot_webhook_secret_ref"  # Referência, não o segredo real

  mercado_livre:
    enabled: false
    config:
      app_id: "ML123456"
      client_secret_ref: "ml_secret_account_2"  # Referência, não o segredo real
      access_token_ref: "ml_token_account_2"    # Referência, não o token real

  # Configuração do Redis para persistência e cache
  redis:
    enabled: true
    config:
      host: "localhost"
      port: 6379
      db: 0
      ttl: 86400  # 24 horas em segundos
      prefix: "account_2:"

  # Configuração do Qdrant para busca semântica
  qdrant:
    enabled: true
    config:
      host: "localhost"
      port: 6333
      collection: "products_account_2"
```

### Mapeamento de Account_ID para Domínios

```yaml
# config/chatwoot_mapping.yaml
accounts:
  "1": "furniture"  # Account ID 1 usa o domínio furniture (pasta)
  "2": "furniture"  # Account ID 2 usa o domínio furniture (pasta)
  "3": "cosmetics"  # Account ID 3 usa o domínio cosmetics (pasta)
  "4": "cosmetics"  # Account ID 4 usa o domínio cosmetics (pasta)
```

## Persistência e Cache com Redis

O Redis desempenha um papel fundamental na arquitetura do sistema, fornecendo três funções críticas:

### 1. Persistência de Crews

O sistema utiliza o Redis para persistir instâncias de crews, evitando a necessidade de recriá-las a cada requisição:

```python
def get_or_create_crew(self, account_id, crew_type, config):
    """Obtém uma crew existente do cache ou cria uma nova."""
    # Gerar chave única para a crew
    crew_key = f"crew:{account_id}:{crew_type}"

    # Verificar se a crew já existe no Redis
    if self.redis_client.exists(crew_key):
        # Recuperar a crew serializada do Redis
        crew_data = self.redis_client.get(crew_key)
        crew = pickle.loads(crew_data)
        logger.info(f"Crew recuperada do Redis: {crew_key}")
        return crew

    # Se não existir, criar uma nova crew
    crew = self.crew_factory.create_crew(account_id, crew_type, config)

    # Serializar e armazenar no Redis
    crew_data = pickle.dumps(crew)
    self.redis_client.set(crew_key, crew_data)
    self.redis_client.expire(crew_key, 3600)  # Expira em 1 hora

    logger.info(f"Nova crew criada e armazenada no Redis: {crew_key}")
    return crew
```

Esta abordagem oferece várias vantagens:

- **Redução de Tempo de Inicialização**: Evita o tempo de inicialização das crews, que pode ser significativo
- **Economia de Tokens**: Reduz o número de chamadas ao LLM para inicializar agentes
- **Manutenção de Estado**: Permite que as crews mantenham estado entre requisições
- **Escalabilidade**: Facilita a distribuição do sistema em múltiplos servidores

### 2. Cache de Consultas com Redis

O sistema utiliza o Redis para cachear resultados de consultas frequentes, reduzindo a carga nos bancos de dados e melhorando o desempenho:

```python
def search_products(self, query, filters=None, limit=10):
    """Busca produtos com base em uma consulta de texto."""
    # Gerar chave de cache
    cache_key = f"search:{hash(query)}:{hash(str(filters))}"

    # Verificar se o resultado já está no cache
    if self.redis_client.exists(cache_key):
        # Recuperar o resultado do cache
        result_data = self.redis_client.get(cache_key)
        results = json.loads(result_data)
        logger.info(f"Resultados recuperados do cache: {cache_key}")
        return results

    # Se não estiver no cache, realizar a busca
    results = self._perform_hybrid_search(query, filters, limit)

    # Armazenar no cache
    result_data = json.dumps(results)
    self.redis_client.set(cache_key, result_data)
    self.redis_client.expire(cache_key, 300)  # Expira em 5 minutos

    return results
```

Esta abordagem oferece várias vantagens:

- **Redução de Latência**: Respostas mais rápidas para consultas frequentes
- **Economia de Recursos**: Menos chamadas ao Odoo e ao Qdrant
- **Economia de Tokens**: Menos chamadas à API da OpenAI para geração de embeddings
- **Consistência**: Resultados consistentes para a mesma consulta

### 3. Gerenciamento de Estado

O Redis é utilizado para armazenar informações de estado do sistema, como mapeamentos de account_id, configurações e metadados:

```python
def get_domain_by_account_id(self, account_id):
    """Obtém o domínio associado a um account_id."""
    # Verificar no Redis primeiro
    domain_key = f"domain:account:{account_id}"

    if self.redis_client.exists(domain_key):
        domain = self.redis_client.get(domain_key).decode('utf-8')
        return domain

    # Se não estiver no Redis, consultar o mapeamento
    domain = self._load_domain_from_mapping(account_id)

    # Armazenar no Redis para futuras consultas
    if domain:
        self.redis_client.set(domain_key, domain)
        self.redis_client.expire(domain_key, 86400)  # Expira em 24 horas

    return domain
```

## Busca Híbrida (BM42)

O sistema implementa uma estratégia de busca híbrida avançada, combinando busca vetorial densa (semântica) e esparsa (palavras-chave) com verificação de disponibilidade no Odoo para fornecer resultados precisos, relevantes e atualizados.

### O que é Busca Híbrida?

A busca híbrida BM42 combina três abordagens diferentes de busca:

1. **Busca Vetorial Densa** (Qdrant): Encontra produtos com base na similaridade semântica usando embeddings de alta dimensionalidade
2. **Busca Vetorial Esparsa** (BM25): Encontra produtos com base em correspondência de palavras-chave usando algoritmos como BM25
3. **Busca Relacional** (Odoo): Verifica disponibilidade, preço e outras informações estruturadas

### Fluxo da Busca Híbrida

```python
def _perform_hybrid_search(self, query, filters=None, limit=10):
    """Realiza uma busca híbrida combinando busca densa, esparsa e verificação no Odoo."""
    # 1. Gerar embedding denso para a consulta (semântico)
    dense_embedding = self.embedding_service.generate_embedding(query)

    # 2. Gerar representação esparsa para a consulta (palavras-chave)
    sparse_representation = self.sparse_encoder.encode(query)

    # 3. Buscar no Qdrant usando vetores densos (semântica)
    dense_results = self.qdrant_client.search(
        collection_name="products_dense",
        query_vector=dense_embedding,
        limit=limit * 2  # Buscar mais resultados para combinar depois
    )

    # 4. Buscar usando representação esparsa (palavras-chave)
    sparse_results = self.sparse_search.search(
        query=sparse_representation,
        limit=limit * 2
    )

    # 5. Combinar resultados com pesos
    combined_scores = {}

    # Adicionar scores da busca densa (peso: 0.6)
    for result in dense_results:
        combined_scores[result.id] = result.score * 0.6

    # Adicionar scores da busca esparsa (peso: 0.4)
    for result in sparse_results:
        if result.id in combined_scores:
            combined_scores[result.id] += result.score * 0.4
        else:
            combined_scores[result.id] = result.score * 0.4

    # 6. Obter IDs dos produtos com melhores scores combinados
    product_ids = sorted(combined_scores.keys(),
                        key=lambda id: combined_scores[id],
                        reverse=True)[:limit * 2]

    # 7. Verificar disponibilidade e aplicar filtros no Odoo
    odoo_filters = [
        ('id', 'in', product_ids),
        ('active', '=', True),
        ('qty_available', '>', 0)
    ]

    # Adicionar filtros adicionais se fornecidos
    if filters:
        for key, value in filters.items():
            odoo_filters.append((key, '=', value))

    # 8. Consultar o Odoo
    available_products = self.odoo_client.search_read(
        'product.template',
        odoo_filters,
        ['name', 'description', 'list_price', 'qty_available', 'image_url']
    )

    # 9. Ordenar por score combinado
    for product in available_products:
        product['combined_score'] = combined_scores.get(product['id'], 0)

    # Ordenar por score combinado
    sorted_products = sorted(available_products,
                            key=lambda p: p['combined_score'],
                            reverse=True)

    # Limitar ao número solicitado
    return sorted_products[:limit]
```

### Vantagens da Busca Híbrida BM42

1. **Relevância Semântica**: Encontra produtos semanticamente relevantes para a consulta do usuário, mesmo que não contenham exatamente as mesmas palavras

2. **Precisão de Palavras-Chave**: Captura correspondências exatas de termos importantes através da busca esparsa

3. **Dados Atualizados**: Garante que apenas produtos disponíveis sejam recomendados, pois verifica a disponibilidade no Odoo

4. **Resultados Balanceados**: Combina o melhor da busca semântica e da busca por palavras-chave

5. **Desempenho Otimizado**: Cada componente faz o que sabe fazer melhor - busca densa para semântica, busca esparsa para palavras-chave, e Odoo para dados estruturados

6. **Escalabilidade**: A arquitetura pode escalar horizontalmente, adicionando mais nós tanto ao Odoo quanto ao Qdrant conforme necessário

### Otimização com Redis

Para otimizar o desempenho da busca híbrida, o sistema utiliza o Redis para cachear:

1. **Embeddings**: Evita gerar embeddings repetidos para as mesmas consultas
2. **Resultados de Busca**: Armazena resultados de buscas frequentes
3. **Metadados de Produtos**: Cacheia informações de produtos frequentemente acessados

Esta abordagem reduz significativamente a latência e o custo de operação do sistema.

## Implementação Técnica

### 1. Hub Central (`src/core/hub.py`)

O Hub é o componente central que orquestra o fluxo de requisições:

```python
def process_request(self, request_data):
    """
    Processa uma requisição e direciona para a crew apropriada.

    Args:
        request_data: Dados da requisição

    Returns:
        dict: Resposta da requisição
    """
    try:
        # Extrair metadados
        metadata = request_data.get('metadata', {})
        source = metadata.get('source')
        account_id = metadata.get('account_id')
        action = metadata.get('action')

        # Verificar se o account_id é válido
        if not is_valid_account_id(account_id):
            return {
                'success': False,
                'error': f'account_id inválido: {account_id}'
            }

        # Carregar configuração do account_id
        config = load_account_config(account_id)

        # Determinar qual crew deve processar a requisição
        crew_type = self._determine_crew_type(source, action)

        # Verificar se a crew está habilitada
        if not is_crew_enabled(config, crew_type):
            return {
                'success': False,
                'error': f'Crew {crew_type} não está habilitada para account_id {account_id}'
            }

        # Obter ou criar a crew apropriada
        crew = self._get_or_create_crew(account_id, crew_type, config)

        # Processar a requisição com a crew apropriada
        return crew.process_request(request_data)
    except Exception as e:
        logger.error(f"Erro ao processar requisição: {str(e)}")
        return {
            'success': False,
            'error': f'Erro interno: {str(e)}'
        }
```

### 2. API REST para Odoo (`src/api/odoo/api.py`)

A API REST para Odoo é o ponto de entrada para requisições do módulo Odoo:

```python
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, Optional

from src.core.hub import HubCrew

app = FastAPI(title="Odoo Integration API")

class OdooRequest(BaseModel):
    metadata: Dict[str, Any]
    params: Dict[str, Any]

@app.post("/api/v1/process")
async def process_request(request: OdooRequest, hub_crew: HubCrew = Depends(get_hub_crew)):
    """
    Process a request from Odoo module.
    """
    try:
        # Processar a requisição através do hub
        result = hub_crew.process_request(request.dict())

        if not result.get('success', False):
            raise HTTPException(status_code=400, detail=result.get('error', 'Unknown error'))

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### 3. MCP-Odoo (`src/mcp_odoo/server.py`)

O MCP-Odoo fornece uma interface padronizada para o Odoo:

```python
@mcp.tool(
    "get_product_metadata",
    description="Get product metadata from Odoo",
)
def get_product_metadata(ctx: Context, request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get product metadata from Odoo.

    This tool retrieves product metadata from Odoo for use in AI processing.
    """
    try:
        # Get Odoo client from context
        odoo = ctx.app.odoo

        # Get product metadata
        product_id = request.get("product_id")
        if not product_id:
            return {
                "success": False,
                "error": "Missing required parameter: product_id"
            }

        # Get product data from Odoo
        product_data = odoo.execute(
            'product.template',
            'read',
            [product_id],
            ['name', 'categ_id', 'description_sale', 'description']
        )[0]

        # Get category name
        category = {}
        if product_data.get('categ_id'):
            category = odoo.execute(
                'product.category',
                'read',
                [product_data['categ_id'][0]],
                ['name']
            )[0]

        # Prepare metadata
        metadata = {
            'id': product_id,
            'name': product_data.get('name', ''),
            'category': category.get('name', ''),
            'description_sale': product_data.get('description_sale', ''),
            'description': product_data.get('description', '')
        }

        return {
            "success": True,
            "metadata": metadata
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
```

## Integração com Múltiplos ERPs

O sistema foi projetado desde o início para ser agnóstico em relação ao ERP, com o MCP (Multi-Client Protocol) servindo como camada de abstração. Esta arquitetura permite duas abordagens principais:

1. **Sistema Completo com Odoo**: Fornecendo uma solução end-to-end com Odoo como ERP integrado
2. **Plataforma de Integração**: Conectando-se a ERPs existentes dos clientes

### Implementação Atual do MCP-Odoo

A implementação atual do MCP-Odoo consiste em dois componentes principais:

1. **OdooClient (`odoo_client.py`)**
   - Implementa a comunicação com o Odoo via XML-RPC
   - Fornece métodos para operações CRUD (Create, Read, Update, Delete)
   - Gerencia a autenticação e sessão com o Odoo
   - Implementa tratamento de erros e retentativas

2. **FastMCP Server (`server.py`)**
   - Expor ferramentas (tools) para interação com o Odoo
   - Implementa ferramentas para vendas, calendário, produtos, clientes, estoque, preços e pagamentos
   - Fornece uma interface consistente para os agentes de IA
   - Abstrai a complexidade do Odoo para os agentes

### Estratégias de Integração com ERPs Externos

#### 1. Adaptadores MCP Específicos

Para cada ERP popular, podemos desenvolver um adaptador MCP específico:

- **MCP-SAP**: Para integração com SAP
- **MCP-Microsoft Dynamics**: Para integração com Dynamics
- **MCP-Oracle NetSuite**: Para NetSuite
- **MCP-Totvs**: Para sistemas brasileiros como Protheus

```
├── odoo_api/                # API REST para integração com Odoo
│   ├── core/              # Núcleo da API
│   │   ├── domain/          # Gerenciamento de domínios
│   │   ├── interfaces/      # Interfaces para serviços
│   │   ├── odoo_connector.py  # Conector Odoo com sistema de referências
│   │   └── services/        # Serviços internos
│   ├── embedding_agents/   # Agentes de embedding especializados
│   │   ├── business_rules_agent.py
│   │   ├── product_description_agent.py
│   │   └── product_mass_agent.py
│   ├── modules/           # Módulos da API
│   │   ├── business_rules/  # API para regras de negócio
│   │   ├── credentials/    # API para gerenciamento de credenciais
│   │   ├── product_management/ # API para gerenciamento de produtos
│   │   └── semantic_product/ # API para descrição semântica de produtos
│   ├── services/          # Serviços compartilhados
│   │   ├── cache_service.py # Serviço de cache
│   │   ├── openai_service.py # Serviço de integração com OpenAI
│   │   └── vector_service.py # Serviço de vetorização
│   ├── config/            # Configurações
│   │   ├── domains/         # Configurações por domínio
│   │   ├── credentials.yaml.example # Exemplo de credenciais
│   │   └── account_mapping.yaml.example # Exemplo de mapeamento
│   ├── main.py            # Ponto de entrada da API REST
│   └── tests/             # Testes automatizados
├── addons/                 # Módulos Odoo
│   ├── ai_credentials_manager/ # Gerenciador de credenciais
│   ├── business_rules/       # Regras de negócio
│   ├── semantic_product_description/ # Descrição semântica de produtos
│   └── product_ai_mass_management/ # Gerenciamento em massa de produtos
├── src/                    # Código fonte principal
│   ├── webhook/           # Webhook para Chatwoot e credenciais
│   │   ├── handlers/        # Handlers específicos
│   │   ├── server.py        # Servidor webhook
│   │   └── webhook_handler.py # Handler principal
│   ├── core/              # Núcleo do sistema
│   │   ├── domain/          # Gerenciamento de domínios
│   │   ├── hub.py           # Hub central (HubCrew)
│   │   └── data_proxy_agent.py # Agente de acesso a dados
│   └── mcp_odoo/          # Implementação MCP para Odoo
│       ├── odoo_client.py   # Cliente para comunicação com Odoo
│       └── server.py        # Servidor MCP
├── config/                 # Configurações globais
│   └── domains/           # Configurações por domínio e account_id
```

Cada implementação MCP fornece a mesma interface para o sistema, mas traduz as operações para o ERP específico.

#### 2. API REST Genérica

Para ERPs menos comuns ou personalizados, oferecemos uma API REST bem documentada que eles podem implementar do lado deles:

```
POST /api/v1/sync/products
POST /api/v1/sync/customers
POST /api/v1/sync/orders
```

#### 3. Webhooks Bidirecionais

Implementamos webhooks para notificações em tempo real:

```
POST /webhook/product_updated
POST /webhook/order_created
```

#### 4. Conectores ETL

Para sincronização de dados em lote, desenvolvemos conectores ETL que funcionam com ferramentas como:

- Pentaho Data Integration
- Talend
- Apache NiFi

### Desafios e Considerações

1. **Mapeamento de Dados**: Cada ERP tem seu próprio modelo de dados, exigindo mapeamentos flexíveis.

2. **Autenticação e Segurança**: Diferentes ERPs têm diferentes mecanismos de autenticação.

3. **Sincronização Bidirecional**: Garantir que as alterações em ambos os sistemas sejam sincronizadas corretamente.

4. **Desempenho**: Garantir que a integração não afete o desempenho do ERP do cliente.

## Próximos Passos

### 1. Implementação da API REST para Odoo

- [x] Criar estrutura básica da API REST
- [x] Implementar endpoints para geração de descrição
- [x] Implementar endpoints para sincronização com Qdrant
- [x] Implementar endpoints para busca semântica
- [x] Adicionar autenticação e autorização
- [x] Implementar logging e monitoramento
- [x] Implementar endpoint para gerenciamento de credenciais

### 2. Expansão do MCP-Odoo

- [x] Adicionar métodos para obter metadados de produtos
- [x] Adicionar métodos para atualizar status de sincronização
- [ ] Adicionar métodos para operações de vendas
- [ ] Adicionar métodos para operações de calendário
- [x] Implementar sistema de referências para credenciais
- [x] Otimizar consultas ao Odoo

### 3. Implementação do Serviço de Vetorização e Busca Híbrida

- [x] Criar estrutura básica do serviço
- [x] Implementar geração de embeddings com OpenAI
- [x] Implementar armazenamento no Qdrant
- [x] Implementar busca semântica básica
- [x] Implementar busca híbrida (BM42) combinando Qdrant e Odoo
- [x] Implementar cache de embeddings com Redis
- [x] Implementar cache de resultados de busca com Redis
- [x] Implementar estratégias de otimização de custos (processamento em lote, pré-processamento de texto)
- [x] Implementar sincronização automática entre Odoo e Qdrant
- [ ] Implementar agentes de embedding especializados por módulo

### 4. Implementação do Redis para Persistência e Cache

- [x] Configurar Redis para persistência de crews
- [x] Implementar serialização e desserialização de crews
- [x] Implementar mecanismo de cache para consultas frequentes
- [x] Implementar cache de configurações e mapeamentos
- [x] Implementar estratégias de expiração de cache
- [ ] Implementar monitoramento de uso do Redis

### 5. Modificação do Hub

- [x] Estender o Hub para processar diferentes tipos de requisições
- [x] Implementar mecanismo para determinar qual crew deve processar cada requisição
- [x] Implementar mecanismo para obter ou criar a crew apropriada usando Redis
- [x] Adicionar suporte para diferentes tipos de ações
- [ ] Implementar mecanismo de fallback para casos de falha

### 6. Implementação de Crews Especializadas com CrewAI

- [x] Implementar Customer Service Crew usando CrewAI
- [x] Implementar Product Management Crew usando CrewAI
- [ ] Implementar Social Media Crew usando CrewAI
- [ ] Implementar Marketplace Crew usando CrewAI
- [ ] Implementar Analytics Crew usando CrewAI
- [x] Configurar ferramentas específicas para cada crew

### 7. Desenvolvimento de Módulos Odoo

- [x] Implementar módulo `ai_credentials_manager` para gerenciamento de credenciais
- [x] Implementar módulo `business_rules` para regras de negócio
- [x] Implementar módulo `semantic_product_description` para descrição semântica de produtos
- [x] Implementar módulo `product_ai_mass_management` para gerenciamento em massa de produtos
- [x] Integrar módulos com o sistema de credenciais
- [ ] Implementar módulo `ai_conversational_bot` para interface de chat no Odoo

### 8. Implementação do Sistema de Referências para Credenciais

- [x] Definir estrutura de arquivos para armazenamento seguro de credenciais
- [x] Implementar sistema de referências em arquivos YAML
- [x] Implementar API para recuperação segura de credenciais
- [x] Integrar com módulos Odoo
- [x] Implementar registro de acessos para auditoria
- [ ] Implementar criptografia de credenciais no banco de dados

### 9. Implementação do Controle de Tokens da OpenAI

- [ ] Implementar contador de tokens por requisição
- [ ] Implementar limites configuráveis por cliente/account_id
- [ ] Desenvolver dashboard de uso de tokens
- [ ] Implementar alertas de limite próximo
- [ ] Gerar relatórios de consumo

### 10. Testes e Documentação

- [x] Implementar testes unitários para componentes principais
- [ ] Implementar testes de integração para fluxos completos
- [ ] Implementar testes de carga para verificar desempenho
- [x] Implementar testes específicos para busca híbrida
- [ ] Implementar testes para persistência de crews com Redis
- [x] Criar documentação detalhada para cada componente
- [x] Criar guias de uso para desenvolvedores
- [ ] Criar guias de integração para clientes com ERPs existentes

## Considerações Futuras

### 1. Agentes Executivos de IA

Uma evolução fundamental do sistema será a transição de agentes puramente informativos para agentes executivos, capazes de realizar ações diretas no sistema com aprovação do usuário:

#### Capacidades Planejadas

- **Análise Contínua**: Monitoramento constante de dados relevantes (vendas, tendências, concorrentes)
- **Identificação de Oportunidades**: Detecção proativa de oportunidades de negócio
- **Recomendações Contextualizadas**: Sugestões baseadas em dados com justificativas claras
- **Execução Assistida**: Capacidade de executar ações diretas no sistema após aprovação

#### Exemplos de Funcionalidades

- **Gestão de Produtos**: "Detectei um produto com alta demanda no mercado. Gostaria que eu o adicionasse ao catálogo?"
- **Marketing Automático**: "Posso criar uma campanha no Instagram para o produto X que está em alta?"
- **Precificação Dinâmica**: "O concorrente reduziu o preço do produto Y. Recomendo ajustarmos nosso preço para Z."
- **Gestão de Estoque**: "O produto A está com estoque baixo e a demanda crescente. Devo criar um pedido de compra?"

#### Requisitos Técnicos

- Sistema de permissões granulares para ações de agentes
- API de ações para cada operação no sistema
- Interface de aprovação para usuários
- Rastreamento detalhado de ações executadas por agentes
- Integração com análise de dados em tempo real

### 2. Integração com Mercado Livre

- Adicionar adaptador específico para Mercado Livre
- Implementar sincronização de produtos com Mercado Livre
- Implementar processamento de pedidos do Mercado Livre

### 3. Integração com Instagram/Facebook

- Adicionar adaptador específico para Instagram/Facebook
- Implementar geração de conteúdo para Instagram/Facebook
- Implementar processamento de interações do Instagram/Facebook

### 4. Análise de Dados e Recomendações

- Implementar análise de dados de vendas, clientes, etc.
- Implementar sistema de recomendação de produtos
- Implementar previsão de demanda

### 5. Escalabilidade

- Implementar sistema de filas para processamento assíncrono
- Adicionar suporte para múltiplas instâncias de cada componente
- Implementar balanceamento de carga

### 6. Monitoramento e Observabilidade

- Implementar métricas de desempenho
- Implementar rastreamento de requisições
- Implementar alertas para falhas

## Conclusão

Esta arquitetura fornece uma base sólida para um sistema completo de atendimento ao cliente e integração com ERPs, com foco em:

1. **Multi-tenancy**: Suporte a múltiplos clientes com configurações específicas
2. **Modularidade**: Componentes claramente separados com responsabilidades bem definidas
3. **Extensibilidade**: Facilidade para adicionar novos componentes e funcionalidades
4. **Escalabilidade**: Capacidade de escalar horizontalmente para atender a demandas crescentes
5. **Flexibilidade**: Adaptação a diferentes domínios de negócio e casos de uso
6. **Interoperabilidade**: Capacidade de integração com diversos ERPs através da camada MCP

A implementação desta arquitetura permite duas abordagens principais:

1. **Sistema Completo**: Fornecendo uma solução end-to-end com Odoo como ERP integrado para clientes que não possuem um ERP existente

2. **Plataforma de Integração**: Conectando-se a ERPs existentes dos clientes (SAP, Microsoft Dynamics, Oracle NetSuite, Totvs, etc.) através de adaptadores MCP específicos

Esta flexibilidade maximiza o mercado potencial, permitindo atender tanto empresas que buscam uma solução completa quanto aquelas que já possuem investimentos significativos em sistemas ERP existentes.

O resultado final é uma plataforma que realmente integra IA profundamente nos processos de negócio, com funcionalidades avançadas de processamento de linguagem natural, busca semântica, análise de dados e automação de marketing, independentemente do ERP utilizado pelo cliente.


### Sugestões de Melhorias

#### 1. Implementação de Filas com RabbitMQ

O sistema utiliza RabbitMQ como sistema de filas para processamento assíncrono, oferecendo:

- **Processamento em background** de operações demoradas como geração de embeddings
- **Resiliência** para operações que podem falhar e precisam ser retentadas
- **Balanceamento de carga** entre múltiplos workers
- **Escalabilidade horizontal** para lidar com picos de demanda
- **Suporte multi-tenant** para processar mensagens de até 15 clientes simultaneamente

#### 2. Busca Híbrida Avançada (BM42)

O sistema implementa uma estratégia de busca híbrida que combina:

- **Busca vetorial densa** para capturar similaridade semântica
- **Busca vetorial esparsa** para correspondência precisa de palavras-chave
- **Verificação de disponibilidade** em tempo real via Odoo

Esta abordagem oferece resultados superiores em comparação com métodos tradicionais de busca.

#### 3. Estratégia de Circuit Breaker

Implementar padrões de circuit breaker para lidar com falhas em componentes externos, especialmente importante para as integrações com Odoo e serviços de IA.

#### 4. Observabilidade

- Adicionar rastreamento distribuído com OpenTelemetry
- Implementar logging centralizado e dashboards de monitoramento
- Monitorar desempenho das filas e tempo de resposta do sistema

#### 5. Gestão de Custos de IA

- Desenvolver estratégias para otimizar o uso de tokens em LLMs
- Utilizar cache eficiente para evitar geração repetida de embeddings
- Implementar processamento em lote para redução de custos

#### 6. Estratégia de DevOps

- Implementar CI/CD desde o início
- Considerar infraestrutura como código para facilitar implantações multi-tenant
- Automatizar testes de desempenho e carga

#### 7. Otimização de Desempenho

Caso o sistema apresente problemas de desempenho mesmo após todas as otimizações, considerar simplificar a arquitetura removendo camadas intermediárias como o DataProxyAgent e testando comunicação direta com as Crews.

## Implementações Futuras

### 1. Integração da API da OpenAI e Controle de Tokens

O módulo `ai_credentials_manager` será expandido para incluir:

- **Gerenciamento de Chaves da OpenAI**: Armazenamento seguro de chaves da OpenAI e outros provedores de LLM
- **Sistema de Controle de Tokens**:
  - Contador de tokens por requisição
  - Limites configuráveis por cliente/account_id
  - Dashboard de uso de tokens
  - Alertas de limite próximo
  - Relatórios de consumo

**Arquitetura de Controle de Tokens**:
```
├── Token Manager Service
│   ├── Token Counter (contagem em tempo real)
│   ├── Token Budget (alocação de orçamento por sessão)
│   ├── Token Cache (cache de respostas para economia)
│   └── Token Analytics (análise de uso e otimização)
```

Para garantir performance em cenários de múltiplos atendimentos simultâneos, o sistema implementará:

1. **Cache Redis** para credenciais e contagens de tokens
2. **Verificação Assíncrona** de tokens (não bloqueante)
3. **Sistema de Budget** pré-alocado para cada sessão de atendimento

### 2. Múltiplas Crews por Cliente

A arquitetura será expandida para suportar múltiplas crews especializadas por cliente:

**Estrutura de Arquivos YAML**:
```
config/
├── domains/
│   └── cosmetics/
│       └── account_1/
│           ├── support_crew.yaml  # Crew de atendimento
│           ├── analytics_crew.yaml  # Crew de analytics
│           └── sales_crew.yaml  # Crew de vendas
```

**Sistema de Roteamento de Crews**:
- Implementação de um "Crew Registry" central
- Mapeamento de tipos de solicitações para crews específicas
- Gerenciamento de credenciais por crew
- Escalonamento horizontal de crews

### 3. Sistema Conversacional no Odoo

Um novo módulo Odoo `ai_conversational_bot` será desenvolvido para:

- **Interface de Chat Integrada**: Chat embutido na interface do Odoo
- **Consultas SQL Seguras**:
  - Sistema de "SQL seguro" com queries parametrizadas
  - Permissões granulares por tabela/view
  - Escopo limitado de consultas possíveis
  - Logging detalhado de todas as consultas
- **Integração com Relatórios**: Capacidade de explicar e detalhar relatórios existentes
- **Geração de Insights**: Análise de dados e sugestões de ações

**Arquitetura de Segurança SQL**:
```
├── SQL Security Layer
│   ├── Query Parser (validação de sintaxe)
│   ├── Query Sanitizer (remoção de comandos perigosos)
│   ├── Permission Checker (verificação de permissões)
│   ├── Query Limiter (limites de tempo/recursos)
│   └── Query Logger (registro detalhado)
```

Para otimizar performance:
- Limites de tempo de execução para consultas
- Cache de resultados frequentes
- Execução assíncrona para consultas pesadas

### Arquitetura Integrada das Implementações Futuras

```
├── Módulos Odoo
│   ├── ai_credentials_manager (Gerenciamento de Credenciais)
│   ├── ai_conversational_bot (Bot Conversacional)
│   └── [Módulos Existentes]
│
├── API Gateway + Auth
│
├── Crew Registry (Registro Central de Crews)
│
├── Token Manager (Gerenciamento de Tokens)
│
├── Crews Especializadas
│   ├── Support Crew
│   ├── Analytics Crew
│   ├── Sales Crew
│   └── [Outras Crews]
│
├── Tool Registry (Registro de Ferramentas)
│   ├── SQL Tools (Ferramentas SQL Seguras)
│   ├── Report Tools (Ferramentas de Relatórios)
│   ├── Insight Tools (Ferramentas de Insights)
│   └── [Outras Ferramentas]
```

Esta arquitetura expandida permitirá que o sistema evolua de forma modular e escalável, mantendo a segurança e performance em níveis ótimos mesmo com a adição de novas funcionalidades.