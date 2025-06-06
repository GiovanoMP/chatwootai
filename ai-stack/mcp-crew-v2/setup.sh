#!/bin/bash
# Script para configurar ambiente virtual e instalar dependências para testes do MCP Adapter

# Cores para saída no terminal
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
RED="\033[0;31m"
BLUE="\033[0;34m"
RESET="\033[0m"

echo -e "${BLUE}==================================================${RESET}"
echo -e "${BLUE}== Configuração do Ambiente para MCP Crew V2    ==${RESET}"
echo -e "${BLUE}==================================================${RESET}"

# Verifica se Python está instalado
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 não encontrado. Por favor, instale o Python 3.${RESET}"
    exit 1
fi

# Cria ambiente virtual se não existir
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}⚠️ Ambiente virtual não encontrado. Criando...${RESET}"
    python3 -m venv venv
    echo -e "${GREEN}✅ Ambiente virtual criado com sucesso!${RESET}"
else
    echo -e "${GREEN}✅ Ambiente virtual já existe.${RESET}"
fi

# Ativa o ambiente virtual
echo -e "${BLUE}ℹ️ Ativando ambiente virtual...${RESET}"
source venv/bin/activate

# Instala dependências
echo -e "${BLUE}ℹ️ Instalando dependências...${RESET}"
pip install --upgrade pip
pip install crewai
pip install crewai-tools[mcp]

echo -e "${GREEN}✅ Dependências instaladas com sucesso!${RESET}"

# Torna o script de teste executável
chmod +x test_mcp_adapter.py

echo -e "${BLUE}==================================================${RESET}"
echo -e "${GREEN}✅ Ambiente configurado com sucesso!${RESET}"
echo -e "${BLUE}==================================================${RESET}"
echo -e "${YELLOW}Para ativar o ambiente virtual, execute:${RESET}"
echo -e "  source venv/bin/activate"
echo -e "${YELLOW}Para executar o teste, execute:${RESET}"
echo -e "  ./test_mcp_adapter.py"
echo -e "${BLUE}==================================================${RESET}"
