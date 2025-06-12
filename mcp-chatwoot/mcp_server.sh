#!/bin/bash

# Cores para saída
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função para verificar se o servidor está rodando
check_server() {
    PID=$(pgrep -f "uvicorn main:app")
    if [ -n "$PID" ]; then
        echo -e "${GREEN}✓ Servidor MCP-Chatwoot está rodando (PID: $PID)${NC}"
        return 0
    else
        echo -e "${RED}✗ Servidor MCP-Chatwoot não está rodando${NC}"
        return 1
    fi
}

# Função para parar o servidor
stop_server() {
    PID=$(pgrep -f "uvicorn main:app")
    if [ -n "$PID" ]; then
        echo -e "${YELLOW}Parando servidor MCP-Chatwoot (PID: $PID)...${NC}"
        kill $PID
        sleep 2
        if pgrep -f "uvicorn main:app" > /dev/null; then
            echo -e "${RED}Falha ao parar o servidor. Tentando kill -9...${NC}"
            kill -9 $PID
            sleep 1
        fi
        if ! pgrep -f "uvicorn main:app" > /dev/null; then
            echo -e "${GREEN}Servidor parado com sucesso.${NC}"
        else
            echo -e "${RED}Não foi possível parar o servidor.${NC}"
            return 1
        fi
    else
        echo -e "${YELLOW}Servidor não está rodando.${NC}"
    fi
    return 0
}

# Função para iniciar o servidor
start_server() {
    echo -e "${BLUE}Iniciando servidor MCP-Chatwoot...${NC}"
    nohup uvicorn main:app --host 0.0.0.0 --port 8004 --reload > server.log 2>&1 &
    sleep 2
    if check_server; then
        echo -e "${GREEN}Servidor iniciado com sucesso na porta 8004.${NC}"
        echo -e "${BLUE}Logs disponíveis em: server.log${NC}"
        return 0
    else
        echo -e "${RED}Falha ao iniciar o servidor. Verifique os logs em server.log${NC}"
        return 1
    fi
}

# Função para reiniciar o servidor
restart_server() {
    echo -e "${BLUE}Reiniciando servidor MCP-Chatwoot...${NC}"
    stop_server
    start_server
}

# Função para mostrar ajuda
show_help() {
    echo -e "${BLUE}=== MCP-Chatwoot Server Manager ===${NC}"
    echo -e "Uso: $0 [comando]"
    echo -e ""
    echo -e "Comandos:"
    echo -e "  ${GREEN}start${NC}    - Inicia o servidor"
    echo -e "  ${RED}stop${NC}     - Para o servidor"
    echo -e "  ${YELLOW}restart${NC}  - Reinicia o servidor"
    echo -e "  ${BLUE}status${NC}   - Verifica o status do servidor"
    echo -e "  ${BLUE}help${NC}     - Mostra esta ajuda"
    echo -e ""
    echo -e "Se nenhum comando for fornecido, o status será verificado e o servidor será iniciado se não estiver rodando."
}

# Processar comando
case "$1" in
    start)
        check_server || start_server
        ;;
    stop)
        stop_server
        ;;
    restart)
        restart_server
        ;;
    status)
        check_server
        ;;
    help)
        show_help
        ;;
    *)
        # Se nenhum comando for fornecido, verifica o status e inicia se não estiver rodando
        check_server || start_server
        ;;
esac

exit 0
