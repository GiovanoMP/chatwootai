# Guia de Continuidade do Projeto ChatwootAI

**Data: 22/03/2025**

Este documento serve como um guia para a continuidade do desenvolvimento do projeto ChatwootAI, fornecendo uma visão geral do projeto, seu estado atual, trabalho recente realizado e próximos passos.

## Visão Geral do Projeto

O ChatwootAI é uma solução de automação de atendimento que integra vários componentes para criar um sistema inteligente de processamento de mensagens. O projeto tem como objetivo fornecer uma plataforma adaptável para diferentes domínios de negócio (cosméticos, saúde, varejo) através de uma arquitetura modular.

### Componentes Principais

1. **Chatwoot**: Hub central para gerenciamento de mensagens de diferentes canais (WhatsApp, Instagram)
2. **CrewAI**: Framework para orquestração de agentes de IA especializados
3. **Qdrant**: Banco de dados vetorial para busca semântica
4. **Redis**: Para armazenamento em cache e otimização de performance
5. **PostgreSQL**: Banco de dados relacional principal
6. **Simulação do Odoo**: Ambiente para testes de integração com ERP

## Arquitetura Atual

A arquitetura do sistema segue uma estrutura hierárquica clara:

```
/src/
├── agents/                     # Agentes do sistema
│   ├── core/                   # Agentes fundamentais (DataProxyAgent)
│   └── functional/             # Agentes funcionais específicos
├── api/                        # Interfaces com sistemas externos
├── services/                   # Serviços do sistema
│   └── data/                   # Serviços relacionados a dados
├── webhook/                    # Servidor webhook e handlers
├── plugins/                    # Sistema de plugins 
│   ├── base/                   # Classes base e interfaces
│   └── implementations/        # Implementações específicas por domínio
└── config/                     # Configurações do sistema
    └── domains/                # Configurações YAML por domínio
```

### Fluxo de Processamento de Mensagens

1. Webhook do Chatwoot recebe mensagens
2. Mensagens são processadas pelo webhook_handler
3. O HubCrew coordena o processamento das mensagens
4. Os agentes funcionais processam as mensagens (via CrewAI)
5. O DataProxyAgent centraliza todas as consultas de dados
6. DataServiceHub conecta-se aos bancos de dados e serviços
7. Respostas são enviadas de volta ao usuário via Chatwoot

## Trabalho Recente Realizado

### Refatoração da Arquitetura (21/03/2025)

1. **Remoção da WhatsAppChannelCrew**:
   - Removemos a `WhatsAppChannelCrew` da arquitetura para simplificar o fluxo de processamento
   - Eliminamos uma camada desnecessária, tornando o sistema mais eficiente
   - Atualizamos os testes de integração para refletir essa mudança

### Refatoração dos Testes do SalesAgent (21/03/2025)

1. **Migração para pytest**:
   - Convertemos os testes do `SalesAgent` do estilo `unittest.TestCase` para o estilo moderno do pytest
   - Implementamos fixtures para melhorar a organização e reutilização de código

2. **Melhorias na Estrutura de Testes**:
   - Criamos fixtures específicas para cada componente
   - Implementamos testes isolados para verificar o comportamento do `SalesAgent`

### Correções de Integração (20/03/2025)

1. **Compatibilidade com Pydantic**:
   - Substituímos `ClassVar` por `PrivateAttr` nas classes `AdaptableAgent` e `SalesAgent`
   - Implementamos validação de configuração usando Pydantic

2. **Interoperabilidade com CrewAI**:
   - Adicionamos métodos delegativos no `DataProxyAgent` para compatibilidade
   - Implementamos suporte para propriedades como `role`, `goal`, etc.

## Estado Atual dos Componentes

### Serviços de Infraestrutura:

- **PostgreSQL**: ✅ Conectando com sucesso
- **Redis**: ✅ Conectando com sucesso
- **Qdrant**: ✅ Conectando com sucesso
- **DataServiceHub**: ✅ Inicializando e gerenciando conexões
- **DataProxyAgent**: ✅ Inicializando com ferramentas de dados integradas

### Componentes do Sistema:

- **SalesAgent**: ✅ Testes refatorados e passando
- **AdaptableAgent**: ✅ Compatível com Pydantic
- **DataProxyAgent**: ✅ Compatível com CrewAI
- **MemorySystem**: ✅ Funcionando com Redis
- **DomainManager**: ✅ Carregando configurações de domínio

### Status dos Testes:

1. **Testes de Conexão**: ✅ PASSOU
2. **Testes de Integração do Hub**: ✅ PASSOU
3. **Testes do SalesAgent**: ✅ PASSOU
4. **Testes de Integração das Crews**: ✅ PASSOU

## Próximos Passos

1. **Melhorias na Arquitetura**:
   - Continuar a simplificação da arquitetura, removendo camadas desnecessárias
   - Otimizar o fluxo de processamento de mensagens
   - Implementar testes adicionais para verificar o comportamento em diferentes cenários

2. **Integração com Chatwoot**:
   - Testar a integração entre o Webhook do Chatwoot e o sistema refatorado
   - Implementar testes de integração end-to-end
   - Verificar o fluxo completo de mensagens

3. **Documentação e Padronização**:
   - Documentar padrões de acesso a dados para desenvolvedores
   - Criar guias de desenvolvimento para novos contribuidores
   - Padronizar a estrutura de testes em todo o projeto

4. **Otimização e Desempenho**:
   - Implementar testes de desempenho para avaliar a escalabilidade
   - Otimizar o acesso ao banco de dados e ao Redis
   - Melhorar o gerenciamento de memória e recursos

5. **Expansão de Funcionalidades**:
   - Implementar suporte para novos domínios de negócio
   - Desenvolver novos plugins para integração com sistemas externos
   - Melhorar a adaptabilidade dos agentes para diferentes contextos

## Documentos Úteis para Consulta

1. **Documentação de Arquitetura**:
   - `/docs/2025-03-21_Atualizacao_Progresso_Testes.md` - Status atual do projeto e testes
   - `/docs/2025-03-19_Conexoes_Servicos_Docker.md` - Configuração dos serviços Docker

2. **Código-fonte Essencial**:
   - `/src/webhook/webhook_handler.py` - Ponto de entrada para processamento de mensagens
   - `/src/core/hub.py` - Coordenação central de mensagens
   - `/src/agents/core/data_proxy_agent.py` - Agente central para acesso a dados
   - `/src/services/data/data_service_hub.py` - Hub de serviços de dados

3. **Testes**:
   - `/tests/test_crew_integration.py` - Testes de integração das crews
   - `/tests/test_sales_agent.py` - Testes do SalesAgent
   - `/tests/test_qdrant_connection.py` - Testes de conexão com Qdrant

## Diretrizes de Desenvolvimento

1. **Princípios Arquiteturais**:
   - O `DataProxyAgent` é o ÚNICO ponto de acesso autorizado para consultas de dados
   - Manter a arquitetura modular e adaptável para diferentes domínios
   - Evitar duplicação de código e funcionalidades

2. **Boas Práticas**:
   - Seguir as melhores práticas de engenharia de software
   - Escrever testes para todas as novas funcionalidades
   - Manter a documentação atualizada
   - Organizar novos arquivos em diretórios apropriados

3. **Fluxo de Trabalho**:
   - Verificar a existência de arquivos antes de criar novos
   - Excluir arquivos antigos e disfuncionais ao substituí-los
   - Verificar regularmente se há arquivos que não fazem mais sentido na estrutura

## Conclusão

O projeto ChatwootAI está progredindo bem, com melhorias significativas na estrutura de testes e na integração entre componentes. A refatoração para o estilo pytest e a simplificação da arquitetura estão facilitando a manutenção e o desenvolvimento do sistema.

Os próximos passos focam na resolução das falhas restantes, na integração completa com o Chatwoot e na expansão das funcionalidades do sistema. Com a base sólida que está sendo construída, o projeto está bem posicionado para crescer e se adaptar a diferentes domínios de negócio.
