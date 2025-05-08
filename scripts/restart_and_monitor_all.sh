#!/bin/bash

# Script para reiniciar e monitorar todos os serviços (servidor principal, serviço de configuração e visualizador)

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
CONFIG_VIEWER_DIR="${BASE_DIR}/config-viewer"

# Criar diretório de logs se não existir
mkdir -p "${BASE_DIR}/logs"
mkdir -p "${CONFIG_SERVICE_DIR}/logs"

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

# Função para matar processos
kill_processes() {
    show_header "🚀 REINICIANDO E MONITORANDO TODOS OS SERVIÇOS"
    
    echo -e "${BLUE}🔍 Procurando processos do servidor principal...${NC}"
    SERVER_PIDS=$(pgrep -f "uvicorn main:app")
    if [[ -n "$SERVER_PIDS" ]]; then
        echo -e "${RED}🛑 Matando processo do servidor principal (PID: ${SERVER_PIDS})...${NC}"
        kill -9 $SERVER_PIDS
        echo -e "${GREEN}✅ Processo do servidor principal finalizado${NC}"
    else
        echo -e "${YELLOW}⚠️ Nenhum processo do servidor principal encontrado${NC}"
    fi
    
    echo -e "${BLUE}🔍 Procurando processos do serviço de configuração...${NC}"
    CONFIG_SERVICE_PIDS=$(pgrep -f "python.*run.py")
    if [[ -n "$CONFIG_SERVICE_PIDS" ]]; then
        echo -e "${RED}🛑 Matando processo do serviço de configuração (PID: ${CONFIG_SERVICE_PIDS})...${NC}"
        kill -9 $CONFIG_SERVICE_PIDS
        echo -e "${GREEN}✅ Processo do serviço de configuração finalizado${NC}"
    else
        echo -e "${YELLOW}⚠️ Nenhum processo do serviço de configuração encontrado${NC}"
    fi
    
    echo -e "${BLUE}🔍 Procurando processos do visualizador de configurações...${NC}"
    CONFIG_VIEWER_PIDS=$(pgrep -f "python.*app.py")
    if [[ -n "$CONFIG_VIEWER_PIDS" ]]; then
        echo -e "${RED}🛑 Matando processo do visualizador de configurações (PID: ${CONFIG_VIEWER_PIDS})...${NC}"
        kill -9 $CONFIG_VIEWER_PIDS
        echo -e "${GREEN}✅ Processo do visualizador de configurações finalizado${NC}"
    else
        echo -e "${YELLOW}⚠️ Nenhum processo do visualizador de configurações encontrado${NC}"
    fi
}

# Função para configurar o sistema de logs
setup_logs() {
    show_header "🔧 CONFIGURANDO SISTEMA DE LOGS"
    
    # Limpar logs
    > "${SERVER_LOG}"
    > "${WEBHOOK_LOG}"
    > "${HUB_LOG}"
    > "${ODOO_API_LOG}"
    > "${CONFIG_SERVICE_LOG}"
    > "${CONFIG_VIEWER_LOG}"
    
    # Configurar logs
    cd "${BASE_DIR}" && python -c "
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/server.log'),
        logging.StreamHandler()
    ]
)
logging.info('🔧 Sistema de logs configurado')
" 2>&1

    echo -e "${GREEN}✅ Sistema de logs configurado com sucesso${NC}"
    echo -e "${BLUE}📝 Log do servidor: ${SERVER_LOG}${NC}"
    echo -e "${BLUE}📝 Log do webhook: ${WEBHOOK_LOG}${NC}"
    echo -e "${BLUE}📝 Log do hub: ${HUB_LOG}${NC}"
    echo -e "${BLUE}📝 Log da API Odoo: ${ODOO_API_LOG}${NC}"
    echo -e "${BLUE}📝 Log do serviço de configuração: ${CONFIG_SERVICE_LOG}${NC}"
    echo -e "${BLUE}📝 Log do visualizador de configurações: ${CONFIG_VIEWER_LOG}${NC}"
    
    show_header "✅ SISTEMA DE LOGS CONFIGURADO COM SUCESSO"
}

# Função para iniciar o serviço de configuração
start_config_service() {
    echo -e "${BLUE}🖥️ Iniciando serviço de configuração...${NC}"
    cd "${CONFIG_SERVICE_DIR}" && python run.py > "${CONFIG_SERVICE_LOG}" 2>&1 &
    CONFIG_SERVICE_PID=$!
    echo -e "${GREEN}✅ Serviço de configuração iniciado com PID: ${CONFIG_SERVICE_PID}${NC}"
    
    # Aguardar o serviço iniciar
    echo -e "${YELLOW}⏳ Aguardando o serviço de configuração iniciar (5 segundos)...${NC}"
    sleep 5
    
    # Verificar se o serviço está em execução
    if kill -0 $CONFIG_SERVICE_PID 2>/dev/null; then
        echo -e "${GREEN}✅ Serviço de configuração iniciado com sucesso!${NC}"
    else
        echo -e "${RED}⚠️ Serviço de configuração pode não ter iniciado corretamente. Verifique os logs.${NC}"
    fi
}

# Função para iniciar o visualizador de configurações
start_config_viewer() {
    echo -e "${BLUE}🖥️ Iniciando visualizador de configurações...${NC}"
    cd "${CONFIG_VIEWER_DIR}" && python app.py > "${CONFIG_VIEWER_LOG}" 2>&1 &
    CONFIG_VIEWER_PID=$!
    echo -e "${GREEN}✅ Visualizador de configurações iniciado com PID: ${CONFIG_VIEWER_PID}${NC}"
    
    # Aguardar o visualizador iniciar
    echo -e "${YELLOW}⏳ Aguardando o visualizador de configurações iniciar (5 segundos)...${NC}"
    sleep 5
    
    # Verificar se o visualizador está em execução
    if kill -0 $CONFIG_VIEWER_PID 2>/dev/null; then
        echo -e "${GREEN}✅ Visualizador de configurações iniciado com sucesso!${NC}"
    else
        echo -e "${RED}⚠️ Visualizador de configurações pode não ter iniciado corretamente. Verifique os logs.${NC}"
    fi
}

# Função para iniciar o servidor principal
start_server() {
    echo -e "${BLUE}🖥️ Criando sessão screen para servidor principal...${NC}"
    cd "${BASE_DIR}" && screen -dmS server python -m uvicorn main:app --host 0.0.0.0 --port 8001
    
    # Aguardar o servidor iniciar
    echo -e "${YELLOW}⏳ Aguardando o servidor principal iniciar (5 segundos)...${NC}"
    sleep 5
    
    # Verificar se o servidor está em execução
    if pgrep -f "uvicorn main:app" > /dev/null; then
        echo -e "${GREEN}✅ Servidor principal iniciado com sucesso!${NC}"
    else
        echo -e "${RED}⚠️ Servidor principal pode não ter iniciado corretamente. Verifique os logs.${NC}"
    fi
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

# Executar funções
kill_processes
setup_logs
start_config_service
start_config_viewer
start_server
monitor_logs
