#!/bin/bash

# Script para reiniciar o servidor da API e aplicar as alterações

echo "Reiniciando o servidor da API..."

# Verificar se o servidor está em execução
PID=$(pgrep -f "uvicorn main:app")

if [ -n "$PID" ]; then
    echo "Servidor encontrado com PID $PID. Parando..."
    kill $PID
    sleep 2
    
    # Verificar se o servidor foi parado
    if ps -p $PID > /dev/null; then
        echo "Servidor não parou. Forçando parada..."
        kill -9 $PID
        sleep 1
    fi
    
    echo "Servidor parado."
else
    echo "Servidor não está em execução."
fi

# Iniciar o servidor
echo "Iniciando o servidor..."
cd odoo_api
nohup python -m uvicorn main:app --host 0.0.0.0 --port 8001 > ../api_server.log 2>&1 &

echo "Servidor iniciado. Logs em api_server.log"
echo "Aguardando 5 segundos para o servidor iniciar..."
sleep 5

# Verificar se o servidor está em execução
PID=$(pgrep -f "uvicorn main:app")
if [ -n "$PID" ]; then
    echo "Servidor em execução com PID $PID."
    echo "Para testar as correções, execute:"
    echo "python testar_correcoes.py"
else
    echo "Erro: Servidor não iniciou corretamente."
    echo "Verifique os logs em api_server.log"
fi
