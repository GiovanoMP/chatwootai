# Guia de Inicialização Rápida - Webhook Chatwoot

Este guia fornece instruções passo a passo para inicializar o sistema de webhook do Chatwoot, configurar o Ngrok para expor o servidor local, e monitorar os logs para verificar o funcionamento correto do sistema.

## Visão Geral do Processo

1. Configurar o sistema de logs
2. Iniciar o servidor webhook local com o DomainManager corretamente inicializado
3. Iniciar o Ngrok para criar um túnel
4. Monitorar os logs
5. Atualizar a URL do Ngrok na VPS
6. Testar a conexão

## Instruções Detalhadas

### Terminal 1: Configurar Logs e Iniciar Servidor Webhook

```bash
# Passo 1: Configurar o sistema de logs
cd /home/giovano/Projetos/Chatwoot\ V4
python scripts/webhook/setup_logging.py

# Passo 2: Iniciar o servidor webhook com o DomainManager corretamente inicializado
cd /home/giovano/Projetos/Chatwoot\ V4
python scripts/webhook/start_webhook_server.py
```

> **IMPORTANTE**: Use o script `start_webhook_server.py` em vez de `server.py` diretamente. Este script garante que o DomainManager seja inicializado corretamente antes de iniciar o servidor webhook, evitando o erro "DomainManager não disponível".

### Terminal 2: Iniciar o Ngrok

```bash
# Passo 3: Iniciar o Ngrok para criar o túnel
cd /home/giovano/Projetos/Chatwoot\ V4
python scripts/webhook/simple_ngrok_starter.py
```

### Terminal 3: Monitorar os Logs

```bash
# Passo 4: Iniciar o monitor de logs

# Passo 4: Iniciar o monitor de logs
cd /home/giovano/Projetos/Chatwoot\ V4
python scripts/webhook/monitor_webhook_logs.py --webhook-log logs/webhook.log --hub-log logs/hub.log

### Terminal 4 ou SSH para a VPS: Atualizar a URL na VPS

```bash
# Passo 5: Conectar-se à VPS
ssh root@srv692745.hstgr.cloud

# Passo 6: Verificar o ID do container atual
docker ps | grep webhook

# Passo 7: Atualizar a URL no arquivo de configuração
# O nome do container atual é webhook-proxy
# IMPORTANTE: Substitua a URL abaixo pela URL gerada pelo Ngrok e mantenha tudo em uma única linha
docker exec webhook-proxy sed -i "s|FORWARD_URL *= *[\"'][^\"']*[\"']|FORWARD_URL = 'https://sua-url-do-ngrok.ngrok-free.app/webhook'|g" /app/simple_webhook.py

# Passo 8: Verificar se a atualização foi bem-sucedida
docker exec webhook-proxy grep FORWARD_URL /app/simple_webhook.py

# Passo 9: Reiniciar o container para aplicar as mudanças
docker restart webhook-proxy
```

### Terminal 5 (opcional): Testar a Conexão

```bash
# Passo 10: Testar se tudo está funcionando corretamente
cd /home/giovano/Projetos/Chatwoot\ V4
python scripts/webhook/test_webhook_connection.py
```

## Verificação do Funcionamento

### Verificar se o Webhook está Recebendo Mensagens

```bash
# Verificar os logs do webhook
cd /home/giovano/Projetos/Chatwoot\ V4
tail -f logs/webhook.log

# Verificar os logs do servidor webhook
cd /home/giovano/Projetos/Chatwoot\ V4
tail -f logs/20250326_webhook_server.log  # Substitua a data conforme necessário
```

### Verificar se as Mensagens estão sendo Processadas

```bash
# Verificar os logs do hub
cd /home/giovano/Projetos/Chatwoot\ V4
tail -f logs/hub.log
```

## Solução de Problemas Comuns

### Problema: O comando sed não funciona corretamente

Se o comando sed apresentar erro, certifique-se de que:
1. A URL está em uma única linha sem quebras
2. As aspas simples estão sendo usadas corretamente
3. O caminho `/webhook` está incluído no final da URL

### Problema: DomainManager não disponível

Se você ver mensagens como "DomainManager não disponível, ferramentas não serão inicializadas" nos logs, verifique:

1. Se o diretório `config/domains/default` existe
2. Se os arquivos de configuração YAML estão presentes nesse diretório

### Problema: Mensagens não estão sendo processadas

Se as mensagens chegam ao webhook mas não são processadas corretamente, verifique:

1. Se o `account_id` está sendo corretamente identificado nos logs
2. Se o domínio está sendo determinado corretamente com base no `account_id`
3. Se as configurações do domínio estão carregadas corretamente
3. Se as permissões dos arquivos estão corretas

### Problema: URL do Ngrok Desatualizada na VPS

Se as mensagens não estão chegando ao seu ambiente local, verifique se a URL do Ngrok na VPS está atualizada:

```bash
# Na VPS
docker exec webhook-proxy grep FORWARD_URL /app/simple_webhook.py
```

Se a URL estiver desatualizada, siga os passos 7-9 da seção "Terminal 4 ou SSH para a VPS" acima.

### Problema: Webhook não Recebe Mensagens do Chatwoot

Verifique se o Chatwoot está configurado para enviar webhooks para a URL correta:

```
http://147.93.9.211:8802/webhook
```

Esta URL deve apontar para a VPS na porta 8802, que está mapeada para a porta 8002 do container `webhook-proxy`.cd /home/giovano/Projetos/Chatwoot\ V4
python scripts/webhook/monitor_webhook_logs.py --webhook-log logs/webhook.log --hub-log logs/hub.log