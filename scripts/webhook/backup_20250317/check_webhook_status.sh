#!/bin/bash

# Script para verificar o status do servidor webhook
# Autor: Cascade AI
# Data: 2025-03-16

# Definir cores para melhor legibilidade
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Verificando o Status do Servidor Webhook ===${NC}"

# Carregar variáveis de ambiente
if [ -f "/home/giovano/Projetos/Chatwoot V4/.env" ]; then
    source /home/giovano/Projetos/Chatwoot\ V4/.env
else
    echo -e "${RED}Arquivo .env não encontrado. Usando valores padrão.${NC}"
    WEBHOOK_DOMAIN="webhook.server.efetivia.com.br"
    WEBHOOK_PORT=8001
    WEBHOOK_USE_HTTPS=true
fi

# Construir a URL do webhook
if [ "$WEBHOOK_USE_HTTPS" = "true" ]; then
    WEBHOOK_URL="https://${WEBHOOK_DOMAIN}/health"
else
    WEBHOOK_URL="http://${WEBHOOK_DOMAIN}:${WEBHOOK_PORT}/health"
fi

echo -e "${YELLOW}Verificando se o servidor webhook está acessível em: ${WEBHOOK_URL}${NC}"

# Verificar se o servidor está respondendo
if curl -s --head --request GET $WEBHOOK_URL | grep "200 OK" > /dev/null; then
    echo -e "${GREEN}✓ Servidor webhook está online e respondendo!${NC}"
else
    echo -e "${RED}✗ Servidor webhook não está respondendo. Verificando possíveis problemas...${NC}"
    
    # Verificar se o contêiner Docker está em execução
    echo -e "${YELLOW}Verificando o status do contêiner Docker...${NC}"
    if docker-compose ps | grep webhook_server | grep "Up" > /dev/null; then
        echo -e "${GREEN}✓ Contêiner webhook_server está em execução.${NC}"
    else
        echo -e "${RED}✗ Contêiner webhook_server não está em execução. Tente iniciar com:${NC}"
        echo -e "   docker-compose up -d webhook_server"
    fi
    
    # Verificar se a porta está aberta
    echo -e "${YELLOW}Verificando se a porta ${WEBHOOK_PORT} está aberta...${NC}"
    if nc -z localhost ${WEBHOOK_PORT}; then
        echo -e "${GREEN}✓ Porta ${WEBHOOK_PORT} está aberta.${NC}"
    else
        echo -e "${RED}✗ Porta ${WEBHOOK_PORT} não está aberta. Verifique se o servidor está escutando na porta correta.${NC}"
    fi
    
    # Verificar logs do contêiner
    echo -e "${YELLOW}Últimas 10 linhas de log do contêiner:${NC}"
    docker-compose logs --tail=10 webhook_server
    
    # Verificar configuração do Nginx
    echo -e "${YELLOW}Verificando configuração do Nginx...${NC}"
    if [ -f "/etc/nginx/sites-enabled/webhook.conf" ]; then
        echo -e "${GREEN}✓ Configuração do Nginx encontrada.${NC}"
        
        # Verificar status do Nginx
        if systemctl is-active --quiet nginx; then
            echo -e "${GREEN}✓ Nginx está em execução.${NC}"
        else
            echo -e "${RED}✗ Nginx não está em execução. Tente iniciar com:${NC}"
            echo -e "   sudo systemctl start nginx"
        fi
    else
        echo -e "${RED}✗ Configuração do Nginx não encontrada. Execute o script setup_webhook_ssl.sh primeiro.${NC}"
    fi
fi

# Exibir informações úteis
echo -e "\n${GREEN}=== Informações do Servidor Webhook ===${NC}"
echo -e "URL do Webhook: ${WEBHOOK_URL}"
echo -e "Porta: ${WEBHOOK_PORT}"
echo -e "HTTPS: ${WEBHOOK_USE_HTTPS}"
echo -e "\nPara visualizar os logs em tempo real, execute:"
echo -e "   docker-compose logs -f webhook_server"
echo -e "\nPara reiniciar o servidor webhook, execute:"
echo -e "   docker-compose restart webhook_server"
