#!/bin/bash

# Script para iniciar o servidor unificado
# Este script inicia o servidor unificado que combina o webhook do Chatwoot e a API Odoo

# Configurar diretório de logs
mkdir -p logs

# Iniciar o servidor
echo -e "\n======================================================================="
echo "🚀 INICIANDO SISTEMA INTEGRADO ODOO-AI"
echo "======================================================================="

# Executar o servidor
python main.py
