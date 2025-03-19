#!/bin/bash

# Script para executar a integração com o Chatwoot
# Este script inicia o serviço de monitoramento do Chatwoot em um contêiner Docker

set -e

# Carrega variáveis de ambiente
if [ -f .env ]; then
  echo "Carregando variáveis de ambiente de .env"
  export $(grep -v '^#' .env | xargs)
else
  echo "Arquivo .env não encontrado. Certifique-se de criar um arquivo .env baseado no .env.chatwoot.example"
  exit 1
fi

# Verifica se as variáveis necessárias estão definidas
if [ -z "$CHATWOOT_BASE_URL" ] || [ -z "$CHATWOOT_API_KEY" ] || [ -z "$CHATWOOT_ACCOUNT_ID" ]; then
  echo "Variáveis de ambiente do Chatwoot não definidas. Verifique seu arquivo .env"
  exit 1
fi

echo "Iniciando o serviço de integração com o Chatwoot..."

# Executa o contêiner Docker com o exemplo de integração
docker run --rm \
  --name chatwootai_integration \
  --network chatwootai_network \
  -v "$(pwd):/app" \
  -w /app \
  --env-file .env \
  python:3.10-slim \
  bash -c "pip install -r requirements.txt && python examples/chatwoot_integration_example.py"

echo "Serviço de integração com o Chatwoot iniciado!"
