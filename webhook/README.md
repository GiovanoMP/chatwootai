
# Sistema de Webhook para Chatwoot

Este diretório contém os componentes necessários para configurar e gerenciar a integração de webhooks entre o Chatwoot e o sistema local além de informações complementares sobre o webhook rodando na VPS

## Estrutura do Diretório

```
webhook/
├── README.md                      # Este arquivo
├── start_webhook_standalone.py    # Servidor webhook standalone
└── scripts/
    ├── start_webhook_connection.sh # Script para iniciar a conexão webhook
    └── update_vps_webhook_url.sh   # Script para atualizar a URL na VPS
```

## Guia Rápido

### Iniciar o Sistema de Conexão Completo (Recomendado)

O método mais simples para iniciar todo o sistema é usar o script unificado `start_webhook.sh`:

```bash
cd ~/Projetos/Chatwoot\ V4/webhook
chmod +x start_webhook.sh  # Garantir que o script é executável
./start_webhook.sh
```

Este script automatiza todo o processo:

1. Verifica se o servidor webhook já está rodando; se não, inicia-o
2. Verifica se o Ngrok já está rodando; se não, inicia-o
3. Exibe a URL do Ngrok gerada
4. Pergunta se você deseja atualizar a URL na VPS
5. Fornece informações sobre como monitorar os logs

### Configuração Manual (Alternativa)

1. **Iniciar o servidor webhook local**:
   ```bash
   cd ~/Projetos/Chatwoot\ V4/webhook
   python start_webhook_standalone.py
   ```
   
   Este comando inicia o servidor webhook na porta 8001, que receberá os webhooks do Chatwoot.

2. **Iniciar o túnel Ngrok**:
   ```bash
   cd ~/Projetos/Chatwoot\ V4/webhook
   ngrok http 8001
   ```
   
   Este comando cria um túnel Ngrok para a porta 8001, permitindo que a VPS envie webhooks para o seu servidor local.

3. **Usar o script de conexão alternativo**:
   ```bash
   cd ~/Projetos/Chatwoot\ V4/webhook
   ./scripts/start_webhook_connection.sh
   ```
   
   Este script também verifica se o servidor webhook está rodando, inicia o Ngrok e oferece a opção de atualizar a URL na VPS.

### Atualização da URL na VPS

Quando o Ngrok é reiniciado, ele gera uma nova URL. Para atualizar esta URL na VPS:

```bash
cd ~/Projetos/Chatwoot\ V4/webhook
./scripts/update_vps_webhook_url.sh
```

Este script:
1. Obtém a URL atual do Ngrok
2. Conecta-se à VPS via SSH
3. Atualiza o arquivo de configuração
4. Reconstrói e reinicia o serviço Docker
5. Verifica os logs para confirmar o funcionamento

### Configuração na VPS

A VPS está configurada com um serviço Docker Swarm chamado `simple_webhook_simple_webhook` que:
1. Recebe webhooks do Chatwoot na porta 8802
2. Encaminha esses webhooks para a URL do Ngrok configurada
3. Registra todas as interações nos logs do Docker

### Estrutura de Arquivos na VPS

O serviço webhook está localizado em: `/root/simple_webhook/`

Arquivos importantes:
```
/root/simple_webhook/
├── simple_webhook.py      # Script principal que recebe e encaminha webhooks
├── Dockerfile            # Configuração para construção da imagem Docker
├── docker-stack.yml      # Configuração do serviço Docker Swarm
├── docker-compose.yml    # Configuração alternativa (não usada atualmente)
└── README.md             # Documentação
```

### Verificação do Serviço na VPS

Para verificar se o serviço está rodando na VPS:
```bash
ssh -o ServerAliveInterval=60 root@srv692745.hstgr.cloud "docker service ls | grep webhook"
```

O resultado deve mostrar algo como:
```
b1mi1iag71e2   simple_webhook_simple_webhook   replicated   1/1        simple_webhook:latest   *:8802->8002/tcp
```

### Logs do Serviço na VPS

Para verificar os logs do serviço na VPS:
```bash
ssh -o ServerAliveInterval=60 root@srv692745.hstgr.cloud "docker service logs simple_webhook_simple_webhook --tail 20"
```

### Estrutura de Backups na VPS

Os diretórios de backup estão localizados em:
```
/root/webhook_backup/       # Diretório de backup principal
/root/chatwoot_webhook_backup/ # Backup adicional de configurações antigas
```

## Como Testar a Conexão com WhatsApp

Para verificar se a conexão completa com o WhatsApp está funcionando corretamente:

1. **Verifique o status do sistema**:
   ```bash
   # Verificar se o servidor webhook está rodando
   ps aux | grep webhook
   
   # Verificar se o Ngrok está rodando e obter a URL
   curl -s http://localhost:4040/api/tunnels | grep -o '"public_url":"[^"]*' | grep -o 'https://[^"]*'
   ```

2. **Teste o webhook local com um comando curl**:
   ```bash
   curl -s -X POST http://localhost:8001/webhook \
     -H "Content-Type: application/json" \
     -d '{"event":"test_message", "message":{"content":"Testando conexão"}}'
   ```
   
   Uma resposta bem-sucedida será algo como:
   ```json
   {"status":"received","event_type":"test_message","processing_time":"0.003s"}
   ```

3. **Teste com uma mensagem real do WhatsApp**:
   - Envie uma mensagem pelo WhatsApp para o número configurado no Chatwoot
   - Verifique os logs do webhook para confirmar o recebimento:
   ```bash
   tail -n 50 /home/giovano/Projetos/Chatwoot\ V4/logs/webhook_standalone_*.log
   ```
   
   Você deverá ver uma entrada de log semelhante a:
   ```
   2025-03-19 15:21:55,446 - webhook_standalone - INFO - Webhook recebido: message_created de 127.0.0.1 em 2025-03-19T15:21:55.445930
   ```

4. **Verificar funcionamento na VPS**:
   ```bash
   # Verificar se o serviço está rodando na VPS
   ssh root@srv692745.hstgr.cloud "docker service ls | grep webhook"
   
   # Verificar logs do serviço na VPS
   ssh root@srv692745.hstgr.cloud "docker service logs simple_webhook_simple_webhook --tail 20"
   ```

## Monitoramento

### Logs do Servidor Webhook

Os logs são armazenados em:
```
/home/giovano/Projetos/Chatwoot V4/logs/webhook_standalone_*.log
```

Estes logs contêm informações detalhadas sobre cada mensagem recebida, incluindo:
- Tipo de evento (message_created, conversation_created, etc.)
- Remetente e destinatário
- Conteúdo da mensagem
- Timestamps

### Logs do Ngrok

Para verificar as requisições recebidas pelo Ngrok:
```bash
curl -s http://localhost:4040/api/requests/http
```

## Solução de Problemas

Se você encontrar problemas com os webhooks:

1. **Verifique se o servidor webhook local está rodando**:
   ```bash
   ps aux | grep webhook
   ```

2. **Verifique se o Ngrok está rodando**:
   ```bash
   ps aux | grep ngrok
   ```

3. **Verifique os logs na VPS**:
   ```bash
   ssh root@srv692745.hstgr.cloud "docker service logs simple_webhook_simple_webhook --tail 20"
   ```

4. **Reinicie todo o sistema**:
   ```bash
   cd ~/Projetos/Chatwoot\ V4/webhook
   ./scripts/start_webhook_connection.sh
   ```
