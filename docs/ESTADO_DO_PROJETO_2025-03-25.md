# ESTADO DO PROJETO - 2025-03-25

## Visão Geral do Projeto

O ChatwootAI é um sistema avançado de atendimento ao cliente que integra o Chatwoot como hub central de mensagens com uma arquitetura Hub and Spoke baseada em CrewAI. O sistema é projetado para ser multi-tenant, adaptando-se dinamicamente a diferentes domínios de negócio (cosméticos, saúde, varejo, etc.) através de configurações YAML.

## Estado Atual

Atualmente, o sistema está em fase de testes, com foco na integração do webhook com o Chatwoot. A estrutura principal do sistema está implementada, incluindo o HubCrew, as crews especializadas, o DataProxyAgent e o DomainManager. O sistema de webhook está configurado e operacional, mas apresenta alguns problemas que precisam ser resolvidos.

### Componentes Funcionais

1. **Servidor Webhook**: O servidor está operacional e recebendo mensagens do Chatwoot.
2. **Ngrok**: O túnel Ngrok está configurado e funcionando, permitindo que o servidor webhook local receba mensagens da internet.
3. **Proxy na VPS**: O servidor proxy na VPS está configurado e encaminhando mensagens para o ambiente local via Ngrok.
4. **Sistema de Logs**: O sistema de logs está configurado e registrando informações importantes sobre o funcionamento do sistema.

### Problemas Identificados

Durante os testes realizados em 25/03/2025, foram identificados os seguintes problemas:

#### 1. Problema com o DomainManager

**Descrição**: O sistema está gerando avisos de que o DomainManager não está disponível, o que impede a inicialização das ferramentas necessárias para o processamento adequado das mensagens.

```
WARNING - DomainManager não disponível, ferramentas não serão inicializadas
```

**Causa Provável**: Embora o DomainManager esteja sendo inicializado corretamente no servidor webhook, ele não está sendo passado adequadamente para o DataProxyAgent. Isso pode ocorrer devido a um problema na cadeia de inicialização dos componentes.

**Solução Proposta**: Verificar a inicialização do DataProxyAgent e garantir que ele receba corretamente a instância do DomainManager. Pode ser necessário revisar o código de inicialização no arquivo `server.py` e garantir que o DomainManager seja passado corretamente para todos os componentes que dependem dele.

#### 2. Mensagens sendo Ignoradas

**Descrição**: O sistema está recebendo mensagens do Chatwoot, mas algumas delas estão sendo ignoradas com a mensagem:

```
"status": "ignored", "reason": "Not an incoming message"
```

**Causa**: Este comportamento é esperado para mensagens que não são de entrada (de clientes), como mensagens enviadas pelo sistema ou por agentes. Isso evita loops infinitos de mensagens.

**Solução Proposta**: Este comportamento é normal e desejado. No entanto, podemos melhorar o log para torná-lo mais informativo e menos alarmante, especificando claramente que este é um comportamento esperado.

#### 3. Eventos Desconhecidos

**Descrição**: O webhook está recebendo eventos do tipo "contact_updated", mas não sabe como processá-los:

```
WARNING - Tipo de evento desconhecido: contact_updated
```

**Causa**: O webhook handler não está configurado para processar eventos do tipo "contact_updated".

**Solução Proposta**: Implementar um manipulador específico para eventos do tipo "contact_updated" no webhook handler, ou configurar o sistema para ignorar silenciosamente esses eventos sem gerar avisos.

## Próximos Passos

1. **Corrigir o Problema do DomainManager**: Garantir que o DomainManager seja passado corretamente para todos os componentes que dependem dele.

2. **Melhorar o Tratamento de Eventos**: Implementar manipuladores para todos os tipos de eventos que o Chatwoot pode enviar, ou configurar o sistema para ignorar silenciosamente eventos não suportados.

3. **Testar com Mensagens Reais**: Enviar mensagens reais através do Chatwoot para verificar se o sistema está processando corretamente as mensagens e gerando respostas adequadas.

4. **Monitorar os Logs**: Continuar monitorando os logs para identificar e resolver quaisquer outros problemas que possam surgir.

5. **Expandir os Testes**: Implementar testes mais abrangentes para garantir que todos os componentes do sistema estejam funcionando corretamente em diferentes cenários.

## Contexto para o Próximo Desenvolvedor

Para facilitar a continuidade do desenvolvimento, incluímos abaixo informações importantes sobre a configuração e o funcionamento do sistema.

### Configuração do Webhook

O webhook é o ponto de entrada para mensagens do Chatwoot. Ele recebe mensagens, determina o domínio de negócio apropriado para a conversa, e encaminha as mensagens para o HubCrew.

#### Fluxo de Determinação de Domínio

O webhook handler determina o domínio seguindo uma hierarquia de fontes:

1. Primeiro tenta pelo account_id (nível da empresa)
2. Se não encontrar, tenta pelo inbox_id (nível do canal)
3. Por último, consulta metadados adicionais via API do Chatwoot

#### Configuração da VPS

O sistema utiliza uma VPS para hospedar um servidor proxy que recebe as mensagens do Chatwoot e as encaminha para o ambiente local via Ngrok.

- **Servidor VPS**: srv692745.hstgr.cloud
- **Container**: webhook-proxy
- **Porta Externa**: 8802

### Inicialização do Sistema

Para inicializar o sistema, siga os passos descritos no documento `src/webhook/inicializacao_rapida.md`. Em resumo:

1. Configure o sistema de logs
2. Inicie o servidor webhook local
3. Inicie o Ngrok para criar um túnel
4. Monitore os logs
5. Atualize a URL do Ngrok na VPS
6. Teste a conexão

### Arquitetura do Sistema

O ChatwootAI segue o modelo Hub and Spoke (Centro e Raios), com um hub central que coordena múltiplos componentes especializados. Os principais componentes são:

1. **Hub Central (`src/core/hub.py`)**
   - `HubCrew`: Orquestração principal de mensagens
   - `OrchestratorAgent`: Análise de intenção e roteamento inteligente
   - `ContextManagerAgent`: Gerenciamento do contexto da conversa
   - `IntegrationAgent`: Integrações com sistemas externos
   - `DataProxyAgent`: Único ponto de acesso a dados

2. **Crews Especializadas**
   - `SalesCrew`: Processamento de consultas e vendas de produtos
   - `SupportCrew`: Suporte técnico e atendimento a reclamações
   - `MarketingCrew`: Campanhas, promoções e engajamento
   - `SchedulingCrew`: Agendamentos e compromissos

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

### Documentação Adicional

Para mais informações sobre o sistema, consulte os seguintes documentos:

- **README.md**: Visão geral do sistema, arquitetura e componentes
- **src/webhook/README.md**: Detalhes sobre o servidor webhook e sua configuração
- **src/webhook/inicializacao_rapida.md**: Guia passo a passo para inicializar o sistema
- **docs/ARQUITETURA_DATA_SERVICES_OTIMIZADA.md**: Detalhes sobre a camada de dados
- **docs/ESTADO_DO_PROJETO_2025-03-22.md**: Estado anterior do projeto
- **docs/ESTADO_DO_PROJETO_2025-03-23.md**: Estado anterior do projeto

## Conclusão

O sistema ChatwootAI está em um estágio avançado de desenvolvimento, com a maioria dos componentes principais implementados e funcionais. Os problemas identificados são relativamente menores e podem ser resolvidos com ajustes pontuais no código. Com a resolução desses problemas, o sistema estará pronto para testes mais abrangentes e, eventualmente, para implantação em produção.

---

Desenvolvido com ❤️ pela Equipe ChatwootAI
