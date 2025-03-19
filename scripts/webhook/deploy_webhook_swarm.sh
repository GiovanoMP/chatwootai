#!/bin/bash

# Script para implantar o servidor webhook no Docker Swarm
# Autor: Cascade AI
# Data: 2025-03-16

# Definir cores para melhor legibilidade
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Implantando Servidor Webhook no Docker Swarm ===${NC}"

# Verificar se o Docker está instalado
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker não está instalado. Por favor, instale o Docker primeiro.${NC}"
    exit 1
fi

# Verificar se o Docker Swarm está inicializado
SWARM_STATUS=$(docker info --format '{{.Swarm.LocalNodeState}}')
if [ "$SWARM_STATUS" != "active" ]; then
    echo -e "${YELLOW}Docker Swarm não está ativo. Inicializando...${NC}"
    docker swarm init --advertise-addr $(hostname -I | awk '{print $1}')
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}Falha ao inicializar o Docker Swarm. Verifique se o servidor tem um IP válido.${NC}"
        exit 1
    fi
fi

# Verificar se o arquivo .env existe
if [ ! -f .env ]; then
    echo -e "${YELLOW}Arquivo .env não encontrado. Criando arquivo com valores padrão...${NC}"
    
    cat > .env << EOF
# Configurações do Chatwoot
CHATWOOT_API_KEY=seu_api_key_aqui
CHATWOOT_BASE_URL=http://chatwoot_web:3000/api/v1
CHATWOOT_ACCOUNT_ID=1

# Configurações do Webhook
WEBHOOK_PORT=8001
WEBHOOK_AUTH_TOKEN=efetivia_webhook_secret_token_2025

# Configurações do Docker
DOCKER_IMAGE=chatwootai:latest
EOF
    
    echo -e "${YELLOW}Arquivo .env criado. Por favor, edite-o com suas configurações reais antes de continuar.${NC}"
    echo -e "${YELLOW}Pressione Enter para continuar ou Ctrl+C para cancelar...${NC}"
    read
fi

# Verificar se o arquivo docker-stack.yml existe
if [ ! -f docker-stack.yml ]; then
    echo -e "${RED}Arquivo docker-stack.yml não encontrado. Verifique se você está no diretório correto.${NC}"
    exit 1
fi

# Criar a rede overlay se não existir
NETWORK_EXISTS=$(docker network ls --filter name=chatwoot_network --format '{{.Name}}')
if [ -z "$NETWORK_EXISTS" ]; then
    echo -e "${YELLOW}Criando rede overlay 'chatwoot_network'...${NC}"
    docker network create --driver overlay --attachable chatwoot_network
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}Falha ao criar a rede overlay. Verifique as permissões do Docker.${NC}"
        exit 1
    fi
fi

# Implantar o stack no Docker Swarm
echo -e "${YELLOW}Implantando o servidor webhook no Docker Swarm...${NC}"
docker stack deploy -c docker-stack.yml chatwootai

if [ $? -ne 0 ]; then
    echo -e "${RED}Falha ao implantar o stack. Verifique o arquivo docker-stack.yml e as configurações do Docker.${NC}"
    exit 1
fi

# Verificar o status do serviço
echo -e "${YELLOW}Verificando o status do serviço...${NC}"
sleep 5
docker service ls --filter name=chatwootai_webhook_server

# Exibir logs do serviço
echo -e "${YELLOW}Exibindo logs do serviço (pressione Ctrl+C para sair)...${NC}"
docker service logs -f chatwootai_webhook_server

echo -e "${GREEN}=== Servidor Webhook implantado com sucesso! ===${NC}"
echo -e "O servidor webhook agora está em execução no Docker Swarm."
echo -e "Para verificar o status do serviço, execute: docker service ls"
echo -e "Para visualizar os logs, execute: docker service logs -f chatwootai_webhook_server"
