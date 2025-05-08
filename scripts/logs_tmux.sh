#!/bin/bash

# Script para monitorar logs usando tmux
# Uso: ./scripts/logs_tmux.sh

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

# Verificar se o tmux está instalado
if ! command -v tmux &> /dev/null; then
    echo "O comando tmux não está instalado. Instalando..."
    sudo apt-get update
    sudo apt-get install -y tmux
fi

# Verificar se os arquivos de log existem e criá-los se necessário
touch "${SERVER_LOG}" "${WEBHOOK_LOG}" "${HUB_LOG}" "${ODOO_API_LOG}" "${CONFIG_SERVICE_LOG}" "${CONFIG_VIEWER_LOG}"

# Nome da sessão tmux
SESSION_NAME="logs-monitor"

# Matar sessão existente, se houver
tmux kill-session -t "${SESSION_NAME}" 2>/dev/null

# Criar nova sessão
tmux new-session -d -s "${SESSION_NAME}" -n "server" "tail -f ${SERVER_LOG} | sed -e 's/^/[SERVER] /'"

# Dividir a janela em painéis
tmux split-window -h -t "${SESSION_NAME}" "tail -f ${WEBHOOK_LOG} | sed -e 's/^/[WEBHOOK] /'"
tmux split-window -v -t "${SESSION_NAME}" "tail -f ${HUB_LOG} | sed -e 's/^/[HUB] /'"
tmux select-pane -t 0
tmux split-window -v -t "${SESSION_NAME}" "tail -f ${ODOO_API_LOG} | sed -e 's/^/[ODOO_API] /'"
tmux select-pane -t 2
tmux split-window -v -t "${SESSION_NAME}" "tail -f ${CONFIG_SERVICE_LOG} | sed -e 's/^/[CONFIG_SERVICE] /'"
tmux select-pane -t 4
tmux split-window -v -t "${SESSION_NAME}" "tail -f ${CONFIG_VIEWER_LOG} | sed -e 's/^/[CONFIG_VIEWER] /'"

# Anexar à sessão
tmux attach-session -t "${SESSION_NAME}"
