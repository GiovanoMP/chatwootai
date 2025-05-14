#!/bin/bash

# Script para limpar o cache de assets do Odoo no contêiner Docker

echo "=== Limpando cache de assets do Odoo no contêiner Docker ==="

# Identificar o contêiner do Odoo
ODOO_CONTAINER=$(docker ps | grep odoo | awk '{print $1}')

if [ -z "$ODOO_CONTAINER" ]; then
    echo "Erro: Não foi possível encontrar o contêiner do Odoo."
    echo "Verifique se o Odoo está em execução com 'docker ps'."
    exit 1
fi

echo "Contêiner do Odoo encontrado: $ODOO_CONTAINER"

# Limpar o cache de assets
echo "Limpando cache de assets..."
docker exec $ODOO_CONTAINER bash -c "find /var/lib/odoo -type d -name 'web_editor_assets*' -exec rm -rf {} \; 2>/dev/null || true"
docker exec $ODOO_CONTAINER bash -c "find /var/lib/odoo -type d -name 'web_assets*' -exec rm -rf {} \; 2>/dev/null || true"

# Reiniciar o contêiner do Odoo
echo "Reiniciando o contêiner do Odoo..."
docker restart $ODOO_CONTAINER

echo "Aguardando o Odoo reiniciar (30 segundos)..."
sleep 30

echo "=== Processo concluído ==="
echo "Tente acessar o Odoo novamente e verificar se o problema foi resolvido."
