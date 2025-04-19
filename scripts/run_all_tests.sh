#!/bin/bash

# Script para executar todos os testes da arquitetura multi-tenant

echo "===== Iniciando testes da arquitetura multi-tenant ====="
echo ""

# Verificar se o Qdrant está rodando
echo "Verificando se o Qdrant está rodando..."
curl -s http://localhost:6333/collections > /dev/null
if [ $? -ne 0 ]; then
    echo "❌ Erro: Qdrant não está rodando. Inicie o Qdrant antes de executar os testes."
    exit 1
fi
echo "✅ Qdrant está rodando."
echo ""

# Inicializar as coleções compartilhadas
echo "===== Inicializando coleções compartilhadas ====="
python3 scripts/initialize_shared_collections.py
echo ""

# Executar teste de multi-tenancy geral
echo "===== Executando teste geral de multi-tenancy ====="
python3 scripts/test_multi_tenant.py
echo ""

# Executar teste de sincronização de metadados
echo "===== Executando teste de sincronização de metadados ====="
python3 scripts/test_sync_metadata.py
echo ""

# Executar teste de busca de regras de negócio
echo "===== Executando teste de busca de regras de negócio ====="
python3 scripts/test_search_business_rules.py
echo ""

echo "===== Todos os testes concluídos ====="
