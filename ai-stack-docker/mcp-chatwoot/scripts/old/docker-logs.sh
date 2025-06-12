#!/bin/bash

# Cores para saída
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Nome do contêiner
CONTAINER_NAME="mcp-chatwoot"

# Função de ajuda
show_help() {
    echo -e "${BLUE}=== Monitor de Logs do MCP-Chatwoot ===${NC}"
    echo -e "Uso: $0 [opção]"
    echo -e "\nOpções:"
    echo -e "  all       - Exibe todos os logs (padrão)"
    echo -e "  follow    - Acompanha os logs em tempo real"
    echo -e "  errors    - Exibe apenas erros e avisos"
    echo -e "  webhook   - Exibe logs relacionados a webhooks"
    echo -e "  health    - Exibe logs relacionados ao health check"
    echo -e "  help      - Exibe esta mensagem de ajuda"
    echo -e "\nExemplo: $0 follow"
}

# Verificar se o contêiner está em execução
check_container() {
    if ! docker ps -q -f name=$CONTAINER_NAME | grep -q .; then
        echo -e "${RED}Erro: O contêiner $CONTAINER_NAME não está em execução${NC}"
        echo -e "${YELLOW}Inicie o contêiner primeiro com: docker-compose up -d${NC}"
        exit 1
    fi
}

# Exibir todos os logs
show_all_logs() {
    echo -e "${BLUE}=== Exibindo todos os logs do $CONTAINER_NAME ===${NC}"
    docker logs $CONTAINER_NAME
}

# Acompanhar logs em tempo real
follow_logs() {
    echo -e "${BLUE}=== Monitorando logs do $CONTAINER_NAME em tempo real ===${NC}"
    echo -e "${YELLOW}Pressione Ctrl+C para sair${NC}"
    docker logs -f $CONTAINER_NAME
}

# Exibir apenas erros e avisos
show_errors() {
    echo -e "${BLUE}=== Exibindo erros e avisos do $CONTAINER_NAME ===${NC}"
    docker logs $CONTAINER_NAME 2>&1 | grep -E "ERROR|WARN|Exception|Error:|Warning:|Failed|Traceback"
}

# Exibir logs relacionados a webhooks
show_webhook_logs() {
    echo -e "${BLUE}=== Exibindo logs de webhook do $CONTAINER_NAME ===${NC}"
    docker logs $CONTAINER_NAME 2>&1 | grep -E "webhook|Webhook|WEBHOOK|/webhook"
}

# Exibir logs relacionados ao health check
show_health_logs() {
    echo -e "${BLUE}=== Exibindo logs de health check do $CONTAINER_NAME ===${NC}"
    docker logs $CONTAINER_NAME 2>&1 | grep -E "health|Health|/health|status"
}

# Verificar se o contêiner está em execução
check_container

# Processamento dos argumentos
case "${1:-all}" in
    all)
        show_all_logs
        ;;
    follow)
        follow_logs
        ;;
    errors)
        show_errors
        ;;
    webhook)
        show_webhook_logs
        ;;
    health)
        show_health_logs
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo -e "${RED}Opção inválida: $1${NC}"
        show_help
        exit 1
        ;;
esac
