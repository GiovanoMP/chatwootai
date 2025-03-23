# Estrutura de Agentes no ChatwootAI

Este diretório contém os agentes utilizados na arquitetura ChatwootAI. A estrutura atual é organizada da seguinte forma:

## Organização da Pasta `agents`

```
/agents/
├── base/                  # Classes base para todos os agentes
│   ├── functional_agent.py # Classe base para agentes funcionais
│   └── adaptable_agent.py  # Classe base para agentes adaptáveis
├── specialized/           # Agentes especializados em funções específicas
│   ├── sales_agent.py     # Agente especializado em vendas
│   ├── support_agent.py   # Agente especializado em suporte
│   └── scheduling_agent.py # Agente especializado em agendamentos
├── channel/               # Agentes para canais de comunicação
│   └── channel_agents.py  # Implementação dos agentes de canal
└── README.md             # Este arquivo de documentação
```

## Explicação dos Componentes

### 1. Agentes Base (`base/`)

A pasta `base/` contém as classes fundamentais que servem como base para todos os outros agentes:

- **FunctionalAgent** (`functional_agent.py`) - Classe base com funcionalidades comuns a todos os agentes funcionais
- **AdaptableAgent** (`adaptable_agent.py`) - Agente base com capacidade de adaptação a diferentes domínios de negócio

### 2. Agentes Especializados (`specialized/`)

A pasta `specialized/` contém agentes que implementam comportamentos específicos para diferentes funções de negócio:

- **SalesAgent** (`sales_agent.py`) - Vendas e recomendações de produtos
- **SupportAgent** (`support_agent.py`) - Suporte ao cliente e solução de problemas
- **SchedulingAgent** (`scheduling_agent.py`) - Agendamentos e gerenciamento de compromissos

### 3. Agentes de Canal (`channel/`)

A pasta `channel/` contém agentes responsáveis por processar mensagens de diferentes canais de comunicação (WhatsApp, Instagram, etc.):

- **ChannelCrew** - Orquestra o processamento de mensagens de um canal específico
- **MessageProcessorAgent** - Normaliza e processa mensagens brutas
- **ChannelMonitorAgent** - Monitora eventos e status do canal

## Fluxo de Processamento

1. **Canal** → **ChannelCrew** → **Hub** → **FunctionalCrew**

   - Mensagens chegam de um canal (WhatsApp, Instagram)
   - ChannelCrew pré-processa e normaliza a mensagem
   - Hub direciona para a FunctionalCrew adequada (vendas, suporte)
   - Agentes funcionais processam e geram respostas

## Interação com Outras Camadas

- **DataProxyAgent**: Todos os agentes funcionais utilizam o DataProxyAgent para acessar dados
- **PluginManager**: Os agentes adaptáveis usam plugins específicos para cada domínio
- **DomainManager**: Gerencia o domínio de negócio ativo que os agentes adaptáveis utilizam

## Observações Importantes

1. Nunca faça acesso direto a dados sem passar pelo DataProxyAgent
2. Ao adicionar novos agentes, siga a hierarquia existente
3. Os agentes adaptáveis devem verificar o domínio atual antes de processar mensagens
