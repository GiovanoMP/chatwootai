#!/bin/bash

# Cores para saída
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Configurações
CONTAINER_NAME="mcp-chatwoot"

# Arquivo temporário para armazenar o último timestamp
TIMESTAMP_FILE="/tmp/mcp_chatwoot_last_log.timestamp"

# Função para verificar se o contêiner está em execução
check_container() {
    if ! docker ps -q -f name=$CONTAINER_NAME | grep -q .; then
        echo -e "${RED}✗ Contêiner $CONTAINER_NAME não está em execução${NC}"
        echo -e "${YELLOW}Inicie o contêiner primeiro com: docker-compose up -d${NC}"
        return 1
    fi
    return 0
}

# Função para salvar o timestamp atual
save_timestamp() {
    date +%s > "$TIMESTAMP_FILE"
}

# Função para obter o timestamp salvo ou retornar 0 se não existir
get_timestamp() {
    if [ -f "$TIMESTAMP_FILE" ]; then
        cat "$TIMESTAMP_FILE"
    else
        echo "0"
    fi
}

# Função para limpar o timestamp salvo
clear_timestamp() {
    rm -f "$TIMESTAMP_FILE"
    echo -e "${GREEN}Histórico de logs reiniciado${NC}"
}

# Função para mostrar todos os logs
show_all_logs() {
    echo -e "${BLUE}=== Todos os logs do $CONTAINER_NAME ===${NC}"
    echo ""
    docker logs $CONTAINER_NAME
}

# Função para mostrar logs recentes (desde o último acesso)
show_recent_logs() {
    local timestamp=$(get_timestamp)
    echo -e "${BLUE}=== Logs recentes do $CONTAINER_NAME (desde o último acesso) ===${NC}"
    echo ""
    
    if [ "$timestamp" = "0" ]; then
        echo -e "${YELLOW}Nenhum registro de acesso anterior. Mostrando todos os logs.${NC}"
        docker logs $CONTAINER_NAME
    else
        local since_time=$(date -d @$timestamp +"%Y-%m-%dT%H:%M:%S")
        echo -e "${YELLOW}Mostrando logs desde: $since_time${NC}"
        docker logs --since="$since_time" $CONTAINER_NAME
    fi
    
    # Atualiza o timestamp para o próximo acesso
    save_timestamp
}

# Função para mostrar apenas logs importantes
show_important_logs() {
    echo -e "${BLUE}=== Logs importantes do $CONTAINER_NAME ===${NC}"
    echo -e "${YELLOW}Filtrando mensagens de webhook, erros e avisos${NC}"
    echo ""
    docker logs $CONTAINER_NAME 2>&1 | grep -E "ERROR|WARNING|Webhook recebido|Payload completo|Mensagem recebida|POST /webhook|Mensagem enviada|conversation.created|conversation.updated|message.created" | \
    sed -e "s/\(3\[0;\|3\[1;\)\([0-9]\+\)m//g" | \
    sed -e "s/ERROR/${RED}ERROR${NC}/g" \
        -e "s/WARNING/${YELLOW}WARNING${NC}/g" \
        -e "s/Webhook recebido/${GREEN}Webhook recebido${NC}/g" \
        -e "s/Payload completo/${CYAN}Payload completo${NC}/g" \
        -e "s/Mensagem recebida/${PURPLE}Mensagem recebida${NC}/g" \
        -e "s/Mensagem enviada/${GREEN}Mensagem enviada${NC}/g" \
        -e "s/conversation.created/${BLUE}conversation.created${NC}/g" \
        -e "s/conversation.updated/${BLUE}conversation.updated${NC}/g" \
        -e "s/message.created/${CYAN}message.created${NC}/g" \
        -e "s/POST \/webhook/${BLUE}POST \/webhook${NC}/g"
    
    # Atualiza o timestamp para o próximo acesso
    save_timestamp
}

# Função para mostrar apenas logs importantes recentes
show_recent_important_logs() {
    local timestamp=$(get_timestamp)
    echo -e "${BLUE}=== Logs importantes recentes do $CONTAINER_NAME ===${NC}"
    echo -e "${YELLOW}Filtrando mensagens de webhook, erros e avisos${NC}"
    echo ""
    
    if [ "$timestamp" = "0" ]; then
        echo -e "${YELLOW}Nenhum registro de acesso anterior. Mostrando todos os logs importantes.${NC}"
        show_important_logs
        return
    fi
    
    local since_time=$(date -d @$timestamp +"%Y-%m-%dT%H:%M:%S")
    echo -e "${YELLOW}Mostrando logs desde: $since_time${NC}"
    
    docker logs --since="$since_time" $CONTAINER_NAME 2>&1 | grep -E "ERROR|WARNING|Webhook recebido|Payload completo|Mensagem recebida|POST /webhook|Mensagem enviada|conversation.created|conversation.updated|message.created" | \
    sed -e "s/\(3\[0;\|3\[1;\)\([0-9]\+\)m//g" | \
    sed -e "s/ERROR/${RED}ERROR${NC}/g" \
        -e "s/WARNING/${YELLOW}WARNING${NC}/g" \
        -e "s/Webhook recebido/${GREEN}Webhook recebido${NC}/g" \
        -e "s/Payload completo/${CYAN}Payload completo${NC}/g" \
        -e "s/Mensagem recebida/${PURPLE}Mensagem recebida${NC}/g" \
        -e "s/Mensagem enviada/${GREEN}Mensagem enviada${NC}/g" \
        -e "s/conversation.created/${BLUE}conversation.created${NC}/g" \
        -e "s/conversation.updated/${BLUE}conversation.updated${NC}/g" \
        -e "s/message.created/${CYAN}message.created${NC}/g" \
        -e "s/POST \/webhook/${BLUE}POST \/webhook${NC}/g"
    
    # Atualiza o timestamp para o próximo acesso
    save_timestamp
}

# Função para monitorar logs em tempo real (todos)
monitor_all_logs() {
    echo -e "${BLUE}=== Monitorando todos os logs em tempo real ===${NC}"
    echo -e "${YELLOW}Pressione Ctrl+C para sair${NC}"
    echo -e "${YELLOW}Aguardando novas mensagens...${NC}"
    echo ""
    
    # Usar --tail=0 para mostrar apenas novos logs, sem histórico
    docker logs -f --tail=0 $CONTAINER_NAME
}

# Função para monitorar logs importantes em tempo real
monitor_important_logs() {
    echo -e "${BLUE}=== Monitorando logs importantes em tempo real ===${NC}"
    echo -e "${YELLOW}Pressione Ctrl+C para sair${NC}"
    echo ""
    
    # Usar --tail=0 para mostrar apenas novos logs, sem histórico
    # Usar stdbuf -oL para garantir saída em tempo real sem buffer
    docker logs -f --tail=0 $CONTAINER_NAME 2>&1 | stdbuf -oL grep -E "ERROR|WARNING|Webhook recebido|Payload completo|Mensagem recebida|POST /webhook|Mensagem enviada|conversation.created|conversation.updated|message.created|message_created|message_updated" | \
    stdbuf -oL sed -r "s/\x1B\[([0-9]{1,2}(;[0-9]{1,2})?)?[mGK]//g" | \
    stdbuf -oL sed -e "s/ERROR/${RED}ERROR${NC}/g" \
        -e "s/WARNING/${YELLOW}WARNING${NC}/g" \
        -e "s/Webhook recebido/${GREEN}Webhook recebido${NC}/g" \
        -e "s/Payload completo/${CYAN}Payload completo${NC}/g" \
        -e "s/Mensagem recebida/${PURPLE}Mensagem recebida${NC}/g" \
        -e "s/Mensagem enviada/${GREEN}Mensagem enviada${NC}/g" \
        -e "s/conversation.created/${BLUE}conversation.created${NC}/g" \
        -e "s/conversation.updated/${BLUE}conversation.updated${NC}/g" \
        -e "s/message.created/${CYAN}message.created${NC}/g" \
        -e "s/message_created/${CYAN}message_created${NC}/g" \
        -e "s/message_updated/${CYAN}message_updated${NC}/g" \
        -e "s/POST \/webhook/${BLUE}POST \/webhook${NC}/g"
}

# Função para mostrar logs de erros
show_errors() {
    echo -e "${BLUE}=== Logs de erros do $CONTAINER_NAME ===${NC}"
    echo ""
    docker logs $CONTAINER_NAME 2>&1 | grep -E "ERROR|Exception|Error:|Failed|Traceback" | \
    sed -e "s/ERROR/${RED}ERROR${NC}/g" \
        -e "s/Exception/${RED}Exception${NC}/g" \
        -e "s/Error:/${RED}Error:${NC}/g" \
        -e "s/Failed/${RED}Failed${NC}/g" \
        -e "s/Traceback/${RED}Traceback${NC}/g"
}

# Função para mostrar logs de webhook e mensagens
show_webhook_logs() {
    echo -e "${BLUE}=== Logs de webhook e mensagens do $CONTAINER_NAME ===${NC}"
    echo -e "${YELLOW}Pressione Ctrl+C para sair${NC}"
    echo -e "${YELLOW}Aguardando novas mensagens...${NC}"
    echo ""
    
    # Usar --tail=0 para mostrar apenas novos logs, sem histórico
    # Usar stdbuf -oL para garantir saída em tempo real sem buffer
    docker logs -f --tail=0 $CONTAINER_NAME 2>&1 | \
    stdbuf -oL grep -E "webhook|Webhook|WEBHOOK|/webhook|Mensagem recebida|Mensagem enviada|conversation.created|conversation.updated|message.created|message_created|message_updated|Payload completo|POST /webhook|INFO:.*POST /webhook" | \
    stdbuf -oL sed -r "s/\x1B\[([0-9]{1,2}(;[0-9]{1,2})?)?[mGK]//g" | \
    stdbuf -oL sed -e "s/webhook/${GREEN}webhook${NC}/g" \
        -e "s/Webhook/${GREEN}Webhook${NC}/g" \
        -e "s/WEBHOOK/${GREEN}WEBHOOK${NC}/g" \
        -e "s/\/webhook/${GREEN}\/webhook${NC}/g" \
        -e "s/Mensagem recebida/${PURPLE}Mensagem recebida${NC}/g" \
        -e "s/Mensagem enviada/${GREEN}Mensagem enviada${NC}/g" \
        -e "s/conversation.created/${BLUE}conversation.created${NC}/g" \
        -e "s/conversation.updated/${BLUE}conversation.updated${NC}/g" \
        -e "s/message.created/${CYAN}message.created${NC}/g" \
        -e "s/message_created/${CYAN}message_created${NC}/g" \
        -e "s/message_updated/${CYAN}message_updated${NC}/g" \
        -e "s/Payload completo/${YELLOW}Payload completo${NC}/g" \
        -e "s/POST \/webhook/${BLUE}POST \/webhook${NC}/g"
}

# Função para limpar logs
clear_logs() {
    docker logs -c $CONTAINER_NAME > /dev/null
    echo -e "${GREEN}Logs limpos com sucesso${NC}"
}

# Função de ajuda
show_help() {
    echo -e "${BLUE}=== Script de Monitoramento de Logs do MCP-Chatwoot ===${NC}"
    echo -e "Uso: $0 [comando]"
    echo -e "Comandos disponíveis:"
    echo -e "  ${GREEN}all${NC} - Exibe todos os logs"
    echo -e "  ${GREEN}recent${NC} - Exibe logs desde o último acesso"
    echo -e "  ${GREEN}follow${NC} - Acompanha os logs em tempo real"
    echo -e "  ${GREEN}important${NC} - Exibe apenas logs importantes"
    echo -e "  ${GREEN}recent-important${NC} - Exibe logs importantes desde o último acesso"
    echo -e "  ${GREEN}follow-important${NC} - Acompanha os logs importantes em tempo real"
    echo -e "  ${GREEN}errors${NC} - Exibe apenas logs de erros"
    echo -e "  ${GREEN}webhook${NC} - Exibe logs de webhook e mensagens do Chatwoot"
    echo -e "  ${GREEN}clear${NC} - Limpa o histórico de logs (reinicia o timestamp)"
    echo -e "  ${GREEN}clear-logs${NC} - Limpa os logs do contêiner"
    echo -e "  ${GREEN}help${NC} - Exibe esta mensagem de ajuda"
}

# Verificar se o contêiner está em execução
if ! check_container; then
    exit 1
fi

# Processamento dos argumentos
case "$1" in
    all|"")
        show_all_logs
        ;;
    recent)
        show_recent_logs
        ;;
    follow)
        monitor_all_logs
        ;;
    important)
        show_important_logs
        ;;
    recent-important)
        show_recent_important_logs
        ;;
    follow-important)
        monitor_important_logs
        ;;
    errors)
        show_errors
        ;;
    webhook)
        show_webhook_logs
        ;;
    clear)
        clear_timestamp
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo -e "${RED}Comando inválido: $1${NC}"
        show_help
        exit 1
        ;;
esac
