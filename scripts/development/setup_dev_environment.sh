#!/bin/bash

# Script para configurar o ambiente de desenvolvimento
# Autor: Cascade AI
# Data: 2025-03-16

# Definir cores para melhor legibilidade
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Configurando Ambiente de Desenvolvimento para ChatwootAI ===${NC}"

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

# Iniciar o servidor webhook local
echo -e "${YELLOW}Iniciando o servidor webhook local...${NC}"
./scripts/start_webhook_dev.sh &
WEBHOOK_PID=$!

# Aguardar o servidor iniciar
echo -e "${YELLOW}Aguardando o servidor iniciar...${NC}"
sleep 5

# Iniciar o túnel ngrok
echo -e "${YELLOW}Iniciando o túnel ngrok...${NC}"
ngrok http 8001 --log=stdout > ngrok.log &
NGROK_PID=$!

# Aguardar o ngrok iniciar
echo -e "${YELLOW}Aguardando o ngrok iniciar...${NC}"
sleep 5

# Obter a URL do ngrok
NGROK_URL=$(grep -o "https://.*\.ngrok\.io" ngrok.log | head -n 1)

if [ -z "$NGROK_URL" ]; then
    echo -e "${RED}Falha ao obter a URL do ngrok. Verifique o arquivo ngrok.log.${NC}"
    exit 1
fi

echo -e "${GREEN}=== Ambiente de Desenvolvimento Configurado! ===${NC}"
echo -e "URL do ngrok: ${NGROK_URL}"
echo -e "\n${YELLOW}Instruções para configurar o webhook na VPS:${NC}"
echo -e "1. Edite o arquivo src/api/webhook_server.py na VPS"
echo -e "2. Adicione a seguinte linha no início do manipulador de webhook:"
echo -e "   FORWARD_URL = '${NGROK_URL}/webhook'"
echo -e "3. Adicione código para encaminhar eventos para esta URL"
echo -e "4. Reinicie o serviço webhook na VPS"
echo -e "\n${YELLOW}Para encerrar este ambiente, pressione Ctrl+C${NC}"

# Aguardar o usuário encerrar
trap "kill $WEBHOOK_PID $NGROK_PID; echo -e '\n${GREEN}Ambiente encerrado.${NC}'" EXIT
wait
