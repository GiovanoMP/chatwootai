#!/bin/bash
# Script para carregar variáveis de ambiente e executar o teste de sincronização

# Carregar variáveis de ambiente do arquivo .env
if [ -f "../../.env" ]; then
  echo "Carregando variáveis de ambiente do arquivo .env..."
  export $(grep -v '^#' ../../.env | xargs)
elif [ -f "../.env" ]; then
  echo "Carregando variáveis de ambiente do arquivo .env..."
  export $(grep -v '^#' ../.env | xargs)
elif [ -f ".env" ]; then
  echo "Carregando variáveis de ambiente do arquivo .env..."
  export $(grep -v '^#' .env | xargs)
else
  echo "Arquivo .env não encontrado!"
  exit 1
fi

# Verificar se as variáveis necessárias foram carregadas
if [ -z "$DATABASE_URL" ] || [ -z "$QDRANT_URL" ] || [ -z "$OPENAI_API_KEY" ]; then
  echo "Erro: Uma ou mais variáveis de ambiente necessárias não foram definidas:"
  echo "DATABASE_URL: ${DATABASE_URL:-não definida}"
  echo "QDRANT_URL: ${QDRANT_URL:-não definida}"
  echo "OPENAI_API_KEY: ${OPENAI_API_KEY:-não definida}"
  exit 1
fi

echo "Variáveis de ambiente carregadas com sucesso!"
echo "DATABASE_URL: $DATABASE_URL"
echo "QDRANT_URL: $QDRANT_URL"
echo "OPENAI_API_KEY: ${OPENAI_API_KEY:0:5}... (parcialmente oculta por segurança)"

# Executar o script de teste
echo "Executando o script de teste..."
python test_sync_services.py

# Fim do script
echo "Teste concluído!"
