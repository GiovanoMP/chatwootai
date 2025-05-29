# Arquitetura do MCP-Crew

## Visão Geral

O MCP-Crew é um protocolo central de contexto para modelos (Model Context Protocol) projetado para gerenciar múltiplas crews de agentes de IA de forma eficiente, escalável e segura. Este sistema atua como um "cérebro central" que coordena a comunicação entre diferentes crews especializadas (Mercado Livre, Instagram, Facebook, etc.) e facilita a integração com diversos serviços externos.

## Princípios de Design

1. **Modularidade**: Componentes independentes que podem ser desenvolvidos, testados e escalados separadamente
2. **Extensibilidade**: Facilidade para adicionar novas crews, MCPs e funcionalidades
3. **Escalabilidade**: Capacidade de lidar com aumento de carga e complexidade
4. **Segurança**: Controle granular de permissões e auditoria de ações
5. **Performance**: Otimização para operações de alta demanda com caching e processamento paralelo

## Arquitetura de Alto Nível

```
┌─────────────────────────────────────────────────────────────────┐
│                           MCP-Crew                              │
│                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐  │
│  │             │    │             │    │                     │  │
│  │  Gerenciador│    │ Gerenciador │    │    Gerenciador      │  │
│  │  de Agentes │    │    de       │    │        de           │  │
│  │             │◄──►│ Autorização │◄──►│    Comunicação      │  │
│  │             │    │             │    │                     │  │
│  └─────────────┘    └─────────────┘    └─────────────────────┘  │
│         ▲                  ▲                     ▲              │
│         │                  │                     │              │
│         ▼                  ▼                     ▼              │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐  │
│  │             │    │             │    │                     │  │
│  │ Gerenciador │    │  Redis      │    │    Conectores       │  │
│  │ de Contexto │◄──►│ Integration │◄──►│    de MCPs          │  │
│  │             │    │             │    │                     │  │
│  └─────────────┘    └─────────────┘    └─────────────────────┘  │
│                                               ▲                 │
└───────────────────────────────────────────────┼─────────────────┘
                                                │
                                                ▼
                  ┌─────────────────────────────────────────────┐
                  │                                             │
                  │              MCPs Específicos               │
                  │  (Mercado Livre, Instagram, Facebook, etc)  │
                  │                                             │
                  └─────────────────────────────────────────────┘
```

## Componentes Principais

### 1. Gerenciador de Agentes (`agent_manager.py`)

Responsável pelo ciclo de vida dos agentes de IA, incluindo:

- Registro e remoção de agentes
- Atribuição de papéis e responsabilidades
- Agrupamento de agentes em crews especializadas
- Monitoramento de status e desempenho

**Classes Principais**:
- `Agent`: Representa um agente individual com ID, nome, papel e capacidades
- `AgentManager`: Gerencia o ciclo de vida dos agentes

### 2. Gerenciador de Autorização (`auth_manager.py`)

Controla permissões e aprovações para ações dos agentes:

- Políticas de autorização configuráveis
- Níveis de permissão granulares
- Sistema de aprovação para ações críticas
- Auditoria completa de ações

**Classes Principais**:
- `AuthorizationPolicy`: Define regras de acesso
- `AuthManager`: Aplica políticas e gerencia aprovações
- `AuditLog`: Registra ações para auditoria

### 3. Gerenciador de Comunicação (`communication.py`)

Facilita a comunicação entre agentes, crews e sistemas externos:

- Protocolos padronizados para troca de mensagens
- Roteamento inteligente de mensagens
- Filas de prioridade para mensagens
- Suporte para comunicação síncrona e assíncrona

**Classes Principais**:
- `Message`: Representa uma mensagem no sistema
- `CommunicationProtocol`: Gerencia o roteamento e entrega de mensagens
- `MessageHandler`: Interface para processadores de mensagens

### 4. Gerenciador de Contexto (`context_manager.py`)

Mantém o estado e o contexto das interações:

- Armazenamento de histórico de conversas
- Persistência de estado entre interações
- Gerenciamento de memória de curto e longo prazo
- Expiração automática de dados temporários

**Classes Principais**:
- `Context`: Representa um contexto no sistema
- `ContextManager`: Gerencia o ciclo de vida dos contextos

### 5. Conectores de MCPs (`mcp_connector.py`)

Integra o MCP-Crew com MCPs específicos:

- Interface padronizada para todos os MCPs
- Adaptadores específicos para cada plataforma
- Tradução de protocolos
- Gerenciamento de autenticação

**Classes Principais**:
- `MCPConnector`: Interface base para conectores
- `MercadoLivreMCPConnector`: Implementação específica para Mercado Livre
- `MCPConnectorRegistry`: Registro de conectores disponíveis

### 6. Integração com Redis

Otimiza o desempenho e a escalabilidade:

- Cache de alta velocidade para dados frequentes
- Filas para processamento assíncrono
- Pub/Sub para comunicação em tempo real
- Armazenamento de estado distribuído

## Fluxos de Comunicação

### Entre Agentes e Crews

1. **Baseado em Eventos**: Comunicação assíncrona via sistema de eventos
2. **Mensagens Estruturadas**: Formato padronizado para todas as mensagens
3. **Contexto Compartilhado**: Acesso a contexto comum quando necessário

### Entre MCP-Crew e MCPs Específicos

1. **API RESTful**: Interface HTTP para comunicação com MCPs
2. **Webhooks**: Para notificações assíncronas de MCPs
3. **Adaptadores**: Tradução entre protocolos específicos e o protocolo interno

## Estratégia de Autorização

### Níveis de Permissão

1. **READ**: Apenas leitura de dados
2. **EXECUTE**: Execução de ações pré-aprovadas
3. **WRITE**: Modificação de dados
4. **ADMIN**: Controle administrativo completo

### Tipos de Ações

1. **QUERY**: Consulta de informações
2. **DATA_MODIFICATION**: Modificação de dados
3. **COMMUNICATION**: Comunicação com outros agentes/sistemas
4. **SYSTEM**: Operações de sistema
5. **AUTONOMOUS**: Ações autônomas

## Extensibilidade

### Adição de Novas Crews

1. Criar uma classe que herda de `BaseCrew`
2. Implementar métodos específicos da crew
3. Registrar a crew no MCP-Crew

### Adição de Novos MCPs

1. Criar uma classe que implementa a interface `MCPConnector`
2. Implementar métodos específicos do MCP
3. Registrar o conector no MCP-Crew

## Integração com o MCP do Mercado Livre

O MCP-Crew se integra com o MCP do Mercado Livre através do conector `MercadoLivreMCPConnector`, que:

1. Gerencia autenticação OAuth 2.0 com o Mercado Livre
2. Mapeia operações para endpoints específicos da API
3. Lida com renovação de tokens e erros de comunicação
4. Traduz dados entre o formato do Mercado Livre e o formato interno do MCP-Crew

## Considerações de Segurança

1. **Autenticação Robusta**: Para todas as integrações externas
2. **Autorização Granular**: Controle preciso sobre o que cada agente pode fazer
3. **Auditoria Completa**: Registro detalhado de todas as ações
4. **Sanitização de Dados**: Validação de todas as entradas externas
5. **Secrets Management**: Armazenamento seguro de credenciais
