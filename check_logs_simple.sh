#!/bin/bash

# Script simples para verificar os logs do Odoo

# ID do contêiner do Odoo
ODOO_CONTAINER="170eef37c62e"

echo "=== Verificando logs do Odoo (contêiner $ODOO_CONTAINER) ==="

# Verificar os logs
echo "Últimas 100 linhas do log:"
docker exec $ODOO_CONTAINER bash -c "tail -n 100 /var/log/odoo/odoo-server.log || tail -n 100 /var/log/odoo.log || echo 'Arquivo de log não encontrado'"

echo "=== Concluído ==="
