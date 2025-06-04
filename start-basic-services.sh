#!/bin/bash

# Cores para saída
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Iniciando serviços básicos da AI Stack ===${NC}"

# Criar diretório para scripts de inicialização do MongoDB
mkdir -p mongo-init

# Criar script de inicialização para MongoDB
cat > mongo-init/init-mongo.js <<EOF
// Criar usuário para o banco de dados
db.createUser({
  user: 'mcp_user',
  pwd: 'mcp_password',
  roles: [
    { role: 'readWrite', db: 'mcp_database' }
  ]
});

// Criar banco de dados e coleções iniciais
db = db.getSiblingDB('mcp_database');
db.createCollection('tenants');
db.createCollection('crews');
db.createCollection('agents');
db.createCollection('contexts');
EOF

echo -e "${GREEN}Scripts de inicialização do MongoDB criados com sucesso.${NC}"

# Iniciar contêineres
echo -e "${BLUE}Construindo e iniciando contêineres...${NC}"
docker-compose -f docker-compose.basic-services.yml up -d

# Aguardar inicialização
echo -e "${BLUE}Aguardando inicialização dos serviços...${NC}"
sleep 10

# Verificar status dos serviços
echo -e "${BLUE}=== Verificando status dos serviços ===${NC}"

check_container() {
  local container_name=$1
  if [ "$(docker ps -q -f name=$container_name)" ]; then
    echo -e "✅ ${GREEN}$container_name está rodando${NC}"
    return 0
  else
    echo -e "❌ ${RED}$container_name não está rodando${NC}"
    return 1
  fi
}

check_container "ai-mongodb"
check_container "ai-mongo-express"
check_container "ai-redis"
check_container "ai-qdrant"

# Exibir URLs de acesso
echo -e "${BLUE}=== URLs de acesso ===${NC}"
echo -e "MongoDB Express: ${GREEN}http://localhost:8082${NC}"
echo -e "Qdrant UI: ${GREEN}http://localhost:6333/dashboard${NC}"

# Exibir comandos úteis
echo -e "${BLUE}=== Comandos úteis ===${NC}"
echo -e "Para ver logs: ${GREEN}docker-compose -f docker-compose.basic-services.yml logs -f${NC}"
echo -e "Para ver logs de um serviço específico: ${GREEN}docker-compose -f docker-compose.basic-services.yml logs -f [serviço]${NC}"
echo -e "Para parar a stack: ${GREEN}docker-compose -f docker-compose.basic-services.yml down${NC}"
echo -e "Para reiniciar um serviço: ${GREEN}docker-compose -f docker-compose.basic-services.yml restart [serviço]${NC}"
echo -e "Para limpar volumes (CUIDADO - apaga dados): ${GREEN}docker-compose -f docker-compose.basic-services.yml down -v${NC}"

echo -e "${GREEN}Serviços básicos da AI Stack iniciados com sucesso!${NC}"
