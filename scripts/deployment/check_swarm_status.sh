#!/bin/bash

# Script para verificar o status do Docker Swarm
# Autor: Cascade AI
# Data: 2025-03-16

# Definir cores para melhor legibilidade
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Verificando Status do Docker Swarm ===${NC}"

# Verificar se o Docker está instalado
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker não está instalado. Por favor, instale o Docker primeiro.${NC}"
    exit 1
fi

# Verificar se o Swarm está inicializado
echo -e "${YELLOW}Verificando se o Swarm está inicializado...${NC}"
SWARM_STATUS=$(docker info | grep -i "swarm" | grep -i "active" | wc -l)

if [ "$SWARM_STATUS" -eq 0 ]; then
    echo -e "${RED}Docker Swarm não está inicializado neste nó.${NC}"
    echo -e "${YELLOW}Para inicializar o Swarm, execute:${NC}"
    echo -e "docker swarm init"
    exit 1
else
    echo -e "${GREEN}Docker Swarm está ativo neste nó.${NC}"
fi

# Listar os nós do Swarm
echo -e "\n${YELLOW}Nós do Swarm:${NC}"
docker node ls

# Listar os serviços do Swarm
echo -e "\n${YELLOW}Serviços do Swarm:${NC}"
docker service ls

# Listar as redes do Swarm
echo -e "\n${YELLOW}Redes do Swarm:${NC}"
docker network ls | grep -i "overlay"

# Listar os stacks do Swarm
echo -e "\n${YELLOW}Stacks do Swarm:${NC}"
docker stack ls

# Para cada stack, listar seus serviços
STACKS=$(docker stack ls --format "{{.Name}}")
for STACK in $STACKS; do
    echo -e "\n${YELLOW}Serviços do stack $STACK:${NC}"
    docker stack services $STACK
done

# Verificar logs dos serviços (últimas 10 linhas)
echo -e "\n${YELLOW}Deseja ver os logs de algum serviço específico? (s/n)${NC}"
read -p "> " VIEW_LOGS

if [[ $VIEW_LOGS == "s" || $VIEW_LOGS == "S" ]]; then
    echo -e "${YELLOW}Digite o nome do serviço:${NC}"
    read -p "> " SERVICE_NAME
    
    echo -e "\n${YELLOW}Logs do serviço $SERVICE_NAME (últimas 10 linhas):${NC}"
    docker service logs --tail 10 $SERVICE_NAME
fi

echo -e "\n${GREEN}=== Verificação concluída! ===${NC}"
