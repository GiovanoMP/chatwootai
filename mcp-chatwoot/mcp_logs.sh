#!/bin/bash

# Cores para saída
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Arquivo de log
LOG_FILE="mcp_chatwoot.log"

# Função para limpar os logs
clear_logs() {
    echo -e "${YELLOW}Limpando logs...${NC}"
    echo "$(date) - Logs limpos" > $LOG_FILE
    echo -e "${GREEN}Logs limpos com sucesso.${NC}"
}

# Função para mostrar os logs completos
show_all_logs() {
    echo -e "${BLUE}=== Logs completos do MCP-Chatwoot ===${NC}"
    echo -e "${YELLOW}Pressione Ctrl+C para sair${NC}"
    echo ""
    strings $LOG_FILE | less
}

# Função para mostrar apenas logs importantes
show_important_logs() {
    echo -e "${BLUE}=== Logs importantes do MCP-Chatwoot ===${NC}"
    echo -e "${YELLOW}Pressione Ctrl+C para sair${NC}"
    echo ""
    strings $LOG_FILE | grep -E "ERROR|WARNING|Webhook recebido|Payload completo|Mensagem recebida|POST /webhook" | less
}

# Função para monitorar logs em tempo real (todos)
monitor_all_logs() {
    echo -e "${BLUE}=== Monitorando todos os logs em tempo real ===${NC}"
    echo -e "${YELLOW}Pressione Ctrl+C para sair${NC}"
    echo ""
    tail -f $LOG_FILE | strings
}

# Função para monitorar logs importantes em tempo real
monitor_important_logs() {
    echo -e "${BLUE}=== Monitorando logs importantes em tempo real ===${NC}"
    echo -e "${YELLOW}Pressione Ctrl+C para sair${NC}"
    echo ""
    
    tail -f $LOG_FILE | strings | grep --line-buffered -E "ERROR|WARNING|Webhook recebido|Payload completo|Mensagem recebida|POST /webhook" | \
    sed -e "s/ERROR/${RED}ERROR${NC}/g" \
        -e "s/WARNING/${YELLOW}WARNING${NC}/g" \
        -e "s/Webhook recebido/${GREEN}Webhook recebido${NC}/g" \
        -e "s/Payload completo/${BLUE}Payload completo${NC}/g" \
        -e "s/Mensagem recebida/${CYAN}Mensagem recebida${NC}/g" \
        -e "s/POST \/webhook/${PURPLE}POST \/webhook${NC}/g"
}

# Função para monitorar apenas webhooks
monitor_webhooks() {
    echo -e "${BLUE}=== Monitorando webhooks em tempo real ===${NC}"
    echo -e "${YELLOW}Pressione Ctrl+C para sair${NC}"
    echo ""
    
    tail -f $LOG_FILE | strings | grep --line-buffered -E "Webhook recebido|Payload completo|POST /webhook" | \
    sed -e "s/Webhook recebido/${GREEN}Webhook recebido${NC}/g" \
        -e "s/Payload completo/${BLUE}Payload completo${NC}/g" \
        -e "s/POST \/webhook/${PURPLE}POST \/webhook${NC}/g"
}

# Função para mostrar ajuda
show_help() {
    echo -e "${BLUE}=== MCP-Chatwoot Log Manager ===${NC}"
    echo -e "Uso: $0 [comando]"
    echo -e ""
    echo -e "Comandos:"
    echo -e "  ${GREEN}all${NC}        - Mostra todos os logs"
    echo -e "  ${GREEN}important${NC}   - Mostra apenas logs importantes"
    echo -e "  ${GREEN}monitor${NC}     - Monitora todos os logs em tempo real"
    echo -e "  ${GREEN}watch${NC}       - Monitora logs importantes em tempo real (padrão)"
    echo -e "  ${GREEN}webhooks${NC}    - Monitora apenas webhooks em tempo real"
    echo -e "  ${RED}clear${NC}       - Limpa os logs"
    echo -e "  ${BLUE}help${NC}        - Mostra esta ajuda"
    echo -e ""
    echo -e "Se nenhum comando for fornecido, os logs importantes serão monitorados em tempo real."
}

# Verificar se o arquivo de log existe
if [ ! -f "$LOG_FILE" ]; then
    echo -e "${RED}Arquivo de log não encontrado: $LOG_FILE${NC}"
    echo -e "${YELLOW}Criando arquivo de log vazio...${NC}"
    echo "$(date) - Log iniciado" > $LOG_FILE
    echo -e "${GREEN}Arquivo de log criado.${NC}"
fi

# Processar comando
case "$1" in
    all)
        show_all_logs
        ;;
    important)
        show_important_logs
        ;;
    monitor)
        monitor_all_logs
        ;;
    watch)
        monitor_important_logs
        ;;
    webhooks)
        monitor_webhooks
        ;;
    clear)
        clear_logs
        ;;
    help)
        show_help
        ;;
    *)
        # Se nenhum comando for fornecido, monitora logs importantes em tempo real
        monitor_important_logs
        ;;
esac

exit 0
