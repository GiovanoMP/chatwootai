#!/bin/bash

# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Iniciando serviços MongoDB...${NC}"

# Verificar se o Docker está instalado
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker não está instalado. Por favor, instale o Docker antes de continuar.${NC}"
    exit 1
fi

# Verificar se o Docker Compose está instalado
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Docker Compose não está instalado. Por favor, instale o Docker Compose antes de continuar.${NC}"
    exit 1
fi

# Carregar variáveis de ambiente
if [ -f .env ]; then
    echo -e "${GREEN}Carregando variáveis de ambiente de .env...${NC}"
    export $(grep -v '^#' .env | xargs)
else
    echo -e "${YELLOW}Arquivo .env não encontrado. Usando valores padrão.${NC}"
fi

# Iniciar os serviços
echo -e "${GREEN}Iniciando serviços com Docker Compose...${NC}"
docker-compose up -d

# Verificar se os serviços estão rodando
echo -e "${YELLOW}Verificando status dos serviços...${NC}"
sleep 5

if docker ps | grep -q "chatwoot-mongodb"; then
    echo -e "${GREEN}✓ MongoDB está rodando${NC}"
else
    echo -e "${RED}✗ MongoDB não está rodando. Verifique os logs com 'docker logs chatwoot-mongodb'${NC}"
fi

if docker ps | grep -q "chatwoot-mongo-express"; then
    echo -e "${GREEN}✓ Mongo Express está rodando${NC}"
    echo -e "${GREEN}✓ Interface web disponível em: http://localhost:8082${NC}"
    echo -e "${YELLOW}  Usuário: ${MONGO_EXPRESS_USER:-admin}${NC}"
    echo -e "${YELLOW}  Senha: ${MONGO_EXPRESS_PASSWORD:-express_password}${NC}"
else
    echo -e "${RED}✗ Mongo Express não está rodando. Verifique os logs com 'docker logs chatwoot-mongo-express'${NC}"
fi

if docker ps | grep -q "chatwoot-webhook-mongo"; then
    echo -e "${GREEN}✓ Webhook MongoDB está rodando${NC}"
    echo -e "${GREEN}✓ API disponível em: http://localhost:8003${NC}"
    echo -e "${GREEN}✓ Documentação da API: http://localhost:8003/docs${NC}"
else
    echo -e "${RED}✗ Webhook MongoDB não está rodando. Verifique os logs com 'docker logs chatwoot-webhook-mongo'${NC}"
fi

echo -e "\n${GREEN}Configuração do MongoDB para o módulo company_services:${NC}"
echo -e "${YELLOW}URI de Conexão: mongodb://config_user:config_password@localhost:27017/config_service${NC}"
echo -e "${YELLOW}Banco de Dados: config_service${NC}"
echo -e "${YELLOW}Coleção: company_services${NC}"

echo -e "\n${GREEN}Para parar os serviços:${NC}"
echo -e "${YELLOW}docker-compose down${NC}"

echo -e "\n${GREEN}Para ver os logs:${NC}"
echo -e "${YELLOW}docker-compose logs -f${NC}"

echo -e "\n${GREEN}Configuração concluída!${NC}"
