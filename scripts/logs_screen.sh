#!/bin/bash

# Script para monitorar logs usando screen
# Uso: ./scripts/logs_screen.sh

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

# Verificar se o screen está instalado
if ! command -v screen &> /dev/null; then
    echo "O comando screen não está instalado. Instalando..."
    sudo apt-get update
    sudo apt-get install -y screen
fi

# Verificar se os arquivos de log existem e criá-los se necessário
touch "${SERVER_LOG}" "${WEBHOOK_LOG}" "${HUB_LOG}" "${ODOO_API_LOG}" "${CONFIG_SERVICE_LOG}" "${CONFIG_VIEWER_LOG}"

# Nome da sessão screen
SESSION_NAME="logs-monitor"

# Matar sessão existente, se houver
screen -wipe "${SESSION_NAME}" 2>/dev/null
screen -X -S "${SESSION_NAME}" quit 2>/dev/null

# Criar arquivo de configuração do screen
cat > /tmp/screenrc <<EOF
# Configuração do screen para monitoramento de logs
startup_message off
caption always "%{= kw}%-w%{= BW}%n %t%{-}%+w %-= %c"
hardstatus alwayslastline
hardstatus string '%{= kG}[ %{G}%H %{g}][%= %{= kw}%?%-Lw%?%{r}(%{W}%n*%f%t%?(%u)%?%{r})%{w}%?%+Lw%?%?%= %{g}][%{B} %d/%m %{W}%c %{g}]'
screen -t SERVER 0 bash -c "tail -f ${SERVER_LOG} | sed -e 's/^/[SERVER] /'"
screen -t WEBHOOK 1 bash -c "tail -f ${WEBHOOK_LOG} | sed -e 's/^/[WEBHOOK] /'"
screen -t HUB 2 bash -c "tail -f ${HUB_LOG} | sed -e 's/^/[HUB] /'"
screen -t ODOO_API 3 bash -c "tail -f ${ODOO_API_LOG} | sed -e 's/^/[ODOO_API] /'"
screen -t CONFIG_SERVICE 4 bash -c "tail -f ${CONFIG_SERVICE_LOG} | sed -e 's/^/[CONFIG_SERVICE] /'"
screen -t CONFIG_VIEWER 5 bash -c "tail -f ${CONFIG_VIEWER_LOG} | sed -e 's/^/[CONFIG_VIEWER] /'"
EOF

# Iniciar screen com o arquivo de configuração
screen -c /tmp/screenrc -S "${SESSION_NAME}" -d -m

# Anexar à sessão
screen -r "${SESSION_NAME}"
