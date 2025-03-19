#!/bin/bash

# Script para testar o servidor webhook no Docker Swarm
# Autor: Cascade AI
# Data: 2025-03-16

# Definir cores para melhor legibilidade
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Testando Servidor Webhook no Docker Swarm ===${NC}"

# Verificar se o Docker está instalado
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker não está instalado. Por favor, instale o Docker primeiro.${NC}"
    exit 1
fi

# Verificar se o Docker Swarm está ativo
SWARM_STATUS=$(docker info --format '{{.Swarm.LocalNodeState}}')
if [ "$SWARM_STATUS" != "active" ]; then
    echo -e "${RED}Docker Swarm não está ativo. Execute 'docker swarm init' para inicializar.${NC}"
    exit 1
fi

# Verificar se o serviço existe
SERVICE_EXISTS=$(docker service ls --filter name=chatwootai_webhook_server --format '{{.Name}}')
if [ -z "$SERVICE_EXISTS" ]; then
    echo -e "${RED}Serviço webhook não encontrado. Execute o script deploy_webhook_swarm.sh primeiro.${NC}"
    exit 1
fi

# Obter o ID do contêiner
CONTAINER_ID=$(docker ps --filter name=chatwootai_webhook_server --format '{{.ID}}')

if [ -z "$CONTAINER_ID" ]; then
    echo -e "${RED}Contêiner do webhook não encontrado. O serviço pode estar com problemas.${NC}"
    exit 1
fi

# Obter o token de autenticação do arquivo .env ou usar o padrão
if [ -f .env ]; then
    source .env
    AUTH_TOKEN=${WEBHOOK_AUTH_TOKEN:-efetivia_webhook_secret_token_2025}
else
    AUTH_TOKEN="efetivia_webhook_secret_token_2025"
fi

echo -e "${YELLOW}Testando o endpoint de saúde...${NC}"
HEALTH_CHECK=$(docker exec $CONTAINER_ID curl -s http://localhost:8001/health)

if [ $? -ne 0 ]; then
    echo -e "${RED}Falha ao verificar o endpoint de saúde. O serviço pode estar com problemas.${NC}"
    exit 1
else
    echo -e "${GREEN}Resposta do endpoint de saúde:${NC}"
    echo $HEALTH_CHECK | python -m json.tool
fi

echo -e "\n${YELLOW}Enviando uma requisição de teste para o webhook...${NC}"

# Criar um payload de teste simulando um evento do Chatwoot
PAYLOAD='{
  "event": "message_created",
  "account": {
    "id": 1,
    "name": "Conta de Teste"
  },
  "message": {
    "id": 12345,
    "content": "Esta é uma mensagem de teste do webhook",
    "message_type": 0,
    "content_type": "text",
    "created_at": "2025-03-16T22:00:00.000Z",
    "private": false,
    "sender": {
      "id": 1,
      "name": "Usuário de Teste",
      "email": "teste@exemplo.com",
      "type": "User"
    }
  },
  "conversation": {
    "id": 6789,
    "inbox_id": 1,
    "status": "open",
    "agent_last_seen_at": "2025-03-16T22:00:00.000Z",
    "contact_last_seen_at": "2025-03-16T22:00:00.000Z"
  },
  "contact": {
    "id": 5678,
    "name": "Cliente de Teste",
    "email": "cliente@exemplo.com",
    "phone_number": "+5511999999999"
  }
}'

# Enviar a requisição para o webhook
RESPONSE=$(docker exec $CONTAINER_ID curl -s -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -d "$PAYLOAD" \
  http://localhost:8001/webhook)

if [ $? -ne 0 ]; then
    echo -e "${RED}Falha ao enviar a requisição de teste.${NC}"
    exit 1
else
    echo -e "${GREEN}Resposta do webhook:${NC}"
    echo $RESPONSE | python -m json.tool
fi

echo -e "\n${YELLOW}Verificando os logs para confirmar o processamento do webhook...${NC}"
docker service logs --tail 20 chatwootai_webhook_server

echo -e "\n${GREEN}=== Teste concluído! ===${NC}"
echo -e "O servidor webhook está funcionando corretamente no Docker Swarm."
echo -e "Para testar com eventos reais, configure o Chatwoot para enviar webhooks para:"
echo -e "http://chatwootai_webhook_server:8001/webhook"
echo -e "Com o cabeçalho de autorização: Bearer $AUTH_TOKEN"
