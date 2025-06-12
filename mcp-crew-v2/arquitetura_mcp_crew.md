# Arquitetura e Design do Sistema MCP-Crew

## 1. Visão Geral da Arquitetura MCP-First para CrewAI

O sistema MCP-Crew é concebido como o cérebro central de uma arquitetura multi-agente distribuída, seguindo o paradigma **MCP-First**. Isso significa que cada fonte de dados ou capacidade de ação é abstraída e exposta através de um Model Context Protocol (MCP) específico. O MCP-Crew, por sua vez, orquestra a interação entre diferentes Crews (equipes de agentes) e esses MCPs, garantindo que as operações sejam realizadas de forma contextualizada, eficiente e segura, especialmente em um ambiente multi-tenant.

A arquitetura proposta visa a máxima modularidade, escalabilidade e resiliência, com o Redis desempenhando um papel fundamental na otimização de performance e na gestão de estado e contexto. A integração com o Odoo, tanto para consumo quanto para operação, é um pilar central, com a visão de um agente universal no Odoo que possa interagir com o sistema via linguagem natural.

### Diagrama de Arquitetura Geral

```mermaid
graph TD
    subgraph Odoo ERP
        OdooModules[Módulos Funcionais Odoo] --> UniversalIntegrator[Módulo Integrador Universal]
    end

    UniversalIntegrator --> RedisCache[Redis Cache]
    RedisCache --> MCPCrew[MCP-Crew (Cérebro Central)]

    MCPCrew -- Gerenciamento de Contexto & Orquestração --> SpecificMCPs

    subgraph SpecificMCPs[MCPs Específicos]
        MCPMongo[MCP-MongoDB] -- ATA de Comportamento & Configuração --> MCPCrew
        MCPQdrant[MCP-Qdrant] -- Coleções Vetorizadas --> MCPCrew
        MCPChatwoot[MCP-Chatwoot] -- Entrada/Saída de Mensagens --> MCPCrew
        MCPOdoo[MCP-Odoo] -- Operações ERP --> MCPCrew
        OtherMCPs[Outros MCPs (Social, Marketplaces, etc.)] --> MCPCrew
    end

    MCPCrew -- Delegação de Tarefas --> Crews

    subgraph Crews[Crews de Agentes CrewAI]
        WhatsAppCrew[WhatsApp Crew] --> MCPChatwoot
        FacebookCrew[Facebook Crew] --> MCPChatwoot
        OdooOperationCrew[Odoo Operation Crew] --> MCPOdoo
        ResearchCrew[Research Crew] --> MCPQdrant
        BehavioralCrew[Behavioral Crew] --> MCPMongo
        OtherCrews[Outras Crews Especializadas] --> SpecificMCPs
    end

    MCPChatwoot -- Webhook --> Chatwoot[Chatwoot (Plataforma de Comunicação)]
    Chatwoot --> MCPChatwoot

    style UniversalIntegrator fill:#f9f,stroke:#333,stroke-width:2px
    style MCPCrew fill:#ccf,stroke:#333,stroke-width:2px
    style RedisCache fill:#ffc,stroke:#333,stroke-width:2px
    style OdooModules fill:#cfc,stroke:#333,stroke-width:2px
    style SpecificMCPs fill:#fcf,stroke:#333,stroke-width:2px
    style Crews fill:#cff,stroke:#333,stroke-width:2px
    style Chatwoot fill:#fcc,stroke:#333,stroke-width:2px
```

### 1.1. Fluxos de Comunicação Chave

1.  **Odoo para MCP-Crew (e MCPs):** Módulos funcionais do Odoo interagem com o `Módulo Integrador Universal`. Este módulo atua como um proxy inteligente, utilizando o `Redis Cache` para otimização e encaminhando as requisições para o `MCP-Crew`. O `MCP-Crew` então roteia para o `MCP Específico` apropriado (ex: `MCP-Odoo` para operações no ERP, `MCP-Qdrant` para busca semântica).
2.  **Comunicação Externa (Chatwoot) para MCP-Crew:** Mensagens de plataformas como WhatsApp ou Facebook chegam ao `MCP-Chatwoot` via webhooks do Chatwoot. O `MCP-Chatwoot` formata e encaminha essas mensagens para o `MCP-Crew`. O `MCP-Crew` determina a `Crew` apropriada com base no canal e no contexto do tenant, e orquestra a resposta, que pode envolver a consulta a outros `MCPs Específicos`.
3.  **MCP-Crew para Crews de Agentes:** O `MCP-Crew` é responsável por instanciar e gerenciar as `Crews` de agentes CrewAI. Com base na solicitação recebida e no contexto do tenant, ele seleciona a `Crew` mais adequada para a tarefa. As `Crews` utilizam os `MCPs Específicos` como ferramentas para interagir com o mundo exterior (Odoo, MongoDB, Qdrant, etc.).
4.  **Redis como Camada de Otimização:** O `Redis Cache` é utilizado em múltiplos pontos para reduzir a latência e o consumo de tokens de LLMs. Ele armazena contexto de conversas, resultados de consultas frequentes, embeddings e configurações por tenant, com políticas de TTL (Time-To-Live) otimizadas.

## 2. Componentes Principais e Suas Responsabilidades

### 2.1. Módulo Integrador Universal (no Odoo)

Este módulo é a porta de entrada para as funcionalidades do sistema multi-agente a partir do Odoo. Ele abstrai a complexidade da comunicação com os MCPs e o MCP-Crew, oferecendo uma API consistente para os módulos funcionais do Odoo.

**Responsabilidades:**
*   **Configuração Centralizada:** Gerencia credenciais, endpoints e configurações específicas de cada tenant para os MCPs e o MCP-Crew.
*   **Cache Inteligente:** Implementa estratégias de cache agressivas usando Redis para resultados de consultas frequentes, dados de configuração e tokens/sessões, reduzindo chamadas externas e custos de LLM.
*   **API Interna:** Fornece uma interface padronizada para os módulos funcionais do Odoo interagirem com o sistema multi-agente.
*   **Gerenciamento Multi-tenant:** Garante o isolamento de dados e configurações por tenant, prefixando chaves de cache e roteando requisições com base no `account_id`.
*   **Auditoria e Logging:** Registra detalhadamente todas as operações para fins de troubleshooting e monitoramento.
*   **Conectores MCP:** Interfaces para comunicação com diferentes MCPs, adaptando as requisições do Odoo para o formato esperado pelos MCPs.
*   **Gerenciamento de Sessão:** Mantém e renova automaticamente tokens de autenticação para os serviços externos.
*   **Roteamento Inteligente:** Direciona as solicitações para o MCP apropriado com base na natureza da requisição.
*   **Tratamento de Erros:** Implementa estratégias de retry e fallback para operações críticas, aumentando a resiliência do sistema.

### 2.2. MCP-Crew (Cérebro Central)

O MCP-Crew é o orquestrador principal do sistema multi-agente. Ele recebe requisições do Módulo Integrador Universal (Odoo) ou diretamente de MCPs de entrada (como MCP-Chatwoot), determina a Crew de agentes mais adequada para a tarefa e coordena a execução, utilizando os MCPs específicos como ferramentas.

**Responsabilidades:**
*   **Gerenciamento de Agentes e Crews:** Controla o ciclo de vida das Crews de agentes CrewAI, instanciando-as e gerenciando seus estados.
*   **Motor de Decisão/Roteamento:** Com base no contexto da requisição (canal de entrada, `account_id`, intenção do usuário), determina qual Crew de agentes deve ser ativada e quais MCPs específicos devem ser utilizados.
*   **Gerenciamento de Contexto:** Mantém o contexto da conversa e das interações entre os agentes e os MCPs, utilizando o Redis para memória persistente e temporária.
*   **Integração com Redis:** Utiliza o Redis para cache de resultados intermediários, estado de conversas e memória de agentes, otimizando a performance e reduzindo o uso de LLMs.
*   **Agregação de Resultados:** Combina os resultados de múltiplos MCPs ou Crews quando uma tarefa exige informações de diferentes fontes.
*   **Autorização e Permissões:** Garante que os agentes e Crews acessem apenas os recursos e dados permitidos para o `account_id` em questão.
*   **Delegação de Decisões:** Implementa lógica para delegar decisões baseadas no comportamento configurado por tenant (obtido via MCP-MongoDB).

### 2.3. MCPs Específicos

São servidores especializados que abstraem a complexidade de diferentes sistemas e fontes de dados, expondo suas funcionalidades de forma padronizada para o MCP-Crew e as Crews de agentes. Cada MCP é responsável por interagir com um sistema externo específico.

**MCPs Atuais e Futuros:**
*   **MCP-MongoDB:** Interage com o MongoDB para armazenar e recuperar a ATA de comportamento e configuração por tenant (formato JSON). Isso inclui como os agentes devem se comportar (alegre, formal, objetivo), horários de atendimento, e serviços disponíveis (agendamento, delivery, produtos, etc.).
*   **MCP-Qdrant:** Interage com o Qdrant para gerenciar e consultar coleções vetorizadas (embeddings) de Produtos, Agendamentos, Regras de Negócio, etc., com flags de ativação semântica e detalhada. Essencial para busca de informações contextuais e relevantes.
*   **MCP-Chatwoot:** Atua como a principal interface de entrada e saída de mensagens para canais como WhatsApp, Facebook, etc. Recebe webhooks do Chatwoot e envia respostas de volta para a plataforma. É responsável por formatar as mensagens para o MCP-Crew e vice-versa.
*   **MCP-Redis:** Embora o Redis seja usado em todo o sistema, um MCP-Redis dedicado pode ser considerado para operações mais complexas ou para expor funcionalidades específicas do Redis como ferramentas para agentes (ex: manipulação de listas, sets, etc.).
*   **MCP-Odoo (Futuro):** Permitirá que os agentes consultem e operem o ERP Odoo. Exemplos incluem verificar disponibilidade de produtos, registrar pedidos de venda, consultar dados de clientes, etc. Será crucial para o Agente Odoo Operador.
*   **Outros MCPs:** MCP-Social (redes sociais), MCP-Marketplaces (Mercado Livre, Amazon, Shopee), etc., serão adicionados conforme a necessidade.

**Responsabilidades Comuns dos MCPs Específicos:**
*   **Abstração:** Esconder a complexidade do sistema externo subjacente.
*   **Normalização:** Padronizar a entrada e saída de dados para o MCP-Crew.
*   **Segurança:** Gerenciar a autenticação e autorização para o sistema externo.
*   **Multi-tenancy:** Garantir que as operações sejam isoladas por tenant, utilizando `account_id` para acesso a dados específicos.
*   **Tratamento de Erros:** Lidar com erros específicos do sistema externo e reportá-los de forma consistente.

### 2.4. Redis Cache

O Redis é um componente crítico para a performance, escalabilidade e custo-eficiência do sistema. Ele é utilizado como uma camada de cache e para gerenciamento de estado e contexto em tempo real.

**Estratégias de Cache e Uso:**
*   **Cache de Primeiro Nível (Módulo Integrador Universal):** Armazena resultados de consultas frequentes do Odoo para os MCPs, dados de configuração e tokens/sessões. Reduz a carga sobre o MCP-Crew e os MCPs específicos.
*   **Cache de Segundo Nível (MCP-Crew):** Armazena estado de conversas, contexto de agentes, resultados intermediários de processamento e embeddings. Isso minimiza a necessidade de reprocessar informações e reduz chamadas a LLMs.
*   **Memória Temporária de Conversa:** Utiliza o Redis para manter o histórico de conversas por tenant, permitindo que os agentes tenham memória de interações passadas.
*   **Cache de Resultados e Embeddings:** Armazena resultados de consultas a MCPs (ex: resultados de busca no Qdrant, dados do MongoDB) e embeddings gerados por LLMs, evitando recalcular ou reconsultar dados.
*   **Minimização de Chamadas à LLM:** Ao armazenar contexto e resultados intermediários, o Redis reduz drasticamente o número de chamadas necessárias aos LLMs, resultando em economia de custos e respostas mais rápidas.

**Estrutura de Chaves para Multi-tenancy:**

Para garantir o isolamento de dados e a escalabilidade em um ambiente multi-tenant, todas as chaves no Redis devem ser prefixadas com o `account_id` do tenant. A estrutura de chaves recomendada é:

`{account_id}:{mcp_ou_modulo}:{tipo_recurso}:{id_recurso}:{acao}`

**Exemplos:**
*   `tenant123:mcp_mongo:behavior_ata:config_agente:details`
*   `tenant456:mcp_qdrant:products:product_xyz:embeddings`
*   `tenant123:mcp_crew:conversation:session_abc:history`
*   `tenant456:universal_integrator:config:api_keys:mcp_chatwoot`

**Políticas de TTL (Time-To-Live):**

*   **Dados Transitórios (ex: resultados de busca, contexto de sessão de curta duração):** 5-15 minutos.
*   **Dados de Sessão (ex: histórico de conversa):** 1-24 horas, dependendo da inatividade do usuário.
*   **Dados de Configuração (ex: ATA de comportamento):** 1-7 dias, com invalidação explícita em caso de alterações para garantir a consistência.

### 2.5. Crews de Agentes CrewAI

As Crews são as equipes de agentes que realizam as tarefas específicas do negócio. Elas são instanciadas e orquestradas pelo MCP-Crew e utilizam os MCPs específicos como suas ferramentas.

**Exemplos de Crews e Suas Funções:**
*   **WhatsAppCrew / FacebookCrew:** Responsáveis por interagir com os usuários nesses canais, entender a intenção e coordenar a resposta. Utilizam o MCP-Chatwoot para comunicação e outros MCPs para obter informações.
*   **OdooOperationCrew:** Equipe de agentes especializada em interagir com o Odoo via MCP-Odoo para realizar operações como consulta de estoque, registro de vendas, etc.
*   **ResearchCrew:** Agentes focados em pesquisa de informações, utilizando MCP-Qdrant para busca semântica em bases de conhecimento e MCP-MongoDB para configurações.
*   **BehavioralCrew:** Agentes que interpretam e aplicam as configurações de comportamento do tenant (obtidas via MCP-MongoDB) para guiar as interações com os usuários.

**Características Importantes das Crews:**
*   **Especialização:** Cada Crew tem um conjunto de habilidades e ferramentas específicas para sua área de atuação.
*   **Colaboração:** Agentes dentro de uma Crew colaboram entre si, e Crews podem delegar tarefas a outras Crews ou ao MCP-Crew.
*   **Uso de Ferramentas:** As Crews acessam os MCPs específicos como ferramentas, permitindo-lhes interagir com sistemas externos de forma controlada e padronizada.
*   **Memória:** As Crews e seus agentes mantêm memória de longo e curto prazo, utilizando o Redis para persistência de contexto.

## 3. Orquestração Inteligente e Multi-tenancy no MCP-Crew

O coração do sistema é a capacidade do MCP-Crew de orquestrar dinamicamente as Crews e os MCPs, garantindo a robustez e o isolamento multi-tenant.

### 3.1. Estrutura do MCP-Crew para Orquestração

O MCP-Crew atuará como um **dispatcher** e **gerenciador de fluxo**. Ao receber uma requisição (ex: uma mensagem do Chatwoot via MCP-Chatwoot), ele realizará os seguintes passos:

1.  **Identificação do Tenant:** Extrair o `account_id` da requisição para garantir o isolamento multi-tenant.
2.  **Recuperação da ATA de Comportamento:** Consultar o `MCP-MongoDB` (utilizando o `account_id`) para obter a "ATA de Comportamento e Configuração" específica do tenant. Esta ATA definirá o perfil do agente (alegre, formal, objetivo), horários de atendimento, serviços disponíveis e regras de negócio personalizadas.
3.  **Análise de Intenção e Contexto:** Utilizar um LLM (ou um agente especializado dentro do MCP-Crew) para analisar a mensagem de entrada e o contexto da conversa (recuperado do Redis) para determinar a intenção do usuário.
4.  **Seleção Dinâmica da Crew:** Com base na intenção do usuário, no canal de entrada e na ATA de Comportamento do tenant, o MCP-Crew selecionará a `Crew` de agentes CrewAI mais apropriada para lidar com a solicitação. Por exemplo, se a intenção for "agendamento" e o serviço de agendamento estiver ativo para o tenant, a `SchedulingCrew` será ativada.
5.  **Delegação de Tarefas:** O MCP-Crew delegará a tarefa à `Crew` selecionada, passando o contexto necessário e as ferramentas (MCPs específicos) que a `Crew` pode utilizar.
6.  **Coordenação da Execução:** O MCP-Crew monitorará o progresso da `Crew` e, se necessário, intervirá para redirecionar, fornecer informações adicionais ou acionar mecanismos de fallback.
7.  **Agregação e Formatação da Resposta:** Uma vez que a `Crew` tenha concluído a tarefa, o MCP-Crew agregará os resultados, formatará a resposta de acordo com o perfil de comportamento do tenant (definido na ATA) e a enviará de volta ao `Módulo Integrador Universal` ou ao `MCP-Chatwoot`.

### 3.2. Delegação de Decisões Baseadas em Comportamento por Tenant

A ATA de Comportamento e Configuração, armazenada no MongoDB e acessada via MCP-MongoDB, é fundamental para a personalização multi-tenant. O MCP-Crew e as Crews de agentes utilizarão essa ATA para:

*   **Tom de Voz e Estilo:** Ajustar o tom de voz (formal, informal, alegre, objetivo) e o estilo de comunicação dos agentes.
*   **Horários de Atendimento:** Definir se o agente deve responder ou encaminhar para um atendimento humano fora do horário comercial.
*   **Serviços Disponíveis:** Ativar ou desativar funcionalidades específicas (ex: agendamento, delivery, consulta de produtos) com base na assinatura ou configuração do tenant.
*   **Regras de Negócio Personalizadas:** Aplicar regras específicas do tenant para promoções, descontos, fluxos de aprovação, etc.

O MCP-Crew garantirá que, antes de qualquer interação significativa, o contexto do tenant seja carregado e as decisões dos agentes sejam guiadas por essas configurações personalizadas.

### 3.3. Integração Dinâmica de MCPs

O MCP-Crew não terá uma conexão estática com todos os MCPs. Em vez disso, ele manterá um registro dos MCPs disponíveis e suas capacidades. Quando uma `Crew` precisar de uma ferramenta específica (ex: buscar um produto, registrar um cliente), o MCP-Crew identificará o `MCP Específico` responsável por essa funcionalidade e estabelecerá a conexão ou roteará a requisição dinamicamente. Isso permite a fácil adição de novos MCPs sem a necessidade de reconfigurar todo o sistema.

## 4. Aplicação de Redis para Performance e Eficiência

O Redis será o pilar da performance e eficiência do sistema, atuando em diversas frentes:

### 4.1. Chaves por Tenant/Contexto (`account_id`)

Conforme detalhado na seção 2.4, a prefixação de todas as chaves com `account_id` é mandatório para garantir o isolamento e a escalabilidade multi-tenant. Isso permite que cada tenant tenha seu próprio espaço de dados no Redis, evitando colisões e garantindo a privacidade.

### 4.2. Memória Temporária de Conversa

O Redis será usado para armazenar o histórico de conversas de cada usuário por um período definido (TTL). Isso permite que os agentes mantenham o contexto da conversa, mesmo que a interação seja interrompida e retomada. A estrutura de dados `LIST` do Redis pode ser utilizada para armazenar as mensagens em ordem cronológica.

**Exemplo de Chave:** `tenant123:conversation:user_id_xyz:history`

### 4.3. Cache de Resultados e Embeddings

Resultados de consultas a MCPs (ex: dados de produtos do Odoo via MCP-Odoo, resultados de busca semântica do Qdrant) e embeddings gerados por LLMs serão cacheados no Redis. Isso evita chamadas repetidas a APIs externas e LLMs, economizando custos e acelerando as respostas.

**Exemplos de Chaves:**
*   `tenant123:mcp_odoo:product:sku_123:details` (para detalhes de produto)
*   `tenant456:mcp_qdrant:query_hash_abc:embeddings` (para embeddings de consultas)

### 4.4. Minimização de Chamadas à LLM

O uso extensivo do Redis para cache de contexto, memória de conversa e resultados intermediários reduzirá drasticamente a necessidade de chamar os LLMs. Antes de enviar uma requisição a um LLM, o sistema verificará o cache do Redis. Se a informação necessária já estiver disponível e válida, a chamada ao LLM será evitada, resultando em:

*   **Economia de Custos:** Menos chamadas de API significam menores gastos com provedores de LLM.
*   **Respostas Mais Rápidas:** A recuperação de dados do cache é significativamente mais rápida do que uma chamada a um LLM.
*   **Maior Resiliência:** Menor dependência de serviços externos, aumentando a robustez do sistema.

## 5. Base de Sistema Escalável e Multi-tenant

Para garantir que o sistema seja escalável e robusto em um ambiente multi-tenant, as seguintes práticas serão adotadas:

### 5.1. Configurações Isoladas

Todas as configurações sensíveis e específicas de tenant (credenciais de API, endpoints, regras de negócio, ATA de comportamento) serão armazenadas de forma isolada. O `MCP-MongoDB` é o local ideal para a ATA de comportamento, enquanto outras configurações podem ser gerenciadas pelo `Módulo Integrador Universal` no Odoo, que as acessará de forma segura e as cacheará no Redis.

### 5.2. Conexões e Coleções Separadas

*   **MongoDB:** Embora o MCP-MongoDB possa usar uma única instância, as coleções serão logicamente separadas por tenant (ex: `tenant_id_config`, `tenant_id_behavior`).
*   **Qdrant:** Coleções vetorizadas serão separadas por tenant para garantir o isolamento de dados e a relevância da busca semântica. Isso pode ser feito criando coleções distintas para cada tenant (ex: `products_tenant_id`, `rules_tenant_id`).
*   **Odoo:** O `MCP-Odoo` e o `Módulo Integrador Universal` garantirão que as operações no Odoo respeitem o contexto do tenant, acessando apenas os dados e funcionalidades permitidos para aquele tenant.

### 5.3. Otimização para Baixo Custo e Alta Performance

*   **Uso Agressivo de Cache Redis:** Conforme detalhado, o Redis é a principal ferramenta para otimização de custos (redução de chamadas LLM) e performance (respostas rápidas).
*   **Design de Agentes Eficiente:** As Crews e agentes CrewAI serão projetados para serem o mais eficientes possível, minimizando o número de iterações e o volume de dados processados pelos LLMs.
*   **Monitoramento de Custos:** Implementar ferramentas de monitoramento para rastrear o consumo de tokens de LLMs e o uso de recursos do Redis, permitindo ajustes e otimizações contínuas.
*   **Processamento Assíncrono:** Utilizar filas de mensagens (ex: Redis Streams, RabbitMQ) para processamento assíncrono de tarefas que não exigem resposta imediata, liberando recursos e melhorando a responsividade.

## 6. Sugestões de Arquitetura e Boas Práticas

### 6.1. Segurança por Tenant

*   **Autenticação e Autorização:** Implementar mecanismos robustos de autenticação e autorização em todos os pontos de entrada do sistema (Módulo Integrador, MCPs). O `account_id` deve ser validado em cada requisição.
*   **Isolamento de Dados:** Garantir que os dados de um tenant nunca sejam acessíveis por outro. A prefixação de chaves no Redis e a separação lógica/física de coleções em bancos de dados são cruciais.
*   **Gerenciamento de Segredos:** Utilizar um sistema seguro para gerenciar credenciais e chaves de API (ex: HashiCorp Vault, variáveis de ambiente seguras).
*   **Princípio do Menor Privilégio:** Agentes e MCPs devem ter apenas as permissões mínimas necessárias para realizar suas tarefas.

### 6.2. Observabilidade (Logs, Tracing, Métricas)

*   **Logging Centralizado:** Todos os componentes (Módulo Integrador, MCP-Crew, MCPs, Crews) devem gerar logs estruturados e enviá-los para um sistema de logging centralizado (ex: ELK Stack, Grafana Loki). Os logs devem incluir o `account_id` para facilitar o troubleshooting multi-tenant.
*   **Tracing Distribuído:** Implementar tracing distribuído (ex: OpenTelemetry) para rastrear o fluxo de uma requisição através de todos os componentes do sistema. Isso é essencial para depurar problemas em arquiteturas distribuídas.
*   **Métricas:** Coletar métricas de desempenho (latência, taxa de erro, uso de CPU/memória, consumo de tokens de LLM, hits/misses do cache Redis) e visualizá-las em dashboards (ex: Grafana). As métricas devem ser segmentadas por tenant.

### 6.3. Testes Automatizados para Agentes e MCPs

*   **Testes Unitários:** Para cada componente (Módulo Integrador, MCP-Crew, MCPs, agentes individuais).
*   **Testes de Integração:** Para verificar a comunicação entre os componentes (ex: Módulo Integrador com MCP-Crew, MCP-Crew com MCP-MongoDB).
*   **Testes de Sistema/End-to-End:** Simular fluxos completos de usuário, desde a entrada da mensagem no Chatwoot até a resposta final, validando a orquestração e a lógica de negócio multi-tenant.
*   **Testes de Performance e Carga:** Para garantir que o sistema possa lidar com o volume esperado de requisições e usuários, especialmente em um ambiente multi-tenant.

### 6.4. Extensibilidade com Novos Canais e MCPs

O design modular da arquitetura MCP-First facilita a adição de novos canais de comunicação e MCPs:

*   **Novos Canais:** Para adicionar um novo canal (ex: Telegram), basta desenvolver um novo MCP (ex: MCP-Telegram) que se integre à API do Telegram e ao MCP-Crew. Nenhuma alteração é necessária nos componentes existentes.
*   **Novos MCPs:** Para integrar um novo sistema externo, basta desenvolver um novo MCP específico que exponha suas funcionalidades de forma padronizada. O MCP-Crew pode ser configurado dinamicamente para reconhecer e utilizar as ferramentas oferecidas pelo novo MCP.
*   **Novas Crews:** Novas Crews de agentes podem ser adicionadas para lidar com novas funcionalidades ou otimizar tarefas existentes, sem impactar a arquitetura central.

## 7. Considerações sobre o Agente Universal no Odoo

A visão de um "Agente Odoo Operador" que interage com o Odoo via linguagem natural é totalmente alinhada com esta arquitetura. Este agente seria uma `Crew` especializada dentro do sistema CrewAI, utilizando o `MCP-Odoo` como sua principal ferramenta.

**Como funcionaria:**

1.  **Entrada:** Um usuário (ou outro agente) faria uma requisição em linguagem natural (ex: "qual o total de vendas hoje?", "registre um novo cliente") através de um canal (ex: Chatwoot, ou diretamente via Módulo Integrador no Odoo).
2.  **MCP-Crew:** O MCP-Crew identificaria a intenção e delegaria a tarefa à `OdooOperationCrew` (ou `AgenteOdooOperadorCrew`).
3.  **OdooOperationCrew:** Esta Crew utilizaria o `MCP-Odoo` para traduzir a requisição em linguagem natural em chamadas de API ou operações no Odoo. Por exemplo, "qual o total de vendas hoje?" seria traduzido para uma consulta de vendas no Odoo via MCP-Odoo.
4.  **MCP-Odoo:** O MCP-Odoo executaria a operação no Odoo, recuperaria os dados e os retornaria à `OdooOperationCrew`.
5.  **Resposta:** A `OdooOperationCrew` formataria a resposta em linguagem natural e a enviaria de volta ao usuário via MCP-Crew e o canal de origem.

Esta abordagem garante que o Agente Universal no Odoo seja uma extensão natural do sistema multi-agente, aproveitando toda a infraestrutura de orquestração, multi-tenancy e otimização com Redis.

## Conclusão

A arquitetura proposta para o sistema MCP-Crew, baseada no paradigma MCP-First e com forte ênfase no uso do Redis para performance e multi-tenancy, oferece uma base robusta, escalável e flexível para o desenvolvimento de sistemas multi-agentes. Ao centralizar a orquestração e a gestão de contexto, e ao abstrair as interações com sistemas externos através de MCPs modulares, o sistema estará preparado para lidar com a complexidade de múltiplos canais, tenants e funcionalidades, pavimentando o caminho para um "Agente Universal" no Odoo e para a liderança em arquiteturas multi-agentes.




## 8. Especificação Técnica Detalhada

Esta seção aprofunda os aspectos técnicos da arquitetura do sistema MCP-Crew, fornecendo detalhes sobre APIs, modelos de dados, implementação do Redis, diretrizes de CrewAI e considerações de multi-tenancy.

### 8.1. Especificações de API

As APIs são o backbone da comunicação entre os componentes. Serão definidas interfaces claras para o `Módulo Integrador Universal` e o `MCP-Crew`.

#### 8.1.1. API do Módulo Integrador Universal (Odoo)

Este módulo exporá uma API interna para os módulos funcionais do Odoo e uma API externa para comunicação com o MCP-Crew. A comunicação interna será via chamadas de função Python, enquanto a externa será via HTTP/HTTPS.

**Exemplo de Endpoint (Interno/Externo):** `/api/mcp_crew/process_request`

**Método:** `POST`

**Descrição:** Envia uma requisição para o MCP-Crew para processamento, com base na intenção do usuário ou em uma ação do sistema.

**Corpo da Requisição (JSON):**

```json
{
    "account_id": "string",
    "channel": "string",
    "message_type": "string",
    "payload": {
        "text": "string",
        "sender_id": "string",
        "conversation_id": "string",
        "metadata": {
            "source_ip": "string",
            "user_agent": "string",
            "timestamp": "datetime"
        }
    },
    "context": {
        "conversation_history": [
            {"role": "user", "content": "string"},
            {"role": "assistant", "content": "string"}
        ],
        "current_state": "string"
    },
    "requested_mcp": "string" (opcional, para roteamento direto a um MCP específico)
}
```

**Parâmetros da Requisição:**
*   `account_id` (obrigatório): Identificador único do tenant. Essencial para multi-tenancy.
*   `channel` (obrigatório): Canal de origem da requisição (ex: "whatsapp", "facebook", "odoo_internal").
*   `message_type` (obrigatório): Tipo da mensagem (ex: "text", "event", "command").
*   `payload` (obrigatório): Conteúdo principal da requisição.
    *   `text`: Texto da mensagem ou comando.
    *   `sender_id`: Identificador do remetente.
    *   `conversation_id`: Identificador da conversa para manter o contexto.
    *   `metadata`: Informações adicionais sobre a requisição.
*   `context` (opcional): Contexto da conversa ou estado atual do sistema.
    *   `conversation_history`: Histórico de mensagens.
    *   `current_state`: Estado atual da interação.
*   `requested_mcp` (opcional): Permite que o Módulo Integrador solicite diretamente um MCP específico, ignorando a orquestração do MCP-Crew em certos casos.

**Corpo da Resposta (JSON):**

```json
{
    "status": "string" (ex: "success", "error", "pending"),
    "response_type": "string" (ex: "text", "action_required", "info"),
    "payload": {
        "text": "string",
        "actions": [
            {"type": "string", "details": {}}
        ],
        "metadata": {}
    },
    "error": {
        "code": "string",
        "message": "string"
    }
}
```

**Parâmetros da Resposta:**
*   `status`: Indica o sucesso ou falha da operação.
*   `response_type`: Tipo da resposta esperada (texto, ação, informação).
*   `payload`: Conteúdo da resposta.
    *   `text`: Texto da resposta para o usuário.
    *   `actions`: Lista de ações que o sistema de origem (Odoo, Chatwoot) deve tomar.
    *   `metadata`: Metadados adicionais.
*   `error`: Detalhes do erro, se houver.

#### 8.1.2. API do MCP-Crew

O MCP-Crew exporá uma API para receber requisições do `Módulo Integrador Universal` e de outros `MCPs` (como o `MCP-Chatwoot`). Internamente, ele se comunicará com os `MCPs Específicos` e as `Crews` de agentes.

**Exemplo de Endpoint:** `/process_mcp_request`

**Método:** `POST`

**Descrição:** Recebe e processa requisições de entrada, orquestrando a execução das Crews e a interação com os MCPs.

**Corpo da Requisição (JSON):** Similar ao `payload` do Módulo Integrador Universal, mas com campos adicionais para contexto interno do MCP-Crew.

```json
{
    "account_id": "string",
    "source_mcp": "string",
    "request_id": "string",
    "timestamp": "datetime",
    "message_payload": { ... }, // Conteúdo da requisição original
    "internal_context": { ... } // Contexto interno do MCP-Crew
}
```

**Corpo da Resposta (JSON):** Similar ao `payload` de resposta do Módulo Integrador Universal.

#### 8.1.3. APIs dos MCPs Específicos

Cada MCP específico terá sua própria API, padronizada para interagir com o MCP-Crew. O `crewai-tools` com `MCPServerAdapter` será a base para essa comunicação.

**Exemplo (MCP-MongoDB):**

**Endpoint:** `/get_behavior_ata`

**Método:** `POST`

**Corpo da Requisição:**

```json
{
    "account_id": "string",
    "config_key": "string" (ex: "agent_profile", "service_hours")
}
```

**Corpo da Resposta:**

```json
{
    "status": "success",
    "data": { ... } // JSON da ATA de comportamento
}
```

### 8.2. Modelos de Dados

#### 8.2.1. ATA de Comportamento e Configuração (MCP-MongoDB)

Armazenada no MongoDB, esta estrutura JSON define o comportamento e as configurações específicas de cada tenant. Será acessada pelo MCP-Crew e pelas Crews de agentes para personalizar as interações.

```json
{
    "_id": "<account_id>",
    "agent_profile": {
        "tone": "formal" | "informal" | "friendly" | "objective",
        "personality": "helpful" | "empathetic" | "direct",
        "language": "pt-BR" | "en-US"
    },
    "service_hours": {
        "monday": {"start": "09:00", "end": "18:00"},
        "tuesday": {"start": "09:00", "end": "18:00"},
        "out_of_hours_message": "string",
        "out_of_hours_fallback_agent_id": "string" (para atendimento humano)
    },
    "available_services": [
        {"name": "scheduling", "active": true, "config": { ... }},
        {"name": "product_inquiry", "active": true, "config": { ... }}
    ],
    "business_rules": [
        {"rule_id": "string", "condition": "string", "action": "string"}
    ],
    "llm_config": {
        "model_name": "string",
        "temperature": "float",
        "max_tokens": "integer"
    },
    "tool_access": {
        "mcp_odoo": {"enabled": true, "permissions": ["read_products", "create_sale_order"]},
        "mcp_qdrant": {"enabled": true, "collections": ["products_embeddings", "rules_embeddings"]}
    }
}
```

#### 8.2.2. Contexto de Conversa (Redis)

Armazenado no Redis, este modelo representa o estado atual de uma conversa, permitindo que os agentes mantenham o contexto.

**Chave Redis:** `{account_id}:conversation:{conversation_id}:context`

**Valor (JSON):**

```json
{
    "history": [
        {"role": "user", "content": "Olá, preciso de ajuda com um produto.", "timestamp": "datetime"},
        {"role": "assistant", "content": "Claro! Qual produto você está procurando?", "timestamp": "datetime"}
    ],
    "current_intent": "string" (ex: "product_inquiry", "scheduling"),
    "entities": {"product_name": "string", "date": "string"},
    "last_interaction_timestamp": "datetime",
    "agent_state": {"current_agent": "string", "sub_task": "string"}
}
```

### 8.3. Detalhes de Implementação do Redis

O Redis será utilizado de forma extensiva para cache, gerenciamento de sessão e memória de agentes. A biblioteca `redis-py` será utilizada para interagir com o Redis.

#### 8.3.1. Conexão e Configuração

A conexão com o Redis será gerenciada por um pool de conexões para otimizar o desempenho. As configurações (host, porta, senha) serão carregadas de variáveis de ambiente ou de um arquivo de configuração seguro.

```python
import redis

# Exemplo de configuração (em um módulo de utilitários ou configuração)
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)

redis_client = redis.StrictRedis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    password=REDIS_PASSWORD,
    decode_responses=True # Decodifica respostas para strings Python
)

# Teste de conexão
try:
    redis_client.ping()
    print("Conexão com Redis estabelecida com sucesso!")
except redis.exceptions.ConnectionError as e:
    print(f"Erro ao conectar ao Redis: {e}")
    # Lidar com o erro, talvez com um fallback ou log de alerta
```

#### 8.3.2. Funções Utilitárias para Cache e Contexto

Serão desenvolvidas funções utilitárias para abstrair as operações comuns do Redis, garantindo a aplicação das políticas de TTL e a prefixação por `account_id`.

```python
import json

def get_redis_key(account_id: str, resource_type: str, resource_id: str, action: str = "details") -> str:
    """Gera uma chave Redis com prefixo de tenant."""
    return f"{account_id}:{resource_type}:{resource_id}:{action}"

def set_cached_data(account_id: str, resource_type: str, resource_id: str, data: dict, ttl_seconds: int, action: str = "details"):
    """Armazena dados no Redis com TTL."""
    key = get_redis_key(account_id, resource_type, resource_id, action)
    redis_client.setex(key, ttl_seconds, json.dumps(data))

def get_cached_data(account_id: str, resource_type: str, resource_id: str, action: str = "details") -> dict | None:
    """Recupera dados do Redis."""
    key = get_redis_key(account_id, resource_type, resource_id, action)
    data = redis_client.get(key)
    if data:
        return json.loads(data)
    return None

def append_conversation_history(account_id: str, conversation_id: str, role: str, content: str, ttl_seconds: int = 3600):
    """Adiciona uma mensagem ao histórico da conversa no Redis."""
    key = get_redis_key(account_id, "conversation", conversation_id, "history")
    message = {"role": role, "content": content, "timestamp": datetime.now().isoformat()}
    redis_client.rpush(key, json.dumps(message))
    redis_client.expire(key, ttl_seconds) # Atualiza o TTL a cada nova mensagem

def get_conversation_history(account_id: str, conversation_id: str, limit: int = 10) -> list:
    """Recupera o histórico da conversa do Redis."""
    key = get_redis_key(account_id, "conversation", conversation_id, "history")
    history_raw = redis_client.lrange(key, -limit, -1) # Últimas 'limit' mensagens
    return [json.loads(msg) for msg in history_raw]
```

#### 8.3.3. Minimização de Chamadas à LLM

Antes de qualquer chamada a um LLM, o MCP-Crew e os agentes deverão implementar uma lógica de verificação de cache. Isso pode ser feito através de um decorador ou de uma função utilitária que encapsule a chamada ao LLM.

```python
from functools import wraps

def llm_cache(func):
    """Decorador para cachear resultados de chamadas LLM no Redis."""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        account_id = kwargs.get("account_id") or getattr(self, "account_id", None)
        if not account_id:
            raise ValueError("account_id é necessário para cache LLM.")

        # Gerar uma chave de cache baseada nos argumentos da função e account_id
        # Pode ser um hash dos args e kwargs para garantir unicidade
        cache_key_parts = [str(account_id), func.__name__] + [str(arg) for arg in args] + [f"{k}={v}" for k, v in kwargs.items()]
        cache_key = ":".join(cache_key_parts)
        
        cached_result = redis_client.get(cache_key)
        if cached_result:
            print(f"[CACHE HIT] para {cache_key}")
            return json.loads(cached_result)

        print(f"[CACHE MISS] para {cache_key} - Chamando LLM...")
        result = func(self, *args, **kwargs)
        redis_client.setex(cache_key, 3600, json.dumps(result)) # Cache por 1 hora
        return result
    return wrapper

# Exemplo de uso em um método de agente ou do MCP-Crew
class MyAgent:
    def __init__(self, account_id):
        self.account_id = account_id

    @llm_cache
    def analyze_intent(self, text: str, conversation_history: list, account_id: str) -> str:
        # Lógica de chamada ao LLM para análise de intenção
        # ...
        return "product_inquiry"

# Exemplo de chamada:
# agent = MyAgent(account_id="tenant123")
# intent = agent.analyze_intent(text="Qual o preço do produto X?", conversation_history=[], account_id="tenant123")
```

### 8.4. Diretrizes de Implementação do CrewAI

#### 8.4.1. Estrutura de Agentes, Tarefas e Crews

*   **Agentes:** Cada agente terá um `role`, `goal` e `backstory` bem definidos. As `tools` serão injetadas dinamicamente pelo MCP-Crew com base na ATA de comportamento do tenant e na necessidade da tarefa.
    ```python
    from crewai import Agent

    def create_product_inquiry_agent(account_id: str, tools: list):
        return Agent(
            role='Product Expert',
            goal='Provide accurate and detailed information about products based on user inquiries.',
            backstory='An expert in product catalogs and specifications, capable of retrieving and explaining product details.',
            tools=tools,
            verbose=True,
            allow_delegation=True,
            # Adicionar callback para persistir memória no Redis
        )
    ```

*   **Tarefas:** As tarefas serão específicas e acionáveis, com `description` e `expected_output` claros. Elas poderão ser atribuídas a agentes específicos ou delegadas.
    ```python
    from crewai import Task

    def create_product_search_task(agent: Agent, product_name: str):
        return Task(
            description=f"Search for product details for '{product_name}' using available product tools.",
            expected_output=f"A comprehensive summary of '{product_name}' including price, availability, and features.",
            agent=agent
        )
    ```

*   **Crews:** As Crews serão definidas para orquestrar um conjunto de agentes e tarefas para um objetivo maior. O `process` da Crew definirá o fluxo de trabalho.
    ```python
    from crewai import Crew, Process

    def create_product_inquiry_crew(account_id: str, product_name: str, mcp_qdrant_tool, mcp_odoo_tool):
        product_expert_agent = create_product_inquiry_agent(account_id, tools=[mcp_qdrant_tool, mcp_odoo_tool])
        search_task = create_product_search_task(product_expert_agent, product_name)

        return Crew(
            agents=[product_expert_agent],
            tasks=[search_task],
            process=Process.sequential, # Ou Process.hierarchical para fluxos mais complexos
            verbose=True
        )
    ```

#### 8.4.2. Injeção Dinâmica de Ferramentas (MCPs)

O MCP-Crew será responsável por injetar as ferramentas (MCPs específicos) nas Crews e agentes no momento da instanciação, com base nas permissões do tenant e na necessidade da tarefa. Isso garante que os agentes só tenham acesso às ferramentas relevantes e autorizadas.

```python
from crewai_tools import MCPServerAdapter
from mcp import StdioServerParameters # Ou outros tipos de server_params

class MCPCrewOrchestrator:
    def __init__(self, account_id: str):
        self.account_id = account_id
        self.mcp_tools = {}

    def _load_mcp_tools(self, mcp_config: dict):
        """Carrega ferramentas MCP com base na configuração do tenant."""
        # Exemplo simplificado: em produção, isso seria mais dinâmico e robusto
        if mcp_config.get("mcp_qdrant", {}).get("enabled"):
            # server_params para MCP-Qdrant
            qdrant_server_params = StdioServerParameters(
                command="python3", 
                args=["path/to/mcp_qdrant_server.py"],
                env={"ACCOUNT_ID": self.account_id, **os.environ}
            )
            self.mcp_tools["mcp_qdrant"] = MCPServerAdapter(qdrant_server_params)

        if mcp_config.get("mcp_odoo", {}).get("enabled"):
            # server_params para MCP-Odoo
            odoo_server_params = StdioServerParameters(
                command="python3", 
                args=["path/to/mcp_odoo_server.py"],
                env={"ACCOUNT_ID": self.account_id, **os.environ}
            )
            self.mcp_tools["mcp_odoo"] = MCPServerAdapter(odoo_server_params)

    def orchestrate_request(self, request_payload: dict):
        account_id = request_payload["account_id"]
        # 1. Recuperar ATA de Comportamento do MCP-MongoDB
        # mcp_mongo_tool = self.mcp_tools.get("mcp_mongo") # Assumindo que MCP-MongoDB é sempre carregado
        # ata_comportamento = mcp_mongo_tool.get_behavior_ata(account_id=account_id)
        # self._load_mcp_tools(ata_comportamento["tool_access"])

        # 2. Análise de Intenção e Seleção da Crew
        # ... (lógica para determinar a crew e as ferramentas necessárias)

        # 3. Instanciar Crew com ferramentas injetadas
        # Exemplo: se a intenção for "product_inquiry"
        # product_inquiry_crew = create_product_inquiry_crew(
        #     account_id,
        #     request_payload["payload"]["text"],
        #     self.mcp_tools.get("mcp_qdrant"),
        #     self.mcp_tools.get("mcp_odoo")
        # )
        # result = product_inquiry_crew.kickoff()
        # return result
```

#### 8.4.3. Gerenciamento de Memória e Contexto

Os agentes CrewAI podem ser configurados para usar um sistema de memória. O Redis será o backend para essa memória, garantindo persistência e isolamento por tenant. A integração pode ser feita através de callbacks ou de uma classe de memória customizada que interaja com as funções utilitárias do Redis.

### 8.5. Multi-tenancy Enforcement

O isolamento multi-tenant será garantido em todas as camadas do sistema:

*   **Nível de Aplicação (Módulo Integrador, MCP-Crew, MCPs):**
    *   Todas as requisições devem conter o `account_id`.
    *   Todas as operações de leitura/escrita em bancos de dados e Redis devem usar o `account_id` para filtrar ou prefixar dados.
    *   As configurações (ATA de Comportamento, permissões de ferramentas) são carregadas por `account_id`.
*   **Nível de Banco de Dados:**
    *   **MongoDB:** Coleções logicamente separadas por tenant ou documentos com `account_id` como parte da chave primária/índice.
    *   **Qdrant:** Coleções separadas por tenant (ex: `products_tenant123`, `rules_tenant123`).
    *   **Odoo:** O `MCP-Odoo` e o `Módulo Integrador Universal` devem garantir que as consultas e operações no Odoo respeitem as regras de segurança e acesso por empresa/tenant do Odoo.
*   **Nível de Ferramentas (MCPs):** Cada MCP deve ser projetado para operar em um contexto multi-tenant, recebendo o `account_id` e aplicando-o em suas operações internas.

### 8.6. Tratamento de Erros e Observabilidade

#### 8.6.1. Tratamento de Erros

*   **Exceções Customizadas:** Definir exceções customizadas para erros específicos do domínio (ex: `TenantNotFoundError`, `MCPServiceUnavailableError`).
*   **Retries e Fallbacks:** Implementar lógicas de retry com backoff exponencial para chamadas a serviços externos (MCPs, LLMs) e mecanismos de fallback para cenários críticos (ex: se um LLM falhar, tentar outro ou retornar uma mensagem padrão).
*   **Mensagens de Erro Claras:** As respostas de erro devem ser informativas para facilitar o diagnóstico, mas sem expor informações sensíveis.

#### 8.6.2. Logging

*   **Formato Estruturado:** Logs em formato JSON para facilitar a análise por ferramentas de logging centralizado.
*   **Contexto da Requisição:** Incluir `account_id`, `request_id`, `conversation_id` em todos os logs para rastreabilidade.
*   **Níveis de Log:** Utilizar `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` apropriadamente.
*   **Exemplo de Log:**
    ```json
    {
        "timestamp": "2025-06-11T10:30:00Z",
        "level": "INFO",
        "service": "mcp-crew",
        "account_id": "tenant123",
        "request_id": "req_abc123",
        "message": "Processing incoming request",
        "details": {"channel": "whatsapp", "intent": "product_inquiry"}
    }
    ```

#### 8.6.3. Tracing Distribuído

*   **OpenTelemetry:** Utilizar OpenTelemetry para instrumentar o código em todos os componentes. Isso permitirá gerar traces que mostram o fluxo completo de uma requisição através do Módulo Integrador, MCP-Crew, Redis e MCPs.
*   **Spans e Atributos:** Criar spans para operações chave (ex: `process_request`, `call_mcp_qdrant`, `llm_inference`) e adicionar atributos relevantes (ex: `account_id`, `mcp.name`, `llm.model_name`).

#### 8.6.4. Métricas

*   **Prometheus/Grafana:** Expor métricas em formato Prometheus para coleta e visualização no Grafana.
*   **Métricas Chave:**
    *   `request_total`: Contador de requisições por `account_id`, `channel`, `status`.
    *   `request_duration_seconds`: Histograma da latência das requisições.
    *   `llm_calls_total`: Contador de chamadas a LLMs por `account_id`, `model_name`.
    *   `redis_cache_hits_total`, `redis_cache_misses_total`: Contadores para eficiência do cache.
    *   `mcp_calls_total`: Contador de chamadas a MCPs específicos por `account_id`, `mcp_name`.
    *   `crew_execution_duration_seconds`: Histograma da duração da execução das Crews.

### 8.7. Considerações de Segurança Adicionais

*   **Validação de Entrada:** Todas as entradas de API devem ser rigorosamente validadas para prevenir ataques como injeção de código ou dados maliciosos.
*   **Comunicação Segura:** Usar HTTPS para todas as comunicações entre serviços.
*   **Segurança de Dados Sensíveis:** Criptografar dados sensíveis em repouso (no MongoDB, por exemplo) e em trânsito.
*   **Auditoria de Acesso:** Registrar quem acessou o quê e quando, especialmente para operações que modificam dados.

### 8.8. Estratégias de Deployment

*   **Contêineres (Docker):** Empacotar cada componente (MCP-Crew, MCPs específicos) em contêineres Docker para portabilidade e isolamento.
*   **Orquestração (Kubernetes):** Utilizar Kubernetes para orquestrar o deployment, escalabilidade e gerenciamento dos contêineres, facilitando a operação em larga escala e a resiliência.
*   **CI/CD:** Implementar pipelines de CI/CD para automação de testes, build e deployment, garantindo entregas rápidas e confiáveis.

Esta especificação técnica detalhada serve como um guia para a implementação do sistema MCP-Crew, garantindo que os requisitos de robustez, multi-tenancy, performance e extensibilidade sejam atendidos.




## 4. Provisão Dinâmica de Ferramentas e Compartilhamento de Conhecimento

### 4.1 Descoberta Dinâmica de Ferramentas via MCPs

A arquitetura do MCP-Crew será aprimorada para permitir que os agentes descubram e utilizem ferramentas fornecidas dinamicamente pelos MCPs conectados, eliminando a necessidade de hardcoding de ferramentas. Isso será alcançado através da utilização e extensão do `MCPServerAdapter` do CrewAI-Tools [1].

Cada MCP (Model Context Protocol) atuará como um provedor de serviços, expondo um catálogo de ferramentas específicas para seu domínio (e.g., MCP-MongoDB para operações de banco de dados, MCP-Chatwoot para interações de chat, MCP-Redis para manipulação de dados em cache). O `MCPServerAdapter` se conectará a esses MCPs e, em tempo de execução, consultará as ferramentas disponíveis. Essas ferramentas serão então convertidas em objetos `Tool` do CrewAI e disponibilizadas para os agentes.

**Mecanismo de Descoberta:**

1.  **Registro de MCPs:** O orquestrador do MCP-Crew manterá um registro dos MCPs disponíveis e suas URLs de acesso. Este registro pode ser configurado via YAML ou descoberto dinamicamente em um ambiente de microsserviços.
2.  **Adaptação de Ferramentas:** Para cada MCP registrado, uma instância do `MCPServerAdapter` será criada. Este adaptador é responsável por:
    *   Conectar-se ao endpoint do MCP (e.g., `/resources` para MCP-MongoDB, ou diretamente ao servidor para MCP-Redis).
    *   Consultar a lista de ferramentas e suas especificações (nome, descrição, parâmetros).
    *   Converter essas especificações em objetos `Tool` compatíveis com o CrewAI.
3.  **Provisão aos Agentes:** As ferramentas dinamicamente descobertas serão injetadas nos agentes no momento de sua criação ou quando uma crew for instanciada. Isso significa que um agente não precisará ter suas ferramentas pré-definidas em seu código, mas sim recebê-las com base nos MCPs acessíveis e na sua função.

**Exemplo de Fluxo:**

Um agente `ProductResearcher` não terá uma ferramenta `search_products_semantic` hardcoded. Em vez disso, ele receberá essa ferramenta do `MCP-Qdrant` (via `MCPServerAdapter`) quando for instanciado. Se o `MCP-Qdrant` for atualizado para incluir uma nova ferramenta `filter_products_by_price_range`, essa ferramenta estará automaticamente disponível para o `ProductResearcher` sem qualquer alteração no código do agente.

### 4.2 Otimização com Cache de Ferramentas no Redis

Para evitar a sobrecarga de consultar os MCPs para descoberta de ferramentas a cada nova requisição, o Redis será utilizado como um cache de ferramentas. Quando o MCP-Crew iniciar ou quando um novo MCP for registrado, as ferramentas expostas por ele serão descobertas e seus metadados (nome, descrição, parâmetros) serão armazenados no Redis.

**Estratégia de Cache:**

*   **Chave de Cache:** As ferramentas serão armazenadas usando uma chave padronizada, por exemplo, `{account_id}:mcp_tools:{mcp_name}:{tool_name}`. Isso garante o isolamento multi-tenant e permite a invalidação granular.
*   **TTL (Time-To-Live):** Um TTL apropriado será configurado para o cache de ferramentas. Em ambientes de desenvolvimento, pode ser um TTL curto para refletir mudanças rapidamente. Em produção, um TTL mais longo pode ser usado, com mecanismos de invalidação baseados em eventos (e.g., um webhook do MCP informando sobre uma nova ferramenta ou atualização).
*   **Autodescoberta Otimizada:** Em vez de consultar o MCP diretamente a cada vez, o sistema primeiro verificará o cache do Redis. Se a ferramenta estiver presente e válida, ela será carregada do cache. Caso contrário, a descoberta dinâmica será realizada, e o resultado será armazenado no cache para futuras requisições.

Essa abordagem reduzirá significativamente a latência e a carga sobre os MCPs, garantindo que as ferramentas estejam sempre atualizadas e disponíveis de forma eficiente.

### 4.3 Compartilhamento de Conhecimento entre Agentes e Crews

O compartilhamento de conhecimento é crucial para a colaboração eficaz em sistemas multi-agentes. O sistema MCP-Crew implementará mecanismos para que agentes e crews possam compartilhar informações, insights e resultados de forma estruturada e eficiente, utilizando o Redis como um hub de conhecimento compartilhado.

**Mecanismos de Compartilhamento:**

1.  **Base de Conhecimento Compartilhada (Redis Hashes/JSON):**
    *   Agentes e crews poderão publicar informações relevantes em uma base de conhecimento centralizada no Redis. Esta base será organizada por `account_id` e `topic` (e.g., `tenant123:knowledge:product_insights`).
    *   As informações serão armazenadas em formatos estruturados (e.g., JSON) dentro de hashes Redis, permitindo consultas eficientes.
    *   Exemplo: Um `ProductResearcher` pode publicar um resumo das características de um produto recém-pesquisado, que pode ser acessado por um `ProductAdvisor` para gerar recomendações.
2.  **Redis Streams para Eventos de Conhecimento:**
    *   Eventos significativos (e.g., "nova informação de produto disponível", "análise de mercado concluída") serão publicados em Redis Streams dedicados.
    *   Outros agentes ou crews interessados poderão se inscrever nesses streams (usando consumer groups) e reagir a esses eventos, puxando o conhecimento relevante da base de conhecimento compartilhada.
    *   Isso permite um modelo de comunicação assíncrona e desacoplada, onde os produtores de conhecimento não precisam saber quem consumirá a informação.
3.  **Memória de Longo Prazo (Qdrant/MongoDB):**
    *   Para conhecimento que precisa ser persistido por longos períodos ou que requer busca semântica avançada, o `MCP-Qdrant` (para embeddings vetoriais) e o `MCP-MongoDB` (para dados estruturados/não estruturados) serão utilizados.
    *   Agentes poderão armazenar e recuperar informações complexas, como perfis de clientes, históricos de conversas detalhados ou documentos de referência, que podem ser acessados por outros agentes com as ferramentas apropriadas.

**Benefícios:**

*   **Redução de Redundância:** Evita que múltiplos agentes pesquisem ou processem a mesma informação.
*   **Colaboração Aprimorada:** Permite que agentes construam sobre o trabalho uns dos outros, levando a soluções mais completas e eficientes.
*   **Contexto Enriquecido:** Agentes podem acessar um contexto mais rico e atualizado, melhorando a qualidade de suas decisões e respostas.
*   **Aprendizado Contínuo:** A base de conhecimento compartilhada pode ser usada para treinar e refinar modelos de agentes ao longo do tempo.

Essas melhorias permitirão que o sistema MCP-Crew se adapte dinamicamente a novas ferramentas e que seus agentes colaborem de forma mais inteligente, tornando-o uma plataforma verdadeiramente robusta e escalável para sistemas multi-agentes.

