#!/bin/bash

# Script para limpar o cache do Odoo em ambiente Docker

echo "=== Limpando cache do Odoo em ambiente Docker ==="

# Identificar o contêiner do Odoo
ODOO_CONTAINER=$(docker ps | grep odoo | head -n 1 | awk '{print $1}')

if [ -z "$ODOO_CONTAINER" ]; then
    echo "Erro: Não foi possível encontrar o contêiner do Odoo."
    echo "Verifique se o Odoo está em execução com 'docker ps'."
    exit 1
fi

echo "Contêiner do Odoo encontrado: $ODOO_CONTAINER"

# Limpar o cache de assets
echo "Limpando cache de assets..."
docker exec $ODOO_CONTAINER bash -c "rm -rf /var/lib/odoo/.local/share/Odoo/filestore/*/attachment/*/web_editor_assets*"
docker exec $ODOO_CONTAINER bash -c "rm -rf /var/lib/odoo/.local/share/Odoo/filestore/*/attachment/*/web_assets*"
docker exec $ODOO_CONTAINER bash -c "find /var/lib/odoo -name '*web_editor*' -type f -delete"
docker exec $ODOO_CONTAINER bash -c "find /var/lib/odoo -name '*assets_*' -type f -delete"

# Limpar o cache do navegador no Odoo
echo "Limpando cache do navegador no Odoo..."
docker exec $ODOO_CONTAINER bash -c "python3 -c 'from odoo.tools.func import reset_cache; reset_cache()' || echo 'Comando não disponível'"

# Reiniciar o contêiner do Odoo
echo "Reiniciando o contêiner do Odoo: $ODOO_CONTAINER"
docker restart $ODOO_CONTAINER

echo "Aguardando o Odoo reiniciar (30 segundos)..."
sleep 30

echo "=== Processo concluído ==="
echo "Tente acessar o Odoo novamente e verificar se o problema foi resolvido."
echo "Se o problema persistir, pode ser necessário atualizar os módulos manualmente."
