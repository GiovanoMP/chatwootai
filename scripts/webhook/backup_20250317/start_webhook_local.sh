#!/bin/bash
# Script para iniciar o servidor webhook local
# Uso: ./start_webhook_local.sh

# Definir variáveis
WEBHOOK_PORT=8000
NGROK_PORT=8000

# Verificar se o ngrok está instalado
if ! command -v ngrok &> /dev/null; then
    echo "Erro: ngrok não está instalado"
    echo "Instale o ngrok seguindo as instruções em: https://ngrok.com/download"
    exit 1
fi

# Verificar se o servidor webhook está em execução
if pgrep -f "python -m src.api.webhook_server" > /dev/null; then
    echo "O servidor webhook já está em execução"
    echo "Para reiniciar, execute: pkill -f 'python -m src.api.webhook_server' && ./start_webhook_local.sh"
    exit 1
fi

# Iniciar o servidor webhook em segundo plano
echo "Iniciando o servidor webhook na porta $WEBHOOK_PORT..."
python -m src.api.webhook_server > webhook_server.log 2>&1 &
WEBHOOK_PID=$!
echo "Servidor webhook iniciado com PID: $WEBHOOK_PID"

# Aguardar alguns segundos para o servidor iniciar
echo "Aguardando o servidor iniciar..."
sleep 3

# Verificar se o servidor está em execução
if ! ps -p $WEBHOOK_PID > /dev/null; then
    echo "Erro: O servidor webhook não iniciou corretamente"
    echo "Verifique o arquivo webhook_server.log para mais informações"
    exit 1
fi

# Iniciar o ngrok em uma nova janela de terminal
echo "Iniciando o ngrok na porta $NGROK_PORT..."
gnome-terminal -- bash -c "ngrok http $NGROK_PORT"

echo "Servidor webhook e ngrok iniciados com sucesso"
echo "Para verificar os logs do servidor webhook, execute: tail -f webhook_server.log"
echo "Para obter a URL do ngrok, acesse: http://localhost:4040/status"
echo "Lembre-se de atualizar a URL do webhook na VPS quando a URL do ngrok mudar"
echo "Para atualizar a URL na VPS, use o script: ./scripts/update_webhook_url.sh <nova_url>"
