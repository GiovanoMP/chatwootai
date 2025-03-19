# Scripts de Webhook

Este diretório contém scripts para gerenciar a integração de webhook entre o Chatwoot e o sistema ChatwootAI.

## Script Principal

O script principal para iniciar a conexão webhook é:

- **`start_webhook_connection.sh`**: Script unificado que verifica, inicia e configura todos os componentes necessários para a conexão webhook.

```bash
# Para iniciar a conexão webhook
./scripts/webhook/start_webhook_connection.sh
```

Este script faz o seguinte:
1. Verifica se o servidor webhook está rodando
2. Inicia o servidor webhook se necessário
3. Verifica se o túnel ngrok está ativo
4. Inicia o túnel ngrok se necessário
5. Fornece instruções para atualizar a URL do webhook na VPS
6. Oferece a opção de testar o webhook

## Scripts Mantidos

Os seguintes scripts foram mantidos após a limpeza:

### Desenvolvimento Local

- **`start_webhook_dev.sh`**: Inicia o servidor webhook em modo de desenvolvimento (com hot reload)

### Implantação em Produção

- **`deploy_webhook_swarm.sh`**: Implanta o servidor webhook no Docker Swarm
- **`check_webhook_swarm.sh`**: Verifica o status do webhook no Docker Swarm
- **`test_webhook_swarm.sh`**: Testa o webhook no ambiente Docker Swarm
- **`setup_webhook_ssl.sh`**: Configura SSL para o webhook em produção

### Utilitários

- **`update_webhook_url.sh`**: Atualiza a URL do webhook na VPS

## Fluxo de Trabalho Recomendado

1. **Desenvolvimento Local**:
   ```bash
   ./scripts/webhook/start_webhook_connection.sh
   ```

2. **Atualização da URL na VPS**:
   ```bash
   ./scripts/webhook/update_webhook_url.sh https://sua-url-ngrok.ngrok-free.app/webhook
   ```

3. **Implantação em Produção**:
   ```bash
   ./scripts/webhook/deploy_webhook_swarm.sh
   ```

## Scripts Removidos

Os seguintes scripts foram movidos para backup por serem redundantes:

- `start_webhook_local.sh` (substituído por `start_webhook_connection.sh`)
- `start_test_webhook.sh` (funcionalidade incluída em `start_webhook_connection.sh`)
- `start_webhook.sh` (substituído por `start_webhook_dev.sh` ou `start_webhook_connection.sh`)
- `start_ngrok.sh` (funcionalidade incluída em `start_webhook_connection.sh`)
- `test_webhook.sh` (funcionalidade incluída em `start_webhook_connection.sh`)
- `check_webhook_status.sh` (funcionalidade incluída em `start_webhook_connection.sh`)
- `configure_local_webhook.sh` (não é mais necessário com o novo script unificado)
