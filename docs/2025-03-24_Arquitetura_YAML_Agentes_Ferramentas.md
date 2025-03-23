# Arquitetura do ChatwootAI: Configuração YAML, Agentes e Ferramentas

**Data:** 2025-03-24  
**Autor:** Equipe de Desenvolvimento ChatwootAI  
**Versão:** 1.0

## Sumário

1. [Introdução](#introdução)
2. [Arquitetura Baseada em YAML](#arquitetura-baseada-em-yaml)
3. [Configuração de Agentes e Crews](#configuração-de-agentes-e-crews)
4. [Gerenciamento Centralizado de Ferramentas](#gerenciamento-centralizado-de-ferramentas)
5. [Fluxo de Execução](#fluxo-de-execução)
6. [Vantagens da Arquitetura](#vantagens-da-arquitetura)
7. [Exemplos Práticos](#exemplos-práticos)
8. [Conclusão](#conclusão)

## Introdução

O ChatwootAI implementa uma arquitetura modular e flexível, baseada em configurações YAML para definição de agentes, crews e ferramentas. Este documento explica como essa arquitetura funciona, com foco especial no papel do DataProxyAgent como gerenciador centralizado de acesso a dados e ferramentas.

## Arquitetura Baseada em YAML

### Conceito Fundamental

A arquitetura do ChatwootAI separa claramente **configuração** de **implementação**. Toda a definição de comportamentos, fluxos de trabalho e atribuições de ferramentas é feita através de arquivos YAML, enquanto o código-fonte implementa a lógica subjacente.

### Estrutura de Diretórios

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

### Herança e Sobreposição

- Cada domínio herda as configurações base
- Configurações específicas do domínio podem sobrescrever as configurações base
- Isso permite personalização sem duplicação de código

## Configuração de Agentes e Crews

### Definição de Agentes

Os agentes são definidos nos arquivos YAML com suas características e comportamentos:

```yaml
agents:
  sales_expert:
    type: SalesAgent
    config:
      role: "Consultor de Beleza"
      goal: "Auxiliar clientes na escolha de produtos cosméticos adequados"
      backstory: |
        Especialista em produtos de beleza com profundo conhecimento
        de formulações cosméticas e preferências de clientes.
    tools:
      - product_catalog
      - skin_analyzer
      - beauty_recommender
```

### Definição de Crews

As crews (equipes) são compostas por múltiplos agentes organizados em um fluxo de trabalho:

```yaml
crew:
  name: CosmeticsSalesCrew
  description: "Equipe especializada em vendas de produtos cosméticos"
  agents:
    - sales_expert
    - skincare_specialist
  workflow:
    - step: initial_contact
      agent: sales_expert
      tools: [product_catalog]
    - step: skin_analysis
      agent: skincare_specialist
      tools: [skin_analyzer]
```

### Carregamento Dinâmico

Em tempo de execução, o sistema:
1. Carrega as configurações YAML
2. Instancia os agentes conforme definido
3. Configura as crews e seus fluxos de trabalho
4. Atribui as ferramentas apropriadas a cada agente

## Gerenciamento Centralizado de Ferramentas

### Definição de Ferramentas

As ferramentas são definidas no arquivo `base_tools.yaml`:

```yaml
tools:
  # Ferramentas de busca
  basic_search:
    name: "Busca Básica"
    description: "Realiza buscas simples em texto"
    class: "src.tools.search.BasicSearchTool"
    parameters:
      max_results: 10
      use_fuzzy: true
  
  # Ferramentas de consulta a dados
  data_query:
    name: "Consulta de Dados"
    description: "Consulta dados em diferentes fontes de forma unificada"
    class: "src.tools.data.DataQueryTool"
    parameters:
      timeout: 30
      cache_results: true
```

### O Papel do DataProxyAgent

O DataProxyAgent atua como um **intermediário obrigatório** entre os agentes e as ferramentas de acesso a dados:

1. **Registro Centralizado**: Todas as ferramentas são registradas no `ToolRegistry`
2. **Controle de Acesso**: O DataProxyAgent verifica se um agente tem permissão para usar uma ferramenta
3. **Gerenciamento de Cache**: Implementa cache em dois níveis (memória local + Redis)
4. **Adaptação ao Domínio**: Ajusta consultas conforme o domínio ativo

### Distribuição de Ferramentas

Embora as ferramentas sejam definidas globalmente, elas são **distribuídas seletivamente** para os agentes que precisam delas:

```python
# Pseudocódigo de como as ferramentas são distribuídas
def get_agent_tools(agent_name, domain_name):
    # Obter a lista de ferramentas do agente
    tool_ids = domain_manager.get_agent_tools(agent_name, domain_name)
    
    # Obter instâncias das ferramentas
    return tool_registry.get_tools_for_agent(tool_ids)
```

## Fluxo de Execução

### Inicialização do Sistema

1. Carregamento das configurações YAML
2. Inicialização do `DomainManager` com o domínio padrão
3. Inicialização do `DataServiceHub` com todos os serviços de dados
4. Inicialização do `ToolRegistry` com todas as ferramentas disponíveis
5. Inicialização do `DataProxyAgent` como intermediário para acesso a dados
6. Inicialização do `HubCrew` com os agentes centrais

### Processamento de Mensagens

1. Cliente envia mensagem via Chatwoot
2. `HubCrew` recebe a mensagem
3. `OrchestratorAgent` analisa a intenção e determina a crew apropriada
4. A crew especializada é ativada com seus agentes e ferramentas
5. Os agentes acessam dados **exclusivamente** via `DataProxyAgent`
6. A resposta é gerada e retornada ao cliente

## Vantagens da Arquitetura

### 1. Flexibilidade e Adaptabilidade

- **Configuração Declarativa**: Mudanças de comportamento sem alterar código-fonte
- **Adaptação por Domínio**: Diferentes comportamentos para diferentes domínios de negócio
- **Extensibilidade**: Fácil adição de novos agentes, ferramentas e fluxos

### 2. Segurança e Consistência

- **Acesso Centralizado**: Todas as operações de dados passam pelo DataProxyAgent
- **Auditoria Simplificada**: Monitoramento centralizado de todas as consultas
- **Consistência de Dados**: Formatação padronizada para todos os agentes

### 3. Performance e Otimização

- **Cache Centralizado**: Evita consultas redundantes ao banco de dados
- **Otimização de Consultas**: Análise de padrões para melhorar performance
- **Reutilização de Instâncias**: Ferramentas são instanciadas uma única vez e reutilizadas

### 4. Manutenção e Escalabilidade

- **Separação de Responsabilidades**: Código e configuração separados
- **Testabilidade**: Fácil mockar componentes para testes unitários
- **Escalabilidade Horizontal**: Possibilidade de escalar componentes específicos

## Exemplos Práticos

### Exemplo 1: Consulta de Produto em Diferentes Domínios

Quando um cliente pergunta "Você tem creme para as mãos?", o processamento ocorre assim:

**Domínio de Cosméticos:**
1. Mensagem recebida pelo `HubCrew`
2. Roteada para `CosmeticsSalesCrew`
3. `sales_expert` usa a ferramenta `product_catalog` via DataProxyAgent
4. DataProxyAgent consulta o catálogo de cosméticos
5. Resposta: "Sim, temos vários cremes para mãos. Recomendo o Hidratante Intensivo para Mãos com manteiga de karité..."

**Domínio de Saúde:**
1. Mesmo fluxo inicial
2. Roteada para `HealthSalesCrew`
3. `health_advisor` usa a mesma ferramenta `product_catalog` via DataProxyAgent
4. DataProxyAgent consulta o catálogo de produtos de saúde
5. Resposta: "Sim, temos cremes terapêuticos para mãos. Para pele ressecada, recomendo o Creme Reparador Dermatológico..."

**Mesma ferramenta, comportamentos diferentes baseados no domínio!**

### Exemplo 2: Adição de Nova Ferramenta

Para adicionar uma nova ferramenta de análise de sentimento:

1. Adicionar definição em `base_tools.yaml`:
```yaml
sentiment_analyzer:
  name: "Analisador de Sentimento"
  description: "Analisa o sentimento do cliente na mensagem"
  class: "src.tools.nlp.SentimentAnalyzerTool"
  parameters:
    model: "advanced"
    threshold: 0.7
```

2. Atribuir a ferramenta aos agentes que precisam dela:
```yaml
agents:
  customer_support:
    tools:
      - sentiment_analyzer
      - response_template
```

3. A ferramenta estará disponível automaticamente para os agentes especificados, sem necessidade de alterar o código-fonte.

## Conclusão

A arquitetura baseada em YAML com gerenciamento centralizado de ferramentas via DataProxyAgent oferece o equilíbrio ideal entre flexibilidade e controle. Esta abordagem permite:

- Adaptar o sistema para diferentes domínios de negócio
- Manter segurança e consistência no acesso a dados
- Otimizar performance com cache centralizado
- Facilitar manutenção e extensão do sistema

Esta arquitetura segue as melhores práticas de engenharia de software, com clara separação de responsabilidades, configuração declarativa e acesso controlado a recursos.

---

**Próximos Passos:**
- Implementação de validação de esquema para arquivos YAML
- Desenvolvimento de interface administrativa para edição de configurações
- Expansão do sistema de plugins para integração com serviços externos
