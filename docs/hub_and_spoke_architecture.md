# Arquitetura Hub-and-Spoke no ChatwootAI

## Visão Geral

A arquitetura Hub-and-Spoke é um modelo de design de sistemas distribuídos onde múltiplos componentes (spokes) se comunicam através de um componente central (hub). No contexto do ChatwootAI, implementamos esta arquitetura para otimizar o fluxo de comunicação entre diferentes canais de entrada (WhatsApp, Instagram, etc.) e equipes funcionais especializadas (Vendas, Suporte, Agendamento, etc.).

![Diagrama da Arquitetura Hub-and-Spoke](https://miro.medium.com/v2/resize:fit:1400/1*KpFC3K-IgNjnXV5J0JF1Xw.png)

## Princípios Fundamentais

Nossa implementação da arquitetura Hub-and-Spoke segue cinco princípios fundamentais:

1. **Roteamento Direto**: As mensagens são encaminhadas diretamente para as equipes especializadas sem intermediários desnecessários, reduzindo latência e pontos de falha.

2. **Coordenação Centralizada**: O orquestrador mantém uma visão global do sistema e coordena a comunicação entre as equipes, garantindo consistência.

3. **Componentes Desacoplados**: Cada equipe opera de forma independente, comunicando-se através de interfaces bem definidas, facilitando a manutenção e evolução do sistema.

4. **Design Escalável**: Os componentes podem escalar independentemente com base na carga, permitindo alocação eficiente de recursos.

5. **Operação Resiliente**: Falhas em um componente não comprometem o sistema inteiro, garantindo alta disponibilidade.

## Componentes Principais

### 1. Hub Central (Chatwoot)

O Chatwoot atua como o hub central, recebendo todas as mensagens de diferentes canais e gerenciando o estado global das conversas. Ele é responsável por:

- Receber mensagens de múltiplos canais (WhatsApp, Instagram, etc.)
- Manter o histórico de conversas
- Fornecer uma interface unificada para os agentes humanos
- Integrar-se com o sistema de orquestração de agentes de IA

### 2. Orquestrador Central (OrchestratorAgent)

O Orquestrador é o componente mais crítico da arquitetura, responsável por:

- Analisar o conteúdo das mensagens recebidas
- Determinar qual equipe funcional é mais adequada para lidar com cada mensagem
- Manter uma visão de alto nível de todas as conversas ativas
- Garantir a distribuição eficiente do trabalho em todo o sistema
- Implementar estratégias de cache para otimizar o desempenho

O Orquestrador está implementado no módulo `src/core/hub.py` como parte dos componentes fundamentais do sistema.

```python
def route_message(self, message, context):
    # Analisa a mensagem e determina a equipe mais adequada
    # Utiliza histórico de conversa e perfil do cliente
    # Retorna decisão de roteamento com equipe, justificativa e nível de confiança
```

### 3. Gerenciador de Contexto (ContextManagerAgent)

O Gerenciador de Contexto é responsável por:

- Manter o contexto das conversas ao longo do tempo
- Garantir que todos os agentes tenham acesso às informações relevantes
- Implementar estratégias de persistência e recuperação de contexto
- Gerenciar a expiração e atualização de contextos

O Gerenciador de Contexto está implementado no módulo `src/core/hub.py` junto com os outros componentes centrais da arquitetura.

### 4. Agente de Integração (IntegrationAgent)

O Agente de Integração facilita a comunicação com sistemas externos:

- Integração com o Odoo para acesso a dados de clientes e produtos
- Recuperação e atualização de informações conforme necessário
- Implementação de cache para dados frequentemente acessados
- Tratamento de erros e fallbacks para garantir operação contínua

O Agente de Integração também está implementado no módulo `src/core/hub.py`, completando o trio de agentes centrais da arquitetura.

### 5. Equipes Funcionais (Spokes)

As equipes funcionais são especializadas em diferentes domínios:

- **Equipe de Vendas**: Lida com consultas sobre produtos, preços e pedidos
- **Equipe de Suporte**: Gerencia problemas técnicos e reclamações
- **Equipe de Agendamento**: Coordena agendamentos e disponibilidade
- **Equipe de CRM**: Gerencia relacionamento com clientes e programas de fidelidade
- **Equipe de Inventário**: Fornece informações sobre estoque e disponibilidade

## Fluxo de Dados

1. **Recebimento de Mensagem**: Uma mensagem é recebida através do Chatwoot de um canal específico.

2. **Processamento Inicial**: O HubCrew processa a mensagem e recupera ou cria o contexto da conversa.

3. **Análise e Roteamento**: O OrchestratorAgent analisa o conteúdo da mensagem e determina qual equipe funcional deve processá-la.

4. **Enriquecimento de Contexto**: O ContextManagerAgent atualiza o contexto da conversa com a nova mensagem e a decisão de roteamento.

5. **Processamento Especializado**: A equipe funcional apropriada processa a mensagem e gera uma resposta.

6. **Resposta ao Cliente**: A resposta é enviada de volta ao cliente através do Chatwoot.

## Otimizações de Desempenho

### Sistema de Cache em Dois Níveis

Implementamos um sistema de cache em dois níveis para otimizar o desempenho:

1. **Cache de Roteamento**: Decisões de roteamento são armazenadas em cache para mensagens similares, reduzindo a carga no modelo de linguagem.

2. **Cache de Dados**: Informações frequentemente acessadas (dados de clientes, produtos, regras de negócio) são armazenadas em cache para reduzir chamadas a sistemas externos.

### Processamento Assíncrono

O processamento de mensagens é realizado de forma assíncrona, permitindo:

- Maior throughput do sistema
- Melhor utilização de recursos
- Resposta mais rápida ao usuário para operações simples

## Escalabilidade

A arquitetura Hub-and-Spoke permite escalar componentes independentemente:

- **Escalabilidade Horizontal**: Adicionar mais instâncias de equipes funcionais específicas com base na demanda.
- **Escalabilidade Vertical**: Aumentar recursos para componentes críticos como o Orquestrador.
- **Particionamento**: Dividir o processamento por domínio de negócio ou região geográfica.

## Monitoramento e Observabilidade

Implementamos logging abrangente em todos os componentes:

- **Logs de Roteamento**: Registram decisões de roteamento com níveis de confiança.
- **Logs de Contexto**: Monitoram atualizações e recuperações de contexto.
- **Logs de Integração**: Rastreiam interações com sistemas externos.

## Considerações de Implementação

### Organização do Código

A implementação da arquitetura Hub-and-Spoke segue uma estrutura organizada:

- **Componentes Centrais** (`src/core/hub.py`): Contém os agentes principais do hub (Orquestrador, Gerenciador de Contexto e Agente de Integração)
- **Crews** (`src/crews/`): Implementações específicas de crews para diferentes funções
- **Agentes Adaptáveis** (`src/agents/adaptable/`): Agentes especializados que se adaptam ao domínio de negócio
- **Ferramentas** (`src/tools/`): Utilitários compartilhados por diferentes componentes

Esta organização reflete os princípios da arquitetura, mantendo os componentes centrais no diretório `core` e os componentes especializados em seus respectivos diretórios.

### Gerenciamento de Estado

O gerenciamento de estado é crítico na arquitetura Hub-and-Spoke:

- Utilizamos Redis para armazenamento de contexto de curto prazo
- Implementamos persistência em PostgreSQL para dados de longo prazo
- Mantemos histórico limitado para evitar crescimento descontrolado de contexto

### Tratamento de Erros

Implementamos estratégias robustas de tratamento de erros:

- **Fallbacks**: Rotas alternativas quando componentes falham
- **Retry Logic**: Tentativas automáticas para operações temporariamente falhas
- **Circuit Breakers**: Prevenção de falhas em cascata

### Segurança

Considerações de segurança importantes:

- **Isolamento de Dados**: Cada conversa tem seu próprio contexto isolado
- **Controle de Acesso**: Permissões granulares para diferentes equipes funcionais
- **Auditoria**: Registro de todas as decisões de roteamento e acessos a dados

## Conclusão

A arquitetura Hub-and-Spoke implementada no ChatwootAI oferece um equilíbrio ideal entre centralização e distribuição, permitindo:

- **Flexibilidade**: Fácil adição de novos canais e equipes funcionais
- **Eficiência**: Roteamento direto para processamento especializado
- **Escalabilidade**: Crescimento independente de componentes com base na demanda
- **Resiliência**: Operação contínua mesmo em caso de falhas parciais

Esta arquitetura forma a espinha dorsal do sistema ChatwootAI, permitindo uma experiência de atendimento ao cliente fluida, eficiente e escalável.
