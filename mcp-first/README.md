# ChatwootAI: Arquitetura MCP First

## Visão Geral

ChatwootAI é uma plataforma de atendimento omnichannel baseada em IA que integra Odoo ERP, Chatwoot, e agentes de IA especializados através do Model Context Protocol (MCP). A arquitetura "MCP First" permite uma comunicação padronizada entre todos os componentes, resultando em um sistema multi-tenant altamente flexível, escalável e inteligente.

## Princípios da Arquitetura MCP First

- **Padronização Universal**: Todos os componentes se comunicam através do protocolo MCP
- **Descoberta Dinâmica**: Agentes descobrem ferramentas disponíveis em tempo de execução
- **Modularidade**: Componentes podem ser substituídos sem impactar o sistema como um todo
- **Multi-tenant**: Isolamento completo de dados e configurações entre tenants usando `account_id`
- **Extensibilidade**: Novos componentes podem ser adicionados facilmente

## Componentes Principais

### 1. Odoo ERP (Núcleo de Negócios)
- Base do sistema com módulos personalizados (`company_services`, `business_rules2`, etc.)
- Odoo Bot aprimorado como agente central de IA
- Webhook para sincronização de dados com MongoDB

### 2. Chatwoot (Hub de Comunicação)
- Gerenciamento centralizado de múltiplos canais de comunicação
- Integração com WhatsApp, Facebook, Instagram, Email e chat no site
- Webhook para notificação de novas mensagens

### 3. AI Stack (Inteligência e Conhecimento)
- **MongoDB**: Armazenamento de configurações enviadas pelo Odoo
- **Qdrant**: Armazenamento vetorial para busca semântica
- **CrewAI**: Orquestração de equipes de agentes especializados por canal
- **Serviço de Vetorização**: Conversão de textos em embeddings vetoriais

### 4. MCP Layer (Camada de Integração)
- **MCP-Odoo**: Interface para acesso e manipulação de dados do Odoo (adaptado do existente)
- **MCP-MongoDB**: Interface para acesso às configurações (implementação oficial)
- **MCP-Qdrant**: Interface para consulta e atualização de bases vetoriais (implementação oficial)
- **MCP-Redis**: Cache e gerenciamento de estado (implementação oficial, opcional)
- **MCP-Chatwoot**: Interface para gerenciamento de comunicações (a ser implementado posteriormente)

## Fluxo de Processamento Multi-tenant

1. Cliente envia mensagem através de um canal (WhatsApp, Facebook, etc.)
2. Chatwoot recebe a mensagem e a encaminha para o sistema via webhook com `account_id`
3. Sistema identifica o tenant baseado no `account_id` e carrega configurações específicas do MongoDB
4. Com base no canal de origem, o sistema ativa a crew correspondente
5. A crew consulta bases de conhecimento via MCP-Qdrant usando coleções específicas do tenant
6. Se necessário, a crew verifica dados em tempo real via MCP-Odoo conectando ao banco de dados do tenant
7. A resposta é formulada e enviada de volta ao cliente através do Chatwoot

## Implementações MCP Existentes

Utilizaremos implementações MCP oficiais e comunitárias:

- **MCP-Odoo**: Adaptação do MCP-Odoo existente ou [github.com/tuanle96/mcp-odoo](https://github.com/tuanle96/mcp-odoo)
- **MCP-MongoDB**: [github.com/mongodb-developer/mongodb-mcp-server](https://github.com/mongodb-developer/mongodb-mcp-server)
- **MCP-Qdrant**: [github.com/qdrant/mcp-server-qdrant](https://github.com/qdrant/mcp-server-qdrant)
- **MCP-Redis**: [github.com/redis/mcp-redis](https://github.com/redis/mcp-redis) (opcional)

## Estrutura do Repositório

```
mcp-first/
├── docs/                      # Documentação detalhada
│   ├── architecture.md        # Visão geral da arquitetura
│   ├── mcp-protocol.md        # Detalhes do protocolo MCP
│   ├── multi-tenant.md        # Arquitetura multi-tenant
│   ├── integration-guide.md   # Guia de integração
│   └── deployment.md          # Instruções de implantação
│
├── docker/                    # Configurações Docker
│   ├── mcp-odoo/              # Containerização do MCP-Odoo
│   ├── mcp-mongodb/           # Containerização do MCP-MongoDB
│   ├── mcp-qdrant/            # Containerização do MCP-Qdrant
│   └── docker-compose.yml     # Composição de todos os serviços
│
├── src/                       # Código-fonte
│   ├── crewai/                # Implementação de crews especializadas
│   │   ├── whatsapp_crew/     # Crew para WhatsApp
│   │   ├── facebook_crew/     # Crew para Facebook
│   │   └── email_crew/        # Crew para Email
│   └── mcp-chatwoot/          # Implementação futura para Chatwoot
│
└── examples/                  # Exemplos de uso
    ├── whatsapp-flow/         # Fluxo de atendimento WhatsApp
    ├── product-search/        # Busca de produtos via MCP
    └── order-creation/        # Criação de pedidos via MCP
```

## Roadmap de Implementação

### Fase 1: Fundação (2-3 meses)
- Containerizar MCP-Odoo existente
- Integrar MCP-MongoDB oficial
- Integrar MCP-Qdrant oficial
- Desenvolver WhatsAppCrew básica com suporte multi-tenant

### Fase 2: Expansão (3-4 meses)
- Melhorar integração com serviço de vetorização
- Desenvolver crews para canais adicionais
- Implementar cache com MCP-Redis
- Melhorar orquestração de agentes

### Fase 3: Integração Avançada (4-6 meses)
- Desenvolver MCP-Chatwoot
- Implementar análise de desempenho
- Desenvolver dashboards de monitoramento
- Implementar sistema de feedback e aprendizado

### Fase 4: Multi-ERP (Futuro)
- Desenvolver camada de abstração universal
- Criar conectores MCP para outros ERPs
- Implementar mapeamento semântico entre ERPs
- Desenvolver dashboard unificado

## Próximos Passos

1. Baixar e configurar implementações MCP oficiais (MongoDB, Qdrant)
2. Containerizar MCP-Odoo existente
3. Implementar prova de conceito com WhatsAppCrew
4. Baixar e configurar módulos Odoo necessários

## Documentação Adicional

Para mais detalhes sobre a arquitetura e implementação, consulte os documentos na pasta `docs/`.
