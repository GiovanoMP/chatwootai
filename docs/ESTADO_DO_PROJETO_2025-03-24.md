# Estado do Projeto - 24 de Março de 2025

## Visão Geral

Estamos trabalhando na implementação e teste do fluxo completo de mensagens usando a arquitetura hub-and-spoke com a GenericCrew. Este documento resume o estado atual do desenvolvimento, os desafios encontrados e os próximos passos.

## Componentes Atuais em Desenvolvimento

### 1. Testes de Fluxo Completo com GenericCrew

Estamos implementando testes para validar o fluxo completo de processamento de mensagens, desde a entrada via webhook do Chatwoot até o processamento pela GenericCrew especializada e o retorno da resposta.

**Arquivo principal**: `/tests/test_generic_crew_flow.py`

Este teste simula o seguinte fluxo:
1. Cliente → Chatwoot → Webhook → HubCrew
2. HubCrew (OrchestratorAgent) → GenericCrew especializada (definida em YAML)
3. GenericCrew → DataProxyAgent → DataServiceHub → Serviços específicos
4. Resposta volta pelo mesmo caminho

### 2. Ajustes na GenericCrew

A classe GenericCrew foi modificada para suportar o mapeamento de IDs de tarefas, similar ao mapeamento existente de IDs de agentes. Isso permite um melhor gerenciamento e rastreamento das tarefas durante o processamento de mensagens.

**Arquivo modificado**: `/src/core/crews/generic_crew.py`

### 3. Correções no CrewFactory

O método `_create_tasks_from_workflow` no CrewFactory foi corrigido para não definir o ID da tarefa, já que a biblioteca CrewAI gerencia isso internamente.

**Arquivo modificado**: `/src/core/crews/crew_factory.py`

## Desafios Atuais

1. **Métodos Assíncronos no HubCrew**: O método `process_message` no HubCrew é assíncrono (`async def`), o que requer ajustes nos testes para trabalhar corretamente com funções assíncronas.

2. **Integração com o MemorySystem**: O HubCrew requer um sistema de memória para funcionar corretamente, o que exige a criação de mocks adequados para os testes.

3. **Roteamento de Mensagens**: Estamos ajustando o teste para usar o método correto de roteamento de mensagens no HubCrew, já que o método `_route_to_crew` parece não existir na implementação atual.

## Próximos Passos

1. **Finalizar os Testes de Fluxo Completo**: Corrigir os problemas nos testes para garantir que eles funcionem corretamente com a implementação atual do HubCrew e da GenericCrew.

2. **Implementar Testes para Diferentes Domínios**: Adicionar testes que verificam a adaptação do sistema a diferentes domínios de negócio (cosméticos, saúde, varejo).

3. **Melhorar a Documentação**: Atualizar a documentação com informações sobre o fluxo de mensagens e a integração entre os componentes.

## Arquivos Importantes

- `/src/core/hub.py`: Implementação do HubCrew, componente central da arquitetura hub-and-spoke.
- `/src/core/crews/generic_crew.py`: Implementação da GenericCrew, que processa mensagens com base em configurações YAML.
- `/src/core/crews/crew_factory.py`: Fábrica para criar crews a partir de configurações YAML.
- `/src/core/domain/domain_manager.py`: Gerenciador de domínios de negócio.
- `/src/core/memory.py`: Sistema de memória compartilhada para o hub-and-spoke.
- `/tests/test_generic_crew_flow.py`: Testes para o fluxo completo de mensagens.

## Observações

- A arquitetura hub-and-spoke está funcionando conforme esperado, com o HubCrew como componente central e as crews especializadas como raios.
- O sistema de adaptação a diferentes domínios de negócio está implementado e funcionando.
- Os testes estão sendo ajustados para trabalhar corretamente com funções assíncronas e mocks adequados.
