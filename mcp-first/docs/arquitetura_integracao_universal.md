# Arquitetura de Integração Universal para ChatwootAI

## Sumário Executivo

Este documento apresenta uma proposta de arquitetura para simplificar e otimizar a integração entre os diversos componentes do sistema ChatwootAI. A abordagem central é a implementação de um **Módulo Integrador Universal** no Odoo que centraliza todas as comunicações com os serviços MCP (Model Context Protocol), maximiza o uso de cache via Redis, e simplifica a configuração e manutenção do sistema.

## Visão Geral da Arquitetura

A arquitetura proposta reorganiza o fluxo de comunicação entre os componentes do sistema ChatwootAI, criando um caminho mais direto e eficiente para a troca de informações:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                               Odoo ERP                                   │
│                                                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │ Business    │  │ Company     │  │ Product AI  │  │ Semantic    │    │
│  │ Rules2      │  │ Services    │  │ Management  │  │ Product     │    │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘    │
│         │                 │                │                │           │
│         └─────────────────┼────────────────┼────────────────┘           │
│                           │                │                            │
│                           ▼                ▼                            │
│                    ┌─────────────────────────────┐                     │
│                    │                             │                     │
│                    │  Módulo Integrador Universal│                     │
│                    │                             │                     │
│                    └──────────────┬──────────────┘                     │
└────────────────────────────────────┼──────────────────────────────────┘
                                     │
                                     │ HTTP/API
                                     │
                                     ▼
┌───────────────────────────────────────────────────────────────────────┐
│                              Redis Cache                               │
└─────────────────────────────────┬─────────────────────────────────────┘
                                  │
                                  │
                                  ▼
┌───────────────────────────────────────────────────────────────────────┐
│                               MCP-Crew                                 │
│                          (Cérebro Central)                             │
└─────────────────────────────────┬─────────────────────────────────────┘
                                  │
                                  │
                 ┌────────────────┼────────────────┐
                 │                │                │
                 ▼                ▼                ▼
        ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
        │  MCP-Odoo   │   │ MCP-MongoDB │   │ MCP-Qdrant  │   ...
        └─────────────┘   └─────────────┘   └─────────────┘
```

## Componentes Principais

### 1. Módulo Integrador Universal

Este módulo Odoo atua como ponto central de integração entre os módulos funcionais do Odoo e o ecossistema MCP.

#### Características Principais:

- **Configuração Centralizada**: Gerencia todas as credenciais e endpoints em um único lugar
- **Cache Inteligente**: Implementa estratégias de cache agressivas usando Redis
- **API Interna**: Fornece uma API consistente para os módulos funcionais
- **Gerenciamento Multi-tenant**: Suporte nativo para múltiplos tenants com isolamento de dados
- **Auditoria e Logging**: Registro detalhado de todas as operações para troubleshooting

#### Funcionalidades:

- **Conectores MCP**: Interfaces para comunicação com diferentes MCPs
- **Gerenciamento de Sessão**: Manutenção e renovação automática de tokens
- **Roteamento Inteligente**: Direcionamento de solicitações para o MCP apropriado
- **Tratamento de Erros**: Estratégias de retry e fallback para operações críticas
- **Monitoramento**: Métricas de desempenho e uso

### 2. MCP-Crew (Cérebro Central)

O MCP-Crew atua como orquestrador central, coordenando a comunicação entre os diferentes MCPs específicos.

#### Características Principais:

- **Gerenciamento de Agentes**: Controle do ciclo de vida dos agentes de IA
- **Motor de Decisão**: Determinação da crew mais adequada para cada solicitação
- **Gerenciamento de Contexto**: Manutenção de contexto entre interações
- **Integração com Redis**: Cache e mensageria para comunicação eficiente

#### Funcionalidades:

- **Roteamento de Solicitações**: Direciona solicitações para o MCP específico apropriado
- **Agregação de Resultados**: Combina resultados de múltiplos MCPs quando necessário
- **Gerenciamento de Estado**: Mantém o estado das conversas e interações
- **Autorização e Permissões**: Controle granular de acesso às funcionalidades

### 3. MCPs Específicos

Servidores MCP especializados para diferentes sistemas e funcionalidades.

#### MCPs Implementados/Planejados:

- **MCP-Odoo**: Interface para o Odoo ERP
- **MCP-MongoDB**: Acesso a configurações e dados estruturados
- **MCP-Qdrant**: Busca vetorial e gerenciamento de embeddings
- **MCP-Redes Sociais**: Integração com Facebook, Instagram, WhatsApp
- **MCP-Marketplaces**: Integração com Mercado Livre, Amazon, Shopee

### 4. Redis Cache

Sistema de cache centralizado para otimização de desempenho e economia de tokens.

#### Estratégias de Cache:

- **Cache por Tenant**: Prefixo account_id em todas as chaves
- **TTL Otimizado**: Tempos de expiração adequados para cada tipo de dado
- **Estruturas de Dados Apropriadas**: Uso de strings, hashes, listas e sets conforme necessário
- **Invalidação Seletiva**: Atualização apenas dos dados modificados

### 5. MCP-Chatwoot como Central de Comunicação

#### Visão Geral

O MCP-Chatwoot será expandido para atuar como uma central unificada de comunicação, consolidando todas as interações de diferentes canais (WhatsApp, Instagram, Facebook, Marketplaces, etc.) em uma única interface no Chatwoot.

#### Arquitetura Proposta

```
MCPs Específicos (Instagram, ML, etc.) → MCP-Crew → Módulos Odoo
                                       ↓
                                  MCP-Chatwoot → Chatwoot
```

Nesta arquitetura:
1. Os MCPs específicos enviam dados para o MCP-Crew (cérebro central)
2. O MCP-Crew processa e encaminha para os módulos Odoo apropriados
3. O MCP-Crew também encaminha para o MCP-Chatwoot
4. O MCP-Chatwoot formata e envia para as caixas de entrada do Chatwoot

#### Benefícios

- **Centralização de Comunicações**: Todas as interações em um único lugar
- **Mobilidade**: Acesso via aplicativo mobile do Chatwoot
- **Redução de Duplicidade**: Interface unificada para todos os canais
- **Consistência**: Experiência padronizada para os usuários

#### Considerações Técnicas

- **Mapeamento de Canais**: Cada fonte mapeada para um canal no Chatwoot
- **Sincronização Bidirecional**: Respostas do Chatwoot são capturadas e encaminhadas de volta
- **Metadados e Contexto**: Informações adicionais enviadas como metadados
- **Isolamento Multi-tenant**: Prefixação com account_id em todas as operações

## Fluxos de Comunicação

### 1. Fluxo de Módulos Odoo para MCPs

```
Módulo Funcional → Módulo Integrador → [Cache Redis] → MCP-Crew → MCP Específico
```

1. O módulo funcional (ex: business_rules2) chama a API do Módulo Integrador
2. O Módulo Integrador verifica o cache Redis para dados existentes
3. Se não encontrado no cache, encaminha a solicitação para o MCP-Crew
4. O MCP-Crew roteia para o MCP específico apropriado
5. A resposta é armazenada no cache e retornada ao módulo funcional

### 2. Fluxo de Chatwoot para Agentes de IA

```
Chatwoot → Chatwoot Connector → MCP-Crew → [MCPs Específicos] → Resposta
```

1. O Chatwoot envia uma mensagem via webhook para o Chatwoot Connector
2. O Chatwoot Connector formata e encaminha para o MCP-Crew
3. O MCP-Crew determina a crew apropriada e coordena a resposta
4. Os MCPs específicos são consultados conforme necessário
5. A resposta é enviada de volta ao Chatwoot

## Otimização com Redis

### Estratégias de Cache

1. **Cache de Primeiro Nível**: No Módulo Integrador
   - Resultados frequentes de consultas
   - Dados de configuração
   - Tokens e sessões

2. **Cache de Segundo Nível**: No MCP-Crew
   - Estado de conversas
   - Contexto de agentes
   - Resultados intermediários

3. **Políticas de TTL**:
   - Dados transitórios: 5-15 minutos
   - Dados de sessão: 1-24 horas
   - Dados de configuração: 1-7 dias (com invalidação explícita em alterações)

### Estrutura de Chaves

```
{account_id}:{module}:{resource_type}:{resource_id}:{action}
```

Exemplos:
- `account_1:business_rules:rule:123:details`
- `account_2:products:search:electronics:results`
- `account_1:company:services:list`

### Economia de Tokens

A implementação de cache agressivo resultará em:

- Redução de 70-90% nas chamadas a APIs externas
- Economia significativa em custos de API de LLMs
- Respostas mais rápidas para consultas frequentes
- Melhor experiência do usuário com tempos de resposta reduzidos

## Considerações Multi-tenant

### Isolamento de Dados

- Prefixo `account_id` em todas as chaves de cache
- Conexão dinâmica com banco de dados específico do tenant no Odoo
- Coleções vetoriais separadas por tenant no Qdrant
- Configurações específicas por tenant no MongoDB

### Configuração por Tenant

- Credenciais específicas por tenant
- Regras de negócio personalizadas
- Personalização de comportamento de agentes
- Integrações específicas por tenant

## Implementação Prática

### 1. Módulo Integrador Universal

Baseado no módulo `odoo-integration-to-mcp-crew` existente, com expansões para:

- Suporte a todos os tipos de MCPs
- Implementação de cache agressivo
- API interna padronizada
- Configuração centralizada

### 2. Adaptação dos Módulos Funcionais

Modificações mínimas para utilizar a API do Módulo Integrador:

- Substituir chamadas diretas a APIs/webhooks por chamadas à API interna
- Manter a lógica de negócio existente
- Remover configurações duplicadas

### 3. Fortalecimento do MCP-Crew

Expansão do MCP-Crew existente para:

- Suportar todos os MCPs específicos
- Implementar roteamento inteligente
- Otimizar uso de cache
- Melhorar gerenciamento de contexto

### 4. Implementação do MCP-Odoo

Desenvolvimento do MCP-Odoo híbrido que:

- Expõe todas as funcionalidades do Odoo via MCP
- Implementa cache eficiente
- Suporta operações multi-tenant
- Integra-se com o MCP-Crew

## Benefícios da Arquitetura

1. **Simplificação Significativa**:
   - Redução de pontos de configuração
   - Fluxo de dados mais claro
   - Menos código duplicado

2. **Economia de Recursos**:
   - Uso otimizado de cache
   - Redução no consumo de tokens de LLM
   - Melhor desempenho geral

3. **Manutenção Facilitada**:
   - Configuração centralizada
   - Troubleshooting simplificado
   - Monitoramento unificado

4. **Escalabilidade Aprimorada**:
   - Fácil adição de novos MCPs
   - Suporte robusto para multi-tenancy
   - Preparação para crescimento futuro

5. **Segurança Reforçada**:
   - Gerenciamento centralizado de credenciais
   - Auditoria completa
   - Controle de acesso granular

## Próximos Passos

1. **Desenvolvimento do Módulo Integrador Universal**:
   - Expandir o módulo existente
   - Implementar estratégias de cache
   - Criar API interna padronizada

2. **Implementação do MCP-Odoo**:
   - Desenvolver com base nas implementações existentes
   - Integrar com Redis para cache
   - Implementar suporte multi-tenant

3. **Integração com MCP-Crew**:
   - Expandir para suportar todos os MCPs
   - Implementar roteamento inteligente
   - Otimizar gerenciamento de contexto

4. **Adaptação Gradual dos Módulos Funcionais**:
   - Começar com um módulo de cada vez
   - Testar exaustivamente
   - Refinar com base no feedback

## Conclusão

A arquitetura de integração universal proposta representa uma evolução significativa para o sistema ChatwootAI, simplificando a complexidade atual, otimizando o desempenho e preparando o sistema para crescimento futuro. Ao centralizar a comunicação através do Módulo Integrador Universal e maximizar o uso de cache via Redis, o sistema ganhará em eficiência, manutenibilidade e escalabilidade.

Esta abordagem permitirá que o ChatwootAI ofereça uma experiência de usuário excepcional, com agentes de IA capazes de acessar e utilizar eficientemente todas as informações necessárias para fornecer respostas precisas e contextualizadas, seguindo as regras de negócio específicas de cada tenant.
