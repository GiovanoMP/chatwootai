#!/bin/bash

# Script para verificar o status do servidor webhook no Docker Swarm
# Autor: Cascade AI
# Data: 2025-03-16

# Definir cores para melhor legibilidade
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Verificando Status do Servidor Webhook no Docker Swarm ===${NC}"

# Verificar se o Docker está instalado
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker não está instalado. Por favor, instale o Docker primeiro.${NC}"
    exit 1
fi

# Verificar se o Docker Swarm está ativo
SWARM_STATUS=$(docker info --format '{{.Swarm.LocalNodeState}}')
if [ "$SWARM_STATUS" != "active" ]; then
    echo -e "${RED}Docker Swarm não está ativo. Execute 'docker swarm init' para inicializar.${NC}"
    exit 1
fi

# Verificar se o serviço existe
SERVICE_EXISTS=$(docker service ls --filter name=chatwootai_webhook_server --format '{{.Name}}')
if [ -z "$SERVICE_EXISTS" ]; then
    echo -e "${RED}Serviço webhook não encontrado. Execute o script deploy_webhook_swarm.sh primeiro.${NC}"
    exit 1
fi

# Verificar o status do serviço
echo -e "${YELLOW}Status do serviço:${NC}"
docker service ls --filter name=chatwootai_webhook_server

# Verificar as réplicas do serviço
REPLICAS=$(docker service ps chatwootai_webhook_server --format '{{.Name}}\t{{.Node}}\t{{.CurrentState}}')
echo -e "\n${YELLOW}Réplicas do serviço:${NC}"
echo -e "NOME\tNÓ\tESTADO"
echo -e "$REPLICAS"

# Verificar logs do serviço
echo -e "\n${YELLOW}Últimas 10 linhas de log:${NC}"
docker service logs --tail 10 chatwootai_webhook_server

# Verificar a saúde do serviço
echo -e "\n${YELLOW}Verificando a saúde do serviço...${NC}"

# Obter o ID do contêiner
CONTAINER_ID=$(docker ps --filter name=chatwootai_webhook_server --format '{{.ID}}')

if [ -z "$CONTAINER_ID" ]; then
    echo -e "${RED}Contêiner do webhook não encontrado. O serviço pode estar com problemas.${NC}"
else
    # Verificar o endpoint de saúde
    HEALTH_CHECK=$(docker exec $CONTAINER_ID curl -s http://localhost:8001/health)
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}Falha ao verificar o endpoint de saúde. O serviço pode estar com problemas.${NC}"
    else
        echo -e "${GREEN}Resposta do endpoint de saúde:${NC}"
        echo $HEALTH_CHECK | python -m json.tool
    fi
fi

# Verificar conectividade com o Chatwoot
echo -e "\n${YELLOW}Verificando conectividade com o Chatwoot...${NC}"

# Verificar se o serviço do Chatwoot existe
CHATWOOT_SERVICE=$(docker service ls --filter name=chatwoot_web --format '{{.Name}}')
if [ -z "$CHATWOOT_SERVICE" ]; then
    echo -e "${YELLOW}Serviço do Chatwoot não encontrado no Docker Swarm.${NC}"
    echo -e "${YELLOW}Verifique se o Chatwoot está configurado corretamente.${NC}"
else
    echo -e "${GREEN}Serviço do Chatwoot encontrado: $CHATWOOT_SERVICE${NC}"
    
    # Verificar conectividade de rede
    if [ ! -z "$CONTAINER_ID" ]; then
        echo -e "${YELLOW}Testando conectividade de rede com o Chatwoot...${NC}"
        PING_RESULT=$(docker exec $CONTAINER_ID ping -c 1 chatwoot_web 2>&1)
        
        if [[ $PING_RESULT == *"1 received"* ]]; then
            echo -e "${GREEN}Conectividade de rede OK!${NC}"
        else
            echo -e "${RED}Falha na conectividade de rede com o Chatwoot.${NC}"
            echo -e "${RED}Verifique se ambos os serviços estão na mesma rede overlay.${NC}"
        fi
    fi
fi

echo -e "\n${GREEN}=== Verificação concluída! ===${NC}"
echo -e "Para mais detalhes, execute: docker service logs -f chatwootai_webhook_server"
