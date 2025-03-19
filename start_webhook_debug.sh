#!/bin/bash

# Script para iniciar o servidor webhook em modo de depuração

# Verifica se estamos em ambiente de desenvolvimento
ENVIRONMENT=${ENVIRONMENT:-development}
echo "Ambiente: $ENVIRONMENT"

# Define nível de log mais detalhado para depuração
export LOG_LEVEL=DEBUG

# Se o WEBHOOK_DOMAIN não estiver definido, tenta obter automaticamente do ngrok
if [ -z "$WEBHOOK_DOMAIN" ]; then
    # Tenta obter URL do ngrok se estiver em execução
    NGROK_URL=$(curl -s http://127.0.0.1:4040/api/tunnels | grep -o '"public_url":"[^"]*' | grep -o 'http[^"]*' | head -1)
    
    if [ ! -z "$NGROK_URL" ]; then
        echo "Detectado Ngrok em execução, usando URL: $NGROK_URL"
        # Extrai apenas o domínio do ngrok
        WEBHOOK_DOMAIN=$(echo $NGROK_URL | sed -e 's|^[^/]*//||' -e 's|/.*$||')
        export WEBHOOK_DOMAIN=$WEBHOOK_DOMAIN
        echo "WEBHOOK_DOMAIN definido como: $WEBHOOK_DOMAIN"
    else
        echo "Ngrok não detectado. Usando localhost como padrão."
        export WEBHOOK_DOMAIN=localhost
    fi
fi

# Cria diretório de logs se não existir
mkdir -p logs

# Configurações adicionais para depuração
export PYTHONPATH=$(pwd)
export WEBHOOK_PORT=${WEBHOOK_PORT:-8001}

echo "Iniciando servidor webhook em http://$WEBHOOK_DOMAIN:$WEBHOOK_PORT"
echo "URL completa do webhook: http://$WEBHOOK_DOMAIN:$WEBHOOK_PORT/webhook"
echo "Logs detalhados serão salvos em ./logs/"

# Inicia o servidor com saída detalhada
python3 -m src.api.webhook_server
