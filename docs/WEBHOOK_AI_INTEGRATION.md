# Integração do Webhook com o Sistema de Agentes IA

## Visão Geral

Este documento descreve a integração entre o webhook do Chatwoot e o sistema de agentes baseado em CrewAI para o projeto ChatwootAI. Esta integração permite que as mensagens de clientes recebidas pelo Chatwoot sejam processadas por agentes de IA inteligentes que podem fornecer respostas automatizadas.

## Arquitetura

A integração segue o fluxo abaixo:

1. **Chatwoot recebe mensagem**: Um cliente envia uma mensagem através do WhatsApp ou outra plataforma.
2. **Chatwoot envia webhook**: Chatwoot envia um webhook HTTP POST para o nosso servidor.
3. **Webhook Server processa**: Nosso servidor recebe o webhook e extrai informações relevantes.
4. **HubCrew processa mensagem**: A mensagem é enviada para o HubCrew.
5. **Orquestrador analisa**: O OrchestratorAgent analisa a intenção -
6. **Crew Funcional processa**: A crew especializada (vendas, suporte, etc.) processa a mensagem.
7. **Resposta enviada**: A resposta é enviada de volta para o Chatwoot.
8. **Cliente recebe resposta**: O Chatwoot envia a resposta para o cliente.

```
+-----------+     +-----------+     +----------------+     +-----------+
|  Cliente  | --> |  Chatwoot | --> | Webhook Server | --> |  HubCrew  |
+-----------+     +-----------+     +----------------+     +-----------+
      ^                 ^                                        |
      |                 |                                        v
      |                 |                               +----------------+
      |                 |                               |  Orchestrator  |
      |                 |                               +----------------+
      |                 |                                        |
      |                 |                                        v
      |                 |     +----------------+     +----------------------+
      +-----------------|-----|  API Chatwoot  |<----| Crews (Sales/Support)|
                        |     +----------------+     +----------------------+
                        |                                        ^
                        |                                        |
                        |                      +----------------+|
                        |                      | DataProxyAgent ||
                        |                      +----------------+|
                        |                              ^
                        |                              |
                        |               +----------------+
                        +---------------|  Data Services |
                                        +----------------+
```

**NOTA IMPORTANTE:** O DataProxyAgent é o único ponto de acesso permitido aos serviços de dados (DataServices). Toda consulta de dados no sistema DEVE ser feita através deste agente, nunca acessando diretamente a camada de dados.

## Componentes Principais

### 1. Webhook Handler

O `ChatwootWebhookHandler` é o componente responsável por receber e processar os webhooks do Chatwoot, extraindo informações relevantes e encaminhando para o sistema de agentes.

- **Processamento de mensagens**: Extrai conteúdo, ID da conversa, dados do contato.
- **Normalização de dados**: Converte o formato do Chatwoot para o formato interno.
- **Encaminhamento**: Envia a mensagem para o HubCrew para processamento.

### 2. HubCrew

O HubCrew é o componente central que coordena o processamento de mensagens:

- **OrchestratorAgent**: Analisa a intenção da mensagem e decide qual crew funcional deve processá-la.
- **ContextManagerAgent**: Gerencia o contexto da conversa para manter a coerência.
- **IntegrationAgent**: Integra com sistemas externos como o Odoo.

### 3. Crews Funcionais

Crews especializadas em diferentes domínios:

- **SalesCrew**: Processa consultas relacionadas a vendas, como informações sobre produtos e preços.
- **SupportCrew**: Lida com problemas de suporte, como status de pedidos e reclamações.
- **InfoCrew**: Fornece informações gerais, como horários de funcionamento e políticas.

### 4. DataProxyAgent

O **DataProxyAgent** é um componente crítico na arquitetura, funcionando como intermediário e único conector autorizado com a camada de DataService:

- **Tradução de consultas**: Converte solicitações em linguagem natural feitas pelos agentes em operações específicas de dados.
- **Intermediário obrigatório**: É o único ponto de acesso autorizado para os serviços de dados, impedindo acesso direto dos agentes à camada de dados.
- **Otimização de consultas**: Aplica técnicas como caching, batching e otimização de consultas para melhorar performance.
- **Consistência de formatação**: Garante que os dados retornados sigam um formato consistente independente da fonte.
- **Adaptação por domínio**: Adapta consultas conforme o domínio de negócio ativo, aplicando regras específicas do contexto.

### 5. API do Chatwoot

O cliente da API do Chatwoot (`ChatwootClient`) é usado para enviar respostas de volta para o Chatwoot:

- **Envio de mensagens**: Envia respostas para conversas específicas.
- **Gerenciamento de conversas**: Atualiza status, atribui a agentes, adiciona etiquetas.

## Fluxo Detalhado

1. **Recepção do Webhook**
   - O servidor webhook recebe uma solicitação POST do Chatwoot.
   - O payload é validado e registrado para fins de depuração.

2. **Processamento do Evento**
   - Eventos diferentes (message_created, conversation_created, etc.) são processados de forma diferente.
   - Para mensagens de entrada, o conteúdo é extraído e normalizado.

3. **HubCrew Processing**
   - A mensagem normalizada é enviada para o HubCrew.
   - O OrchestratorAgent analisa a intenção e seleciona a crew apropriada.
   - O ContextManagerAgent adiciona contexto da conversa anterior.

4. **Processamento pela Crew Funcional**
   - A crew especializada processa a mensagem usando seus agentes.
   - **Toda consulta de dados é obrigatoriamente feita através do DataProxyAgent**, que age como único ponto de acesso aos serviços de dados.
   - O DataProxyAgent traduz as consultas em linguagem natural para operações específicas no DataServiceHub.
   - Uma resposta é gerada com base no domínio de negócio ativo.

5. **Envio da Resposta**
   - A resposta é enviada de volta para o Chatwoot usando o ChatwootClient.
   - Metadados adicionais podem ser adicionados, como etiquetas ou atribuições.

6. **Registro e Monitoramento**
   - Todo o fluxo é registrado para fins de depuração e monitoramento.
   - Métricas de desempenho são coletadas (tempo de resposta, taxa de sucesso, etc.).

## Configuração

O sistema de integração webhook-agentes requer as seguintes configurações:

### Variáveis de Ambiente

```dotenv
# Configurações do Chatwoot
CHATWOOT_API_KEY=sua_api_key
CHATWOOT_BASE_URL=https://seu-chatwoot.com/api/v1
CHATWOOT_ACCOUNT_ID=1

# Configurações do Webhook
WEBHOOK_PORT=8001
WEBHOOK_HOST=0.0.0.0

# Configurações de Domínio
ACTIVE_DOMAIN=cosmetics
```

### Mapeamento de Canais

No arquivo de configuração, você pode mapear IDs de inbox do Chatwoot para tipos de canais:

```python
channel_mapping = {
    "1": "whatsapp",
    "2": "instagram",
    "3": "web"
}
```

## Iniciando o Sistema

Para iniciar o sistema integrado:

1. Execute o script `start_integrated_webhook.sh`:
   ```bash
   bash webhook/start_integrated_webhook.sh
   ```

2. O script:
   - Verifica dependências
   - Inicia o servidor webhook
   - Inicia o ngrok para exposição externa
   - Atualiza a URL do webhook na VPS (opcional)

## Testando a Integração

Para testar a integração:

1. Execute o script de teste:
   ```bash
   python tests/test_webhook_integration.py
   ```

2. O script irá:
   - Verificar se o servidor está funcionando
   - Enviar mensagens de teste para diferentes cenários
   - Verificar se as respostas são adequadas

## Depuração

Para depurar problemas na integração:

1. **Logs do Webhook Server**:
   ```bash
   tail -f logs/webhook_server_*.log
   ```

2. **Logs do Ngrok**:
   ```bash
   tail -f ngrok.log
   ```

3. **Verificar Endpoint de Saúde**:
   ```bash
   curl http://localhost:8001/health
   ```

## Considerações de Segurança

1. **Autenticação**: Considerar adicionar autenticação ao endpoint webhook.
2. **Validação de Dados**: Sempre validar dados de entrada antes do processamento.
3. **Limitação de Taxa**: Implementar limites de taxa para evitar sobrecarga.
4. **Logs Sensíveis**: Evitar registrar informações sensíveis de clientes.

## Próximos Passos

1. **Integração com mais canais**: Expandir para outros canais além do WhatsApp.
2. **Analytics**: Adicionar mais métricas para monitorar desempenho.
3. **Testes de Carga**: Testar o sistema com volume maior de mensagens.
4. **Melhorias na IA**: Aprimorar a precisão e capacidade dos agentes de IA.

## Perguntas Frequentes

### O que acontece se o servidor webhook estiver indisponível?
O Chatwoot tentará reenviar o webhook várias vezes. Configure a política de reenvio no Chatwoot.

### Como lidar com mensagens em diferentes idiomas?
Os agentes de IA podem ser configurados para detectar e responder em múltiplos idiomas.

### É possível personalizar respostas por domínio de negócio?
Sim, através do sistema de plugins e configuração de domínio ativo.

### Por que é obrigatório usar o DataProxyAgent para acessar dados?
Por três razões principais:
1. **Segurança**: Centraliza o controle de acesso aos dados, evitando acessos indevidos.
2. **Consistência**: Garante que todos os dados sejam formatados e processados de forma padronizada.
3. **Otimização**: Implementa técnicas de cache, indexação e otimização de consultas de forma centralizada, melhorando o desempenho geral do sistema.

Acessar diretamente a camada de dados sem passar pelo DataProxyAgent quebra a arquitetura do sistema e pode levar a inconsistências, problemas de segurança e degradação de performance.
