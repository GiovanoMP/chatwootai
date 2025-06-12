#!/bin/bash

# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔍 Verificando conectividade entre serviços na rede Docker...${NC}"

# Verificar redes Docker
echo -e "${YELLOW}📊 Redes Docker disponíveis:${NC}"
docker network ls

# Verificar se a rede ai-stack existe
if ! docker network ls | grep -q ai-stack; then
    echo -e "${RED}❌ Rede ai-stack não encontrada. Criando...${NC}"
    docker network create ai-stack
    echo -e "${GREEN}✅ Rede ai-stack criada${NC}"
else
    echo -e "${GREEN}✅ Rede ai-stack já existe${NC}"
fi

# Listar contêineres na rede ai-stack
echo -e "${YELLOW}📋 Contêineres na rede ai-stack:${NC}"
docker network inspect ai-stack -f '{{range .Containers}}{{.Name}} {{end}}'
echo ""

# Verificar serviços em execução
echo -e "${YELLOW}📋 Serviços em execução:${NC}"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Função para testar conectividade entre contêineres
test_connectivity() {
    source_container=$1
    target_container=$2
    target_port=$3
    
    echo -e "${YELLOW}🔌 Testando conectividade de $source_container para $target_container:$target_port...${NC}"
    
    # Verificar se os contêineres existem
    if ! docker ps | grep -q $source_container; then
        echo -e "${RED}❌ Contêiner $source_container não está rodando${NC}"
        return 1
    fi
    
    if ! docker ps | grep -q $target_container; then
        echo -e "${RED}❌ Contêiner $target_container não está rodando${NC}"
        return 1
    fi
    
    # Instalar ferramentas de rede se necessário
    if ! docker exec $source_container which nc &>/dev/null; then
        echo -e "${YELLOW}⚠️ Netcat não encontrado em $source_container, instalando...${NC}"
        if docker exec $source_container which apt-get &>/dev/null; then
            docker exec $source_container apt-get update -qq
            docker exec $source_container apt-get install -y netcat-openbsd -qq
        elif docker exec $source_container which apk &>/dev/null; then
            docker exec $source_container apk add --no-cache netcat-openbsd
        else
            echo -e "${RED}❌ Não foi possível instalar netcat em $source_container${NC}"
            return 1
        fi
    fi
    
    # Testar conectividade usando netcat
    if docker exec $source_container nc -z -v $target_container $target_port 2>&1; then
        echo -e "${GREEN}✅ Conectividade OK: $source_container → $target_container:$target_port${NC}"
        return 0
    else
        echo -e "${RED}❌ Falha na conectividade: $source_container → $target_container:$target_port${NC}"
        return 1
    fi
}

# Testar conectividade entre serviços críticos
echo -e "${BLUE}🔄 Testando conectividade entre serviços críticos...${NC}"

# Lista de testes de conectividade (origem, destino, porta)
connectivity_tests=(
    "mcp-mongodb mongodb 27017"
    "mcp-qdrant qdrant 6333"
    "mcp-redis redis 6379"
)

# Adicionar mcp-chatwoot se estiver rodando
if docker ps | grep -q mcp-chatwoot; then
    connectivity_tests+=("mcp-chatwoot redis 6379")
    connectivity_tests+=("mcp-chatwoot mongodb 27017")
fi

# Executar testes de conectividade
for test in "${connectivity_tests[@]}"; do
    read -r source target port <<< "$test"
    test_connectivity $source $target $port
done

# Verificar status dos serviços
echo -e "${BLUE}🔍 Verificando status dos serviços...${NC}"
services=("ai-qdrant" "ai-mongodb" "ai-redis" "ai-mongo-express" "mcp-mongodb" "mcp-qdrant" "mcp-redis")

# Adicionar mcp-chatwoot se existir
if docker ps -a | grep -q mcp-chatwoot; then
    services+=("mcp-chatwoot")
fi

for service in "${services[@]}"; do
    if docker ps | grep -q $service; then
        status=$(docker inspect --format='{{.State.Status}}' $service)
        health_status=$(docker inspect --format='{{if .State.Health}}{{.State.Health.Status}}{{else}}N/A{{end}}' $service)
        echo -e "${YELLOW}$service${NC}: Status=$status, Health=$health_status"
        
        # Verificar logs recentes para serviços unhealthy
        if [ "$health_status" = "unhealthy" ]; then
            echo -e "${RED}⚠️ Serviço $service está unhealthy. Últimos logs:${NC}"
            docker logs --tail 10 $service
        fi
    else
        echo -e "${RED}❌ Serviço $service não está rodando${NC}"
    fi
done

echo -e "${GREEN}✅ Verificação de conectividade concluída${NC}"
