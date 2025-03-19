# Configuração do Webhook no Docker Swarm

Este documento explica como configurar o servidor webhook para trabalhar com múltiplas instâncias do Chatwoot e Odoo no Docker Swarm.

## Visão Geral

Ao usar o Docker Swarm, podemos obter os seguintes benefícios:

1. **Comunicação de alta velocidade** entre os serviços
2. **Maior segurança** por manter o tráfego dentro da rede interna
3. **Escalabilidade** para lidar com múltiplas instâncias
4. **Gerenciamento simplificado** dos serviços

## Arquivos de Configuração

Os seguintes arquivos foram criados para configurar o webhook no Docker Swarm:

1. **docker-stack.yml**: Define os serviços, redes e volumes para o Docker Swarm
2. **scripts/deploy_webhook_swarm.sh**: Script para implantar o servidor webhook no Swarm
3. **scripts/check_webhook_swarm.sh**: Script para verificar o status do servidor webhook
4. **scripts/test_webhook_swarm.sh**: Script para testar o servidor webhook

## Passos para Configuração

### 1. Preparação do Ambiente

Antes de começar, certifique-se de que o Docker está instalado e o Docker Swarm está inicializado:

```bash
# Verificar a versão do Docker
docker --version

# Inicializar o Docker Swarm (se ainda não estiver inicializado)
docker swarm init --advertise-addr $(hostname -I | awk '{print $1}')
```

### 2. Configuração do Arquivo .env

Crie ou edite o arquivo `.env` na raiz do projeto com as seguintes variáveis:

```
# Configurações do Chatwoot
CHATWOOT_API_KEY=seu_api_key_aqui
CHATWOOT_ACCOUNT_ID=1

# Configurações do Webhook
WEBHOOK_PORT=8001
WEBHOOK_AUTH_TOKEN=efetivia_webhook_secret_token_2025

# Configurações do Docker
DOCKER_IMAGE=chatwootai:latest
```

### 3. Implantação do Servidor Webhook

Execute o script de implantação:

```bash
chmod +x scripts/deploy_webhook_swarm.sh
./scripts/deploy_webhook_swarm.sh
```

Este script irá:
- Verificar se o Docker Swarm está ativo
- Criar a rede overlay se necessário
- Implantar o servidor webhook como um serviço no Swarm
- Exibir os logs do serviço

### 4. Verificação do Status

Para verificar o status do servidor webhook:

```bash
chmod +x scripts/check_webhook_swarm.sh
./scripts/check_webhook_swarm.sh
```

Este script irá:
- Verificar o status do serviço no Swarm
- Exibir as réplicas do serviço
- Verificar os logs recentes
- Testar o endpoint de saúde
- Verificar a conectividade com o Chatwoot

### 5. Teste do Servidor Webhook

Para testar o servidor webhook:

```bash
chmod +x scripts/test_webhook_swarm.sh
./scripts/test_webhook_swarm.sh
```

Este script irá:
- Enviar uma requisição de teste para o webhook
- Verificar a resposta
- Exibir os logs para confirmar o processamento

## Configuração do Chatwoot

Para configurar o Chatwoot para enviar webhooks para o servidor:

1. Acesse o painel administrativo do Chatwoot
2. Vá para Configurações > Webhooks
3. Adicione um novo webhook com a URL: `http://chatwootai_webhook_server:8001/webhook`
4. Adicione o cabeçalho de autorização: `Authorization: Bearer efetivia_webhook_secret_token_2025`
5. Selecione os eventos que deseja receber (message_created, conversation_created, etc.)

## Escalabilidade

Para escalar o servidor webhook para lidar com mais instâncias:

```bash
# Aumentar o número de réplicas do servidor webhook
docker service scale chatwootai_webhook_server=3
```

## Monitoramento

Para monitorar o servidor webhook:

```bash
# Visualizar os logs em tempo real
docker service logs -f chatwootai_webhook_server

# Verificar o status do serviço
docker service ps chatwootai_webhook_server
```

## Solução de Problemas

Se o servidor webhook não estiver funcionando corretamente:

1. Verifique se o serviço está em execução:
   ```bash
   docker service ls --filter name=chatwootai_webhook_server
   ```

2. Verifique os logs do serviço:
   ```bash
   docker service logs chatwootai_webhook_server
   ```

3. Verifique se a rede overlay está configurada corretamente:
   ```bash
   docker network inspect chatwoot_network
   ```

4. Verifique se o Chatwoot e o webhook estão na mesma rede:
   ```bash
   docker network inspect chatwoot_network | grep -A 10 "Containers"
   ```
