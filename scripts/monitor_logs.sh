#!/bin/bash

# Script simplificado para monitorar todos os logs

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

# Função para exibir cabeçalho
show_header() {
    echo -e "\n${YELLOW}======================================================================${NC}"
    echo -e "${GREEN}$1${NC}"
    echo -e "${YELLOW}======================================================================${NC}"
}

# Função para monitorar logs
monitor_logs() {
    show_header "🔍 MONITOR DE LOGS DOS SERVIÇOS"
    
    echo -e "${GREEN}✅ Monitorando log do servidor: ${SERVER_LOG}${NC}"
    echo -e "${GREEN}✅ Monitorando log do webhook: ${WEBHOOK_LOG}${NC}"
    echo -e "${GREEN}✅ Monitorando log do hub: ${HUB_LOG}${NC}"
    echo -e "${GREEN}✅ Monitorando log da API Odoo: ${ODOO_API_LOG}${NC}"
    echo -e "${CYAN}✅ Monitorando log do serviço de configuração: ${CONFIG_SERVICE_LOG}${NC}"
    echo -e "${PURPLE}✅ Monitorando log do visualizador de configurações: ${CONFIG_VIEWER_LOG}${NC}"
    
    show_header "📊 LOGS EM TEMPO REAL (Ctrl+C para sair)"
    
    # Monitorar todos os logs
    tail -f "${SERVER_LOG}" "${WEBHOOK_LOG}" "${HUB_LOG}" "${ODOO_API_LOG}" "${CONFIG_SERVICE_LOG}" "${CONFIG_VIEWER_LOG}" | awk '
        /server.log/ {print "\033[0;32m[SERVER]\033[0m " $0}
        /webhook.log/ {print "\033[0;33m[WEBHOOK]\033[0m " $0}
        /hub.log/ {print "\033[0;34m[HUB]\033[0m " $0}
        /odoo_api.log/ {print "\033[0;35m[ODOO_API]\033[0m " $0}
        /config_service.log/ {print "\033[0;36m[CONFIG_SERVICE]\033[0m " $0}
        /config_viewer.log/ {print "\033[0;35m[CONFIG_VIEWER]\033[0m " $0}
    '
}

# Executar função
monitor_logs
