# MCP-Chatwoot Dockerizado

Este é o ambiente dockerizado para o MCP-Chatwoot, que permite a integração entre o Chatwoot e o MCP (Message Control Protocol).

## Requisitos

- Docker e Docker Compose
- NGROK instalado localmente (para expor o webhook)

## Configuração Inicial

1. Verifique se o arquivo `.env` contém as configurações corretas:
   - `MCP_HOST`, `MCP_PORT`, `MCP_TRANSPORT`, `MCP_SERVICE_NAME`
   - `CHATWOOT_BASE_URL`, `CHATWOOT_ACCESS_TOKEN`
   - `MCP_CREW_URL`, `MCP_CREW_TOKEN` (se necessário)
   - `NGROK_AUTHTOKEN` (já configurado no sistema local)

2. Construa e inicie o contêiner:
   ```bash
   ./build_and_run.sh
   ```

## Scripts Disponíveis

### Gerenciamento de Túnel NGROK

O script `ngrok.sh` gerencia o túnel NGROK para expor o webhook do MCP-Chatwoot:

```bash
# Verificar status do NGROK
./ngrok.sh status

# Iniciar o túnel NGROK
./ngrok.sh start

# Parar o túnel NGROK
./ngrok.sh stop

# Mostrar a URL atual do NGROK
./ngrok.sh url

# Mostrar ajuda
./ngrok.sh help
```

### Monitoramento de Logs

O script `logs.sh` permite monitorar os logs do contêiner MCP-Chatwoot. Para monitoramento em tempo real (recomendado para acompanhar webhooks e mensagens):

```bash
# Acompanhar logs importantes em tempo real (apenas novos logs)
./logs.sh follow-important

# Acompanhar logs de webhook e mensagens em tempo real (apenas novos logs)
./logs.sh webhook

# Acompanhar todos os logs em tempo real (apenas novos logs)
./logs.sh follow
```

Outros comandos disponíveis:

```bash
# Exibir todos os logs históricos
./logs.sh all

# Exibir logs desde o último acesso
./logs.sh recent

# Exibir apenas logs importantes
./logs.sh important

# Exibir logs importantes desde o último acesso
./logs.sh recent-important

# Reiniciar o histórico de logs (limpar timestamp)
./logs.sh clear

# Exibir apenas logs de erros
./logs.sh errors

# Exibir logs de webhook e mensagens do Chatwoot
./logs.sh webhook

# Mostrar ajuda
./logs.sh help
```

## Fluxo de Trabalho Típico

1. Inicie o contêiner MCP-Chatwoot (se ainda não estiver rodando):
   ```bash
   docker-compose up -d
   ```

2. Inicie o túnel NGROK:
   ```bash
   ./ngrok.sh start
   ```

3. Configure o webhook no Chatwoot com a URL fornecida pelo NGROK.

4. Monitore os logs para verificar se as mensagens estão sendo recebidas e processadas:
   ```bash
   ./logs.sh follow-important
   ```

## Solução de Problemas

- **Problema**: NGROK não inicia
  **Solução**: Verifique se o NGROK está instalado e configurado corretamente no sistema local.

- **Problema**: Mensagens não aparecem nos logs
  **Solução**: Verifique se o webhook está configurado corretamente no Chatwoot e se o túnel NGROK está acessível.

- **Problema**: Contêiner MCP-Chatwoot não inicia
  **Solução**: Verifique os logs do Docker para identificar o problema: `docker logs mcp-chatwoot`

Este diretório contém a configuração Docker para o serviço MCP-Chatwoot, que integra o Chatwoot com o ecossistema MCP.

## Sobre o MCP-Chatwoot

O MCP-Chatwoot é um serviço que:
- Recebe webhooks do Chatwoot para processar mensagens em tempo real
- Expõe ferramentas MCP (tools) para integração com agentes de IA
- Permite comunicação bidirecional entre o Chatwoot e outros serviços MCP
- Fornece um endpoint de health check para monitoramento

## Ferramentas MCP (Tools)

O MCP-Chatwoot expõe as seguintes ferramentas para os agentes de IA:

### Tools de Conversação
- **get_conversation**: Obtém detalhes de uma conversa específica
- **reply_to_conversation**: Permite que o agente responda a uma conversa existente
- **list_conversations**: Lista as conversas disponíveis com filtros

### Tools de Contato
- **create_contact**: Cria um novo contato no Chatwoot
- **get_contact**: Obtém detalhes de um contato específico
- **search_contacts**: Pesquisa contatos por critérios

### Tools de Inbox
- **list_inboxes**: Lista todas as caixas de entrada disponíveis
- **get_inbox**: Obtém detalhes de uma caixa de entrada específica
- **create_conversation**: Cria uma nova conversa em uma caixa de entrada

Estas ferramentas são consumidas pelo adaptador dinâmico (`chatwoot_dynamic_adapter.py`) localizado no diretório `ai-stack-docker/mcp-conectors`, que as converte em objetos Tool do CrewAI para uso pelos agentes.

## Pré-requisitos

- Docker e Docker Compose instalados
- Rede Docker `ai-stack` criada (use o script `network.sh` na raiz do diretório ai-stack-docker)
- Credenciais do Chatwoot configuradas (token de acesso, chave HMAC, etc.)

## Configuração

1. Crie um arquivo `.env` na raiz deste diretório com as seguintes variáveis:

```
CHATWOOT_BASE_URL=http://seu-chatwoot-url
CHATWOOT_ACCESS_TOKEN=seu-token-de-acesso

MCP_CREW_URL=http://mcp-crew:8000
MCP_CREW_TOKEN=seu-token-mcp-crew
```

## Uso

### Iniciar o serviço (método simples)

Utilize o script de build e execução que automatiza o processo:

```bash
./build_and_run.sh
```

Este script verifica a existência da rede, cria o arquivo `.env` se necessário, constrói a imagem e inicia o contêiner.

### Comandos manuais

#### Iniciar o serviço
```bash
docker-compose up -d
```

#### Verificar status
```bash
docker-compose ps
```

#### Ver logs
```bash
docker-compose logs -f
```

#### Parar o serviço
```bash
docker-compose down
```

## Endpoints

- **API Principal**: http://localhost:8004
- **Health Check**: http://localhost:8004/health
- **Endpoint Webhook**: http://localhost:8004/webhook
- **Endpoint SSE**: http://localhost:8004/messages/

## Configuração do Webhook no Chatwoot

Para configurar o webhook no Chatwoot:

1. Acesse o painel administrativo do Chatwoot
2. Vá para Configurações -> Webhooks -> Adicionar Webhook
3. Forneça um nome para o webhook (ex: 'MCP Integration')
4. No campo 'URL' coloque a URL do seu webhook (obtida via NGROK ou seu domínio)
5. Selecione os eventos necessários, especialmente 'message_created'
6. Salve o webhook

## Exposição para a Internet com NGROK

O MCP-Chatwoot precisa ser acessível pela internet para receber webhooks do Chatwoot. Para isso, fornecemos um script específico para NGROK que facilita a exposição do serviço:

### Usando o script docker-ngrok.sh

```bash
./docker-ngrok.sh seu-token-ngrok
```

Este script:
1. Inicia um contêiner NGROK temporário conectado à rede ai-stack
2. Cria um túnel para o serviço mcp-chatwoot na porta 8004
3. Exibe a URL pública gerada pelo NGROK

### Lidando com URLs dinâmicas do NGROK

Como as URLs do NGROK mudam a cada execução, recomendamos:

1. **Para desenvolvimento/testes**: Execute o script `docker-ngrok.sh` e atualize manualmente a URL do webhook no Chatwoot quando necessário

2. **Para produção**: Considere uma das seguintes alternativas:
   - Use um domínio fixo com proxy reverso (Nginx, Traefik)
   - Utilize o Cloudflare Tunnel que oferece subdomínios fixos
   - Adquira um plano pago do NGROK que permite reservar subdomínios fixos

3. **Automação**: Se necessário, você pode criar um script que:
   - Inicia o NGROK
   - Captura a URL pública gerada
   - Atualiza automaticamente o webhook no Chatwoot via API

## Monitoramento

O serviço inclui um endpoint de health check em `/health` que pode ser usado com o Uptime Kuma para monitoramento. Consulte o arquivo `uptime-kuma-config.md` para instruções detalhadas de configuração.

O endpoint `/health` retorna:
- Status do serviço (healthy/unhealthy)
- Status da conexão com o Chatwoot
- Informações sobre configurações
- Timestamp da verificação

## Adaptador Dinâmico para CrewAI

O arquivo `chatwoot_dynamic_adapter.py` no diretório `ai-stack-docker/mcp-conectors` é responsável por:

1. Descobrir dinamicamente as ferramentas disponíveis no MCP-Chatwoot
2. Converter essas ferramentas em objetos Tool do CrewAI
3. Permitir que os agentes de IA utilizem as funcionalidades do Chatwoot

Para usar o adaptador com o MCP-Chatwoot dockerizado, basta configurar a URL base corretamente:

```python
chatwoot = ChatwootDynamicAdapter(base_url="http://mcp-chatwoot:8004")
tools = chatwoot.tools
```

## Solução de Problemas

- **Erro de conexão**: Verifique se a rede `ai-stack` está criada e se o contêiner está em execução
- **Webhook não funciona**: Verifique se a URL do webhook está acessível do Chatwoot e se o NGROK está funcionando corretamente
- **Erros nos logs**: Verifique os logs do contêiner para mais detalhes sobre possíveis erros
- **Adaptador não conecta**: Verifique se a URL base configurada no adaptador corresponde à URL do MCP-Chatwoot
