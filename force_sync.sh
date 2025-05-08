#!/bin/bash

# Script para forçar a sincronização das regras de negócio e metadados da empresa

# Definir variáveis
ACCOUNT_ID="account_1"
API_URL_RULES="http://localhost:8001/api/v1/business-rules/sync"
API_URL_METADATA="http://localhost:8001/api/v1/business-rules/sync-company-metadata"

# Executar a sincronização das regras
echo "Forçando sincronização de regras para account_id: $ACCOUNT_ID"
curl -X POST "$API_URL_RULES?account_id=$ACCOUNT_ID" \
  -H "Content-Type: application/json" \
  -d '{}'

echo -e "\n\n"

# Executar a sincronização dos metadados da empresa
echo "Forçando sincronização de metadados da empresa para account_id: $ACCOUNT_ID"
curl -X POST "$API_URL_METADATA?account_id=$ACCOUNT_ID" \
  -H "Content-Type: application/json" \
  -d '{}'

echo -e "\n\nSincronização concluída!"
