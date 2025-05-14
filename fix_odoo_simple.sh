#!/bin/bash

# Script simples para corrigir o Odoo

# ID do contêiner do Odoo
ODOO_CONTAINER="170eef37c62e"

echo "=== Corrigindo o Odoo (contêiner $ODOO_CONTAINER) ==="

# Limpar o cache de assets
echo "Limpando cache de assets..."
docker exec $ODOO_CONTAINER bash -c "find /var/lib/odoo -name '*web_editor*' -type f -delete || echo 'Comando falhou'"
docker exec $ODOO_CONTAINER bash -c "find /var/lib/odoo -name '*assets_*' -type f -delete || echo 'Comando falhou'"
docker exec $ODOO_CONTAINER bash -c "rm -rf /var/lib/odoo/.local/share/Odoo/filestore/*/attachment/*/web_editor_assets* || echo 'Comando falhou'"
docker exec $ODOO_CONTAINER bash -c "rm -rf /var/lib/odoo/.local/share/Odoo/filestore/*/attachment/*/web_assets* || echo 'Comando falhou'"

# Verificar e criar o diretório custom_addons se não existir
echo "Verificando diretório custom_addons..."
docker exec $ODOO_CONTAINER bash -c "mkdir -p /mnt/extra-addons/custom_addons || echo 'Diretório já existe'"
docker exec $ODOO_CONTAINER bash -c "chmod -R 755 /mnt/extra-addons/custom_addons || echo 'Comando falhou'"

# Reiniciar o contêiner
echo "Reiniciando o contêiner..."
docker restart $ODOO_CONTAINER

echo "Aguardando o Odoo reiniciar (10 segundos)..."
sleep 10

echo "=== Concluído ==="
echo "Agora tente instalar os módulos novamente."
