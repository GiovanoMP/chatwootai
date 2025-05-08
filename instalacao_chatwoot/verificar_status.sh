#!/bin/bash

# Cores para melhor visualização
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Status dos Serviços ===${NC}"

# Verificar serviços Docker
echo -e "${YELLOW}Serviços em execução:${NC}"
docker service ls

echo -e "\n${YELLOW}Detalhes dos contêineres:${NC}"
docker ps

echo -e "\n${BLUE}=== Logs do Chatwoot ===${NC}"
CHATWOOT_CONTAINER=$(docker ps | grep chatwoot_app | awk '{print $1}')
if [ -n "$CHATWOOT_CONTAINER" ]; then
    docker logs --tail 50 $CHATWOOT_CONTAINER
else
    echo -e "${RED}Contêiner do Chatwoot não encontrado.${NC}"
fi

echo -e "\n${BLUE}=== Logs da Evolution API ===${NC}"
EVOLUTION_CONTAINER=$(docker ps | grep evolution_v2 | awk '{print $1}')
if [ -n "$EVOLUTION_CONTAINER" ]; then
    docker logs --tail 50 $EVOLUTION_CONTAINER
else
    echo -e "${RED}Contêiner da Evolution API não encontrado.${NC}"
fi

echo -e "\n${BLUE}=== Verificação de Conectividade ===${NC}"
echo -e "${YELLOW}Testando conexão com o Chatwoot:${NC}"
curl -s -o /dev/null -w "%{http_code}" https://chat.sprintia.com.br || echo "Falha na conexão"

echo -e "\n${YELLOW}Testando conexão com a Evolution API:${NC}"
curl -s -o /dev/null -w "%{http_code}" https://evolution.sprintia.com.br || echo "Falha na conexão"

echo -e "\n${GREEN}=== Verificação concluída! ===${NC}"
