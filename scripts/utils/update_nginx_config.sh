#!/bin/bash

# Script para atualizar a configuração do Nginx com o IP real do Chatwoot
# Autor: Cascade AI
# Data: 2025-03-16

# Definir cores para melhor legibilidade
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Atualizando Configuração do Nginx para o Webhook ===${NC}"

# Verificar se está sendo executado como root
if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}Por favor, execute este script como root (sudo)${NC}"
  exit 1
fi

# Verificar se o arquivo de configuração existe
NGINX_CONFIG="/home/giovano/Projetos/Chatwoot V4/nginx/webhook.conf"
if [ ! -f "$NGINX_CONFIG" ]; then
    echo -e "${RED}Arquivo de configuração do Nginx não encontrado: $NGINX_CONFIG${NC}"
    exit 1
fi

# Solicitar o IP do Chatwoot
echo -e "${YELLOW}Digite o IP do servidor Chatwoot:${NC}"
read -p "> " CHATWOOT_IP

# Validar o formato do IP
if [[ ! $CHATWOOT_IP =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo -e "${RED}Formato de IP inválido. Por favor, digite um IP válido (ex: 192.168.1.100)${NC}"
    exit 1
fi

# Solicitar o IP do sistema Odoo (opcional)
echo -e "${YELLOW}Digite o IP do sistema Odoo (deixe em branco se não tiver):${NC}"
read -p "> " ODOO_IP

# Validar o formato do IP do Odoo se não estiver em branco
if [ ! -z "$ODOO_IP" ] && [[ ! $ODOO_IP =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo -e "${RED}Formato de IP inválido. Por favor, digite um IP válido (ex: 192.168.1.100)${NC}"
    exit 1
fi

echo -e "${YELLOW}Atualizando a configuração do Nginx...${NC}"

# Criar backup do arquivo original
cp "$NGINX_CONFIG" "${NGINX_CONFIG}.bak"
echo -e "${GREEN}Backup criado: ${NGINX_CONFIG}.bak${NC}"

# Atualizar a configuração do Nginx
if [ -z "$ODOO_IP" ]; then
    # Se o IP do Odoo não foi fornecido
    sed -i "s/allow IP_DO_CHATWOOT;/allow $CHATWOOT_IP;/g" "$NGINX_CONFIG"
    sed -i "s/allow IP_DO_ODOO;/#allow IP_DO_ODOO;/g" "$NGINX_CONFIG"
else
    # Se o IP do Odoo foi fornecido
    sed -i "s/allow IP_DO_CHATWOOT;/allow $CHATWOOT_IP;/g" "$NGINX_CONFIG"
    sed -i "s/allow IP_DO_ODOO;/allow $ODOO_IP;/g" "$NGINX_CONFIG"
fi

echo -e "${GREEN}Configuração atualizada com sucesso!${NC}"

# Verificar a configuração do Nginx
echo -e "${YELLOW}Verificando a configuração do Nginx...${NC}"
nginx -t

if [ $? -ne 0 ]; then
    echo -e "${RED}Erro na configuração do Nginx. Restaurando backup...${NC}"
    cp "${NGINX_CONFIG}.bak" "$NGINX_CONFIG"
    echo -e "${YELLOW}Backup restaurado. Por favor, verifique o arquivo de configuração manualmente.${NC}"
    exit 1
fi

# Reiniciar o Nginx
echo -e "${YELLOW}Reiniciando o Nginx...${NC}"
systemctl restart nginx

if [ $? -ne 0 ]; then
    echo -e "${RED}Erro ao reiniciar o Nginx. Por favor, verifique o status do serviço.${NC}"
    exit 1
fi

echo -e "${GREEN}=== Configuração do Nginx atualizada com sucesso! ===${NC}"
echo -e "O Nginx agora está configurado para aceitar conexões apenas dos seguintes IPs:"
echo -e "- Localhost (127.0.0.1)"
echo -e "- Chatwoot: ${CHATWOOT_IP}"
if [ ! -z "$ODOO_IP" ]; then
    echo -e "- Odoo: ${ODOO_IP}"
fi

echo -e "\n${YELLOW}Próximos passos:${NC}"
echo -e "1. Execute o script setup_webhook_ssl.sh para configurar o SSL"
echo -e "2. Inicie o servidor webhook com o script start_webhook.sh"
echo -e "3. Configure o webhook no Chatwoot com a URL e o token de autenticação"
