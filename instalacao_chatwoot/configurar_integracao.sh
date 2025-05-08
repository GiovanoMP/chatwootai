#!/bin/bash

# Cores para melhor visualização
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Script de Configuração da Integração Chatwoot e Evolution API ===${NC}"

# Solicitar informações necessárias
echo -e "${YELLOW}Por favor, forneça as seguintes informações:${NC}"
read -p "Token de API do Chatwoot: " CHATWOOT_TOKEN
read -p "ID da conta do Chatwoot: " CHATWOOT_ACCOUNT_ID
read -p "Número de telefone WhatsApp (com código do país, ex: 5545999680334): " WHATSAPP_NUMBER
read -p "Nome da instância WhatsApp (ex: whatsapp1): " INSTANCE_NAME

# Verificar se as informações foram fornecidas
if [[ -z "$CHATWOOT_TOKEN" || -z "$CHATWOOT_ACCOUNT_ID" || -z "$WHATSAPP_NUMBER" || -z "$INSTANCE_NAME" ]]; then
    echo -e "${RED}Todas as informações são obrigatórias. Por favor, execute o script novamente.${NC}"
    exit 1
fi

echo -e "${BLUE}=== Criando instância WhatsApp na Evolution API ===${NC}"

# Criar instância WhatsApp
EVOLUTION_API_KEY="sprintia-evolution-api-key"  # Deve corresponder ao valor em evolutionV2.yaml
EVOLUTION_API_URL="https://evolution.sprintia.com.br"
CHATWOOT_URL="https://chat.sprintia.com.br"

# Payload para criar a instância
PAYLOAD='{
  "instanceName": "'$INSTANCE_NAME'",
  "token": "'$CHATWOOT_TOKEN'",
  "url": "'$CHATWOOT_URL'",
  "signMsg": "Sprintia",
  "phoneNumber": "'$WHATSAPP_NUMBER'",
  "webhook": {
    "url": "",
    "enabled": false
  },
  "chatwoot": {
    "enabled": true,
    "account_id": "'$CHATWOOT_ACCOUNT_ID'",
    "token": "'$CHATWOOT_TOKEN'",
    "url": "'$CHATWOOT_URL'",
    "sign_msg": true,
    "reopen_conversation": true,
    "conversation_pending": false
  }
}'

echo -e "${YELLOW}Enviando solicitação para criar instância...${NC}"
echo -e "${BLUE}Payload:${NC} $PAYLOAD"

# Enviar solicitação para criar instância
RESPONSE=$(curl -s -X POST \
  "$EVOLUTION_API_URL/instance/create" \
  -H "Content-Type: application/json" \
  -H "apikey: $EVOLUTION_API_KEY" \
  -d "$PAYLOAD")

echo -e "${GREEN}Resposta:${NC} $RESPONSE"

# Verificar se a instância foi criada com sucesso
if [[ "$RESPONSE" == *"true"* ]]; then
    echo -e "${GREEN}Instância criada com sucesso!${NC}"
    
    echo -e "${BLUE}=== Conectando ao WhatsApp ===${NC}"
    echo -e "${YELLOW}Obtendo QR Code...${NC}"
    
    # Obter QR Code
    QR_RESPONSE=$(curl -s -X GET \
      "$EVOLUTION_API_URL/instance/connect/$INSTANCE_NAME" \
      -H "apikey: $EVOLUTION_API_KEY")
    
    echo -e "${GREEN}QR Code solicitado. Verifique a interface do Chatwoot para escanear o código.${NC}"
    echo -e "${YELLOW}Resposta:${NC} $QR_RESPONSE"
    
    echo -e "${BLUE}=== Próximos passos ===${NC}"
    echo -e "1. ${YELLOW}Acesse o Chatwoot em:${NC} ${GREEN}$CHATWOOT_URL${NC}"
    echo -e "2. ${YELLOW}Vá para a conta com ID:${NC} ${GREEN}$CHATWOOT_ACCOUNT_ID${NC}"
    echo -e "3. ${YELLOW}Procure pela caixa de entrada do WhatsApp e escaneie o QR Code${NC}"
    
else
    echo -e "${RED}Falha ao criar instância. Verifique os logs para mais detalhes.${NC}"
fi

echo -e "${BLUE}=== Configuração concluída! ===${NC}"
