#!/bin/bash

# Script para configurar e iniciar o servidor MCP Mercado Livre

# Criar ambiente virtual
echo "Criando ambiente virtual..."
python3 -m venv venv
source venv/bin/activate

# Instalar dependências
echo "Instalando dependências..."
pip install -r requirements.txt

# Verificar se o arquivo .env existe
if [ ! -f .env ]; then
    echo "Arquivo .env não encontrado. Criando a partir do exemplo..."
    cp .env.example .env
    echo "Por favor, edite o arquivo .env com suas credenciais antes de iniciar o servidor."
    exit 1
fi

# Iniciar o servidor
echo "Iniciando o servidor MCP Mercado Livre..."
python src/main.py
