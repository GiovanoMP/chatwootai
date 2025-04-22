#!/bin/bash

# Script para reiniciar o servidor

echo "========================================================================"
echo "🔄 REINICIANDO SERVIDOR UNIFICADO"
echo "========================================================================"

# Encontrar e matar o processo do servidor
echo "🔍 Procurando processos do servidor..."
SERVER_PID=$(ps aux | grep "main.py" | grep -v grep | awk '{print $2}')

if [ -n "$SERVER_PID" ]; then
    echo "🛑 Matando processo do servidor (PID: $SERVER_PID)..."
    kill -9 $SERVER_PID
    sleep 2
    echo "✅ Processo do servidor finalizado"
else
    echo "⚠️ Nenhum processo do servidor encontrado"
fi

# Iniciar o servidor novamente
echo "🚀 Iniciando servidor novamente..."
./scripts/start_server.sh
