#!/bin/bash

# Script para monitorar logs de forma unificada e mais limpa
# Uso: ./scripts/logs_unificados.sh

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
    show_header "🔍 MONITOR DE LOGS UNIFICADO"
    
    echo -e "${GREEN}✅ Monitorando log do servidor: ${SERVER_LOG}${NC}"
    echo -e "${GREEN}✅ Monitorando log do webhook: ${WEBHOOK_LOG}${NC}"
    echo -e "${GREEN}✅ Monitorando log do hub: ${HUB_LOG}${NC}"
    echo -e "${GREEN}✅ Monitorando log da API Odoo: ${ODOO_API_LOG}${NC}"
    echo -e "${CYAN}✅ Monitorando log do serviço de configuração: ${CONFIG_SERVICE_LOG}${NC}"
    echo -e "${PURPLE}✅ Monitorando log do visualizador de configurações: ${CONFIG_VIEWER_LOG}${NC}"
    
    show_header "📊 LOGS EM TEMPO REAL (Ctrl+C para sair)"
    
    # Verificar se os arquivos de log existem e criá-los se necessário
    touch "${SERVER_LOG}" "${WEBHOOK_LOG}" "${HUB_LOG}" "${ODOO_API_LOG}" "${CONFIG_SERVICE_LOG}" "${CONFIG_VIEWER_LOG}"
    
    # Monitorar logs do servidor
    tail -f "${SERVER_LOG}" | sed -e "s/^/${GREEN}[SERVER]${NC} /" &
    PID1=$!
    
    # Monitorar logs do webhook
    tail -f "${WEBHOOK_LOG}" | sed -e "s/^/${YELLOW}[WEBHOOK]${NC} /" &
    PID2=$!
    
    # Monitorar logs do hub
    tail -f "${HUB_LOG}" | sed -e "s/^/${BLUE}[HUB]${NC} /" &
    PID3=$!
    
    # Monitorar logs da API Odoo
    tail -f "${ODOO_API_LOG}" | sed -e "s/^/${RED}[ODOO_API]${NC} /" &
    PID4=$!
    
    # Monitorar logs do serviço de configuração
    tail -f "${CONFIG_SERVICE_LOG}" | sed -e "s/^/${CYAN}[CONFIG_SERVICE]${NC} /" &
    PID5=$!
    
    # Monitorar logs do visualizador de configurações
    tail -f "${CONFIG_VIEWER_LOG}" | sed -e "s/^/${PURPLE}[CONFIG_VIEWER]${NC} /" &
    PID6=$!
    
    # Aguardar até que o usuário pressione Ctrl+C
    echo -e "${YELLOW}Pressione Ctrl+C para sair${NC}"
    wait
    
    # Matar processos quando o usuário pressionar Ctrl+C
    trap "kill $PID1 $PID2 $PID3 $PID4 $PID5 $PID6; exit" INT TERM EXIT
}

# Executar função
monitor_logs
