#!/bin/bash

# Script para executar a aplicação config-viewer

# Cores para saída
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Verificar se o ambiente virtual existe
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Ambiente virtual não encontrado. Criando...${NC}"
    python -m venv venv
fi

# Ativar o ambiente virtual
echo -e "${BLUE}Ativando ambiente virtual...${NC}"
source venv/bin/activate

# Instalar dependências
echo -e "${BLUE}Instalando dependências...${NC}"
pip install -r requirements.txt

# Verificar se o diretório static/css existe
if [ ! -d "static/css" ]; then
    echo -e "${YELLOW}Criando diretório static/css...${NC}"
    mkdir -p static/css
fi

# Gerar CSS para Pygments se não existir
if [ ! -f "static/css/pygments.css" ]; then
    echo -e "${YELLOW}Gerando CSS para Pygments...${NC}"
    pygmentize -S default -f html -a .highlight > static/css/pygments.css
fi

# Executar a aplicação
echo -e "${GREEN}Iniciando a aplicação...${NC}"
echo -e "${GREEN}Acesse a aplicação em: http://localhost:8080${NC}"
echo -e "${YELLOW}Use as credenciais fornecidas pelo administrador do sistema${NC}"
python app.py
