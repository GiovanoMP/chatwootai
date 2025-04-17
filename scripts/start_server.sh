#!/bin/bash

# Script para iniciar o servidor unificado
# Este script inicia o servidor unificado que combina o webhook do Chatwoot e a API Odoo

# Configurar diretório de logs
mkdir -p logs

# Iniciar o servidor
echo -e "\n======================================================================="
echo "🚀 INICIANDO SISTEMA INTEGRADO ODOO-AI"
echo "======================================================================="

# Configurar o sistema de logs
echo "🔧 Configurando sistema de logs..."
python scripts/setup_logging.py

# Executar o servidor com redirecionamento de saída para logs
echo "🔄 Iniciando servidor unificado..."
python main.py 2>&1 | tee -a logs/server.log
