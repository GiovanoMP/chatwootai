#!/bin/bash

# Script para iniciar o servidor webhook
# Autor: Cascade AI
# Data: 2025-03-16

# Definir cores para melhor legibilidade
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Iniciando o Servidor Webhook ===${NC}"

# Verificar se o arquivo .env existe
if [ ! -f "/home/giovano/Projetos/Chatwoot V4/.env" ]; then
    echo -e "${RED}Arquivo .env não encontrado. Por favor, verifique se você está no diretório correto.${NC}"
    exit 1
fi

# Navegar até o diretório do projeto
cd /home/giovano/Projetos/Chatwoot\ V4

# Verificar se o Docker está em execução
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}Docker não está em execução. Por favor, inicie o Docker e tente novamente.${NC}"
    exit 1
fi

# Iniciar o servidor webhook
echo -e "${YELLOW}Iniciando o servidor webhook...${NC}"
docker-compose up -d webhook_server

# Verificar se o servidor webhook foi iniciado com sucesso
if [ $? -ne 0 ]; then
    echo -e "${RED}Erro ao iniciar o servidor webhook. Verifique os logs para mais detalhes.${NC}"
    exit 1
fi

# Exibir os logs do servidor webhook
echo -e "${YELLOW}Exibindo os logs do servidor webhook...${NC}"
docker-compose logs -f webhook_server

# Este script não terminará automaticamente, pois o comando logs -f continua exibindo os logs
# Para sair, pressione Ctrl+C
