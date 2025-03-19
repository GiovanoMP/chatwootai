#!/bin/bash

# Script para executar todos os testes do projeto

echo "===== Executando testes unitários ====="
python -m unittest discover tests

echo ""
echo "===== Executando teste de integração ====="
python test_chatwoot_integration.py

echo ""
echo "Todos os testes foram concluídos!"
