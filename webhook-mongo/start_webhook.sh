#!/bin/bash

# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Iniciando webhook-mongo...${NC}"

# Verificar se o Python está instalado
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 não está instalado. Por favor, instale o Python 3 antes de continuar.${NC}"
    exit 1
fi

# Verificar se o pip está instalado
if ! command -v pip3 &> /dev/null; then
    echo -e "${RED}pip3 não está instalado. Por favor, instale o pip3 antes de continuar.${NC}"
    exit 1
fi

# Verificar se as dependências estão instaladas
echo -e "${GREEN}Verificando dependências...${NC}"
if ! pip3 freeze | grep -q "fastapi"; then
    echo -e "${YELLOW}Instalando dependências...${NC}"
    pip3 install -r requirements.txt
fi

# Carregar variáveis de ambiente
if [ -f .env ]; then
    echo -e "${GREEN}Carregando variáveis de ambiente de .env...${NC}"
    export $(grep -v '^#' .env | xargs)
else
    echo -e "${YELLOW}Arquivo .env não encontrado. Usando valores padrão.${NC}"
    # Criar arquivo .env a partir do .env.example
    if [ -f .env.example ]; then
        echo -e "${YELLOW}Criando arquivo .env a partir do .env.example...${NC}"
        cp .env.example .env
        export $(grep -v '^#' .env | xargs)
    fi
fi

# Verificar se o MongoDB está rodando
echo -e "${GREEN}Verificando conexão com o MongoDB...${NC}"
if ! nc -z localhost 27017 &> /dev/null; then
    echo -e "${RED}MongoDB não está rodando. Por favor, inicie o MongoDB antes de continuar.${NC}"
    echo -e "${YELLOW}Você pode iniciar o MongoDB com Docker usando:${NC}"
    echo -e "${YELLOW}cd ../mongo-config-service && ./start-services.sh${NC}"
    exit 1
fi

# Iniciar o servidor
echo -e "${GREEN}Iniciando servidor webhook-mongo...${NC}"
python3 app.py
