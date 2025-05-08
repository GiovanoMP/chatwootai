#!/bin/bash

# Script para monitorar logs usando multitail
# Uso: ./scripts/logs_multitail.sh

# Diretório base
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONFIG_SERVICE_DIR="${BASE_DIR}/config-service"

# Arquivos de log
SERVER_LOG="${BASE_DIR}/logs/server.log"
WEBHOOK_LOG="${BASE_DIR}/logs/webhook.log"
HUB_LOG="${BASE_DIR}/logs/hub.log"
ODOO_API_LOG="${BASE_DIR}/logs/odoo_api.log"
CONFIG_SERVICE_LOG="${CONFIG_SERVICE_DIR}/logs/config_service.log"
CONFIG_VIEWER_LOG="${CONFIG_SERVICE_DIR}/logs/config_viewer.log"

# Verificar se o multitail está instalado
if ! command -v multitail &> /dev/null; then
    echo "O comando multitail não está instalado. Instalando..."
    sudo apt-get update
    sudo apt-get install -y multitail
fi

# Verificar se os arquivos de log existem e criá-los se necessário
touch "${SERVER_LOG}" "${WEBHOOK_LOG}" "${HUB_LOG}" "${ODOO_API_LOG}" "${CONFIG_SERVICE_LOG}" "${CONFIG_VIEWER_LOG}"

# Monitorar logs usando multitail
multitail \
    -cS server -n 100 -i "${SERVER_LOG}" \
    -cS webhook -n 100 -i "${WEBHOOK_LOG}" \
    -cS hub -n 100 -i "${HUB_LOG}" \
    -cS odoo_api -n 100 -i "${ODOO_API_LOG}" \
    -cS config_service -n 100 -i "${CONFIG_SERVICE_LOG}" \
    -cS config_viewer -n 100 -i "${CONFIG_VIEWER_LOG}"
