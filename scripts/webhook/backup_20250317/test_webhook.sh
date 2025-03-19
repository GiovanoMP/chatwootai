#!/bin/bash

# Script para testar o servidor webhook com uma requisição simulada do Chatwoot
# Autor: Cascade AI
# Data: 2025-03-16

# Definir cores para melhor legibilidade
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Testando o Servidor Webhook ===${NC}"

# Carregar variáveis de ambiente
if [ -f "/home/giovano/Projetos/Chatwoot V4/.env" ]; then
    source /home/giovano/Projetos/Chatwoot\ V4/.env
else
    echo -e "${RED}Arquivo .env não encontrado. Usando valores padrão.${NC}"
    WEBHOOK_DOMAIN="webhook.server.efetivia.com.br"
    WEBHOOK_PORT=8001
    WEBHOOK_USE_HTTPS=true
    WEBHOOK_AUTH_TOKEN="efetivia_webhook_secret_token_2025"
fi

# Construir a URL do webhook
if [ "$WEBHOOK_USE_HTTPS" = "true" ]; then
    WEBHOOK_URL="https://${WEBHOOK_DOMAIN}/webhook"
else
    WEBHOOK_URL="http://${WEBHOOK_DOMAIN}:${WEBHOOK_PORT}/webhook"
fi

echo -e "${YELLOW}Enviando uma requisição de teste para: ${WEBHOOK_URL}${NC}"

# Criar um payload de teste simulando um evento de mensagem do Chatwoot
PAYLOAD='{
  "event": "message_created",
  "id": 1,
  "account": {
    "id": 1,
    "name": "Conta de Teste"
  },
  "inbox": {
    "id": 1,
    "name": "Inbox de Teste"
  },
  "conversation": {
    "id": 1,
    "inbox_id": 1,
    "status": "open",
    "assignee_id": 1,
    "contact_inbox": {
      "id": 1,
      "contact": {
        "id": 1,
        "name": "Usuário de Teste",
        "email": "teste@exemplo.com",
        "phone_number": "+5511999999999"
      }
    }
  },
  "message": {
    "id": 1,
    "content": "Olá, esta é uma mensagem de teste para o webhook",
    "message_type": 0,
    "content_type": "text",
    "created_at": "2025-03-16T21:48:59-03:00",
    "private": false,
    "sender": {
      "id": 1,
      "name": "Usuário de Teste",
      "type": "contact"
    }
  }
}'

# Enviar a requisição com o token de autenticação
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${WEBHOOK_AUTH_TOKEN}" \
  -d "${PAYLOAD}" \
  ${WEBHOOK_URL})

# Verificar a resposta
if [ "$RESPONSE" -eq 200 ]; then
    echo -e "${GREEN}✓ Teste bem-sucedido! O servidor webhook respondeu com código 200 OK.${NC}"
    echo -e "${YELLOW}Verifique os logs do servidor webhook para confirmar que o evento foi processado corretamente:${NC}"
    echo -e "   docker-compose logs -f webhook_server"
else
    echo -e "${RED}✗ Teste falhou. O servidor webhook respondeu com código ${RESPONSE}.${NC}"
    echo -e "${YELLOW}Possíveis problemas:${NC}"
    echo -e "1. O servidor webhook não está em execução"
    echo -e "2. O token de autenticação está incorreto"
    echo -e "3. A URL do webhook está incorreta"
    echo -e "4. Há um problema de rede ou firewall"
    echo -e "\n${YELLOW}Verifique os logs do servidor webhook para mais detalhes:${NC}"
    echo -e "   docker-compose logs -f webhook_server"
fi

echo -e "\n${GREEN}=== Informações do Teste ===${NC}"
echo -e "URL do Webhook: ${WEBHOOK_URL}"
echo -e "Tipo de Evento: message_created"
echo -e "Conteúdo da Mensagem: \"Olá, esta é uma mensagem de teste para o webhook\""
