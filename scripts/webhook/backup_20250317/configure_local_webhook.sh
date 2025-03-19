#!/bin/bash

# Script para configurar o webhook para desenvolvimento local
# Autor: Cascade AI
# Data: 2025-03-16

# Definir cores para melhor legibilidade
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Configurando Webhook para Desenvolvimento Local ===${NC}"

# Verificar se está sendo executado como root
if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}Por favor, execute este script como root (sudo)${NC}"
  exit 1
fi

# Obter o IP local
LOCAL_IP=$(hostname -I | awk '{print $1}')
echo -e "${YELLOW}Seu IP local é: $LOCAL_IP${NC}"

# Verificar se o Nginx está instalado
if ! command -v nginx &> /dev/null; then
    echo -e "${YELLOW}Nginx não encontrado. Instalando...${NC}"
    apt update
    apt install -y nginx
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}Falha ao instalar o Nginx. Por favor, instale manualmente.${NC}"
        exit 1
    fi
fi

# Criar configuração do Nginx
echo -e "${YELLOW}Criando configuração do Nginx para o webhook...${NC}"

cat > /etc/nginx/sites-available/webhook.conf << EOF
server {
    listen 80;
    server_name webhook.server.efetivia.com.br;

    location / {
        proxy_pass http://localhost:8001;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Ativar a configuração
ln -sf /etc/nginx/sites-available/webhook.conf /etc/nginx/sites-enabled/

# Verificar a configuração do Nginx
echo -e "${YELLOW}Verificando a configuração do Nginx...${NC}"
nginx -t

if [ $? -ne 0 ]; then
    echo -e "${RED}Erro na configuração do Nginx. Por favor, verifique manualmente.${NC}"
    exit 1
fi

# Reiniciar o Nginx
echo -e "${YELLOW}Reiniciando o Nginx...${NC}"
systemctl restart nginx

# Verificar se o servidor webhook está em execução
if ! curl -s http://localhost:8001/health &> /dev/null; then
    echo -e "${YELLOW}Servidor webhook não parece estar em execução.${NC}"
    echo -e "${YELLOW}Deseja iniciar o servidor webhook agora? (s/n)${NC}"
    read -p "> " START_SERVER
    
    if [[ $START_SERVER == "s" || $START_SERVER == "S" ]]; then
        echo -e "${YELLOW}Iniciando o servidor webhook...${NC}"
        cd /home/giovano/Projetos/Chatwoot\ V4
        ./scripts/start_webhook.sh &
        
        # Aguardar o servidor iniciar
        echo -e "${YELLOW}Aguardando o servidor iniciar...${NC}"
        sleep 10
    fi
fi

echo -e "${GREEN}=== Configuração Concluída! ===${NC}"
echo -e "O webhook agora está configurado para desenvolvimento local."
echo -e "URL do webhook: http://webhook.server.efetivia.com.br/webhook"
echo -e "Para testar, execute: curl http://webhook.server.efetivia.com.br/health"
echo -e "\n${YELLOW}Próximos passos:${NC}"
echo -e "1. Certifique-se de que seu DNS aponta para este servidor"
echo -e "2. Configure o Chatwoot para usar a URL: http://webhook.server.efetivia.com.br/webhook"
echo -e "3. Adicione o cabeçalho de autorização: Bearer efetivia_webhook_secret_token_2025"
