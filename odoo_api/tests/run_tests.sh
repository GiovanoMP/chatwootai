#!/bin/bash

# Script para executar os testes da API

# Cores para saída
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Diretório base
BASE_DIR=$(dirname "$0")
cd "$BASE_DIR/.."

echo -e "${YELLOW}Verificando ambiente...${NC}"
python -m tests.check_environment

if [ $? -ne 0 ]; then
    echo -e "${RED}Verificação de ambiente falhou!${NC}"
    exit 1
fi

# Executar testes unitários
echo -e "${YELLOW}Executando testes unitários...${NC}"
python -m unittest discover -s tests/unit -p "test_*.py"

if [ $? -ne 0 ]; then
    echo -e "${RED}Testes unitários falharam!${NC}"
    exit 1
fi

echo -e "${GREEN}Testes unitários executados com sucesso!${NC}"

# Executar testes de integração
echo -e "${YELLOW}Executando testes de integração...${NC}"
python -m unittest discover -s tests/integration -p "test_*.py"

if [ $? -ne 0 ]; then
    echo -e "${RED}Testes de integração falharam!${NC}"
    exit 1
fi

echo -e "${GREEN}Testes de integração executados com sucesso!${NC}"

echo -e "${GREEN}Todos os testes foram executados com sucesso!${NC}"
exit 0
