# Nova Estrutura do Projeto ChatwootAI

Este documento descreve a nova estrutura padronizada do projeto ChatwootAI após a refatoração abrangente realizada em 19/03/2025.

## Visão Geral

O projeto foi reorganizado seguindo princípios fundamentais de engenharia de software:

1. **Consistência**: Todas as funcionalidades relacionadas seguem um padrão consistente
2. **Coesão**: Código com responsabilidades semelhantes está agrupado
3. **Baixo Acoplamento**: Componentes são desacoplados e comunicam-se através de interfaces bem definidas
4. **Princípio da Responsabilidade Única**: Cada componente tem uma única responsabilidade
5. **Facilidade de Manutenção**: A estrutura facilita localizar e modificar componentes

## Estrutura de Diretórios

```
/home/giovano/Projetos/Chatwoot V4/
├── src/
│   ├── agents/                 # Agentes do sistema
│   │   ├── core/               # Configurações básicas para agentes
│   │   │   └── __init__.py
│   │   └── functional/         # Agentes com funções específicas
│   │       ├── __init__.py
│   │       ├── sales_agent.py
│   │       ├── support_agent.py
│   │       └── scheduling_agent.py
│   ├── api/                    # Clientes de API externos
│   │   ├── chatwoot/           # Cliente do Chatwoot
│   │   │   ├── __init__.py
│   │   │   └── chatwoot_client.py
│   │   └── erp/
│   │       └── simulation/     # Simulação do ERP
│   │           ├── __init__.py
│   │           └── erp_simulation.py
│   ├── business_domain/       # Configurações de domínio (YAML)
│   │   ├── __init__.py
│   │   ├── cosmeticos.yaml
│   │   └── saude.yaml
│   ├── core/                   # Componentes fundamentais
│   │   ├── __init__.py
│   │   ├── data_proxy_agent.py   # Agente intermediário para acesso a dados
│   │   ├── data_service_hub.py   # Hub central para serviços de dados
│   │   ├── domain/             # Gerenciamento de domínios
│   │   │   ├── __init__.py
│   │   │   ├── domain_loader.py  # Carrega configurações YAML
│   │   │   └── domain_manager.py # Gerencia domínios ativos
│   │   └── hub.py              # Hub central para orquestração
│   ├── plugins/                # Sistema de plugins
│   │   ├── base/               # Classes base e interfaces
│   │   │   ├── __init__.py
│   │   │   └── base_plugin.py
│   │   ├── core/               # Plugins essenciais do sistema
│   │   │   ├── __init__.py
│   │   │   ├── appointment_scheduler.py  # Agendamento
│   │   │   ├── business_rules_plugin.py  # Regras de negócio 
│   │   │   ├── plugin_manager.py         # Gerenciador de plugins
│   │   │   └── product_search_plugin.py  # Busca de produtos
│   │   └── implementations/    # Implementações específicas por domínio
│   │       ├── __init__.py
│   │       ├── cosmetics/      # Plugins específicos para cosméticos
│   │       ├── health/         # Plugins específicos para saúde
│   │       └── retail/         # Plugins específicos para varejo
│   ├── services/               # Serviços auxiliares do sistema
│   │   ├── __init__.py
│   │   └── data/               # Implementações específicas de dados
│   │       ├── __init__.py
│   │       └── [outros serviços]
│   └── webhook/                # Serviços de webhook
│       ├── __init__.py
│       └── webhook_handler.py
```

## Componentes-Chave e Fluxo de Dados

### Agentes

Os agentes são componentes autônomos que realizam tarefas específicas:

- **Core Agents**: Agentes fundamentais para a arquitetura
  - **DataProxyAgent**: Único ponto de acesso aos dados do sistema

- **Functional Agents**: Agentes com funções específicas de negócio
  - **SalesAgent**: Agente especializado em vendas
  - **SupportAgent**: Agente especializado em suporte
  - **SchedulingAgent**: Agente especializado em agendamentos

### Sistema de Domínios

O sistema suporta múltiplos domínios de negócio (cosméticos, saúde, varejo):

1. **Configuração**: Arquivos YAML em `/src/business_domain/`
2. **Carregamento**: Classe `DomainLoader` em `/src/core/domain/`
3. **Gerenciamento**: Classe `DomainManager` em `/src/core/domain/`

### Plugins

Sistema extensível de plugins para adicionar funcionalidades específicas:

1. **Base**: Interfaces e classes abstratas em `/src/plugins/base/`
2. **Core**: Plugins essenciais do sistema em `/src/plugins/core/`
   - **plugin_manager.py**: Gerencia descoberta e carregamento de plugins
   - **business_rules_plugin.py**: Implementa regras de negócio
   - **product_search_plugin.py**: Facilita busca de produtos
   - **appointment_scheduler.py**: Gerencia agendamentos
3. **Implementations**: Implementações específicas por domínio de negócio

### Serviços de Dados

O acesso a dados é centralizado no `DataServiceHub`:

1. **Hub**: `/src/services/data/data_service_hub.py`
2. **Serviços Específicos**: Implementações em `/src/services/data/`

## Práticas de Desenvolvimento

1. **Importações**: Use importações relativas para módulos dentro do mesmo pacote
2. **Nomenclatura**: 
   - Arquivos Python: snake_case (ex: `data_service_hub.py`)
   - Classes: CamelCase (ex: `DataServiceHub`)
   - Funções e métodos: snake_case (ex: `get_data`)
   - Constantes: UPPER_SNAKE_CASE (ex: `MAX_RETRY_COUNT`)
3. **Documentação**: Todos os módulos, classes e métodos devem ter docstrings
4. **Tipagem**: Use anotações de tipo (type hints) em todas as funções e métodos

## Fluxo de Acesso aos Dados

Para garantir a coesão e segurança do sistema, o acesso aos dados **SEMPRE** deve seguir o fluxo:

```
Agente Funcional → DataProxyAgent → DataServiceHub → Serviços Específicos → Bancos de Dados
```

O acesso direto aos serviços de dados, contornando o DataProxyAgent, é **PROIBIDO** e quebra a arquitetura do sistema.

## Próximos Passos

1. Continuar a migração de código para a nova estrutura
2. Implementar testes automatizados para validar a arquitetura
3. Documentar interfaces de componentes-chave
4. Revisar e atualizar a documentação existente

---

Documento criado em: 19/03/2025  
Autor: Equipe de Desenvolvimento ChatwootAI
