#!/bin/bash

# Script unificado para reiniciar todos os serviços e mostrar logs
# Uso: ./scripts/reiniciar_tudo.sh

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

# Criar diretórios de logs se não existirem
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
    show_header "🚀 REINICIANDO TODOS OS SERVIÇOS"

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

# Função para iniciar o serviço de configuração
start_config_service() {
    show_header "🚀 INICIANDO SERVIÇO DE CONFIGURAÇÃO"

    echo -e "${BLUE}🖥️ Iniciando serviço de configuração...${NC}"
    cd "${CONFIG_SERVICE_DIR}" && python run.py > "${CONFIG_SERVICE_LOG}" 2>&1 &
    CONFIG_SERVICE_PID=$!
    echo -e "${GREEN}✅ Serviço de configuração iniciado com PID: ${CONFIG_SERVICE_PID}${NC}"

    # Aguardar o serviço iniciar
    echo -e "${YELLOW}⏳ Aguardando o serviço de configuração iniciar (10 segundos)...${NC}"

    # Verificar saúde do serviço com tentativas
    MAX_ATTEMPTS=10
    ATTEMPT=1
    SLEEP_TIME=1

    while [ $ATTEMPT -le $MAX_ATTEMPTS ]; do
        if kill -0 $CONFIG_SERVICE_PID 2>/dev/null; then
            # Verificar saúde do serviço
            HEALTH_CHECK=$(curl -s http://localhost:8002/health 2>/dev/null)
            if [[ "$HEALTH_CHECK" == *"healthy"* ]]; then
                echo -e "${GREEN}✅ Serviço de configuração está saudável!${NC}"
                return 0
            else
                echo -e "${YELLOW}⏳ Tentativa $ATTEMPT de $MAX_ATTEMPTS: Serviço em execução, mas health check falhou. Tentando novamente em ${SLEEP_TIME}s...${NC}"
            fi
        else
            echo -e "${YELLOW}⏳ Tentativa $ATTEMPT de $MAX_ATTEMPTS: Serviço não está em execução. Tentando novamente em ${SLEEP_TIME}s...${NC}"
        fi

        sleep $SLEEP_TIME
        ATTEMPT=$((ATTEMPT + 1))
    done

    echo -e "${RED}⚠️ Serviço de configuração pode não ter iniciado corretamente após $MAX_ATTEMPTS tentativas. Verifique os logs.${NC}"
    return 1
}

# Função para iniciar o visualizador de configurações
start_config_viewer() {
    show_header "🚀 INICIANDO VISUALIZADOR DE CONFIGURAÇÕES"

    echo -e "${BLUE}🖥️ Iniciando visualizador de configurações...${NC}"
    cd "${CONFIG_VIEWER_DIR}" && python app.py > "${CONFIG_VIEWER_LOG}" 2>&1 &
    CONFIG_VIEWER_PID=$!
    echo -e "${GREEN}✅ Visualizador de configurações iniciado com PID: ${CONFIG_VIEWER_PID}${NC}"

    # Aguardar o visualizador iniciar
    echo -e "${YELLOW}⏳ Aguardando o visualizador de configurações iniciar (10 segundos)...${NC}"

    # Verificar saúde do serviço com tentativas
    MAX_ATTEMPTS=10
    ATTEMPT=1
    SLEEP_TIME=1

    while [ $ATTEMPT -le $MAX_ATTEMPTS ]; do
        if kill -0 $CONFIG_VIEWER_PID 2>/dev/null; then
            # Verificar saúde do serviço
            HEALTH_CHECK=$(curl -s http://localhost:8080/health 2>/dev/null)
            if [[ -n "$HEALTH_CHECK" ]]; then
                echo -e "${GREEN}✅ Visualizador de configurações iniciado com sucesso!${NC}"
                echo -e "${GREEN}✅ Acesse o visualizador em: http://localhost:8080${NC}"
                return 0
            else
                echo -e "${YELLOW}⏳ Tentativa $ATTEMPT de $MAX_ATTEMPTS: Serviço em execução, mas health check falhou. Tentando novamente em ${SLEEP_TIME}s...${NC}"
            fi
        else
            echo -e "${YELLOW}⏳ Tentativa $ATTEMPT de $MAX_ATTEMPTS: Serviço não está em execução. Tentando novamente em ${SLEEP_TIME}s...${NC}"
        fi

        sleep $SLEEP_TIME
        ATTEMPT=$((ATTEMPT + 1))
    done

    echo -e "${RED}⚠️ Visualizador de configurações pode não ter iniciado corretamente após $MAX_ATTEMPTS tentativas. Verifique os logs.${NC}"
    return 1
}

# Função para iniciar o servidor principal
start_server() {
    show_header "🚀 INICIANDO SERVIDOR PRINCIPAL"

    echo -e "${BLUE}🖥️ Iniciando servidor principal...${NC}"
    cd "${BASE_DIR}" && python -m uvicorn main:app --host 0.0.0.0 --port 8001 > "${SERVER_LOG}" 2>&1 &
    SERVER_PID=$!
    echo -e "${GREEN}✅ Servidor principal iniciado com PID: ${SERVER_PID}${NC}"

    # Aguardar o servidor iniciar
    echo -e "${YELLOW}⏳ Aguardando o servidor principal iniciar (10 segundos)...${NC}"

    # Verificar saúde do serviço com tentativas
    MAX_ATTEMPTS=10
    ATTEMPT=1
    SLEEP_TIME=1

    while [ $ATTEMPT -le $MAX_ATTEMPTS ]; do
        if kill -0 $SERVER_PID 2>/dev/null; then
            # Verificar se o servidor está respondendo
            SERVER_CHECK=$(curl -s http://localhost:8001 2>/dev/null)
            if [[ -n "$SERVER_CHECK" ]]; then
                echo -e "${GREEN}✅ Servidor principal iniciado com sucesso!${NC}"
                return 0
            else
                echo -e "${YELLOW}⏳ Tentativa $ATTEMPT de $MAX_ATTEMPTS: Servidor em execução, mas não está respondendo. Tentando novamente em ${SLEEP_TIME}s...${NC}"
            fi
        else
            echo -e "${YELLOW}⏳ Tentativa $ATTEMPT de $MAX_ATTEMPTS: Servidor não está em execução. Tentando novamente em ${SLEEP_TIME}s...${NC}"
        fi

        sleep $SLEEP_TIME
        ATTEMPT=$((ATTEMPT + 1))
    done

    echo -e "${RED}⚠️ Servidor principal pode não ter iniciado corretamente após $MAX_ATTEMPTS tentativas. Verifique os logs.${NC}"
    return 1
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

    # Usar o script de monitoramento de logs simples
    "${BASE_DIR}/scripts/logs_simples.sh"
}

# Função para mostrar informações de acesso
show_access_info() {
    show_header "📊 INFORMAÇÕES DE ACESSO"

    echo -e "${GREEN}✅ Servidor principal: http://localhost:8001${NC}"
    echo -e "${GREEN}✅ Serviço de configuração: http://localhost:8002${NC}"
    echo -e "${GREEN}✅ Documentação da API: http://localhost:8002/docs${NC}"
    echo -e "${GREEN}✅ Visualizador de configurações: http://localhost:8080${NC}"
    echo -e "${YELLOW}⚠️ Usuário: admin${NC}"
    echo -e "${YELLOW}⚠️ Senha: Config@Viewer2025!${NC}"
}

# Executar funções
kill_processes
start_config_service
start_config_viewer
start_server
show_access_info
monitor_logs
