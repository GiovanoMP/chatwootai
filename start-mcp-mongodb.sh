#!/bin/bash

# Cores para saída
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Iniciando MCP-MongoDB ===${NC}"

# Verificar se a rede ai_network existe
if ! docker network inspect ai_network &>/dev/null; then
  echo -e "${RED}A rede ai_network não existe. Execute primeiro o script start-basic-services.sh${NC}"
  exit 1
fi

# Verificar se o MongoDB está rodando
if ! docker ps | grep -q "ai-mongodb"; then
  echo -e "${RED}MongoDB não está rodando. Execute primeiro o script start-basic-services.sh${NC}"
  exit 1
fi

# Iniciar MCP-MongoDB
echo -e "${BLUE}Construindo e iniciando MCP-MongoDB...${NC}"
docker-compose -f docker-compose.mcp-mongodb-only.yml up -d

# Aguardar inicialização
echo -e "${BLUE}Aguardando inicialização do MCP-MongoDB...${NC}"
sleep 5

# Verificar status do MCP-MongoDB
echo -e "${BLUE}=== Verificando status do MCP-MongoDB ===${NC}"
if [ "$(docker ps -q -f name=ai-mcp-mongodb)" ]; then
  echo -e "✅ ${GREEN}MCP-MongoDB está rodando${NC}"
else
  echo -e "❌ ${RED}MCP-MongoDB não está rodando${NC}"
  echo -e "${RED}Verificando logs do MCP-MongoDB:${NC}"
  docker-compose -f docker-compose.mcp-mongodb-only.yml logs mcp-mongodb
  exit 1
fi

# Exibir URLs de acesso
echo -e "${BLUE}=== URLs de acesso ===${NC}"
echo -e "MCP-MongoDB API: ${GREEN}http://localhost:8001${NC}"

# Exibir comandos úteis
echo -e "${BLUE}=== Comandos úteis ===${NC}"
echo -e "Para ver logs: ${GREEN}docker-compose -f docker-compose.mcp-mongodb-only.yml logs -f${NC}"
echo -e "Para parar o MCP-MongoDB: ${GREEN}docker-compose -f docker-compose.mcp-mongodb-only.yml down${NC}"
echo -e "Para reiniciar o MCP-MongoDB: ${GREEN}docker-compose -f docker-compose.mcp-mongodb-only.yml restart mcp-mongodb${NC}"

echo -e "${GREEN}MCP-MongoDB iniciado com sucesso!${NC}"
