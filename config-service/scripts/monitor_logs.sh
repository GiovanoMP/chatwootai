#!/bin/bash

# Script para monitorar os logs do serviço de configuração e do visualizador de configurações

# Cores para saída
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Diretório base
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="${BASE_DIR}/logs"

# Criar diretório de logs se não existir
mkdir -p "${LOG_DIR}"

# Arquivos de log
CONFIG_SERVICE_LOG="${LOG_DIR}/config_service.log"
CONFIG_VIEWER_LOG="${LOG_DIR}/config_viewer.log"

# Função para exibir mensagem de ajuda
show_help() {
    echo -e "${BLUE}Uso: $0 [opções]${NC}"
    echo -e "Opções:"
    echo -e "  -h, --help     Exibe esta mensagem de ajuda"
    echo -e "  -s, --service  Monitora apenas os logs do serviço de configuração"
    echo -e "  -v, --viewer   Monitora apenas os logs do visualizador de configurações"
    echo -e "  -a, --all      Monitora todos os logs (padrão)"
    echo -e "  -c, --clear    Limpa os logs antes de iniciar o monitoramento"
    exit 0
}

# Função para limpar os logs
clear_logs() {
    echo -e "${YELLOW}Limpando logs...${NC}"
    > "${CONFIG_SERVICE_LOG}"
    > "${CONFIG_VIEWER_LOG}"
    echo -e "${GREEN}Logs limpos com sucesso!${NC}"
}

# Função para monitorar os logs do serviço de configuração
monitor_config_service() {
    echo -e "${BLUE}Monitorando logs do serviço de configuração...${NC}"
    echo -e "${YELLOW}Log: ${CONFIG_SERVICE_LOG}${NC}"
    
    # Redirecionar saída padrão e de erro para o arquivo de log
    if [[ -n $(pgrep -f "python.*run.py") ]]; then
        echo -e "${GREEN}Serviço de configuração já está em execução.${NC}"
    else
        echo -e "${YELLOW}Iniciando serviço de configuração...${NC}"
        cd "${BASE_DIR}" && python run.py > "${CONFIG_SERVICE_LOG}" 2>&1 &
        echo -e "${GREEN}Serviço de configuração iniciado com PID: $!${NC}"
    fi
    
    # Monitorar o arquivo de log
    tail -f "${CONFIG_SERVICE_LOG}"
}

# Função para monitorar os logs do visualizador de configurações
monitor_config_viewer() {
    echo -e "${BLUE}Monitorando logs do visualizador de configurações...${NC}"
    echo -e "${YELLOW}Log: ${CONFIG_VIEWER_LOG}${NC}"
    
    # Redirecionar saída padrão e de erro para o arquivo de log
    if [[ -n $(pgrep -f "python.*app.py") ]]; then
        echo -e "${GREEN}Visualizador de configurações já está em execução.${NC}"
    else
        echo -e "${YELLOW}Iniciando visualizador de configurações...${NC}"
        cd "${BASE_DIR}/../config-viewer" && python app.py > "${CONFIG_VIEWER_LOG}" 2>&1 &
        echo -e "${GREEN}Visualizador de configurações iniciado com PID: $!${NC}"
    fi
    
    # Monitorar o arquivo de log
    tail -f "${CONFIG_VIEWER_LOG}"
}

# Função para monitorar todos os logs
monitor_all() {
    echo -e "${BLUE}Monitorando todos os logs...${NC}"
    
    # Iniciar serviços se não estiverem em execução
    if [[ -z $(pgrep -f "python.*run.py") ]]; then
        echo -e "${YELLOW}Iniciando serviço de configuração...${NC}"
        cd "${BASE_DIR}" && python run.py > "${CONFIG_SERVICE_LOG}" 2>&1 &
        echo -e "${GREEN}Serviço de configuração iniciado com PID: $!${NC}"
    else
        echo -e "${GREEN}Serviço de configuração já está em execução.${NC}"
    fi
    
    if [[ -z $(pgrep -f "python.*app.py") ]]; then
        echo -e "${YELLOW}Iniciando visualizador de configurações...${NC}"
        cd "${BASE_DIR}/../config-viewer" && python app.py > "${CONFIG_VIEWER_LOG}" 2>&1 &
        echo -e "${GREEN}Visualizador de configurações iniciado com PID: $!${NC}"
    else
        echo -e "${GREEN}Visualizador de configurações já está em execução.${NC}"
    fi
    
    # Monitorar os arquivos de log
    echo -e "${YELLOW}Monitorando logs...${NC}"
    echo -e "${GREEN}=== CONFIG SERVICE LOG ===${NC}"
    echo -e "${BLUE}=== CONFIG VIEWER LOG ===${NC}"
    tail -f "${CONFIG_SERVICE_LOG}" "${CONFIG_VIEWER_LOG}" | awk '
        /config_service.log/ {print "\033[0;32m[CONFIG SERVICE]\033[0m " $0}
        /config_viewer.log/ {print "\033[0;34m[CONFIG VIEWER]\033[0m " $0}
    '
}

# Processar argumentos
if [[ $# -eq 0 ]]; then
    monitor_all
else
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -h|--help)
                show_help
                ;;
            -s|--service)
                monitor_config_service
                exit 0
                ;;
            -v|--viewer)
                monitor_config_viewer
                exit 0
                ;;
            -a|--all)
                monitor_all
                exit 0
                ;;
            -c|--clear)
                clear_logs
                shift
                ;;
            *)
                echo -e "${RED}Opção inválida: $1${NC}"
                show_help
                ;;
        esac
        shift
    done
fi
