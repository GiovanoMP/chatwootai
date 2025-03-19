# Guia de Configuração do Webhook do Chatwoot

Este documento explica como configurar o servidor webhook para receber eventos do Chatwoot em tempo real.

## Visão Geral

O sistema ChatwootAI utiliza webhooks para receber notificações em tempo real do Chatwoot quando novas mensagens são enviadas ou quando o status de uma conversa muda. Isso permite que o sistema responda imediatamente às interações dos usuários, sem a necessidade de consultar periodicamente a API do Chatwoot.

## Arquitetura

```
Cliente (WhatsApp/Instagram/etc) → Evolution API → Chatwoot (VPS) → HTTPS → Nginx (SSL) → Webhook Server (Docker) → ChatwootAI
```

## Requisitos de Segurança

Para garantir que apenas sistemas autorizados possam enviar eventos para o webhook, implementamos duas camadas de segurança:

1. **Restrição por IP**: O Nginx é configurado para aceitar conexões apenas dos IPs do Chatwoot e do sistema Odoo.
2. **Autenticação por Token**: O servidor webhook verifica um token de autenticação em cada requisição.

## Configuração no Servidor

### 1. Configuração do Subdomínio

Criamos um subdomínio dedicado para o webhook:
- **Subdomínio**: `webhook.server.efetivia.com.br`
- **Configuração DNS**: Registro A apontando para o IP do servidor
- **Modo Cloudflare**: DNS Only (sem proxy)

### 2. Configuração do SSL com Let's Encrypt

O script `setup_webhook_ssl.sh` configura automaticamente:
- Instalação do Nginx e Certbot
- Configuração do Nginx como proxy reverso
- Obtenção de certificados SSL do Let's Encrypt
- Restrição de acesso por IP

### 3. Configuração do Servidor Webhook

O servidor webhook é configurado através das seguintes variáveis de ambiente no arquivo `.env`:
- `WEBHOOK_PORT=8001`
- `WEBHOOK_DOMAIN=webhook.server.efetivia.com.br`
- `WEBHOOK_USE_HTTPS=true`
- `WEBHOOK_AUTH_TOKEN=efetivia_webhook_secret_token_2025`

## Configuração no Chatwoot

Para configurar o webhook no Chatwoot:

1. Acesse o painel de administração do Chatwoot
2. Vá para Configurações > Webhooks
3. Adicione um novo webhook com a URL: `https://webhook.server.efetivia.com.br/webhook`
4. Adicione o cabeçalho de autorização: `Authorization: Bearer efetivia_webhook_secret_token_2025`
5. Selecione os eventos que deseja receber (message_created, conversation_created, etc.)
6. Salve as configurações

## Testando a Configuração

Para testar se o webhook está funcionando corretamente:

1. Verifique os logs do servidor webhook:
   ```bash
   docker-compose logs -f webhook_server
   ```

2. Envie uma mensagem de teste pelo Chatwoot e verifique se o webhook recebe a notificação

## Solução de Problemas

Se o webhook não estiver funcionando corretamente, verifique:

1. Se o subdomínio está apontando para o IP correto
2. Se o certificado SSL está válido
3. Se o IP do Chatwoot está permitido no Nginx
4. Se o token de autenticação está configurado corretamente
5. Se o servidor webhook está em execução
6. Se as portas estão abertas no firewall

## Manutenção

O certificado SSL será renovado automaticamente pelo Certbot. No entanto, é importante verificar periodicamente:

1. A validade do certificado SSL
2. Os logs do Nginx e do servidor webhook para identificar possíveis problemas
3. Se o token de autenticação precisa ser atualizado por questões de segurança
