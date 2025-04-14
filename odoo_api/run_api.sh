#!/bin/bash

# Script para iniciar a API

# Verificar se uvicorn está instalado
if ! command -v uvicorn &> /dev/null; then
    echo "uvicorn não encontrado. Instalando..."
    pip install uvicorn
fi

# Verificar se o arquivo .env existe
if [ ! -f .env ]; then
    echo "Arquivo .env não encontrado. Criando a partir de .env.example..."
    cp .env.example .env
    echo "Por favor, edite o arquivo .env com suas configurações antes de continuar."
    exit 1
fi

# Iniciar a API
echo "Iniciando a API..."
uvicorn main:app --reload --host 0.0.0.0 --port 8000
