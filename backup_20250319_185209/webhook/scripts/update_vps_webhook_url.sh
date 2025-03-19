#!/bin/bash

# Script para atualizar automaticamente a URL do Ngrok na VPS
# Autor: Cascade AI
# Data: 2025-03-19

# Cores para saída no terminal
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configurações da VPS
VPS_USER="root"
VPS_HOST="srv692745.hstgr.cloud"
SSH_OPTS="-o ServerAliveInterval=60"

# Função para obter a URL do Ngrok
get_ngrok_url() {
    echo -e "${YELLOW}Obtendo URL do ngrok...${NC}"
    
    # Tentar obter a URL do ngrok via API
    NGROK_API_RESPONSE=$(curl -s http://localhost:4040/api/tunnels)
    
    if [ $? -eq 0 ] && [ ! -z "$NGROK_API_RESPONSE" ]; then
        # Extrair a URL pública do ngrok
        NGROK_URL=$(echo $NGROK_API_RESPONSE | grep -o '"public_url":"[^"]*' | grep -o 'https://[^"]*')
        
        if [ ! -z "$NGROK_URL" ]; then
            echo -e "${GREEN}✓ URL do ngrok: $NGROK_URL${NC}"
            return 0
        fi
    fi
    
    echo -e "${RED}✗ Não foi possível obter a URL do ngrok${NC}"
    echo -e "${YELLOW}Verifique se o ngrok está rodando com:${NC} ps aux | grep ngrok"
    echo -e "${YELLOW}Inicie o ngrok com:${NC} ./scripts/webhook/start_ngrok.sh"
    return 1
}

# Função para atualizar a URL na VPS
update_vps_webhook_url() {
    if [ -z "$NGROK_URL" ]; then
        echo -e "${RED}Erro: URL do Ngrok não definida${NC}"
        return 1
    fi
    
    echo -e "${YELLOW}Atualizando URL do webhook na VPS...${NC}"
    
    # Comando para atualizar o arquivo na VPS
    SSH_COMMAND="cd ~/simple_webhook && \
        cp simple_webhook.py simple_webhook.py.bak && \
        sed -i \"s|FORWARD_URL = '.*'|FORWARD_URL = '$NGROK_URL/webhook'|g\" simple_webhook.py && \
        docker build -t simple_webhook:latest . && \
        docker service update --force simple_webhook_simple_webhook"
    
    # Executar o comando na VPS
    ssh $SSH_OPTS $VPS_USER@$VPS_HOST "$SSH_COMMAND"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ URL do webhook atualizada com sucesso na VPS${NC}"
        echo -e "${GREEN}✓ Serviço Docker reiniciado${NC}"
        return 0
    else
        echo -e "${RED}✗ Falha ao atualizar a URL do webhook na VPS${NC}"
        return 1
    fi
}

# Função para verificar os logs do serviço na VPS
check_vps_logs() {
    echo -e "${YELLOW}Verificando logs do serviço na VPS...${NC}"
    
    ssh $SSH_OPTS $VPS_USER@$VPS_HOST "docker service logs simple_webhook_simple_webhook --tail 10"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Logs verificados com sucesso${NC}"
    else
        echo -e "${RED}✗ Falha ao verificar logs${NC}"
    fi
}

# Função principal
main() {
    echo -e "${GREEN}=== Atualizando URL do Webhook na VPS ===${NC}"
    
    # Obter URL do Ngrok
    get_ngrok_url
    if [ $? -ne 0 ]; then
        exit 1
    fi
    
    # Atualizar URL na VPS
    update_vps_webhook_url
    if [ $? -ne 0 ]; then
        exit 1
    fi
    
    # Verificar logs
    check_vps_logs
    
    echo -e "${GREEN}=== Atualização concluída com sucesso ===${NC}"
    echo -e "${YELLOW}URL do Webhook: $NGROK_URL/webhook${NC}"
}

# Executar função principal
main
