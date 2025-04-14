#!/bin/bash

# Script para executar testes

# Verificar se pytest está instalado
if ! command -v pytest &> /dev/null; then
    echo "pytest não encontrado. Instalando..."
    pip install pytest pytest-asyncio pytest-cov
fi

# Executar testes unitários
echo "Executando testes unitários..."
pytest tests/unit -v

# Executar testes de integração
echo "Executando testes de integração..."
pytest tests/integration -v

# Gerar relatório de cobertura
echo "Gerando relatório de cobertura..."
pytest --cov=odoo_api --cov-report=term-missing

echo "Testes concluídos!"
