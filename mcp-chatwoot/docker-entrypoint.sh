#!/bin/bash

# Cores para saída
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Iniciando MCP-Chatwoot ===${NC}"

# Verificar variáveis de ambiente obrigatórias
if [ -z "$CHATWOOT_ACCESS_TOKEN" ]; then
    echo -e "${RED}ERRO: CHATWOOT_ACCESS_TOKEN não definido${NC}"
    echo -e "${YELLOW}Configure as variáveis de ambiente necessárias no docker-compose.yml${NC}"
    exit 1
fi

# Criar diretório de logs se não existir
mkdir -p /app/logs

# Iniciar o servidor
echo -e "${GREEN}Iniciando servidor na porta $MCP_PORT...${NC}"
exec uvicorn main:app --host $MCP_HOST --port $MCP_PORT
