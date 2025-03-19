#!/bin/bash

# Script para configurar o servidor webhook com SSL usando Let's Encrypt
# Autor: Cascade AI
# Data: 2025-03-16

# Definir cores para melhor legibilidade
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Configuração do Servidor Webhook com SSL ===${NC}"
echo "Este script irá configurar o Nginx e o Let's Encrypt para o webhook"

# Verificar se está sendo executado como root
if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}Por favor, execute este script como root (sudo)${NC}"
  exit 1
fi

# Verificar se o Nginx está instalado
if ! command -v nginx &> /dev/null; then
    echo -e "${YELLOW}Nginx não encontrado. Instalando...${NC}"
    apt-get update
    apt-get install -y nginx
else
    echo -e "${GREEN}Nginx já está instalado.${NC}"
fi

# Verificar se o Certbot está instalado
if ! command -v certbot &> /dev/null; then
    echo -e "${YELLOW}Certbot não encontrado. Instalando...${NC}"
    apt-get update
    apt-get install -y certbot python3-certbot-nginx
else
    echo -e "${GREEN}Certbot já está instalado.${NC}"
fi

# Criar diretório para os arquivos de configuração do Nginx se não existir
mkdir -p /etc/nginx/sites-available/
mkdir -p /etc/nginx/sites-enabled/

# Copiar o arquivo de configuração do Nginx
echo -e "${YELLOW}Copiando arquivo de configuração do Nginx...${NC}"
cp /home/giovano/Projetos/Chatwoot\ V4/nginx/webhook.conf /etc/nginx/sites-available/webhook.conf

# Criar link simbólico para habilitar o site
if [ ! -f /etc/nginx/sites-enabled/webhook.conf ]; then
    ln -s /etc/nginx/sites-available/webhook.conf /etc/nginx/sites-enabled/
    echo -e "${GREEN}Site habilitado no Nginx.${NC}"
else
    echo -e "${GREEN}Site já está habilitado no Nginx.${NC}"
fi

# Verificar a configuração do Nginx
echo -e "${YELLOW}Verificando a configuração do Nginx...${NC}"
nginx -t

if [ $? -ne 0 ]; then
    echo -e "${RED}Erro na configuração do Nginx. Por favor, verifique o arquivo de configuração.${NC}"
    exit 1
fi

# Reiniciar o Nginx
echo -e "${YELLOW}Reiniciando o Nginx...${NC}"
systemctl restart nginx

# Obter certificado SSL com Let's Encrypt
echo -e "${YELLOW}Obtendo certificado SSL com Let's Encrypt...${NC}"
certbot --nginx -d webhook.server.efetivia.com.br --non-interactive --agree-tos -m giovano.m.panatta@gmail.com

if [ $? -ne 0 ]; then
    echo -e "${RED}Erro ao obter certificado SSL. Verifique se o domínio está apontando corretamente para este servidor.${NC}"
    exit 1
fi

echo -e "${GREEN}=== Configuração concluída com sucesso! ===${NC}"
echo -e "Seu servidor webhook está configurado em: ${YELLOW}https://webhook.server.efetivia.com.br${NC}"
echo -e "Agora você pode configurar o Chatwoot para enviar webhooks para este endereço."
echo -e "${GREEN}Próximos passos:${NC}"
echo -e "1. Inicie o servidor webhook com: ${YELLOW}docker-compose up -d webhook_server${NC}"
echo -e "2. Configure o webhook no Chatwoot com a URL: ${YELLOW}https://webhook.server.efetivia.com.br/webhook${NC}"
