#!/bin/bash

# Cores para saída
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Arquivo para salvar a URL do ngrok
URL_FILE="ngrok_url.txt"
SERVER_PORT=8004

# Função para verificar se o servidor está rodando
check_server() {
    PID=$(pgrep -f "uvicorn main:app")
    if [ -n "$PID" ]; then
        echo -e "${GREEN}✓ Servidor MCP-Chatwoot está rodando (PID: $PID)${NC}"
        return 0
    else
        echo -e "${RED}✗ Servidor MCP-Chatwoot não está rodando${NC}"
        echo -e "${YELLOW}Execute ./mcp_server.sh para iniciar o servidor primeiro${NC}"
        return 1
    fi
}

# Função para verificar se o ngrok está rodando
check_ngrok() {
    PID=$(pgrep -f "ngrok http $SERVER_PORT")
    if [ -n "$PID" ]; then
        echo -e "${GREEN}✓ Ngrok está rodando (PID: $PID)${NC}"
        
        # Verificar se o dashboard do ngrok está acessível
        if curl -s http://localhost:4040/api/tunnels > /dev/null; then
            # Obter a URL pública do ngrok
            URL=$(curl -s http://localhost:4040/api/tunnels | grep -o '"public_url":"[^"]*' | grep -o 'http[^"]*' | head -1)
            if [ -n "$URL" ]; then
                echo -e "${GREEN}URL pública: $URL${NC}"
                echo "$URL" > $URL_FILE
                echo -e "${BLUE}URL salva em: $URL_FILE${NC}"
                
                # Verificar se o túnel está acessível
                echo -e "${YELLOW}Testando acesso ao túnel...${NC}"
                HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$URL/webhook")
                if [ "$HTTP_CODE" = "405" ]; then
                    # 405 é esperado porque estamos fazendo GET em um endpoint POST
                    echo -e "${GREEN}✓ Túnel ngrok está acessível${NC}"
                else
                    echo -e "${RED}✗ Túnel ngrok retornou código HTTP inesperado: $HTTP_CODE${NC}"
                    echo -e "${YELLOW}O túnel pode estar com problemas de acesso.${NC}"
                fi
            else
                echo -e "${RED}✗ Não foi possível obter a URL do ngrok${NC}"
                return 1
            fi
        else
            echo -e "${RED}✗ Dashboard do ngrok não está acessível${NC}"
            echo -e "${YELLOW}O processo ngrok pode estar em estado inconsistente.${NC}"
            return 1
        fi
        return 0
    else
        echo -e "${RED}✗ Ngrok não está rodando${NC}"
        return 1
    fi
}

# Função para parar o ngrok
stop_ngrok() {
    PID=$(pgrep -f "ngrok http $SERVER_PORT")
    if [ -n "$PID" ]; then
        echo -e "${YELLOW}Parando ngrok (PID: $PID)...${NC}"
        kill $PID
        sleep 2
        if pgrep -f "ngrok http $SERVER_PORT" > /dev/null; then
            echo -e "${RED}Falha ao parar o ngrok. Tentando kill -9...${NC}"
            kill -9 $PID
            sleep 1
        fi
        if ! pgrep -f "ngrok http $SERVER_PORT" > /dev/null; then
            echo -e "${GREEN}Ngrok parado com sucesso.${NC}"
        else
            echo -e "${RED}Não foi possível parar o ngrok.${NC}"
            return 1
        fi
    else
        echo -e "${YELLOW}Ngrok não está rodando.${NC}"
    fi
    return 0
}

# Função para iniciar o ngrok
start_ngrok() {
    echo -e "${BLUE}Iniciando túnel ngrok para a porta $SERVER_PORT...${NC}"
    nohup ngrok http $SERVER_PORT > ngrok.log 2>&1 &
    sleep 3
    if check_ngrok; then
        echo -e "${GREEN}Túnel ngrok iniciado com sucesso!${NC}"
        URL=$(cat $URL_FILE)
        echo -e ""
        echo -e "${BLUE}=== Instruções para configurar no Chatwoot ===${NC}"
        echo -e "1. Acesse o painel administrativo do Chatwoot"
        echo -e "2. Vá para Configurações -> Webhooks -> Adicionar Webhook"
        echo -e "3. Forneça um nome para o webhook (ex: 'MCP Integration')"
        echo -e "4. No campo 'URL' coloque: ${GREEN}$URL/webhook${NC}"
        echo -e "5. Selecione TODOS os eventos, especialmente 'message_created'"
        echo -e "6. Salve o webhook"
        echo -e ""
        echo -e "${YELLOW}Pressione CTRL+C para encerrar o túnel ngrok quando terminar${NC}"
        return 0
    else
        echo -e "${RED}Falha ao iniciar o túnel ngrok. Verifique os logs em ngrok.log${NC}"
        return 1
    fi
}

# Função para reiniciar o ngrok
restart_ngrok() {
    echo -e "${BLUE}Reiniciando túnel ngrok...${NC}"
    stop_ngrok
    start_ngrok
}

# Função para mostrar ajuda
show_help() {
    echo -e "${BLUE}=== MCP-Chatwoot Ngrok Manager ===${NC}"
    echo -e "Uso: $0 [comando]"
    echo -e ""
    echo -e "Comandos:"
    echo -e "  ${GREEN}start${NC}    - Inicia o túnel ngrok"
    echo -e "  ${RED}stop${NC}     - Para o túnel ngrok"
    echo -e "  ${YELLOW}restart${NC}  - Reinicia o túnel ngrok"
    echo -e "  ${BLUE}status${NC}   - Verifica o status do túnel ngrok"
    echo -e "  ${BLUE}help${NC}     - Mostra esta ajuda"
    echo -e ""
    echo -e "Se nenhum comando for fornecido, o status será verificado e o túnel será iniciado se não estiver rodando."
}

# Processar comando
case "$1" in
    start)
        check_server && (check_ngrok || start_ngrok)
        ;;
    stop)
        stop_ngrok
        ;;
    restart)
        check_server && restart_ngrok
        ;;
    status)
        check_ngrok
        ;;
    help)
        show_help
        ;;
    *)
        # Se nenhum comando for fornecido, verifica o status e inicia se não estiver rodando
        check_server && (check_ngrok || start_ngrok)
        ;;
esac

exit 0
