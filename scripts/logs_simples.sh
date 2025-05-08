#!/bin/bash

# Script para monitorar logs de forma simples
# Uso: ./scripts/logs_simples.sh

# Cores para saída
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

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

# Monitorar logs usando tail e awk
tail -f "${SERVER_LOG}" "${WEBHOOK_LOG}" "${HUB_LOG}" "${ODOO_API_LOG}" "${CONFIG_SERVICE_LOG}" "${CONFIG_VIEWER_LOG}" | awk '
    /server.log/ {print "\033[0;32m[SERVER]\033[0m " $0; next}
    /webhook.log/ {print "\033[1;33m[WEBHOOK]\033[0m " $0; next}
    /hub.log/ {print "\033[0;34m[HUB]\033[0m " $0; next}
    /odoo_api.log/ {print "\033[0;31m[ODOO_API]\033[0m " $0; next}
    /config_service.log/ {print "\033[0;36m[CONFIG_SERVICE]\033[0m " $0; next}
    /config_viewer.log/ {print "\033[0;35m[CONFIG_VIEWER]\033[0m " $0; next}
    {print $0}  # Linhas que não correspondem a nenhum padrão
'
