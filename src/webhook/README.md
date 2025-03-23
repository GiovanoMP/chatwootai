# Webhook Server - ChatwootAI

Este documento explica como configurar, iniciar e testar o servidor webhook que recebe mensagens do Chatwoot e as encaminha para o sistema ChatwootAI.

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Configuração Inicial](#configuração-inicial)
3. [Iniciando o Sistema](#iniciando-o-sistema)
4. [Testando a Conexão](#testando-a-conexão)
5. [Monitoramento e Logs](#monitoramento-e-logs)
6. [Troubleshooting](#troubleshooting)

## 🔍 Visão Geral

O servidor webhook é o ponto de entrada para mensagens do Chatwoot. Ele:

1. Recebe mensagens do Chatwoot via webhook
2. Processa e valida as mensagens
3. Encaminha as mensagens para o `HubCrew` no módulo `hub.py`
4. Retorna respostas apropriadas ao Chatwoot

Para que o Chatwoot possa enviar mensagens ao nosso servidor local, utilizamos o Ngrok para criar um túnel seguro, expondo nosso servidor local à internet.

## ⚙️ Configuração Inicial

### Pré-requisitos

- Python 3.10+
- Ngrok instalado
- Conta no Chatwoot configurada
- Variáveis de ambiente configuradas no arquivo `.env`

### Variáveis de Ambiente Importantes

```
# Configurações do Webhook
WEBHOOK_PORT=8001
WEBHOOK_HOST=0.0.0.0
WEBHOOK_USE_HTTPS=true
WEBHOOK_AUTH_TOKEN=seu_token_secreto

# Configurações do Ngrok
NGROK_AUTH_TOKEN=seu_token_ngrok

# Configurações do Chatwoot
CHATWOOT_API_KEY=sua_chave_api
CHATWOOT_BASE_URL=https://seu.chatwoot.url/api/v1
CHATWOOT_ACCOUNT_ID=1

# Configurações da VPS para atualização automática do proxy
VPS_HOST=seu.servidor.vps
VPS_USER=usuario_vps
VPS_PASSWORD=senha_vps
PROXY_CONTAINER_NAME=id_do_container
PROXY_FILE_PATH=/caminho/para/arquivo_proxy.py
```

## 🚀 Iniciando o Sistema

### Passo 0: Configurar o Sistema de Logs

```bash
# A partir da raiz do projeto
python scripts/webhook/setup_logging.py
```

Este passo é essencial para criar os arquivos de log necessários antes de iniciar o servidor.

### Passo 1: Iniciar o Servidor Webhook

```bash
# A partir da raiz do projeto
python src/webhook/server.py
```

Isso iniciará o servidor webhook na porta especificada no arquivo `.env` (padrão: 8001). Você verá uma mensagem confirmando que o servidor está rodando.

### Passo 2: Iniciar o Ngrok e Configurar o Webhook

```bash
# A partir da raiz do projeto
python scripts/webhook/simple_ngrok_starter.py
```

Este script:
1. Inicia o Ngrok para criar um túnel para o servidor webhook
2. Obtém a URL pública gerada pelo Ngrok
3. Atualiza automaticamente o webhook no Chatwoot
4. Fornece instruções para atualização manual do proxy na VPS

### Passo 3: Verificar se Tudo Está Funcionando

```bash
# A partir da raiz do projeto
python scripts/webhook/test_webhook_connection.py
```

Este script verificará se o Ngrok, o servidor webhook e a conexão com a VPS estão funcionando corretamente.

### Passo 3: Atualizar o Proxy na VPS (Manual)

Siga as instruções fornecidas pelo script `simple_ngrok_starter.py` para atualizar o proxy na VPS. Geralmente, isso envolve:

1. Conectar-se à VPS via SSH
2. Verificar o status do container Docker
3. Atualizar a URL no arquivo de configuração do proxy
4. Reiniciar o container

## 🧪 Testando a Conexão

### Teste Automatizado

Para verificar se todo o sistema está funcionando corretamente:

```bash
# A partir da raiz do projeto
python scripts/webhook/test_webhook_connection.py
```

Este script testa:
1. Se o Ngrok está rodando e acessível
2. Se o servidor webhook está ativo
3. Se a conexão com a VPS está funcionando
4. Se o endpoint do webhook responde corretamente

### Teste Manual com o Chatwoot

Para testar se as mensagens do Chatwoot estão chegando ao sistema:

1. **Enviar uma mensagem de teste pelo WhatsApp** para o número configurado no Chatwoot
2. **Verificar os logs do servidor webhook** para confirmar o recebimento da mensagem:
   ```bash
   # Em outro terminal, a partir da raiz do projeto
   tail -f webhook.log
   ```
3. **Verificar se a mensagem chegou ao `hub.py`** observando os logs:
   ```bash
   # Se o hub.py gerar logs separados
   tail -f hub.log
   ```

### Verificando o Fluxo Completo

Para confirmar que uma mensagem percorreu todo o fluxo:

1. Envie uma mensagem específica pelo WhatsApp (ex: "TESTE_FLUXO_COMPLETO")
2. Nos logs, você deve ver:
   - Recebimento da mensagem pelo servidor webhook
   - Processamento pelo `HubCrew` no `hub.py`
   - Roteamento para a crew especializada apropriada
   - Resposta sendo enviada de volta ao Chatwoot

## 📊 Monitoramento e Logs

### Arquivos de Log Importantes

- `logs/webhook.log`: Logs do servidor webhook (mensagens recebidas, processamento)
- `logs/hub.log`: Logs do hub central (processamento de mensagens, roteamento)
- `logs/webhook_test.log`: Logs dos testes de conexão

### Configuração dos Logs

Antes de iniciar o servidor, configure o sistema de logs executando:

```bash
# A partir da raiz do projeto
python scripts/webhook/setup_logging.py
```

Este script criará os arquivos de log necessários e testará os loggers.

### Monitoramento em Tempo Real

Para monitorar os logs em tempo real, use um dos comandos abaixo:

```bash
# Monitorar logs do webhook
tail -f logs/webhook.log

# Monitorar logs do hub
tail -f logs/hub.log

# Monitorar ambos os logs com destaque colorido
python scripts/webhook/monitor_webhook_logs.py --webhook-log logs/webhook.log --hub-log logs/hub.log

# Monitorar logs do Ngrok
tail -f ngrok.log

# Ver todas as conexões Ngrok no navegador
# Acesse http://localhost:4040
```

## 🔧 Troubleshooting

### Problemas Comuns e Soluções

1. **Webhook não recebe mensagens**
   - Verifique se o Ngrok está rodando: `curl http://localhost:4040/api/tunnels`
   - Confirme se a URL do webhook foi atualizada no Chatwoot
   - Verifique se o proxy na VPS está configurado corretamente

2. **Erro de autenticação**
   - Confirme se o token de autenticação no cabeçalho da requisição corresponde ao `WEBHOOK_AUTH_TOKEN` no arquivo `.env`

3. **Servidor webhook não inicia**
   - Verifique se a porta não está sendo usada por outro processo: `lsof -i:8001`
   - Confirme se todas as dependências estão instaladas

4. **Ngrok não inicia**
   - Verifique se o token do Ngrok está configurado corretamente no arquivo `.env`
   - Confirme se o Ngrok está instalado: `which ngrok`

5. **VPS não atualiza**
   - Tente conectar-se manualmente à VPS e executar os comandos fornecidos pelo script
   - Verifique se as credenciais da VPS estão corretas no arquivo `.env`

### Reiniciando Todo o Sistema

Se encontrar problemas persistentes, tente reiniciar todo o sistema:

```bash
# Encerrar processos
pkill -f ngrok
pkill -f "python src/webhook/server.py"

# Reiniciar o servidor webhook
python src/webhook/server.py &

# Reiniciar o Ngrok
python scripts/webhook/simple_ngrok_starter.py
```

---

## 📝 Fluxo de Processamento de Mensagens

Quando uma mensagem é recebida do Chatwoot:

1. **Entrada da Mensagem**:
   - Cliente envia mensagem pelo WhatsApp
   - Chatwoot recebe a mensagem e a encaminha via webhook para nosso sistema
   - O servidor webhook (`src/webhook/server.py`) recebe a mensagem

2. **Processamento pelo Hub Central**:
   - O servidor webhook encaminha a mensagem para o `HubCrew` no `hub.py`
   - `HubCrew` contém:
     * `OrchestratorAgent`: Analisa e roteia mensagens
     * `ContextManagerAgent`: Gerencia contexto da conversa
     * `IntegrationAgent`: Integra com sistemas externos
     * `DataProxyAgent`: Único ponto de acesso a dados

3. **Orquestração e Roteamento**:
   - `OrchestratorAgent` analisa a intenção da mensagem
   - `ContextManagerAgent` atualiza o contexto da conversa
   - Com base na análise, a mensagem é roteada para a crew especializada apropriada

4. **Processamento pela Crew Especializada**:
   - Para consultas de produtos: `SalesCrew`
   - Para suporte técnico: `SupportCrew`
   - Para agendamentos: `SchedulingCrew`

5. **Retorno da Resposta**:
   - Crew especializada processa dados e gera resposta
   - Resposta retorna para o `HubCrew`
   - `HubCrew` encaminha para o Chatwoot
   - Chatwoot entrega a resposta ao cliente via WhatsApp

---

Desenvolvido como parte do projeto ChatwootAI - 2025
