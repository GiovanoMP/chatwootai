#!/bin/bash

# Script simplificado para iniciar todo o sistema de webhook
# Autor: Cascade AI
# Data: 2025-03-19

# Cores para saída no terminal
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Diretório base do webhook
WEBHOOK_DIR="$(dirname "$(readlink -f "$0")")"
cd "$WEBHOOK_DIR"

echo -e "${GREEN}=== Iniciando Sistema de Webhook para Chatwoot ===${NC}"
echo -e "${YELLOW}Diretório de trabalho: $WEBHOOK_DIR${NC}"

# Verificar se o servidor webhook está rodando
if curl -s http://localhost:8001/health > /dev/null; then
    echo -e "${GREEN}✓ Servidor webhook já está rodando na porta 8001${NC}"
else
    echo -e "${YELLOW}Iniciando servidor webhook...${NC}"
    
    # Iniciar o servidor webhook em segundo plano
    python "$WEBHOOK_DIR/start_webhook_standalone.py" > webhook_server.log 2>&1 &
    WEBHOOK_PID=$!
    
    # Aguardar alguns segundos para o servidor iniciar
    echo -e "${YELLOW}Aguardando o servidor iniciar...${NC}"
    sleep 5
    
    # Verificar se o servidor está em execução
    if ps -p $WEBHOOK_PID > /dev/null; then
        echo -e "${GREEN}✓ Servidor webhook iniciado com PID: $WEBHOOK_PID${NC}"
    else
        echo -e "${RED}✗ Falha ao iniciar o servidor webhook${NC}"
        echo -e "${RED}Verifique o arquivo webhook_server.log para mais informações${NC}"
        exit 1
    fi
fi

# Verificar se o ngrok está rodando
if curl -s http://localhost:4040/api/tunnels > /dev/null; then
    echo -e "${GREEN}✓ Ngrok já está rodando${NC}"
    
    # Obter a URL do ngrok
    NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | grep -o '"public_url":"[^"]*' | grep -o 'https://[^"]*')
    echo -e "${GREEN}✓ URL do ngrok: $NGROK_URL${NC}"
else
    echo -e "${YELLOW}Iniciando ngrok...${NC}"
    
    # Iniciar o ngrok em segundo plano
    nohup ngrok http 8001 --log=stdout > ngrok.log 2>&1 &
    NGROK_PID=$!
    
    # Aguardar alguns segundos para o ngrok iniciar
    echo -e "${YELLOW}Aguardando o ngrok iniciar...${NC}"
    sleep 5
    
    # Verificar se o ngrok está em execução
    if curl -s http://localhost:4040/api/tunnels > /dev/null; then
        # Obter a URL do ngrok
        NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | grep -o '"public_url":"[^"]*' | grep -o 'https://[^"]*')
        echo -e "${GREEN}✓ Ngrok iniciado com sucesso${NC}"
        echo -e "${GREEN}✓ URL do ngrok: $NGROK_URL${NC}"
    else
        echo -e "${RED}✗ Falha ao iniciar o ngrok${NC}"
        echo -e "${RED}Verifique o arquivo ngrok.log para mais informações${NC}"
        exit 1
    fi
fi

# Perguntar se deseja atualizar a URL na VPS
echo -e "${YELLOW}Deseja atualizar a URL do webhook na VPS? (s/n)${NC}"
read -r UPDATE_VPS

if [[ "$UPDATE_VPS" =~ ^[Ss]$ ]]; then
    echo -e "${YELLOW}Atualizando URL na VPS...${NC}"
    "$WEBHOOK_DIR/scripts/update_vps_webhook_url.sh"
else
    echo -e "${YELLOW}Pulando atualização da URL na VPS${NC}"
fi

echo -e "${GREEN}=== Sistema de Webhook iniciado com sucesso ===${NC}"
echo -e "${YELLOW}URL do Webhook: $NGROK_URL/webhook${NC}"
echo -e "${YELLOW}Para verificar os logs do servidor webhook: tail -f webhook_server.log${NC}"
echo -e "${YELLOW}Para verificar os logs do ngrok: tail -f ngrok.log${NC}"
