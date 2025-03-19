# Webhook Server na VPS

Este documento descreve a configuração do servidor webhook na VPS.

## Estrutura de Diretórios

```
~/simple_webhook/           # Diretório principal do webhook
├── Dockerfile              # Configuração do container Docker
├── docker-stack.yml        # Configuração do Docker Swarm
├── simple_webhook.py       # Código principal do servidor webhook
└── simple_webhook.py.bak   # Backup do código

~/webhook_backup/           # Diretório de backup (arquivos antigos)
└── chatwoot_webhook/       # Implementação antiga (não utilizada)
```

## Serviço Atual

O serviço `simple_webhook_simple_webhook` está em execução e configurado para:

- **Porta Externa:** 8802
- **Porta Interna:** 8002
- **URL de Encaminhamento:** Configurada para encaminhar para o ambiente local via Ngrok
- **Autenticação:** Token Bearer para segurança

## Como Atualizar a URL de Encaminhamento

Quando você iniciar um novo túnel Ngrok no ambiente local, você precisará atualizar a URL no servidor webhook:

1. Conecte-se à VPS:
   ```bash
   ssh root@srv692745.hstgr.cloud
   ```

2. Edite o arquivo do servidor webhook:
   ```bash
   nano ~/simple_webhook/simple_webhook.py
   ```

3. Atualize a variável `FORWARD_URL` com a nova URL do Ngrok.

4. Reconstrua e reinicie o serviço:
   ```bash
   cd ~/simple_webhook
   docker build -t simple_webhook:latest .
   docker service update --force simple_webhook_simple_webhook
   ```

## Monitoramento

Para verificar o status do serviço:
```bash
docker service ls | grep webhook
```

Para verificar os logs:
```bash
docker service logs simple_webhook_simple_webhook
```

## Solução de Problemas

Se o serviço não estiver funcionando corretamente:

1. Verifique os logs do serviço
2. Verifique se a URL de encaminhamento está correta
3. Verifique se o Ngrok está em execução no ambiente local
4. Verifique se o servidor webhook local está em execução

## Segurança

O servidor webhook utiliza um token de autenticação para garantir que apenas requisições autorizadas sejam processadas. Este token está configurado no código do servidor.
