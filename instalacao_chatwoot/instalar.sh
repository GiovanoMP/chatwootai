#!/bin/bash

# Cores para melhor visualização
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Script de Instalação do Chatwoot e Evolution API ===${NC}"
echo -e "${YELLOW}Este script irá remover a instalação atual e configurar uma nova.${NC}"
echo -e "${RED}ATENÇÃO: Todos os dados atuais serão perdidos!${NC}"
echo ""
read -p "Deseja continuar? (s/n): " confirm

if [[ $confirm != "s" && $confirm != "S" ]]; then
    echo -e "${RED}Instalação cancelada.${NC}"
    exit 1
fi

echo -e "${BLUE}=== Parando e removendo serviços atuais ===${NC}"

# Lista todos os serviços em execução
echo -e "${YELLOW}Serviços em execução:${NC}"
docker service ls

# Remover serviços existentes (adicione ou remova conforme necessário)
echo -e "${YELLOW}Removendo serviços...${NC}"
docker service rm chatwoot_app chatwoot_sidekiq evolution_v2 postgres redis traefik 2>/dev/null || true
echo -e "${GREEN}Serviços removidos.${NC}"

echo -e "${BLUE}=== Criando volumes necessários ===${NC}"
# Criar volumes necessários
docker volume create network_public 2>/dev/null || true
docker volume create volume_swarm_shared 2>/dev/null || true
docker volume create volume_swarm_certificates 2>/dev/null || true
docker volume create redis_data 2>/dev/null || true
docker volume create postgres_data 2>/dev/null || true
docker volume create chatwoot_data 2>/dev/null || true
docker volume create chatwoot_public 2>/dev/null || true
docker volume create evolution_instancesv2 2>/dev/null || true

echo -e "${GREEN}Volumes criados.${NC}"

echo -e "${BLUE}=== Criando rede Docker ===${NC}"
# Criar rede Docker
docker network create --driver overlay --attachable network_public 2>/dev/null || true
echo -e "${GREEN}Rede criada.${NC}"

echo -e "${BLUE}=== Implantando serviços ===${NC}"
# Implantar serviços na ordem correta
echo -e "${YELLOW}Implantando Traefik...${NC}"
docker stack deploy -c "1 - traefik.yaml" infra
echo -e "${GREEN}Traefik implantado.${NC}"

echo -e "${YELLOW}Implantando Portainer...${NC}"
docker stack deploy -c "2 - portainer.yaml" infra
echo -e "${GREEN}Portainer implantado.${NC}"

echo -e "${YELLOW}Implantando Redis...${NC}"
docker stack deploy -c "3 - redis.yaml" infra
echo -e "${GREEN}Redis implantado.${NC}"

echo -e "${YELLOW}Implantando PostgreSQL...${NC}"
docker stack deploy -c "4 - postgres.yaml" infra
echo -e "${GREEN}PostgreSQL implantado.${NC}"

echo -e "${YELLOW}Aguardando 30 segundos para o PostgreSQL iniciar...${NC}"
sleep 30

echo -e "${YELLOW}Implantando Chatwoot...${NC}"
docker stack deploy -c "5 - chatwoot_v4.yaml" infra
echo -e "${GREEN}Chatwoot implantado.${NC}"

echo -e "${YELLOW}Implantando Evolution API...${NC}"
docker stack deploy -c "6 - evolutionV2.yaml" infra
echo -e "${GREEN}Evolution API implantado.${NC}"

echo -e "${BLUE}=== Verificando serviços ===${NC}"
docker service ls

echo -e "${GREEN}=== Instalação concluída! ===${NC}"
echo -e "${YELLOW}Importante: Você precisa configurar o Chatwoot executando o seguinte comando:${NC}"
echo -e "${BLUE}docker exec -it \$(docker ps | grep chatwoot_app | awk '{print \$1}') bundle exec rails db:chatwoot_prepare${NC}"
echo -e "${YELLOW}Acesse o Chatwoot em:${NC} ${GREEN}https://chat.sprintia.com.br${NC}"
echo -e "${YELLOW}Acesse a Evolution API em:${NC} ${GREEN}https://evolution.sprintia.com.br${NC}"
