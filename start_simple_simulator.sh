#!/bin/bash

# Script para iniciar o simulador de WhatsApp simplificado

echo "========================================================================"
echo "🚀 INICIANDO SIMULADOR DE WHATSAPP SIMPLIFICADO"
echo "========================================================================"

# Verificar se o Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 não encontrado. Por favor, instale o Python 3."
    exit 1
fi

# Verificar se o arquivo do simulador existe
if [ ! -f "simple_simulator.html" ]; then
    echo "❌ Arquivo do simulador não encontrado. Verifique se você está no diretório correto."
    exit 1
fi

# Iniciar um servidor HTTP simples para servir o simulador
echo "🚀 Iniciando servidor HTTP na porta 8080..."
echo "📱 Acesse o simulador em: http://localhost:8080/simple_simulator.html"
echo "🛑 Para encerrar o simulador, pressione Ctrl+C"
echo "========================================================================"

# Iniciar o servidor HTTP
python3 -m http.server 8080
