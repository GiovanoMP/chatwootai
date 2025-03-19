#!/bin/bash

# Script para iniciar um túnel ngrok para o servidor webhook
# Autor: Cascade AI
# Data: 2025-03-16

# Definir cores para melhor legibilidade
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Iniciando Túnel ngrok para o Servidor Webhook ===${NC}"

# Verificar se o ngrok está instalado
if ! command -v ngrok &> /dev/null; then
    echo -e "${YELLOW}ngrok não encontrado. Instalando...${NC}"
    
    # Baixar e instalar o ngrok
    curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
    echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | sudo tee /etc/apt/sources.list.d/ngrok.list
    sudo apt update
    sudo apt install -y ngrok
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}Falha ao instalar o ngrok. Por favor, instale manualmente:${NC}"
        echo -e "https://ngrok.com/download"
        exit 1
    fi
fi

# Verificar se o token do ngrok está configurado
if ! ngrok config check &> /dev/null; then
    echo -e "${YELLOW}Token do ngrok não configurado.${NC}"
    echo -e "${YELLOW}Por favor, crie uma conta em https://ngrok.com e obtenha seu token.${NC}"
    echo -e "${YELLOW}Digite seu token do ngrok:${NC}"
    read -p "> " NGROK_TOKEN
    
    # Configurar o token
    ngrok config add-authtoken $NGROK_TOKEN
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}Falha ao configurar o token do ngrok.${NC}"
        exit 1
    fi
fi

# Verificar se o servidor webhook está em execução
WEBHOOK_PORT=$(grep "WEBHOOK_PORT" .env 2>/dev/null | cut -d '=' -f2 || echo "8001")
if ! curl -s http://localhost:$WEBHOOK_PORT/health &> /dev/null; then
    echo -e "${YELLOW}Servidor webhook não parece estar em execução na porta $WEBHOOK_PORT.${NC}"
    echo -e "${YELLOW}Deseja iniciar o servidor webhook primeiro? (s/n)${NC}"
    read -p "> " START_SERVER
    
    if [[ $START_SERVER == "s" || $START_SERVER == "S" ]]; then
        echo -e "${YELLOW}Iniciando o servidor webhook...${NC}"
        ./scripts/start_webhook.sh &
        
        # Aguardar o servidor iniciar
        echo -e "${YELLOW}Aguardando o servidor iniciar...${NC}"
        sleep 10
    fi
fi

# Iniciar o túnel ngrok
echo -e "${YELLOW}Iniciando o túnel ngrok para a porta $WEBHOOK_PORT...${NC}"
ngrok http $WEBHOOK_PORT --log=stdout

echo -e "${GREEN}=== Túnel ngrok encerrado ===${NC}"
echo -e "Para iniciar novamente, execute este script."
