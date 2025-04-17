# Guia de Inicialização Rápida - Servidor Unificado

Este guia fornece instruções passo a passo para inicializar o sistema integrado Odoo-AI, configurar o Ngrok para expor o servidor local, e monitorar os logs para verificar o funcionamento correto do sistema.

## Visão Geral do Processo

1. Configurar o sistema de logs
2. Iniciar o servidor unificado
3. Iniciar o Ngrok para criar um túnel
4. Monitorar os logs
5. Atualizar a URL do Ngrok na VPS
6. Testar a conexão com o Chatwoot
7. Testar a conexão com o Odoo

## Instruções Detalhadas

### Terminal 1: Configurar Logs e Iniciar Servidor Unificado

```bash
# Passo 1-2: Configurar logs e iniciar servidor unificado
cd /home/giovano/Projetos/Chatwoot\ V4 && python scripts/setup_logging.py && ./scripts/start_server.sh
```

> **IMPORTANTE**: Use o script `start_server.sh` para iniciar o servidor unificado. Este script garante que todos os componentes sejam inicializados corretamente.

### Terminal 2: Iniciar o Ngrok

```bash
# Passo 3: Iniciar o Ngrok para criar o túnel
cd /home/giovano/Projetos/Chatwoot\ V4 && ./scripts/start_ngrok.sh

# Alternativa: Se preferir usar o script Python antigo (adiciona /webhook automaticamente)
# cd /home/giovano/Projetos/Chatwoot\ V4 && python scripts/webhook/simple_ngrok_starter.py
```

> **NOTA**: O script `start_ngrok.sh` agora oferece a opção de usar o script Python antigo (`simple_ngrok_starter.py`) se o token do Ngrok não estiver configurado no arquivo `.env`.

### Terminal 3: Monitorar os Logs

```bash
# Passo 4: Monitorar os logs do servidor unificado
cd /home/giovano/Projetos/Chatwoot\ V4 && python scripts/monitor_logs.py --all

# Alternativas:
# Monitorar logs específicos:
# cd /home/giovano/Projetos/Chatwoot\ V4 && python scripts/monitor_logs.py --server-log logs/server.log --webhook-log logs/webhook.log

# Filtrar mensagens contendo texto específico:
# cd /home/giovano/Projetos/Chatwoot\ V4 && python scripts/monitor_logs.py --all --filter "webhook"

# Filtrar por nível de log:
# cd /home/giovano/Projetos/Chatwoot\ V4 && python scripts/monitor_logs.py --all --level ERROR
```

> **NOTA**: O novo script `monitor_logs.py` fornece uma visualização colorida e formatada dos logs, facilitando a análise. Ele pode monitorar vários arquivos de log simultaneamente e aplicar filtros para encontrar informações específicas.

### Terminal 4 ou SSH para a VPS: Atualizar a URL na VPS

```bash
# Passo 5-9: Atualizar URL do Ngrok na VPS (execute cada comando após o anterior completar)
ssh root@srv692745.hstgr.cloud

# Após conectar na VPS, execute:
docker exec webhook-proxy sed -i "s|FORWARD_URL *= *[\"'][^\"']*[\"']|FORWARD_URL = 'https://sua-url-do-ngrok.ngrok-free.app/webhook'|g" /app/simple_webhook.py && docker exec webhook-proxy grep FORWARD_URL /app/simple_webhook.py && docker restart webhook-proxy
```

> **IMPORTANTE**: Substitua `https://sua-url-do-ngrok.ngrok-free.app/webhook` pela URL real gerada pelo Ngrok. Note que você deve adicionar `/webhook` ao final da URL, pois o script `start_ngrok.sh` não adiciona automaticamente (diferente do script antigo).

## Testes do Sistema

### Teste 1: Verificar se o Webhook está Recebendo Mensagens do Chatwoot

1. Envie uma mensagem pelo Chatwoot para um dos canais configurados
2. Verifique os logs do webhook:

```bash
cd /home/giovano/Projetos/Chatwoot\ V4 && python scripts/monitor_logs.py --webhook-log logs/webhook.log --filter "Webhook recebido"

# Alternativa com grep:
# cd /home/giovano/Projetos/Chatwoot\ V4 && grep "Webhook recebido" logs/webhook.log
```

3. Verifique se a mensagem foi processada corretamente:

```bash
cd /home/giovano/Projetos/Chatwoot\ V4 && python scripts/monitor_logs.py --hub-log logs/hub.log --filter "Mensagem processada"

# Alternativa com grep:
# cd /home/giovano/Projetos/Chatwoot\ V4 && grep "Mensagem processada" logs/hub.log
```

### Teste 2: Verificar se o Odoo está se Comunicando com o Sistema

1. Acesse o módulo `ai_credentials_manager` no Odoo
2. Clique no botão "Sincronizar com Sistema de IA"
3. Verifique os logs da API Odoo:

```bash
cd /home/giovano/Projetos/Chatwoot\ V4 && python scripts/monitor_logs.py --odoo-api-log logs/odoo_api.log --filter "Sincronização de credenciais"

# Alternativa com grep:
# cd /home/giovano/Projetos/Chatwoot\ V4 && grep "Sincronização de credenciais" logs/odoo_api.log
```

4. Verifique se a sincronização foi processada corretamente:

```bash
cd /home/giovano/Projetos/Chatwoot\ V4 && python scripts/monitor_logs.py --odoo-api-log logs/odoo_api.log --filter "Credenciais sincronizadas"

# Alternativa com grep:
# cd /home/giovano/Projetos/Chatwoot\ V4 && grep "Credenciais sincronizadas" logs/odoo_api.log
```

### Teste 3: Verificar se o Business Rules está Funcionando

1. Acesse o módulo `business_rules` no Odoo
2. Crie uma nova regra de negócio
3. Clique no botão "Sincronizar com Sistema de IA"
4. Verifique os logs da API Odoo:

```bash
cd /home/giovano/Projetos/Chatwoot\ V4 && python scripts/monitor_logs.py --odoo-api-log logs/odoo_api.log --filter "Sincronização de regras"

# Alternativa com grep:
# cd /home/giovano/Projetos/Chatwoot\ V4 && grep "Sincronização de regras" logs/odoo_api.log
```

5. Teste a busca semântica de regras:

```bash
# Teste completo: enviar requisição e monitorar logs
cd /home/giovano/Projetos/Chatwoot\ V4 && curl "http://localhost:8001/api/v1/business-rules/semantic-search?account_id=account_1&query=horario%20de%20funcionamento" && python scripts/monitor_logs.py --odoo-api-log logs/odoo_api.log --filter "semantic-search"
```

## Solução de Problemas Comuns

### Problema: O servidor unificado não inicia

Verifique se:
1. Todas as dependências estão instaladas
2. O arquivo `.env` está configurado corretamente
3. Os diretórios de configuração existem e têm as permissões corretas
4. Os logs de erro estão sendo gerados:

```bash
cd /home/giovano/Projetos/Chatwoot\ V4 && python scripts/monitor_logs.py --all --level ERROR
```

### Problema: Webhook não recebe mensagens do Chatwoot

Verifique se:
1. A URL do Ngrok está atualizada na VPS
2. O servidor unificado está rodando
3. O Chatwoot está configurado para enviar webhooks para a URL correta
4. Os logs do webhook estão sendo gerados:

```bash
cd /home/giovano/Projetos/Chatwoot\ V4 && python scripts/monitor_logs.py --webhook-log logs/webhook.log
```

### Problema: Odoo não se comunica com o sistema

Verifique se:
1. O servidor unificado está rodando
2. As credenciais no módulo `ai_credentials_manager` estão configuradas corretamente
3. O token de autenticação no Odoo corresponde ao token configurado no sistema
4. Os logs da API Odoo estão sendo gerados:

```bash
cd /home/giovano/Projetos/Chatwoot\ V4 && python scripts/monitor_logs.py --odoo-api-log logs/odoo_api.log
```

### Problema: Business Rules não funciona

Verifique se:
1. O servidor unificado está rodando
2. O módulo `business_rules` está instalado e configurado corretamente
3. O account_id está sendo passado corretamente nas requisições
4. Os logs da API Odoo estão sendo gerados:

```bash
cd /home/giovano/Projetos/Chatwoot\ V4 && python scripts/monitor_logs.py --odoo-api-log logs/odoo_api.log --filter "business_rules"
```

### Problema: URL do Ngrok Desatualizada na VPS

Se as mensagens não estão chegando ao seu ambiente local, verifique se a URL do Ngrok na VPS está atualizada:

```bash
ssh root@srv692745.hstgr.cloud "docker exec webhook-proxy grep FORWARD_URL /app/simple_webhook.py"
```

Se a URL estiver desatualizada, siga os passos 7-9 da seção "Terminal 4 ou SSH para a VPS" acima.

### Problema: Webhook não Recebe Mensagens do Chatwoot

Verifique se o Chatwoot está configurado para enviar webhooks para a URL correta:

```
http://147.93.9.211:8802/webhook
```

Esta URL deve apontar para a VPS na porta 8802, que está mapeada para a porta 8002 do container `webhook-proxy`.
