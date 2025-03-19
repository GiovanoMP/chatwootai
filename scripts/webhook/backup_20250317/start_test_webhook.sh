#!/bin/bash

# Diretório do projeto
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

# Instalar dependências necessárias
pip install fastapi uvicorn requests python-dotenv

# Iniciar o servidor webhook
echo "Iniciando o servidor webhook de teste na porta 8001..."
echo "Pressione Ctrl+C para parar o servidor."
python test_webhook_server.py
