#!/bin/bash

# Script para iniciar o ngrok
# Este script inicia o ngrok para expor o servidor unificado à internet

# Configurar diretório de logs
mkdir -p logs

# Iniciar o ngrok
echo -e "\n======================================================================="
echo "🚀 INICIANDO NGROK PARA SERVIDOR UNIFICADO"
echo "======================================================================="

# Carregar variáveis de ambiente do arquivo .env
if [ -f ".env" ]; then
    echo "📁 Carregando variáveis de ambiente de .env"
    set -a  # Ativa o modo de exportação automática
    source .env
    set +a  # Desativa o modo de exportação automática

    # Verificar se a variável foi carregada
    echo "Valor do token: $NGROK_AUTH_TOKEN"
else
    echo "⚠️ Arquivo .env não encontrado"
fi

# Verificar se o token do ngrok está configurado
if [ -z "$NGROK_AUTH_TOKEN" ]; then
    echo "❌ Token de autenticação do Ngrok não configurado"
    echo "Por favor, configure o token de autenticação do Ngrok no arquivo .env"

    # Perguntar se deseja usar o script Python antigo
    echo ""
    echo "❓ Deseja usar o script Python antigo para iniciar o Ngrok? (s/n)"
    read -r use_python

    if [ "$use_python" = "s" ] || [ "$use_python" = "S" ]; then
        echo "🔄 Iniciando script Python antigo..."
        python scripts/webhook/simple_ngrok_starter.py
        exit 0
    else
        exit 1
    fi
fi

# Verificar se o servidor está rodando
if ! curl -s http://localhost:8001/health > /dev/null; then
    echo "❌ Servidor unificado não está rodando"
    echo "Por favor, inicie o servidor unificado primeiro"
    exit 1
fi

# Iniciar o ngrok
echo "🔄 Iniciando Ngrok para a porta 8001..."
echo "⚠️ IMPORTANTE: Adicione /webhook ao final da URL gerada pelo Ngrok quando atualizar na VPS"
echo "Exemplo: https://seu-dominio-ngrok.ngrok-free.app/webhook"
ngrok http 8001 --log=stdout
