#!/bin/bash

# Cores para feedback visual
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}📡 Verificando rede ai-stack...${NC}"

# Verificar se a rede ai-stack existe, se não, criar
if ! docker network inspect ai-stack >/dev/null 2>&1; then
    echo -e "${YELLOW}🔨 Criando rede ai-stack...${NC}"
    docker network create ai-stack
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Rede ai-stack criada com sucesso!${NC}"
    else
        echo -e "${RED}❌ Falha ao criar rede ai-stack!${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✅ Rede ai-stack já existe!${NC}"
fi
