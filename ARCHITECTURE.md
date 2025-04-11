# Arquitetura do Sistema ChatwootAI

## Visão Geral

O ChatwootAI é um sistema avançado de atendimento ao cliente e integração com ERPs que combina:

1. **Chatwoot** como hub central de mensagens para atendimento ao cliente
2. **CrewAI** como framework para orquestração de agentes inteligentes
3. **Odoo** como sistema ERP para regras de negócio e dados
4. **Qdrant** como banco de dados vetorial para busca semântica
5. **Redis** como cache distribuído, persistência de crews e gerenciamento de estado

O sistema é projetado para ser **multi-tenant**, adaptando-se dinamicamente a diferentes domínios de negócio (móveis, cosméticos, saúde, etc.) através de configurações YAML, com foco no **account_id** como identificador principal.

## Princípios Arquiteturais Fundamentais

1. **Foco no Account_ID**: O account_id é o identificador principal, com o domínio sendo apenas uma organização de pastas
2. **Simplificação do Fluxo**: Arquitetura hub-and-spoke com o Hub como orquestrador central
3. **Centralização do Acesso a Dados**: Todo acesso a dados passa obrigatoriamente pelo DataProxyAgent
4. **Conexão Direta com ERPs**: Utilização do MCP (Model Context Protocol) para acesso padronizado aos ERPs
5. **Configuração por Account_ID**: Cada account_id possui seu próprio arquivo YAML com todas as configurações necessárias
6. **Múltiplas Crews Especializadas**: Cada account_id pode ter múltiplas crews para diferentes funções (atendimento, produtos, marketing)
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
   - Extrai metadados (account_id, conversation_id, etc.)
   - Direciona para o Hub para processamento

2. **API REST para Odoo (`src/api/odoo/api.py`)**
   - Processa requisições do módulo Odoo
   - Extrai metadados (account_id, action, etc.)
   - Direciona para o Hub para processamento

#### 2. Hub Central (`src/core/hub.py`)

- **Responsabilidade**: Identificar o account_id/domínio e direcionar para a crew apropriada
- **Funcionalidades**:
  - Validar o account_id contra os YAMLs existentes
  - Carregar configurações específicas do account_id
  - Determinar qual crew deve processar a requisição
  - Obter ou criar a crew apropriada
  - Direcionar a requisição para processamento

#### 3. Crews Especializadas

Cada account_id pode ter múltiplas crews especializadas para diferentes funções:

1. **Customer Service Crew**
   - Processa mensagens de clientes via Chatwoot
   - Responde a perguntas sobre produtos, pedidos, etc.
   - Gerencia o fluxo de conversação com clientes

2. **Product Management Crew** aqui precisamos de atenção, dado que isso ainda não está previsto, precisamos pensar melhor
   - Gerencia descrições de produtos
   - Sincroniza produtos com o banco de dados vetorial
   - Processa buscas semânticas de produtos

3. **Social Media Crew**
   - Gera conteúdo para redes sociais
   - Analisa engajamento em redes sociais
   - Gerencia campanhas de marketing

4. **Marketplace Crew**
   - Gerencia integração com marketplaces (Mercado Livre, etc.)
   - Sincroniza produtos com marketplaces
   - Processa pedidos de marketplaces

5. **Analytics Crew**
   - Analisa dados de vendas, clientes, etc.
   - Gera relatórios e insights
   - Fornece recomendações baseadas em dados

#### 4. DataProxyAgent (`src/core/data_proxy_agent.py`)

- **Responsabilidade**: Centralizar o acesso a dados de diferentes fontes
- **Funcionalidades**:
  - Interface unificada para acesso a dados
  - Adaptação de consultas ao account_id ativo
  - Roteamento para o MCP apropriado
  - Formatação e filtragem de resultados

#### 5. MCP-Odoo (`src/mcp_odoo/`)

- **Responsabilidade**: Fornecer interface padronizada para o Odoo
- **Funcionalidades**:
  - Expor métodos para consultar produtos, clientes, vendas, etc.
  - Implementar operações de negócio específicas do Odoo
  - Abstrair a complexidade do Odoo para os agentes de IA
  - Gerenciar conexões com o Odoo

#### 6. Serviço de Vetorização (`src/vector_service/`)

- **Responsabilidade**: Gerenciar embeddings e busca semântica
- **Funcionalidades**:
  - Gerar embeddings para descrições de produtos
  - Armazenar embeddings no Qdrant
  - Fornecer busca semântica
  - Implementar busca híbrida (BM42)

#### 7. Gerenciamento de Domínios (`src/core/domain/`)

- **Responsabilidade**: Gerenciar configurações de domínios e account_ids
- **Funcionalidades**:
  - Carregamento de configurações YAML
  - Mapeamento de account_ids para domínios
  - Validação de configurações
  - Cache de configurações com Redis

## Fluxos de Trabalho

### 1. Atendimento ao Cliente (Chatwoot → Sistema)

1. **Entrada da Mensagem e Identificação do Account_ID**
   - Cliente envia mensagem pelo whasapp ou outro canal
   - Chatwoot recebe a mensagem e a encaminha via webhook para o sistema
   - O `ChatwootWebhookHandler` processa a requisição e extrai o account_id
   - O account_id é usado para determinar qual configuração usar

2. **Processamento pelo Hub**
   - A mensagem é encaminhada para o `HubCrew`
   - O `HubCrew` carrega a configuração do account_id
   - O `HubCrew` determina que a mensagem deve ser processada pela Customer Service Crew
   - O `HubCrew` obtém ou cria a Customer Service Crew

3. **Processamento pela Customer Service Crew**
   - A Customer Service Crew processa a mensagem
   - Os agentes da crew consultam dados via DataProxyAgent
   - O DataProxyAgent direciona as consultas para o MCP-Odoo
   - O MCP-Odoo consulta o Odoo e retorna os resultados
   - A Customer Service Crew gera uma resposta personalizada

4. **Retorno da Resposta**
   - A resposta é enviada de volta ao `HubCrew`
   - O `HubCrew` a encaminha para o Chatwoot
   - O Chatwoot entrega a resposta ao cliente via canal original

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
   - O `HubCrew` determina que a requisição deve ser processada pela Product Management Crew
   - O `HubCrew` obtém ou cria a Product Management Crew

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

Abaixo, apenas o yaml para a crew de atendimento ao cliente, expandiremos mais crews configuadas também via yaml para os modulos futuros

```
/config
  /chatwoot_mapping.yaml   # Mapeamento de account_ids do Chatwoot para domínios
  /furniture               # Domínio (apenas uma organização de pastas)
    account_1.yaml         # Configuração completa para o account_id 1
    account_2.yaml         # Configuração completa para o account_id 2
  /cosmetics               # Outro domínio (apenas uma organização de pastas)
    account_3.yaml         # Configuração completa para o account_id 3
    account_4.yaml         # Configuração completa para o account_id 4
```



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
  odoo:
    enabled: true
    config:
      url: "http://localhost:8069"
      db: "odoo14"
      username: "admin"
      password: "admin"

  chatwoot:
    enabled: true
    config:
      account_id: "chatwoot_account_123"

  mercado_livre:
    enabled: false
    config:
      api_key: ""
      secret_key: ""

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

### 2. Cache de Consultas # DEVEMOS VERIFICAR ONDE O SERVIÇO SERÁ IMPLEMENTADO

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

## Próximos Passos

### 1. Implementação da API REST para Odoo

- [ ] Criar estrutura básica da API REST
- [ ] Implementar endpoints para geração de descrição
- [ ] Implementar endpoints para sincronização com Qdrant
- [ ] Implementar endpoints para busca semântica
- [ ] Adicionar autenticação e autorização
- [ ] Implementar logging e monitoramento

### 2. Expansão do MCP-Odoo

- [ ] Adicionar métodos para obter metadados de produtos
- [ ] Adicionar métodos para atualizar status de sincronização
- [ ] Adicionar métodos para operações de vendas
- [ ] Adicionar métodos para operações de calendário
- [ ] Implementar cache para consultas frequentes
- [ ] Otimizar consultas ao Odoo

### 3. Implementação do Serviço de Vetorização e Busca Híbrida

- [ ] Criar estrutura básica do serviço
- [ ] Implementar geração de embeddings com OpenAI
- [ ] Implementar armazenamento no Qdrant
- [ ] Implementar busca semântica básica
- [ ] Implementar busca híbrida (BM42) combinando Qdrant e Odoo
- [ ] Implementar cache de embeddings com Redis
- [ ] Implementar cache de resultados de busca com Redis
- [ ] Implementar estratégias de otimização de custos (processamento em lote, pré-processamento de texto)
- [ ] Implementar sincronização automática entre Odoo e Qdrant

### 4. Implementação do Redis para Persistência e Cache

- [ ] Configurar Redis para persistência de crews
- [ ] Implementar serialização e desserialização de crews
- [ ] Implementar mecanismo de cache para consultas frequentes
- [ ] Implementar cache de configurações e mapeamentos
- [ ] Implementar estratégias de expiração de cache
- [ ] Implementar monitoramento de uso do Redis

### 5. Modificação do Hub

- [ ] Estender o Hub para processar diferentes tipos de requisições
- [ ] Implementar mecanismo para determinar qual crew deve processar cada requisição
- [ ] Implementar mecanismo para obter ou criar a crew apropriada usando Redis
- [ ] Adicionar suporte para diferentes tipos de ações
- [ ] Implementar mecanismo de fallback para casos de falha

### 6. Implementação de Crews Especializadas com CrewAI

- [ ] Implementar Customer Service Crew usando CrewAI
- [ ] Implementar Product Management Crew usando CrewAI
- [ ] Implementar Social Media Crew usando CrewAI
- [ ] Implementar Marketplace Crew usando CrewAI
- [ ] Implementar Analytics Crew usando CrewAI
- [ ] Configurar ferramentas específicas para cada crew

### 7. Testes e Documentação

- [ ] Implementar testes unitários para cada componente
- [ ] Implementar testes de integração para fluxos completos
- [ ] Implementar testes de carga para verificar desempenho
- [ ] Implementar testes específicos para busca híbrida
- [ ] Implementar testes para persistência de crews com Redis
- [ ] Criar documentação detalhada para cada componente
- [ ] Criar guias de uso para desenvolvedores

## Considerações Futuras

### 1. Integração com Mercado Livre

- Adicionar adaptador específico para Mercado Livre
- Implementar sincronização de produtos com Mercado Livre
- Implementar processamento de pedidos do Mercado Livre

### 2. Integração com Instagram/Facebook

- Adicionar adaptador específico para Instagram/Facebook
- Implementar geração de conteúdo para Instagram/Facebook
- Implementar processamento de interações do Instagram/Facebook

### 3. Análise de Dados e Recomendações

- Implementar análise de dados de vendas, clientes, etc.
- Implementar sistema de recomendação de produtos
- Implementar previsão de demanda

### 4. Escalabilidade

- Implementar sistema de filas para processamento assíncrono
- Adicionar suporte para múltiplas instâncias de cada componente
- Implementar balanceamento de carga

### 5. Monitoramento e Observabilidade

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

A implementação desta arquitetura permitirá a criação de um assistente completo para ERPs, que ajuda tanto clientes quanto usuários do sistema, com funcionalidades avançadas de processamento de linguagem natural, busca semântica, análise de dados e automação de marketing.


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