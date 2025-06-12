#!/bin/bash

# Cores para saída
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Script de Build e Execução do MCP-Chatwoot ===${NC}"

# Verificar se a rede ai-stack existe
if ! docker network inspect ai-stack &>/dev/null; then
    echo -e "${YELLOW}Rede ai-stack não encontrada. Criando...${NC}"
    docker network create ai-stack
    if [ $? -ne 0 ]; then
        echo -e "${RED}Erro ao criar a rede ai-stack${NC}"
        exit 1
    fi
    echo -e "${GREEN}Rede ai-stack criada com sucesso${NC}"
fi

# Verificar se o arquivo .env existe
if [ ! -f .env ]; then
    echo -e "${YELLOW}Arquivo .env não encontrado. Criando a partir do exemplo...${NC}"
    if [ -f .env.example ]; then
        cp .env.example .env
        echo -e "${GREEN}Arquivo .env criado. Por favor, edite-o com suas configurações reais.${NC}"
    else
        echo -e "${RED}Arquivo .env.example não encontrado. Não foi possível criar .env${NC}"
        exit 1
    fi
fi

# Construir a imagem
echo -e "${BLUE}Construindo a imagem do MCP-Chatwoot...${NC}"
docker-compose build
if [ $? -ne 0 ]; then
    echo -e "${RED}Erro ao construir a imagem${NC}"
    exit 1
fi
echo -e "${GREEN}Imagem construída com sucesso${NC}"

# Iniciar o contêiner
echo -e "${BLUE}Iniciando o contêiner MCP-Chatwoot...${NC}"
docker-compose up -d
if [ $? -ne 0 ]; then
    echo -e "${RED}Erro ao iniciar o contêiner${NC}"
    exit 1
fi

# Verificar se o contêiner está em execução
sleep 3
if docker-compose ps | grep -q "Up"; then
    echo -e "${GREEN}MCP-Chatwoot iniciado com sucesso!${NC}"
    echo -e "${BLUE}Endpoints disponíveis:${NC}"
    echo -e "  - API Principal: http://localhost:8004"
    echo -e "  - Health Check: http://localhost:8004/health"
    echo -e "  - Endpoint Webhook: http://localhost:8004/webhook"
    echo -e "  - Endpoint SSE: http://localhost:8004/messages/"
    echo -e "${YELLOW}Para visualizar os logs: docker-compose logs -f${NC}"
else
    echo -e "${RED}Erro: O contêiner não está em execução. Verifique os logs com: docker-compose logs${NC}"
    exit 1
fi
