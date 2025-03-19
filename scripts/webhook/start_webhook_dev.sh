#!/bin/bash

# Script para iniciar o servidor webhook em modo de desenvolvimento
# Autor: Cascade AI
# Data: 2025-03-16

# Definir cores para melhor legibilidade
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Iniciando o Servidor Webhook em Modo de Desenvolvimento ===${NC}"

# Verificar se o Python está instalado
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 não está instalado. Por favor, instale o Python 3 primeiro.${NC}"
    exit 1
fi

# Verificar se o arquivo .env existe
if [ ! -f .env ]; then
    echo -e "${YELLOW}Arquivo .env não encontrado. Criando arquivo com valores padrão...${NC}"
    
    cat > .env << EOF
# Configurações do Chatwoot
CHATWOOT_API_KEY=seu_api_key_aqui
CHATWOOT_BASE_URL=https://chatwoot.efetivia.com.br/api/v1
CHATWOOT_ACCOUNT_ID=1

# Configurações do Webhook
WEBHOOK_PORT=8001
WEBHOOK_DOMAIN=localhost
WEBHOOK_USE_HTTPS=false
WEBHOOK_AUTH_TOKEN=efetivia_webhook_secret_token_2025
EOF
    
    echo -e "${YELLOW}Arquivo .env criado. Por favor, edite-o com suas configurações reais.${NC}"
    echo -e "${YELLOW}Pressione Enter para continuar ou Ctrl+C para cancelar...${NC}"
    read
fi

# Verificar se as dependências Python estão instaladas
echo -e "${YELLOW}Verificando dependências Python...${NC}"
if ! python3 -c "import fastapi" &> /dev/null || ! python3 -c "import uvicorn" &> /dev/null; then
    echo -e "${YELLOW}Instalando dependências Python...${NC}"
    pip install fastapi uvicorn python-dotenv requests
fi

# Carregar variáveis de ambiente
source .env

# Iniciar o servidor webhook
echo -e "${YELLOW}Iniciando o servidor webhook na porta ${WEBHOOK_PORT}...${NC}"
echo -e "${YELLOW}Pressione Ctrl+C para parar o servidor.${NC}"

# Definir o caminho do módulo Python
WEBHOOK_MODULE="src.api.webhook_server"

# Iniciar o servidor com uvicorn
python3 -m uvicorn ${WEBHOOK_MODULE}:app --host 0.0.0.0 --port ${WEBHOOK_PORT} --reload

echo -e "${GREEN}=== Servidor Webhook encerrado ===${NC}"
