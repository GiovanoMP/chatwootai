#!/bin/bash

# Script para configurar links simbólicos para o simulador de WhatsApp

echo "========================================================================"
echo "🔧 CONFIGURANDO LINKS PARA O SIMULADOR DE WHATSAPP"
echo "========================================================================"

# Verificar se estamos no diretório correto
if [ ! -d "logs" ]; then
    echo "❌ Diretório 'logs' não encontrado. Criando..."
    mkdir -p logs
fi

# Criar link simbólico para os logs do Chatwoot
echo "🔄 Criando link simbólico para logs/chatwoot_client.log..."
if [ -f "logs/webhook.log" ]; then
    # Se o arquivo webhook.log existe, criar um link para ele
    ln -sf logs/webhook.log logs/chatwoot_client.log
    echo "✅ Link criado: logs/webhook.log -> logs/chatwoot_client.log"
elif [ -f "logs/server.log" ]; then
    # Se o arquivo server.log existe, criar um link para ele
    ln -sf logs/server.log logs/chatwoot_client.log
    echo "✅ Link criado: logs/server.log -> logs/chatwoot_client.log"
else
    # Se nenhum arquivo de log existe, criar um arquivo vazio
    touch logs/chatwoot_client.log
    echo "✅ Arquivo vazio criado: logs/chatwoot_client.log"
fi

# Verificar se o arquivo last_webhook_payload.json existe
if [ ! -f "logs/last_webhook_payload.json" ]; then
    echo "🔄 Criando arquivo vazio logs/last_webhook_payload.json..."
    echo "{}" > logs/last_webhook_payload.json
    echo "✅ Arquivo criado: logs/last_webhook_payload.json"
fi

echo "========================================================================"
echo "✅ CONFIGURAÇÃO CONCLUÍDA"
echo "========================================================================"
echo "Agora você pode iniciar o simulador com ./start_simulator.sh"
echo "========================================================================"
