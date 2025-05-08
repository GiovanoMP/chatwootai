#!/bin/bash

# Script para reiniciar o serviço de configuração e o visualizador de configurações

# Cores para saída
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Diretório base
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONFIG_SERVICE_DIR="${BASE_DIR}/config-service"
CONFIG_VIEWER_DIR="${BASE_DIR}/config-viewer"

# Função para exibir cabeçalho
show_header() {
    echo -e "\n${YELLOW}======================================================================${NC}"
    echo -e "${GREEN}$1${NC}"
    echo -e "${YELLOW}======================================================================${NC}"
}

# Função para matar processos
kill_processes() {
    show_header "🚀 REINICIANDO SERVIÇOS DE CONFIGURAÇÃO"
    
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
    echo -e "${BLUE}🖥️ Iniciando serviço de configuração...${NC}"
    cd "${CONFIG_SERVICE_DIR}" && python run.py > /dev/null 2>&1 &
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
    cd "${CONFIG_VIEWER_DIR}" && python app.py > /dev/null 2>&1 &
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

# Função para verificar a saúde do serviço de configuração
check_config_service_health() {
    echo -e "${BLUE}🔍 Verificando saúde do serviço de configuração...${NC}"
    HEALTH_CHECK=$(curl -s http://localhost:8002/health)
    if [[ "$HEALTH_CHECK" == *"healthy"* ]]; then
        echo -e "${GREEN}✅ Serviço de configuração está saudável!${NC}"
        echo -e "${GREEN}✅ Resposta: ${HEALTH_CHECK}${NC}"
    else
        echo -e "${RED}⚠️ Serviço de configuração pode não estar saudável. Resposta: ${HEALTH_CHECK}${NC}"
    fi
}

# Função para verificar a saúde do visualizador de configurações
check_config_viewer_health() {
    echo -e "${BLUE}🔍 Verificando saúde do visualizador de configurações...${NC}"
    HEALTH_CHECK=$(curl -s http://localhost:8080)
    if [[ "$HEALTH_CHECK" == *"login"* ]]; then
        echo -e "${GREEN}✅ Visualizador de configurações está saudável!${NC}"
    else
        echo -e "${RED}⚠️ Visualizador de configurações pode não estar saudável.${NC}"
    fi
}

# Função para exibir informações de acesso
show_access_info() {
    show_header "📊 INFORMAÇÕES DE ACESSO"
    
    echo -e "${GREEN}✅ Serviço de configuração: http://localhost:8002${NC}"
    echo -e "${GREEN}✅ Documentação da API: http://localhost:8002/docs${NC}"
    echo -e "${GREEN}✅ Visualizador de configurações: http://localhost:8080${NC}"
    echo -e "${YELLOW}⚠️ Usuário: admin${NC}"
    echo -e "${YELLOW}⚠️ Senha: Config@Viewer2025!${NC}"
    
    echo -e "\n${BLUE}📝 Para monitorar os logs, execute:${NC}"
    echo -e "${YELLOW}   cd ${BASE_DIR} && ./scripts/restart_and_monitor_all.sh${NC}"
}

# Executar funções
kill_processes
start_config_service
start_config_viewer
check_config_service_health
check_config_viewer_health
show_access_info
