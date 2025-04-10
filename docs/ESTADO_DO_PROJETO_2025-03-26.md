# Estado Atual do Projeto ChatwootAI
**Data:** 26 de março de 2025
**Hora:** 13:22

## Visão Geral do Projeto

O ChatwootAI é um sistema de atendimento ao cliente baseado em inteligência artificial que integra o Chatwoot como hub central de comunicação. O sistema utiliza uma arquitetura modular que permite adaptação para diferentes domínios de negócio (cosméticos, saúde, varejo) através de configurações YAML, agentes adaptáveis e um sistema de plugins.

### Componentes Principais:

1. **Chatwoot**: Hub central de comunicação
2. **CrewAI**: Orquestração de agentes inteligentes
3. **Qdrant**: Banco de dados vetorial para pesquisa semântica
4. **Redis**: Cache e armazenamento de estado
5. **Simulação do Odoo**: Regras de negócio e dados de produtos/clientes

## Estado Atual dos Testes

### Testes em Andamento

1. **Simulação de Webhook** (`scripts/testing/webhook_simulator.py`)
   - Envia payloads idênticos aos do Chatwoot real
   - Permite testar o sistema com diferentes account_ids
   - Foco atual: testar o mapeamento correto de account_id para domínios

2. **Monitoramento de Mapeamento de Clientes** (`scripts/monitoring/client_mapping_monitor.py`)
   - Verifica se os clientes estão sendo identificados corretamente
   - Monitora o carregamento de domínios em tempo real

3. **Testes Unitários**
   - Foco em componentes críticos como `DomainLoader`, `DomainManager` e `ClientMapper`
   - Verificação da integridade das configurações YAML

### Abordagem de Testes

Decidimos adotar uma abordagem de testes mais reativa e prática:
- Testar o sistema real em vez de tentar corrigir testes end-to-end complexos
- Usar ferramentas de simulação e monitoramento para identificar problemas em tempo real
- Focar na validação do fluxo completo de processamento de mensagens

## Objetivos Atuais

1. **Resolver Problemas de Mapeamento de Domínios**
   - Garantir que o sistema carregue corretamente o domínio "cosmetics" para o account_id 1
   - Eliminar falhas no carregamento de domínios e no fallback para o domínio "default"

2. **Melhorar o Fluxo de Processamento de Mensagens**
   - Garantir que o `webhook_handler.py` determine corretamente o domínio antes de enviar a mensagem para o `HubCrew`
   - Otimizar a comunicação entre os componentes do sistema

3. **Refinar a Estrutura de Configuração**
   - Validar a estrutura e o conteúdo dos arquivos YAML
   - Garantir que as configurações específicas de domínio e cliente sejam carregadas corretamente

4. **Implementar Logs Detalhados**
   - Adicionar logs estratégicos para facilitar o diagnóstico de problemas
   - Monitorar o fluxo de processamento de mensagens em tempo real

## Problemas Identificados

### 1. Carregamento de Domínios

O sistema está enfrentando dificuldades para carregar o domínio "cosmetics" para o account_id 1:
- O mapeamento no arquivo `config/chatwoot_mapping.yaml` parece correto
- A estrutura de diretórios e arquivos de configuração existe
- No entanto, o sistema tenta fazer fallback para o domínio "default", que também falha

Possíveis causas:
- Problemas na forma como o `DomainManager` consulta o arquivo de mapeamento
- Falhas na passagem do account_id do webhook para o DomainManager
- Problemas no carregamento do arquivo de configuração do domínio

### 2. Fluxo de Responsabilidades

Há uma questão sobre onde e como o mapeamento de account_id para domínio deve ocorrer:
- Atualmente, o `webhook_handler.py` obtém o account_id, mas não determina explicitamente o domínio
- A responsabilidade de determinar o domínio parece estar sendo delegada ao `HubCrew`
- Isso pode estar causando confusão e dificultando o diagnóstico de problemas

### 3. Estrutura de Arquivos

Existem preocupações sobre a organização e duplicação de arquivos:
- Alguns arquivos podem não fazer mais sentido no contexto atual do projeto
- Há potencial para confusão com arquivos duplicados ou obsoletos
- A organização dos testes e scripts precisa ser melhorada

## Próximos Passos

1. **Investigação Detalhada**
   - Analisar o código do `DomainManager` para entender como ele determina o domínio
   - Verificar como o `webhook_handler.py` processa os dados do webhook
   - Examinar os logs para identificar pontos de falha

2. **Implementação de Correções**
   - Modificar o `webhook_handler.py` para determinar explicitamente o domínio
   - Garantir que o `DomainManager` consulte corretamente o arquivo de mapeamento
   - Implementar um fallback robusto para casos em que o domínio não pode ser determinado

3. **Melhorias na Estrutura**
   - Organizar os testes em diretórios apropriados
   - Remover arquivos obsoletos ou duplicados
   - Documentar a estrutura do projeto para facilitar a manutenção

4. **Documentação**
   - Atualizar a documentação do projeto com as mudanças realizadas
   - Criar guias para novos desenvolvedores
   - Documentar os fluxos de processamento de mensagens

## Informações Importantes para Novos Desenvolvedores

### Estrutura de Diretórios

```
config/
  ├── chatwoot_mapping.yaml       # Mapeamento de account_ids para domínios
  └── domains/
      ├── _base/                  # Configurações base para todos os domínios
      ├── cosmetics/              # Domínio de cosméticos
      │   ├── config.yaml         # Configurações do domínio
      │   ├── client_1/           # Cliente específico
      │   │   └── config.yaml     # Configurações do cliente
      │   └── client_2/
      ├── health/                 # Domínio de saúde
      └── retail/                 # Domínio de varejo
```

### Fluxo de Processamento de Mensagens

1. **Chatwoot → Webhook → HubCrew**
2. **HubCrew**:
   - `OrchestratorAgent`: Detecta intenção
   - `ContextManager`: Cria/Atualiza contexto
   - Roteia para a Crew especializada
3. **Crew Especializada** (Sales, Support, Marketing):
   - Processa a mensagem
   - Acessa dados via `DataProxyAgent`
4. **Retorno**: Crew → HubCrew → Chatwoot → Cliente

### Dicas para Desenvolvimento

1. **Logs são seus amigos**: Use logs detalhados para entender o fluxo de execução
2. **Teste com o simulador**: Use o `webhook_simulator.py` para testar diferentes cenários
3. **Entenda o mapeamento**: O arquivo `chatwoot_mapping.yaml` é crucial para o funcionamento do sistema
4. **Respeite a estrutura modular**: Mantenha a separação de responsabilidades entre os componentes

## Conclusão

O projeto ChatwootAI está em um estágio avançado de desenvolvimento, mas enfrenta alguns desafios técnicos relacionados ao carregamento de domínios e ao fluxo de processamento de mensagens. Com uma abordagem focada e metódica, esses problemas podem ser resolvidos, permitindo que o sistema atenda eficientemente a diferentes domínios de negócio e clientes.

A arquitetura modular e a estrutura baseada em configurações YAML oferecem grande flexibilidade, mas também exigem atenção aos detalhes para garantir que todos os componentes funcionem harmoniosamente.
