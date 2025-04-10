# ChatwootAI - Sistema Inteligente de Atendimento Multi-Domínio e Omni Channel

![Versão](https://img.shields.io/badge/versão-4.0-blue)
![Status](https://img.shields.io/badge/status-em%20desenvolvimento-yellow)

## Visão Geral

O ChatwootAI é um sistema avançado de atendimento ao cliente que integra o Chatwoot como hub central de mensagens com uma arquitetura Hub and Spoke baseada em CrewAI. O sistema é projetado para ser multi-tenant, adaptando-se dinamicamente a diferentes domínios de negócio (cosméticos, saúde, varejo, etc.) através de configurações YAML.

## Arquitetura do Sistema

A arquitetura do ChatwootAI segue o modelo **Hub and Spoke** (Centro e Raios), com um hub central que coordena múltiplos componentes especializados. Esta arquitetura é modular e extensível, com componentes claramente separados e responsabilidades bem definidas:

### Componentes Principais

1. **Hub Central (`src/core/hub.py`)**
   - `HubCrew`: Orquestração principal de mensagens
   - `OrchestratorAgent`: Análise de intenção e roteamento inteligente
   - `ContextManagerAgent`: Gerenciamento do contexto da conversa
   - `IntegrationAgent`: Integrações com sistemas externos
   - `DataProxyAgent`: Único ponto de acesso a dados (componente crítico)

2. **Crews Especializadas (definidas em YAML)**
   - `SalesCrew`: Processamento de consultas e vendas de produtos
   - `SupportCrew`: Suporte técnico e atendimento a reclamações
   - `MarketingCrew`: Campanhas, promoções e engajamento
   - `SchedulingCrew`: Agendamentos e compromissos
   
   > **Importante**: Todas as crews, agentes e tarefas são definidos exclusivamente em arquivos YAML, não mais no código-fonte. O HubCrew apenas referencia essas definições para direcionar as conversas para as crews apropriadas.

3. **Camada de Dados**
   - `DataServiceHub`: Coordenação central de serviços de dados
   - `ProductDataService`: Acesso a dados de produtos
   - `CustomerDataService`: Acesso a dados de clientes
   - `DomainRulesService`: Regras de negócio específicas por domínio
   - `VectorSearchService`: Busca semântica em bases de conhecimento

4. **Gerenciamento de Domínios**
   - `DomainManager`: Carregamento e gestão de configurações YAML
   - Configurações específicas por domínio (cosméticos, saúde, varejo)
   - Adaptação dinâmica de comportamentos e respostas

5. **Sistema de Plugins**
   - `PluginManager`: Carregamento e gestão de plugins
   - Extensão de funcionalidades sem modificar o código principal

### Arquitetura Hub and Spoke

O ChatwootAI implementa uma arquitetura Hub and Spoke (Centro e Raios), onde:

- **Hub (Centro)**: O `HubCrew` atua como o centro de coordenação, recebendo todas as mensagens e roteando-as para os componentes especializados.

- **Spokes (Raios)**: As crews especializadas (SalesCrew, SupportCrew, etc.) atuam como raios que se conectam ao hub central, cada uma com responsabilidades específicas.

- **DataProxyAgent**: Atua como um hub secundário para acesso a dados, centralizando todas as operações de dados e conectando-se ao DataServiceHub.

Esta arquitetura oferece várias vantagens:

1. **Escalabilidade**: Novos spokes (crews) podem ser adicionados sem modificar o hub central
2. **Especialização**: Cada spoke pode se especializar em um domínio específico
3. **Resiliência**: Falhas em um spoke não afetam os demais
4. **Flexibilidade**: Spokes podem ser atualizados ou substituídos independentemente

### Arquitetura Multi-Tenant com GenericCrew

O ChatwootAI implementa uma arquitetura multi-tenant que permite mapear IDs de clientes do Chatwoot para configurações de domínio específicas. A implementação utiliza a `GenericCrew` como base para todas as crews, eliminando a necessidade de classes específicas para cada domínio:

#### Implementação da GenericCrew

A `GenericCrew` é uma classe base que permite a criação dinâmica de crews a partir de configurações YAML:

1. **Definição Dinâmica**:
   - Todas as crews são instâncias da classe `GenericCrew`
   - As características específicas (nome, agentes, tarefas) são definidas em YAML
   - Não há necessidade de criar novas classes para novos domínios ou tipos de crew

2. **CrewFactory**:
   - O `CrewFactory` é responsável por instanciar crews a partir de configurações YAML
   - Ele recebe um ID de crew (ex: "sales_crew") e um nome de domínio (ex: "cosmetics")
   - Carrega a configuração apropriada via `DomainManager` e cria uma instância de `GenericCrew`

3. **Estrutura das Configurações YAML**:
   - Cada domínio possui um arquivo `config.yaml` com definições de agentes e crews
   - As crews são definidas com nome, descrição, agentes e tarefas
   - As tarefas especificam qual agente executa cada etapa e qual o resultado esperado

#### Fluxo de Determinação de Domínio

1. **Recebimento do Webhook**:
   - Quando um webhook é recebido do Chatwoot, o `ChatwootWebhookHandler` extrai informações críticas
   - São extraídos: account_id, inbox_id, conversation_id e customer_id

2. **Identificação do Cliente via ClientMapper**:
   - O `ClientMapper` (src/core/client_mapper.py) identifica o cliente com base no account_id do Chatwoot
   - Utiliza o arquivo `config/chatwoot_mapping.yaml` para mapear account_id → cliente/domínio
   - Permite uma identificação precisa e configurável de clientes sem modificar o código

3. **Determinação do Domínio no Webhook Handler**:
   - O `ChatwootWebhookHandler` determina o domínio seguindo uma hierarquia de fontes:
     1. Primeiro tenta pelo account_id (nível da empresa)
     2. Se não encontrar, tenta pelo inbox_id (nível do canal)
     3. Por último, consulta metadados adicionais via API do Chatwoot
   - Esta abordagem segue o princípio de "processar os dados o mais próximo possível da fonte"

3. **Registro da Conversa no HubCrew**:
   - O webhook handler chama `hub_crew.register_conversation(conversation_id, customer_id, domain_name)`
   - O domínio já determinado é passado diretamente para o HubCrew
   - Isso evita consultas redundantes e segue o Princípio da Responsabilidade Única

4. **Inicialização no HubCrew**:
   - O `HubCrew` usa o domain_name recebido para inicializar o contexto da conversa
   - Somente se domain_name for None, ele tentará determinar com base no cliente
   - Carrega configurações específicas do domínio via `DomainManager`
   - Inicializa plugins específicos do domínio via `PluginManager`

5. **Criação Dinâmica de Crews**:
   - As crews são criadas sob demanda para cada conversa, não mais estaticamente
   - O `HubCrew` utiliza o `CrewFactory` para instanciar crews baseadas no domínio determinado
   - Exemplo: `crew_factory.create_crew("sales_crew", domain_name)` cria uma crew adaptada ao domínio

6. **Persistência e Cache**:
   - Configurações de domínio são armazenadas em cache via `MemorySystem`
   - O mapeamento account/inbox para domínio é configurável via variáveis de ambiente
   - Metadados de domínio podem ser armazenados nos metadados do inbox no Chatwoot

Este fluxo garante que, quando um cliente interage com o sistema, a configuração YAML correta é carregada dinamicamente, permitindo que o sistema se adapte às necessidades específicas de cada cliente.

### Tecnologias Utilizadas

- **Chatwoot**: Hub central de mensagens e interface com clientes
- **CrewAI**: Framework para orquestração de agentes inteligentes
- **Qdrant**: Banco de dados vetorial para busca semântica
- **Redis**: Cache distribuído e gerenciamento de estado
- **Odoo** (simulado): Sistema ERP para regras de negócio e dados

## Fluxo de Processamento de Mensagens

O ChatwootAI implementa um fluxo sofisticado de processamento de mensagens, com múltiplas camadas de análise e adaptação ao contexto. O sistema é projetado para determinar dinamicamente o domínio de negócio para cada conversa, garantindo que as respostas sejam sempre contextualizadas e relevantes:

### 1. Entrada da Mensagem e Determinação de Domínio
- Cliente envia mensagem pelo WhatsApp ou outro canal
- Chatwoot recebe a mensagem e a encaminha via webhook para o sistema
- O `ChatwootWebhookHandler` processa a requisição e extrai informações críticas:
  - account_id e inbox_id (para determinar o domínio)
  - conversation_id e customer_id (para identificação)
- O domínio é determinado diretamente no webhook handler seguindo uma hierarquia de fontes:
  1. Mapeamento de account_id para domínio (via arquivo `chatwoot_mapping.yaml`)
  2. Mapeamento de inbox_id para domínio (via arquivo `chatwoot_mapping.yaml`)
  3. Metadados do inbox via API do Chatwoot (usando o método `get_inbox()` do `ChatwootClient`)
  4. Domínio fallback (configurado via variável de ambiente `DEFAULT_DOMAIN`)

### 2. Processamento pelo Hub Central
- A mensagem é encaminhada para o `HubCrew` junto com o domínio já determinado
- O `HubCrew` instancia dinamicamente as crews necessárias para o domínio específico
- O `OrchestratorAgent` analisa a intenção da mensagem
- O `ContextManagerAgent` atualiza o contexto da conversa com informações do domínio

### 3. Roteamento para Crew Especializada
- Com base na análise de intenção, a mensagem é roteada para a crew apropriada
- A crew especializada é ativada com seus agentes e ferramentas
- Cada agente tem acesso apenas às ferramentas definidas em sua configuração YAML (as ferramentas estão disponíveis através do DataProxyAgent)

### 4. Acesso a Dados via DataProxyAgent
- Os agentes NUNCA acessam dados diretamente
- Todas as consultas são feitas exclusivamente através do `DataProxyAgent`
- O `DataProxyAgent` adapta as consultas ao domínio ativo
- As consultas são enriquecidas com informações contextuais do domínio
- O `DataProxyAgent` encaminha as consultas para o `DataServiceHub`, que coordena os serviços específicos:
  - `ProductDataService`: Para dados de produtos
  - `CustomerDataService`: Para dados de clientes
  - `DomainRulesService`: Para regras de negócio específicas
  - `VectorSearchService`: Para buscas semânticas
  - `MemorySystem`: Para consultas ao histórico e memória

### 5. Processamento e Geração de Resposta
- A crew especializada processa os dados recebidos
- Uma resposta personalizada é gerada considerando:
  - O domínio ativo (ex: linguagem específica para cosméticos)
  - O histórico da conversa
  - As regras de negócio aplicáveis
  - As preferências do cliente

### 6. Retorno da Resposta
- A resposta é enviada de volta ao `HubCrew`
- O `HubCrew` a encaminha para o Chatwoot
- O Chatwoot entrega a resposta ao cliente via canal original

## Exemplo de Fluxo de Conversa

### Cenário: Cliente pergunta sobre produto em domínio de cosméticos

1. **Cliente envia mensagem pelo WhatsApp**: "Vocês têm creme para as mãos?"

2. **Fluxo de Processamento**:
   - Chatwoot recebe a mensagem e envia para o webhook
   - `ChatwootWebhookHandler` determina o domínio "cosmetics" com base no account_id/inbox_id
   - `HubCrew` recebe a mensagem junto com o domínio já determinado
   - `OrchestratorAgent` identifica intenção de consulta de produto
   - `ContextManagerAgent` registra a consulta no histórico
   - Sistema verifica que o domínio ativo é "cosméticos"
   - Mensagem é roteada para `SalesCrew`

3. **Processamento pela SalesCrew**:
   - `SalesAgent` (definido em YAML) formula consulta estruturada
   - `SalesAgent` solicita dados ao `DataProxyAgent`
   - `DataProxyAgent` adapta a consulta ao domínio "cosméticos"
   - `DataProxyAgent` encaminha a consulta para o `DataServiceHub`
   - `DataServiceHub` direciona para o `ProductDataService` apropriado
   - `ProductDataService` consulta o catálogo de produtos
   - Resultados retornam pelo `DataServiceHub` ao `DataProxyAgent`
   - Resultados são filtrados e formatados pelo `DataProxyAgent`
   - Dados são retornados ao `SalesAgent`

4. **Geração de Resposta**:
   - `SalesAgent` analisa os dados recebidos
   - Gera resposta personalizada: "Sim, temos vários cremes para mãos! Nosso mais vendido é o Hidratante Intensivo com Manteiga de Karité, ideal para peles ressecadas. Também temos a versão com Ácido Hialurônico para uma hidratação mais leve. Posso dar mais detalhes sobre algum deles?"

5. **Retorno ao Cliente**:
   - Resposta volta para o `HubCrew`
   - `HubCrew` encaminha para o Chatwoot
   - Chatwoot entrega a mensagem ao cliente via WhatsApp

## Princípios Arquiteturais

1. **Arquitetura Hub and Spoke**: Hub central (HubCrew) coordena componentes especializados (Crews)
2. **Centralização do acesso a dados**: Todo acesso a dados passa obrigatoriamente pelo `DataProxyAgent`
3. **Adaptabilidade multi-domínio**: Comportamentos específicos por domínio via configurações YAML
4. **Desacoplamento de componentes**: Interfaces claras entre módulos para facilitar manutenção
5. **Extensibilidade via plugins**: Novas funcionalidades sem alterar o código principal
6. **Orquestração centralizada**: Fluxo coordenado pelo `HubCrew` para garantir consistência

## Configuração e Personalização

### Configuração de Domínios

O sistema é altamente configurável através de arquivos YAML localizados em `/config/domains/`:

```
/config
  /domains
    /_base            # Configurações base herdadas por todos os domínios
      base_agents.yaml
      base_tools.yaml
    /cosmetics        # Configurações específicas para o domínio de cosméticos
      config.yaml
    /health           # Configurações específicas para o domínio de saúde
      config.yaml
    /retail           # Configurações específicas para o domínio de varejo
      config.yaml
```

Cada domínio pode personalizar:
- Comportamento e características dos agentes
- Ferramentas disponíveis para cada agente
- Fluxos de trabalho e etapas de processamento
- Regras de negócio específicas do domínio

### Mapeamento de Contas e Inboxes para Domínios

O sistema utiliza um arquivo de configuração YAML (`config/chatwoot_mapping.yaml`) para mapear accounts e inboxes do Chatwoot para domínios específicos:

```yaml
accounts:
  "1": "cosmetics"  # Account ID 1 usa o domínio de cosméticos
  "2": "health"     # Account ID 2 usa o domínio de saúde
  "3": "retail"     # Account ID 3 usa o domínio de varejo

inboxes:
  "1": "cosmetics"  # Inbox ID 1 usa o domínio de cosméticos
  "2": "health"     # Inbox ID 2 usa o domínio de saúde
  "3": "retail"     # Inbox ID 3 usa o domínio de varejo
  "4": "cosmetics"  # Inbox ID 4 usa o domínio de cosméticos
```

### Mecanismo de Fallback

O sistema implementa um mecanismo de fallback para garantir que todas as mensagens sejam processadas, mesmo quando não é possível determinar o domínio específico:

1. **Domínio Fallback**: Configurado via variável de ambiente `DEFAULT_DOMAIN` (padrão: "cosmetics")
2. **Uso do Fallback**: O domínio fallback é usado apenas quando:
   - O account_id não está mapeado em `chatwoot_mapping.yaml`
   - Ocorre um erro ao carregar o mapeamento de clientes

## Estrutura de Configuração

O ChatwootAI utiliza uma estrutura de configuração baseada em YAML para definir comportamentos específicos por domínio e cliente:

### Mapeamento de Clientes

```
config/chatwoot_mapping.yaml
```

Este arquivo mapeia os account_ids e inbox_ids do Chatwoot para clientes e domínios específicos:

```yaml
mappings:
  # Mapeamento por account_id (preferencial)
  accounts:
    "1":
      client_id: "client_1"
      domain: "cosmetics"
    "2":
      client_id: "client_2"
      domain: "cosmetics"
    "3":
      client_id: "client_3"
      domain: "health"
  
  # Mapeamento por inbox_id (fallback)
  inboxes:
    "101":
      client_id: "client_1"
      domain: "cosmetics"
```

### Estrutura de Domínios

```
config/domains/
```

A estrutura de diretórios segue o padrão:

```
config/domains/
  ├── _base/                # Configurações base para todos os domínios
  ├── cosmetics/            # Domínio de cosméticos
  │   ├── config.yaml       # Configuração geral do domínio
  │   ├── client_1/         # Cliente específico no domínio
  │   │   └── config.yaml   # Configuração específica do cliente
  │   └── client_2/
  │       └── config.yaml
  └── health/               # Domínio de saúde
      ├── config.yaml
      └── client_3/
          └── config.yaml
```

Esta estrutura permite:
1. Configurações compartilhadas em `_base/`
2. Configurações específicas por domínio
3. Customizações por cliente dentro de cada domínio
   - O inbox_id não está mapeado em `chatwoot_mapping.yaml`
   - Não foi possível obter metadados adicionais via API do Chatwoot

> **Nota Importante**: O domínio fallback é apenas uma rede de segurança e não representa uma dependência do sistema em um domínio específico. Em uma implementação futura, será criado um domínio "_generic" totalmente neutro em termos de negócio para servir como fallback universal.

## Testes e Validação

O sistema inclui testes automatizados para validar o funcionamento correto de todos os componentes:

1. **Testes Unitários**: Validam o funcionamento isolado de cada componente
2. **Testes de Integração**: Validam a interação entre componentes
3. **Testes End-to-End**: Simulam o fluxo completo do sistema, incluindo a identificação de clientes

### Testes de Identificação de Clientes

Um aspecto crítico do sistema é a identificação correta dos clientes com base no `account_id` do Chatwoot. O arquivo `tests/integration/end_to_end_test.py` contém testes que validam:

1. A identificação correta do cliente via `ClientMapper` usando o `account_id`
2. O carregamento da configuração específica do cliente e domínio
3. O processamento da mensagem pelo `HubCrew` e roteamento para a crew especializada
4. A consulta de dados via `DataProxyAgent`
5. A geração e envio da resposta de volta ao cliente

Esses testes são fundamentais para garantir que o sistema identifique corretamente os clientes e processe as mensagens de acordo com as configurações específicas de cada domínio e cliente.

Para executar os testes:

```bash
# Testes unitários
python -m pytest tests/unit

# Testes de integração
python -m pytest tests/integration

# Testes end-to-end (fluxo completo com identificação de cliente)
python tests/integration/end_to_end_test.py
```

### Ferramentas de Monitoramento

O sistema inclui ferramentas para monitoramento e diagnóstico:

```bash
# Monitor de mapeamento de clientes (verifica logs em tempo real)
python scripts/monitoring/client_mapping_monitor.py

# Executor de testes com monitoramento detalhado
python scripts/testing/run_e2e_test.py
```

Estas ferramentas ajudam a verificar se o sistema está identificando corretamente os clientes e processando as mensagens conforme esperado.

## Próximos Passos

- Finalização dos testes de fluxo completo com GenericCrew
- Implementação de testes para diferentes domínios de negócio
- Expansão do sistema de plugins para funcionalidades avançadas
- Otimização de performance para processamento em larga escala
- Integração com sistemas adicionais de análise e relatórios

## Contribuição

O projeto está em desenvolvimento ativo. Para contribuir:
1. Siga as convenções de código existentes
2. Documente todas as alterações
3. Mantenha a arquitetura modular e desacoplada
4. Teste exaustivamente antes de submeter alterações

---

Desenvolvido com ❤️ pela Equipe ChatwootAI
