#!/bin/bash

# Script simplificado para reiniciar apenas o serviço de configuração

# Cores para saída
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Diretório base
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONFIG_SERVICE_DIR="${BASE_DIR}/config-service"

# Função para exibir cabeçalho
show_header() {
    echo -e "\n${YELLOW}======================================================================${NC}"
    echo -e "${GREEN}$1${NC}"
    echo -e "${YELLOW}======================================================================${NC}"
}

# Função para matar processos
kill_processes() {
    show_header "🚀 REINICIANDO SERVIÇO DE CONFIGURAÇÃO"
    
    echo -e "${BLUE}🔍 Procurando processos do serviço de configuração...${NC}"
    CONFIG_SERVICE_PIDS=$(pgrep -f "python.*run.py")
    if [[ -n "$CONFIG_SERVICE_PIDS" ]]; then
        echo -e "${RED}🛑 Matando processo do serviço de configuração (PID: ${CONFIG_SERVICE_PIDS})...${NC}"
        kill -9 $CONFIG_SERVICE_PIDS
        echo -e "${GREEN}✅ Processo do serviço de configuração finalizado${NC}"
    else
        echo -e "${YELLOW}⚠️ Nenhum processo do serviço de configuração encontrado${NC}"
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

# Função para verificar a saúde do serviço
check_health() {
    echo -e "${BLUE}🔍 Verificando saúde do serviço de configuração...${NC}"
    HEALTH_CHECK=$(curl -s http://localhost:8002/health)
    if [[ "$HEALTH_CHECK" == *"healthy"* ]]; then
        echo -e "${GREEN}✅ Serviço de configuração está saudável!${NC}"
        echo -e "${GREEN}✅ Resposta: ${HEALTH_CHECK}${NC}"
    else
        echo -e "${RED}⚠️ Serviço de configuração pode não estar saudável. Resposta: ${HEALTH_CHECK}${NC}"
    fi
}

# Executar funções
kill_processes
start_config_service
check_health
