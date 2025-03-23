# Status do Projeto ChatwootAI - 24/03/2023

## Estado Atual do Sistema

### Componentes Funcionais

1. **Servidor Webhook**
   - Implementado em `src/webhook/server.py`
   - Recebe mensagens do Chatwoot via webhook
   - Registra logs detalhados em `logs/webhook.log`
   - Encaminha mensagens para o hub central (hub.py)

2. **Integração com Ngrok**
   - Script `scripts/webhook/simple_ngrok_starter.py` para iniciar o Ngrok
   - Expõe o servidor webhook local à internet
   - Atualiza automaticamente a URL do webhook no Chatwoot

3. **Sistema de Logs**
   - Configurado via `scripts/webhook/setup_logging.py`
   - Logs separados para webhook, hub e testes
   - Monitoramento em tempo real disponível

4. **Testes de Conexão**
   - Script `scripts/webhook/test_webhook_connection.py` para verificar a conexão
   - Testa Ngrok, servidor webhook e conexão com a VPS

### Problemas Identificados

1. **Diretório de Domínios**
   - Aviso: "Diretório de domínios não encontrado: src/business_domain"
   - Impacto: DomainManager não está disponível, afetando a inicialização de ferramentas

2. **Crews Especializadas**
   - Aviso: "Crew 'SalesCrew' não encontrada"
   - Impacto: Mensagens não estão sendo processadas pelas crews especializadas

3. **Serviços de Dados**
   - Aviso: "Tentativa de acessar serviço não registrado: 'VectorSearchService'"
   - Impacto: Busca vetorial não está funcionando

## Desafios Atuais

1. **Configuração de Domínios**
   - O sistema está procurando configurações de domínio em `src/business_domain`, mas esse diretório não existe
   - As configurações de domínio são essenciais para adaptar o sistema a diferentes contextos de negócio

2. **Inicialização de Crews**
   - As crews especializadas (SalesCrew, SupportCrew) não estão sendo inicializadas corretamente
   - Isso impede o processamento adequado das mensagens

3. **Registro de Serviços**
   - Serviços essenciais como VectorSearchService não estão registrados no DataServiceHub
   - Isso afeta a capacidade do sistema de buscar informações relevantes

## Próximos Passos

1. **Configuração de Domínios**
   - Criar diretório `config/domains` com subdiretórios para cada domínio (_base, cosmetics, health, retail)
   - Implementar arquivos YAML de configuração para cada domínio
   - Verificar se o DomainManager está carregando corretamente as configurações

2. **Inicialização de Crews**
   - Revisar o código de inicialização das crews em `src/core/hub.py`
   - Garantir que todas as crews especializadas sejam registradas corretamente
   - Implementar mecanismo de fallback para quando uma crew não estiver disponível

3. **Registro de Serviços**
   - Revisar o código de inicialização do DataServiceHub
   - Garantir que todos os serviços essenciais sejam registrados durante a inicialização
   - Implementar mecanismo de fallback para quando um serviço não estiver disponível

4. **Testes Abrangentes**
   - Desenvolver testes automatizados para cada componente do sistema
   - Criar cenários de teste que cubram o fluxo completo de processamento de mensagens
   - Implementar monitoramento contínuo para detectar falhas em tempo real

## Arquivos Importantes para Inicialização do Webhook

Para facilitar a continuidade do projeto, aqui estão os principais arquivos relacionados à inicialização e monitoramento do webhook:

1. **Inicialização do Servidor Webhook**
   ```
   src/webhook/server.py
   ```

2. **Configuração de Logs**
   ```
   scripts/webhook/setup_logging.py
   ```

3. **Inicialização do Ngrok**
   ```
   scripts/webhook/simple_ngrok_starter.py
   ```

4. **Teste de Conexão**
   ```
   scripts/webhook/test_webhook_connection.py
   ```

5. **Monitoramento de Logs**
   ```
   scripts/webhook/monitor_webhook_logs.py
   ```

6. **Documentação do Webhook**
   ```
   src/webhook/README.md
   ```

## Fluxo de Processamento de Mensagens

Lembrando o fluxo correto de processamento de mensagens no sistema:

1. **Entrada da Mensagem**
   - Cliente envia mensagem via WhatsApp
   - Chatwoot recebe a mensagem e a encaminha via webhook para nosso sistema

2. **Processamento pelo Hub Central**
   - A mensagem é recebida pelo servidor de webhook
   - O servidor encaminha a mensagem para o Hub.py
   - O HubCrew contém OrchestratorAgent, ContextManagerAgent, IntegrationAgent e DataProxyAgent

3. **Orquestração e Roteamento**
   - O OrchestratorAgent analisa a mensagem e determina qual crew especializada deve processá-la
   - O ContextManagerAgent mantém o contexto da conversa
   - Para uma consulta sobre produtos, a mensagem é roteada para a SalesCrew

4. **Acesso a Dados**
   - Todos os agentes especializados acessam dados EXCLUSIVAMENTE através do DataProxyAgent
   - O DataProxyAgent interage com o DataServiceHub para acessar serviços específicos
   - O DataServiceHub coordena os serviços de dados (ProductDataService, CustomerDataService, etc.)

5. **Adaptação ao Domínio**
   - O sistema verifica o domínio ativo (cosméticos, saúde, varejo) para adaptar as respostas
   - Configurações de domínio são carregadas do diretório de configurações YAML

Este fluxo garante a centralização do acesso a dados, desacoplamento de componentes e adaptabilidade a diferentes domínios de negócio.
