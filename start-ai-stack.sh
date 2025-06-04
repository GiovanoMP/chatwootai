#!/bin/bash
# Script para iniciar toda a stack de IA

# Cores para melhor visualização
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Iniciando AI Stack Unificada ===${NC}"

# Verificar se o Docker está rodando
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}Docker não está rodando. Por favor, inicie o Docker e tente novamente.${NC}"
    exit 1
fi

# Verificar se o diretório de inicialização do MongoDB existe
if [ ! -d "./mongodb-init" ]; then
    echo -e "${YELLOW}Criando diretório para scripts de inicialização do MongoDB...${NC}"
    mkdir -p ./mongodb-init
    
    # Criar script de inicialização para o MongoDB
    cat > ./mongodb-init/init-mongo.js << EOF
db = db.getSiblingDB('config_service');

db.createUser({
  user: 'config_user',
  pwd: 'config_password',
  roles: [{ role: 'readWrite', db: 'config_service' }]
});

// Criar coleções iniciais
db.createCollection('company_services');
db.createCollection('tenants');
db.createCollection('configurations');

// Inserir dados iniciais
db.tenants.insertOne({
  account_id: 'account_1',
  name: 'Tenant Padrão',
  active: true,
  created_at: new Date()
});
EOF
    echo -e "${GREEN}Script de inicialização do MongoDB criado com sucesso!${NC}"
fi

# Construir e iniciar os contêineres
echo -e "${YELLOW}Construindo e iniciando contêineres...${NC}"
docker-compose -f docker-compose.ai-stack.yml up -d --build

# Verificar status dos serviços após inicialização
echo -e "\n${BLUE}=== Verificando status dos serviços ===${NC}"
sleep 10

# Função para verificar status de um serviço
check_service() {
    local service_name=$1
    local container_name=$2
    
    if [ "$(docker ps -q -f name=$container_name)" ]; then
        echo -e "${GREEN}✓ $service_name está rodando${NC}"
        return 0
    else
        echo -e "${RED}✗ $service_name não está rodando${NC}"
        return 1
    fi
}

# Verificar todos os serviços
check_service "MongoDB" "ai-mongodb"
check_service "MongoDB Express" "ai-mongo-express"
check_service "Redis" "ai-redis"
check_service "Qdrant" "ai-qdrant"
check_service "MCP-MongoDB" "mcp-mongodb"
check_service "MCP-Qdrant" "mcp-qdrant"
check_service "MCP-Crew" "mcp-crew"

# Mostrar URLs de acesso
echo -e "\n${BLUE}=== URLs de acesso ===${NC}"
echo -e "${YELLOW}MongoDB Express:${NC} http://localhost:8082"
echo -e "${YELLOW}MCP-Crew API:${NC} http://localhost:5000"
echo -e "${YELLOW}MCP-MongoDB API:${NC} http://localhost:8001"
echo -e "${YELLOW}MCP-Qdrant API:${NC} http://localhost:8002"
echo -e "${YELLOW}Qdrant UI:${NC} http://localhost:6333/dashboard"

echo -e "\n${BLUE}=== Comandos úteis ===${NC}"
echo -e "${YELLOW}Para ver logs:${NC} docker-compose -f docker-compose.ai-stack.yml logs -f"
echo -e "${YELLOW}Para ver logs de um serviço específico:${NC} docker-compose -f docker-compose.ai-stack.yml logs -f [serviço]"
echo -e "${YELLOW}Para parar a stack:${NC} docker-compose -f docker-compose.ai-stack.yml down"
echo -e "${YELLOW}Para reiniciar um serviço:${NC} docker-compose -f docker-compose.ai-stack.yml restart [serviço]"
echo -e "${YELLOW}Para limpar volumes (CUIDADO - apaga dados):${NC} docker-compose -f docker-compose.ai-stack.yml down -v"

echo -e "\n${GREEN}AI Stack Unificada iniciada com sucesso!${NC}"
