#!/bin/bash

# Script para iniciar o ngrok
# Este script inicia o ngrok para expor o servidor unificado à internet

# Configurar diretório de logs
mkdir -p logs

# Iniciar o ngrok
echo -e "\n======================================================================="
echo "🚀 INICIANDO NGROK PARA SERVIDOR UNIFICADO"
echo "======================================================================="

# Verificar se o token do ngrok está configurado
if [ -z "$NGROK_AUTH_TOKEN" ]; then
    echo "❌ Token de autenticação do Ngrok não configurado"
    echo "Por favor, configure o token de autenticação do Ngrok no arquivo .env"
    exit 1
fi

# Verificar se o servidor está rodando
if ! curl -s http://localhost:8000/health > /dev/null; then
    echo "❌ Servidor unificado não está rodando"
    echo "Por favor, inicie o servidor unificado primeiro"
    exit 1
fi

# Iniciar o ngrok
echo "🔄 Iniciando Ngrok para a porta 8000..."
ngrok http 8000 --log=stdout
