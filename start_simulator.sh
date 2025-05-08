#!/bin/bash

# Script para iniciar o simulador de WhatsApp

echo "========================================================================"
echo "🚀 INICIANDO SIMULADOR DE WHATSAPP"
echo "========================================================================"

# Limpar processos anteriores
if pgrep -f "python3 whatsapp_proxy.py" > /dev/null; then
    echo "🛑 Encerrando instâncias anteriores do simulador..."
    pkill -f "python3 whatsapp_proxy.py"
    sleep 2
fi

# Verificar se o Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 não encontrado. Por favor, instale o Python 3."
    exit 1
fi

# Verificar se o pip está instalado
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 não encontrado. Por favor, instale o pip3."
    exit 1
fi

# Verificar se as dependências estão instaladas
echo "🔍 Verificando dependências..."
pip3 install requests > /dev/null 2>&1

# Verificar se os arquivos necessários existem
if [ ! -f "whatsapp_simulator.html" ] || [ ! -f "whatsapp_simulator.js" ] || [ ! -f "whatsapp_proxy.py" ]; then
    echo "❌ Arquivos do simulador não encontrados. Verifique se você está no diretório correto."
    exit 1
fi

# Configurar links simbólicos para os logs
echo "🔄 Configurando links simbólicos para os logs..."
./setup_simulator_links.sh

# Verificar se o servidor está rodando
if pgrep -f "python3 whatsapp_proxy.py" > /dev/null; then
    echo "⚠️ O simulador já está rodando. Reiniciando..."
    pkill -f "python3 whatsapp_proxy.py"
    sleep 2
fi

# Iniciar o servidor proxy
echo "🚀 Iniciando servidor proxy..."
python3 whatsapp_proxy.py &

# Aguardar o servidor iniciar
sleep 2

echo "========================================================================"
echo "✅ SIMULADOR INICIADO COM SUCESSO"
echo "========================================================================"
echo "📱 Acesse o simulador em: http://localhost:8080/simulator"
echo "🔄 O simulador está encaminhando mensagens para: http://localhost:8001/webhook"
echo "🛑 Para encerrar o simulador, pressione Ctrl+C"
echo "========================================================================"

# Manter o script rodando
wait
