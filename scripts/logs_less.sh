#!/bin/bash

# Script para monitorar logs usando less
# Uso: ./scripts/logs_less.sh

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

# Verificar se os arquivos de log existem e criá-los se necessário
touch "${SERVER_LOG}" "${WEBHOOK_LOG}" "${HUB_LOG}" "${ODOO_API_LOG}" "${CONFIG_SERVICE_LOG}" "${CONFIG_VIEWER_LOG}"

# Criar arquivo temporário com todos os logs
TMP_LOG="/tmp/all_logs.log"
rm -f "${TMP_LOG}"
touch "${TMP_LOG}"

# Função para adicionar cabeçalho ao arquivo de log
add_header() {
    local log_file="$1"
    local header="$2"
    echo "=== ${header} ===" >> "${TMP_LOG}"
    cat "${log_file}" >> "${TMP_LOG}"
    echo "" >> "${TMP_LOG}"
}

# Adicionar cabeçalhos e conteúdo dos logs ao arquivo temporário
add_header "${SERVER_LOG}" "SERVER LOG"
add_header "${WEBHOOK_LOG}" "WEBHOOK LOG"
add_header "${HUB_LOG}" "HUB LOG"
add_header "${ODOO_API_LOG}" "ODOO API LOG"
add_header "${CONFIG_SERVICE_LOG}" "CONFIG SERVICE LOG"
add_header "${CONFIG_VIEWER_LOG}" "CONFIG VIEWER LOG"

# Abrir o arquivo temporário com less
less -R "${TMP_LOG}"
