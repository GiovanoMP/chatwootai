# Configuração do ChatwootAI

Este diretório contém os arquivos de configuração do projeto ChatwootAI.

## Arquivos Principais

- `.env` - Variáveis de ambiente principais para o projeto
- `.env.chatwoot.example` - Exemplo de configuração para integração com o Chatwoot
- `docker-compose.yml` - Configuração para execução local com Docker Compose
- `docker-stack.yml` - Configuração para implantação em Docker Swarm
- `docker-swarm.yml` - Configuração alternativa para Docker Swarm
- `Dockerfile` - Configuração para construir a imagem Docker principal
- `Dockerfile.api` - Configuração para construir a imagem Docker da API

## Uso

### Configuração de Variáveis de Ambiente

1. Copie o arquivo `.env.chatwoot.example` para `.env` (se ainda não existir):
   ```bash
   cp .env.chatwoot.example .env
   ```

2. Edite o arquivo `.env` com suas configurações:
   ```bash
   nano .env
   ```

### Execução com Docker Compose

```bash
docker-compose -f docker-compose.yml up -d
```

### Implantação em Docker Swarm

```bash
docker stack deploy -c docker-stack.yml chatwootai
```

## Variáveis de Ambiente Importantes

- `CHATWOOT_API_KEY` - Chave de API do Chatwoot
- `CHATWOOT_BASE_URL` - URL base da API do Chatwoot
- `CHATWOOT_ACCOUNT_ID` - ID da conta no Chatwoot
- `WEBHOOK_PORT` - Porta para o servidor webhook
- `WEBHOOK_DOMAIN` - Domínio para o servidor webhook
- `WEBHOOK_USE_HTTPS` - Se o webhook deve usar HTTPS
- `WEBHOOK_AUTH_TOKEN` - Token de autenticação para o webhook
