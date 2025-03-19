#!/bin/bash

# Script unificado para iniciar a conexão webhook com o Chatwoot
# Autor: Cascade AI
# Data: 2025-03-17

# Definir cores para melhor legibilidade
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Diretório base do projeto
PROJECT_DIR="$(pwd)"

echo -e "${GREEN}=== Iniciando Conexão Webhook com Chatwoot ===${NC}"
echo -e "${YELLOW}Este script irá:${NC}"
echo -e "1. Verificar se o servidor webhook está rodando"
echo -e "2. Iniciar o túnel ngrok (se necessário)"
echo -e "3. Atualizar a URL do webhook na VPS (opcional)"
echo ""

# Função para verificar se o servidor webhook está rodando
check_webhook_server() {
    echo -e "${YELLOW}Verificando se o servidor webhook está rodando...${NC}"
    
    if curl -s http://localhost:8001/health > /dev/null; then
        echo -e "${GREEN}✓ Servidor webhook está rodando na porta 8001${NC}"
        return 0
    else
        echo -e "${RED}✗ Servidor webhook não está rodando${NC}"
        return 1
    fi
}

# Função para iniciar o servidor webhook
start_webhook_server() {
    echo -e "${YELLOW}Iniciando o servidor webhook...${NC}"
    
    # Verificar se o arquivo start_webhook_standalone.py existe
    if [ ! -f "${PROJECT_DIR}/start_webhook_standalone.py" ]; then
        echo -e "${RED}Erro: Arquivo start_webhook_standalone.py não encontrado em ${PROJECT_DIR}/start_webhook_standalone.py${NC}"
        exit 1
    fi
    
    # Iniciar o servidor webhook em segundo plano
    python ${PROJECT_DIR}/start_webhook_standalone.py > webhook_server.log 2>&1 &
    WEBHOOK_PID=$!
    
    # Aguardar alguns segundos para o servidor iniciar
    echo -e "${YELLOW}Aguardando o servidor iniciar...${NC}"
    sleep 5
    
    # Verificar se o servidor está em execução
    if ps -p $WEBHOOK_PID > /dev/null; then
        echo -e "${GREEN}✓ Servidor webhook iniciado com PID: $WEBHOOK_PID${NC}"
        return 0
    else
        echo -e "${RED}✗ Falha ao iniciar o servidor webhook${NC}"
        echo -e "${RED}Verifique o arquivo webhook_server.log para mais informações${NC}"
        return 1
    fi
}

# Função para obter a URL do ngrok
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
    return 1
}

# Função para iniciar o túnel ngrok
start_ngrok() {
    echo -e "${YELLOW}Iniciando o túnel ngrok...${NC}"
    
    # Verificar se o ngrok está instalado
    if ! command -v ngrok &> /dev/null; then
        echo -e "${RED}Erro: ngrok não está instalado${NC}"
        echo -e "${YELLOW}Instale o ngrok seguindo as instruções em: https://ngrok.com/download${NC}"
        return 1
    fi
    
    # Verificar se já existe um túnel ngrok ativo
    if curl -s http://localhost:4040/api/tunnels > /dev/null; then
        echo -e "${YELLOW}Já existe um túnel ngrok ativo${NC}"
        get_ngrok_url
        return $?
    fi
    
    # Iniciar o ngrok em segundo plano
    nohup ngrok http 8001 --log=stdout > ngrok.log 2>&1 &
    NGROK_PID=$!
    
    # Aguardar alguns segundos para o ngrok iniciar
    echo -e "${YELLOW}Aguardando o ngrok iniciar...${NC}"
    sleep 5
    
    # Verificar se o ngrok está em execução
    if ps -p $NGROK_PID > /dev/null; then
        echo -e "${GREEN}✓ ngrok iniciado com PID: $NGROK_PID${NC}"
        sleep 2
        get_ngrok_url
        return $?
    else
        echo -e "${RED}✗ Falha ao iniciar o ngrok${NC}"
        echo -e "${RED}Verifique o arquivo ngrok.log para mais informações${NC}"
        return 1
    fi
}

# Função para atualizar a URL do webhook na VPS
update_webhook_url() {
    echo -e "${YELLOW}Deseja atualizar a URL do webhook na VPS? (s/n)${NC}"
    read -p "> " UPDATE_URL
    
    if [[ $UPDATE_URL == "s" || $UPDATE_URL == "S" ]]; then
        echo -e "${YELLOW}Para atualizar a URL do webhook na VPS, execute os seguintes comandos:${NC}"
        echo -e "${GREEN}----------------------------------------${NC}"
        echo -e "cd ~/simple_webhook"
        echo -e "cp simple_webhook.py simple_webhook.py.bak"
        echo -e "sed -i \"s|FORWARD_URL = \\\".*\\\"|FORWARD_URL = \\\"$NGROK_URL\\\"|g\" simple_webhook.py"
        echo -e "docker build -t simple_webhook:latest ."
        echo -e "docker service update --force simple_webhook_simple_webhook"
        echo -e "${GREEN}----------------------------------------${NC}"
        
        echo -e "${YELLOW}Você também pode usar o script update_webhook_url.sh:${NC}"
        echo -e "./scripts/webhook/update_webhook_url.sh $NGROK_URL"
    fi
}

# Função para testar o webhook
test_webhook() {
    echo -e "${YELLOW}Deseja enviar um webhook de teste? (s/n)${NC}"
    read -p "> " TEST_WEBHOOK
    
    if [[ $TEST_WEBHOOK == "s" || $TEST_WEBHOOK == "S" ]]; then
        echo -e "${YELLOW}Enviando webhook de teste para o servidor local...${NC}"
        curl -X POST -H "Content-Type: application/json" -d '{"event": "test_event", "data": "test_data"}' http://localhost:8001/webhook
        
        echo -e "\n${YELLOW}Enviando webhook de teste para o ngrok...${NC}"
        curl -X POST -H "Content-Type: application/json" -d '{"event": "test_event", "data": "test_data"}' $NGROK_URL/webhook
    fi
}

# Verificar se o servidor webhook está rodando
if check_webhook_server; then
    echo -e "${GREEN}O servidor webhook já está rodando${NC}"
else
    echo -e "${YELLOW}O servidor webhook não está rodando${NC}"
    echo -e "${YELLOW}Deseja iniciar o servidor webhook? (s/n)${NC}"
    read -p "> " START_SERVER
    
    if [[ $START_SERVER == "s" || $START_SERVER == "S" ]]; then
        start_webhook_server
    else
        echo -e "${RED}Abortando: O servidor webhook é necessário para continuar${NC}"
        exit 1
    fi
fi

# Verificar se o ngrok está rodando
if get_ngrok_url; then
    echo -e "${GREEN}O túnel ngrok já está ativo${NC}"
else
    echo -e "${YELLOW}O túnel ngrok não está ativo${NC}"
    echo -e "${YELLOW}Deseja iniciar o túnel ngrok? (s/n)${NC}"
    read -p "> " START_NGROK
    
    if [[ $START_NGROK == "s" || $START_NGROK == "S" ]]; then
        start_ngrok
    else
        echo -e "${RED}Abortando: O túnel ngrok é necessário para continuar${NC}"
        exit 1
    fi
fi

# Atualizar a URL do webhook na VPS
update_webhook_url

# Testar o webhook
test_webhook

echo -e "${GREEN}=== Conexão Webhook com Chatwoot Estabelecida ===${NC}"
echo -e "${YELLOW}URL do Webhook: $NGROK_URL/webhook${NC}"
echo -e "${YELLOW}Para verificar os logs do servidor webhook:${NC} tail -f webhook_server.log"
echo -e "${YELLOW}Para verificar os logs do ngrok:${NC} tail -f ngrok.log"
echo -e "${YELLOW}Para encerrar a conexão, pressione Ctrl+C${NC}"

# Manter o script em execução para que o usuário possa ver os logs
echo -e "${YELLOW}Pressione Ctrl+C para encerrar o script${NC}"
tail -f webhook_server.log
