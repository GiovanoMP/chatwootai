# Webhook Server - ChatwootAI

Este documento explica como configurar, iniciar e testar o servidor webhook que recebe mensagens do Chatwoot e as encaminha para o sistema ChatwootAI.

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Fluxo de Determinação de Domínio](#fluxo-de-determinação-de-domínio)
3. [Configuração Inicial](#configuração-inicial)
4. [Configuração da VPS](#configuração-da-vps)
5. [Iniciando o Sistema](#iniciando-o-sistema)
6. [Testando a Conexão](#testando-a-conexão)
7. [Monitoramento e Logs](#monitoramento-e-logs)
8. [Troubleshooting](#troubleshooting)

## 🔍 Visão Geral

O servidor webhook é o ponto de entrada para mensagens do Chatwoot. Ele:

1. Recebe mensagens do Chatwoot via webhook
2. Processa e valida as mensagens
3. Determina o domínio de negócio apropriado para a conversa
4. Encaminha as mensagens para o `HubCrew` no módulo `hub.py`
5. Retorna respostas apropriadas ao Chatwoot

Para que o Chatwoot possa enviar mensagens ao nosso servidor local, utilizamos o Ngrok para criar um túnel seguro, expondo nosso servidor local à internet. Além disso, utilizamos um servidor proxy na VPS que recebe as mensagens do Chatwoot e as encaminha para o nosso ambiente local via Ngrok.

## 🔎 Fluxo de Determinação de Domínio

Uma das principais responsabilidades do webhook handler é determinar o domínio de negócio apropriado para cada conversa. Isso é feito seguindo uma hierarquia de fontes:

### Hierarquia de Determinação

1. **Mapeamento via account_id**:
   - Primeiro, o handler verifica se o `account_id` do webhook está mapeado para um domínio no arquivo `chatwoot_mapping.yaml`
   - Exemplo: `account_id: 1` → domínio: `cosmetics`

2. **Mapeamento via inbox_id**:
   - Se não encontrar pelo account_id, verifica se o `inbox_id` está mapeado
   - Exemplo: `inbox_id: 3` → domínio: `retail`

3. **Consulta à API do Chatwoot**:
   - Se ainda não encontrou, consulta metadados adicionais via API do Chatwoot
   - Utiliza o método `get_inbox()` do `ChatwootClient`

4. **Domínio Fallback**:
   - Como último recurso, utiliza o domínio fallback configurado via variável de ambiente `DEFAULT_DOMAIN`
   - O fallback padrão é "cosmetics", mas é apenas uma rede de segurança

### Arquivo de Mapeamento

O arquivo `config/chatwoot_mapping.yaml` contém o mapeamento de accounts e inboxes para domínios:

```yaml
accounts:
  "1": "cosmetics"  # Account ID 1 usa o domínio de cosméticos
  "2": "health"     # Account ID 2 usa o domínio de saúde
  "3": "retail"     # Account ID 3 usa o domínio de varejo

inboxes:
  "1": "cosmetics"  # Inbox ID 1 usa o domínio de cosméticos
  "2": "health"     # Inbox ID 2 usa o domínio de saúde
  "3": "retail"     # Inbox ID 3 usa o domínio de varejo
  "4": "cosmetics"  # Inbox ID 4 usa o domínio de cosméticos
```

## ⚙️ Configuração Inicial (Ambiente Local)

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
```

## 🖥️ Configuração da VPS

O sistema utiliza uma VPS (Virtual Private Server) para hospedar um servidor proxy que recebe as mensagens do Chatwoot e as encaminha para o ambiente local via Ngrok.

### Detalhes da Configuração Atual

- **Servidor VPS**: srv692745.hstgr.cloud
- **Usuário SSH**: root
- **Container Docker**: webhook-proxy
- **Portas**: 8802:8002 (porta externa 8802 mapeada para porta interna 8002)
- **URL do Webhook no Chatwoot**: http://147.93.9.211:8802/webhook

### Arquivo de Configuração do Proxy

O arquivo de configuração do proxy está localizado em `/app/simple_webhook.py` dentro do container. Ele contém a URL para a qual as mensagens serão encaminhadas:

```python
FORWARD_URL = 'https://be7a-2804-2610-6721-6300-25eb-907f-416b-7703.ngrok-free.app/webhook'
```

### Comandos Úteis para Gerenciar o Proxy na VPS

```bash
# Verificar o status do container
docker ps | grep webhook

# Visualizar o arquivo de configuração
docker exec webhook-proxy cat /app/simple_webhook.py

# Editar o arquivo de configuração (usando sed)
docker exec webhook-proxy sed -i "s|FORWARD_URL *= *[\"'][^\"']*[\"']|FORWARD_URL = 'https://nova-url-do-ngrok.ngrok-free.app/webhook'|g" /app/simple_webhook.py

# Editar o arquivo de configuração (usando nano)
docker exec -it webhook-proxy bash
apt-get update && apt-get install -y nano
nano /app/simple_webhook.py

# Reiniciar o container
docker restart webhook-proxy

# Verificar logs do container
docker logs webhook-proxy
```

## 🚀 Iniciando o Sistema

### Passo 0: Configurar o Sistema de Logs

```bash
# A partir da raiz do projeto
python scripts/webhook/setup_logging.py
```

Este passo é essencial para criar os arquivos de log necessários antes de iniciar o servidor. O script configura os loggers para o webhook e para o hub, e cria os arquivos de log necessários.

### Passo 1: Iniciar o Servidor Webhook

```bash
# A partir da raiz do projeto
python src/webhook/server.py
```

Isso iniciará o servidor webhook na porta especificada no arquivo `.env` (padrão: 8001). Você verá uma mensagem confirmando que o servidor está rodando. O servidor carrega automaticamente o arquivo `chatwoot_mapping.yaml` para determinar os domínios de negócio.

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

Este script verificará se o Ngrok, o servidor webhook e a conexão com a VPS estão funcionando corretamente. Ele também simula o recebimento de uma mensagem do Chatwoot para garantir que o fluxo completo está funcionando.

### Passo 4: Testar a Conexão com a VPS (Opcional)

```bash
# A partir da raiz do projeto
python scripts/webhook/test_vps_connection.py
```

Este script testa especificamente a conexão com a VPS e a capacidade de atualizar o proxy remotamente.

### Passo 5: Monitorar os Logs em Tempo Real

```bash
# A partir da raiz do projeto
python scripts/webhook/monitor_webhook_logs.py
```

Este script monitora os logs do webhook e do hub em tempo real, com destaque colorido para facilitar a identificação de eventos importantes.

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

- `logs/webhook.log`: Logs do servidor webhook (mensagens recebidas, processamento, determinação de domínio)
- `logs/hub.log`: Logs do hub central (processamento de mensagens, roteamento)
- `logs/webhook_test.log`: Logs dos testes de conexão

### Configuração dos Logs

Antes de iniciar o servidor, configure o sistema de logs executando:

```bash
# A partir da raiz do projeto
python scripts/webhook/setup_logging.py
```

Este script criará os arquivos de log necessários e testará os loggers. Ele também gera instruções para implementação de logs em novos arquivos do projeto.

### Monitoramento em Tempo Real

Para monitorar os logs em tempo real, use um dos comandos abaixo:

```bash
# Monitorar logs do webhook
tail -f logs/webhook.log

# Monitorar logs do hub
tail -f logs/hub.log

# Monitorar ambos os logs com destaque colorido (recomendado)
python scripts/webhook/monitor_webhook_logs.py

# Monitorar logs do Ngrok
tail -f ngrok.log

# Ver todas as conexões Ngrok no navegador
# Acesse http://localhost:4040
```

O script `monitor_webhook_logs.py` oferece opções avançadas para filtrar e destacar mensagens importantes. Execute com `--help` para ver todas as opções disponíveis.

## 🔧 Troubleshooting

### Problemas Comuns e Soluções

1. **Webhook não recebe mensagens**
   - Verifique se o Ngrok está rodando: `curl http://localhost:4040/api/tunnels`
   - Confirme se a URL do webhook foi atualizada no Chatwoot
   - Verifique se o proxy na VPS está configurado corretamente

2. **Erro na determinação de domínio**
   - Verifique se o arquivo `chatwoot_mapping.yaml` está corretamente configurado
   - Confirme se os IDs de account e inbox estão corretos
   - Verifique se a conexão com a API do Chatwoot está funcionando

3. **Servidor webhook não inicia**
   - Verifique se todas as dependências estão instaladas
   - Confirme se as variáveis de ambiente estão configuradas corretamente
   - Verifique se a porta 8001 não está sendo usada por outro processo

4. **Mensagens não chegam ao HubCrew**
   - Verifique os logs para identificar onde o processamento está parando
   - Confirme se o domínio está sendo determinado corretamente
   - Verifique se o HubCrew está inicializado corretamente

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
