# Documentação do Conector Chatwoot-MCP-Crew

## Introdução

O Conector Chatwoot-MCP-Crew é um componente intermediário que permite a integração entre o sistema de atendimento omnichannel Chatwoot e o MCP-Crew (Model Context Protocol para Crew AI). Este conector possibilita que mensagens recebidas de diferentes canais (WhatsApp, Facebook, Instagram) através do Chatwoot sejam processadas pelo sistema de decisão inteligente do MCP-Crew e direcionadas para as crews apropriadas.

## Fluxo de Mensagens

### 1. Recebimento de Mensagens do Chatwoot

Quando um cliente envia uma mensagem através de qualquer canal conectado ao Chatwoot (WhatsApp, Facebook, Instagram, etc.), o seguinte fluxo é acionado:

1. **Chatwoot recebe a mensagem** do canal original (ex: WhatsApp)
2. **Chatwoot envia um webhook** para o endpoint `/webhook/chatwoot` do conector
3. **O conector valida a assinatura** do webhook usando HMAC (se configurado)
4. **O processador de mensagens extrai e normaliza** os dados relevantes:
   - Conteúdo da mensagem
   - Informações do remetente
   - Detalhes da conversa
   - Canal de origem
5. **O gerenciador de contexto** recupera ou cria o contexto da conversa
6. **O cliente MCP-Crew** envia a mensagem normalizada para o MCP-Crew
7. **O sistema de decisão do MCP-Crew** analisa a mensagem e determina qual crew deve processá-la

```
Fluxo de Entrada:
Cliente → Canal (WhatsApp/Facebook/etc) → Chatwoot → Webhook → Conector → MCP-Crew → Crew Específica
```

### 2. Envio de Respostas para o Chatwoot

Quando uma crew processa a mensagem e gera uma resposta, o seguinte fluxo é acionado:

1. **A crew gera uma resposta** após processamento
2. **O MCP-Crew envia a resposta** para o conector
3. **O cliente Chatwoot** formata a resposta e a envia para o Chatwoot
4. **O Chatwoot entrega a resposta** ao cliente através do canal original

```
Fluxo de Saída:
Crew Específica → MCP-Crew → Conector → Chatwoot → Canal (WhatsApp/Facebook/etc) → Cliente
```

### 3. Fluxo de Decisão Inteligente

O sistema de decisão do MCP-Crew analisa diversos fatores para determinar qual crew deve processar cada mensagem:

1. **Análise de conteúdo**: O texto da mensagem é analisado para identificar intenções, entidades e sentimento
2. **Contexto da conversa**: O histórico de interações anteriores é considerado
3. **Regras de negócio**: Configurações específicas de roteamento são aplicadas
4. **Canal de origem**: O canal pelo qual a mensagem foi recebida pode influenciar o roteamento

## Configuração do Conector

### Requisitos de Sistema

- Python 3.8+
- Flask 2.0+
- Requests 2.25+
- Acesso à API do Chatwoot
- Acesso à API do MCP-Crew

### Instalação

1. Clone o repositório:
   ```bash
   git clone https://github.com/seu-usuario/chatwoot-mcp-connector.git
   cd chatwoot-mcp-connector
   ```

2. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure as variáveis de ambiente ou o arquivo de configuração:
   ```bash
   cp config/config.example.json config/config.json
   # Edite o arquivo config.json com suas configurações
   ```

### Configuração do Arquivo config.json

```json
{
  "DEBUG": true,
  "CHATWOOT_API_URL": "https://chatwoot.exemplo.com/api",
  "CHATWOOT_API_ACCESS_TOKEN": "seu_token_de_acesso",
  "CHATWOOT_WEBHOOK_SECRET": "seu_segredo_webhook",
  "MCP_CREW_API_URL": "https://mcp-crew.exemplo.com/api",
  "MCP_CREW_API_KEY": "sua_chave_api",
  "MCP_CREW_DECISION_ENGINE_URL": "https://mcp-crew.exemplo.com/decision",
  "MAX_CONTEXT_MESSAGES": 10,
  "ROUTING_RULES": {
    "default_crew": "suporte",
    "rules": [
      {
        "channel": "whatsapp",
        "crew": "whatsapp_crew"
      },
      {
        "channel": "facebook",
        "crew": "facebook_crew"
      }
    ]
  }
}
```

### Configuração do Chatwoot

1. Acesse o painel administrativo do Chatwoot
2. Vá para **Configurações → Integrações → Webhooks**
3. Clique em **Adicionar novo webhook**
4. Configure o webhook:
   - **URL**: `https://seu-servidor.com/webhook/chatwoot`
   - **Eventos**: Selecione pelo menos `message_created`
   - **Segredo**: Crie um segredo e anote-o (será usado na configuração do conector)

### Configuração do MCP-Crew

1. Certifique-se de que o MCP-Crew esteja configurado e em execução
2. Obtenha a chave de API do MCP-Crew
3. Configure o conector com a URL e a chave de API do MCP-Crew

### Execução do Conector

```bash
# Definir variáveis de ambiente (opcional)
export CHATWOOT_API_URL=https://chatwoot.exemplo.com/api
export CHATWOOT_API_ACCESS_TOKEN=seu_token_de_acesso
export CHATWOOT_WEBHOOK_SECRET=seu_segredo_webhook
export MCP_CREW_API_URL=https://mcp-crew.exemplo.com/api
export MCP_CREW_API_KEY=sua_chave_api

# Iniciar o servidor
python app.py
```

Para ambientes de produção, recomenda-se usar Gunicorn ou uWSGI:

```bash
gunicorn -w 4 -b 0.0.0.0:5000 "app:create_app()"
```

## Endpoints da API

### Endpoints de Webhook

#### POST /webhook/chatwoot

Recebe eventos do Chatwoot.

**Headers**:
- `X-Chatwoot-Signature`: Assinatura HMAC para validação
- `Content-Type`: application/json

**Payload de Exemplo**:
```json
{
  "event": "message_created",
  "id": "1",
  "content": "Olá, preciso de ajuda",
  "created_at": "2025-05-27T12:00:00Z",
  "message_type": "incoming",
  "content_type": "text",
  "content_attributes": {},
  "sender": {
    "id": "1",
    "name": "Cliente",
    "email": "cliente@exemplo.com"
  },
  "conversation": {
    "display_id": "1",
    "additional_attributes": {}
  },
  "account": {
    "id": "1",
    "name": "Minha Empresa"
  }
}
```

#### GET /webhook/status

Verifica o status do servidor de webhooks.

### Endpoints de Configuração

#### GET /config

Obtém a configuração atual do conector.

#### POST /config

Atualiza a configuração do conector.

### Endpoints de Administração

#### GET /health

Verifica a saúde do conector.

#### GET /metrics

Obtém métricas do conector.

## Monitoramento e Logs

Os logs do conector são armazenados no diretório `logs/` e incluem informações detalhadas sobre o processamento de mensagens, erros e eventos do sistema.

Para monitorar o conector em tempo real, você pode:

1. Verificar os logs:
   ```bash
   tail -f logs/chatwoot_mcp_connector.log
   ```

2. Acessar o endpoint de métricas:
   ```bash
   curl http://localhost:5000/metrics
   ```

3. Verificar a saúde do sistema:
   ```bash
   curl http://localhost:5000/health
   ```

## Solução de Problemas

### Webhook não está sendo recebido

1. Verifique se o URL do webhook está correto no Chatwoot
2. Confirme se o servidor do conector está acessível publicamente
3. Verifique os logs do conector para erros de conexão

### Mensagens não estão sendo processadas

1. Verifique se o token de acesso do Chatwoot é válido
2. Confirme se a chave de API do MCP-Crew está correta
3. Verifique os logs para erros de processamento

### Respostas não estão sendo enviadas

1. Verifique se o MCP-Crew está processando as mensagens corretamente
2. Confirme se o token de acesso do Chatwoot tem permissões para enviar mensagens
3. Verifique os logs para erros de comunicação com o Chatwoot

## Segurança

O conector implementa várias medidas de segurança:

1. **Validação de assinatura HMAC** para webhooks do Chatwoot
2. **Autenticação por token** para comunicação com as APIs
3. **HTTPS** para todas as comunicações externas
4. **Sanitização de entrada** para prevenir injeções
5. **Logs detalhados** para auditoria

## Próximos Passos e Expansões

O conector foi projetado para ser modular e extensível. Algumas possíveis expansões incluem:

1. **Suporte a mais canais** do Chatwoot
2. **Integração com sistemas de análise** para métricas avançadas
3. **Interface de administração** para configuração visual
4. **Processamento assíncrono** com filas para maior escalabilidade
5. **Cache distribuído** para melhor desempenho em ambientes com múltiplas instâncias
