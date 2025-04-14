# Nova Arquitetura do Sistema

Este documento descreve a nova arquitetura do sistema de integração entre Odoo e IA, incluindo os componentes principais, fluxo de dados e padrões de design.

## Visão Geral

O sistema é projetado para integrar módulos Odoo com serviços de IA, permitindo a vetorização de dados (regras de negócio, produtos, etc.) para busca semântica e outras aplicações de IA.

A arquitetura segue os princípios de:
- **Separação de Responsabilidades**: Cada componente tem uma responsabilidade bem definida
- **Interfaces Claras**: Componentes se comunicam através de interfaces bem definidas
- **Extensibilidade**: Fácil adicionar novos módulos e funcionalidades
- **Testabilidade**: Componentes podem ser testados de forma isolada

## Estrutura de Diretórios

```
odoo_api/
  ├── core/                           # Serviços base e interfaces
  │   ├── interfaces/                 # Interfaces (ports)
  │   ├── services/                   # Implementações concretas
  │   └── domain/                     # Modelos de domínio compartilhados
  ├── embedding_agents/               # Agentes de processamento para embeddings
  ├── modules/                        # Módulos da API correspondentes aos módulos Odoo
  │   ├── business_rules/             # API para o módulo business_rules
  │   ├── product_ai_mass_management/ # API para o módulo product_ai_mass_management
  │   └── semantic_product_description/ # API para o módulo semantic_product_description
  ├── infrastructure/                 # Configurações e utilitários
  │   ├── config/
  │   ├── logging/
  │   └── utils/
  ├── tests/                          # Testes automatizados
  │   ├── unit/                       # Testes unitários
  │   ├── integration/                # Testes de integração
  │   └── fixtures/                   # Dados de teste
  └── docs/                           # Documentação
```

## Componentes Principais

### 1. Interfaces (Core Interfaces)

As interfaces definem contratos claros entre componentes, permitindo substituir implementações sem afetar o restante do sistema.

Principais interfaces:
- `AIService`: Interface para serviços de IA (geração de texto e embeddings)
- `VectorService`: Interface para serviços de vetorização (armazenamento e busca de vetores)
- `CacheService`: Interface para serviços de cache (armazenamento e recuperação de dados em cache)
- `EmbeddingAgent`: Interface para agentes de embedding (processamento de dados para embeddings)

### 2. Serviços Base (Core Services)

Os serviços base implementam as interfaces e fornecem funcionalidades comuns a todos os módulos.

Principais serviços:
- `OpenAIService`: Implementação de `AIService` usando a API da OpenAI
- `QdrantVectorService`: Implementação de `VectorService` usando o Qdrant
- `RedisService`: Implementação de `CacheService` usando o Redis

### 3. Agentes de Embedding

Os agentes de embedding são responsáveis por processar dados brutos antes da geração de embeddings, melhorando a qualidade dos vetores gerados.

Cada módulo Odoo tem seu próprio agente especializado:
- `BusinessRulesEmbeddingAgent`: Processa regras de negócio
- `ProductDescriptionEmbeddingAgent`: Processa descrições de produtos
- `ProductMassEmbeddingAgent`: Processa produtos em massa

**Importante**: Cada agente implementa a interface `EmbeddingAgent` e seu método principal `process_data()`, que recebe dados brutos e retorna texto processado pronto para vetorização.

### 4. Módulos da API

Cada módulo da API corresponde a um módulo Odoo e fornece endpoints para integração.

Estrutura de um módulo:
- `services.py`: Serviços específicos do módulo
- `routes.py`: Endpoints da API
- `schemas.py`: Esquemas de dados (Pydantic)

## Fluxo de Dados

### 1. Sincronização de Dados

```
Módulo Odoo -> API -> Serviço do Módulo -> Agente de Embedding -> Serviço de Vetorização -> Qdrant
                                        -> Serviço de Cache -> Redis
```

1. O módulo Odoo envia dados para a API
2. A API encaminha os dados para o serviço do módulo
3. O serviço do módulo usa o agente de embedding específico para processar os dados
4. O agente de embedding gera texto rico para vetorização
5. O serviço de vetorização gera embeddings e os armazena no Qdrant
6. O serviço de cache armazena os dados no Redis para acesso rápido

### 2. Busca Semântica

```
Consulta -> API -> Serviço do Módulo -> Serviço de Vetorização -> Qdrant
                                     -> Serviço de Cache -> Redis
```

1. Uma consulta é enviada para a API
2. A API encaminha a consulta para o serviço do módulo
3. O serviço do módulo usa o serviço de vetorização para gerar embedding da consulta
4. O serviço de vetorização busca vetores similares no Qdrant
5. O serviço do módulo enriquece os resultados com dados do Redis
6. A API retorna os resultados

## Responsabilidades dos Componentes

### Serviço de Vetorização (VectorService)

O serviço de vetorização é responsável apenas por:
- Gerar embeddings a partir de texto
- Armazenar e recuperar vetores no Qdrant
- Realizar buscas por similaridade

Ele **não** é responsável por:
- Processar dados brutos para vetorização (isso é responsabilidade dos agentes de embedding)
- Lógica de negócio específica de módulos

### Agentes de Embedding

Os agentes de embedding são responsáveis por:
- Processar dados brutos específicos de um módulo
- Gerar texto rico e contextualizado para vetorização
- Aplicar lógica específica do domínio durante o processamento

### Serviços de Módulo

Os serviços de módulo são responsáveis por:
- Coordenar o fluxo de dados entre Odoo, agentes de embedding e serviços base
- Implementar lógica de negócio específica do módulo
- Gerenciar o ciclo de vida dos dados do módulo

## Padrões de Design

### 1. Injeção de Dependência

Os componentes recebem suas dependências através de parâmetros, facilitando a substituição de implementações e os testes.

### 2. Singleton

Os serviços base e agentes de embedding são implementados como singletons para evitar múltiplas instâncias desnecessárias.

### 3. Factory

Funções factory (`get_*_service()`, `get_*_agent()`) são usadas para obter instâncias de serviços e agentes, encapsulando a lógica de criação.

### 4. Repository

Os serviços de módulo atuam como repositories, encapsulando a lógica de acesso a dados.

### 5. Adapter

Os agentes de embedding atuam como adapters, convertendo dados brutos em formato adequado para vetorização.

## Configuração

A configuração do sistema é feita através de:
- Variáveis de ambiente
- Arquivos YAML de configuração
- Configurações específicas por account_id

## Multi-tenancy

O sistema suporta múltiplos tenants (account_ids), com:
- Coleções separadas no Qdrant por account_id
- Chaves separadas no Redis por account_id
- Configurações específicas por account_id

## Integração com CrewAI

Os agentes de IA para interação (atendimento, suporte, vendas, etc.) são definidos em arquivos YAML e baseados em CrewAI. Eles interagem com os dados através do `data_proxy_agent.py`, que se comunica com o servidor MCP para acessar bancos de dados relacionais, Redis e Qdrant.

## Diferenças em Relação à Arquitetura Anterior

A nova arquitetura introduz várias melhorias em relação à anterior:

1. **Interfaces Claras**: Introdução de interfaces formais para todos os componentes principais
2. **Agentes de Embedding Especializados**: Cada módulo Odoo tem seu próprio agente especializado
3. **Estrutura de Diretórios Melhorada**: Organização mais clara e lógica
4. **Separação de Responsabilidades**: Melhor separação entre serviços base e específicos de módulo
5. **Testabilidade Aprimorada**: Componentes mais fáceis de testar isoladamente
6. **Remoção de Acoplamento**: O serviço de vetorização não depende mais de agentes específicos

## Implementação dos Novos Módulos

Para implementar um novo módulo Odoo na API, siga estes passos:

1. **Criar Agente de Embedding**:
   - Criar um novo arquivo em `embedding_agents/` (ex: `my_module_agent.py`)
   - Implementar a interface `EmbeddingAgent`
   - Definir a lógica de processamento específica do módulo
   - Implementar o método `process_data()`
   - Criar uma função factory `get_my_module_agent()`

2. **Criar Módulo da API**:
   - Criar diretório em `modules/` (ex: `my_module/`)
   - Implementar `services.py`, `routes.py` e `schemas.py`
   - No serviço, usar o agente de embedding específico:
     ```python
     from odoo_api.embedding_agents.my_module_agent import get_my_module_agent
     
     # No método de sincronização:
     embedding_agent = await get_my_module_agent()
     processed_text = await embedding_agent.process_data(data, business_area)
     ```

3. **Registrar Rotas**:
   - Adicionar as rotas do módulo ao roteador principal da API

4. **Implementar Testes**:
   - Criar testes unitários para o agente de embedding
   - Criar testes de integração para o módulo completo

## Conclusão

Esta nova arquitetura permite:
- Adicionar facilmente novos módulos Odoo
- Substituir implementações de serviços (ex: trocar OpenAI por outro provedor)
- Testar componentes de forma isolada
- Escalar o sistema para múltiplos tenants

A refatoração para esta arquitetura melhora significativamente a manutenibilidade, extensibilidade e testabilidade do sistema, preparando-o para crescer com a adição de novos módulos e funcionalidades.
