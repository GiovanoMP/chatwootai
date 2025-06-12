#!/bin/bash

# Cores para saída
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configurações
CONTAINER_NAME="mcp-chatwoot"
URL_FILE="ngrok_url.txt"
SERVER_PORT=8004
NGROK_PID_FILE="ngrok.pid"

# Função para verificar se o contêiner MCP-Chatwoot está rodando
check_container() {
    if ! docker ps -q -f name=$CONTAINER_NAME | grep -q .; then
        echo -e "${RED}✗ Contêiner $CONTAINER_NAME não está rodando${NC}"
        echo -e "${YELLOW}Inicie o contêiner primeiro com: docker-compose up -d${NC}"
        return 1
    else
        echo -e "${GREEN}✓ Contêiner $CONTAINER_NAME está rodando${NC}"
        return 0
    fi
}

# Função para verificar se o NGROK está rodando
check_ngrok() {
    # Verificar se o NGROK está rodando usando ps
    if pgrep -f "ngrok http" > /dev/null; then
        NGROK_PID=$(pgrep -f "ngrok http" | head -1)
        echo -e "${GREEN}✓ NGROK está rodando (PID: $NGROK_PID)${NC}"
        
        # Atualizar o arquivo PID
        echo $NGROK_PID > $NGROK_PID_FILE
        
        # Verificar se o dashboard do NGROK está acessível
        if curl -s http://localhost:4040/api/tunnels > /dev/null; then
            # Obter a URL pública do NGROK
            URL=$(curl -s http://localhost:4040/api/tunnels | grep -o '"public_url":"[^"]*"' | grep -o 'https://[^"]*' | head -1)
            
            if [ -n "$URL" ]; then
                echo -e "${GREEN}URL do NGROK: $URL${NC}"
                echo "$URL" > $URL_FILE
                echo -e "${YELLOW}Esta URL foi salva em $URL_FILE${NC}"
                
                # Verificar se o túnel está acessível
                echo -e "${YELLOW}Testando acesso ao túnel...${NC}"
                HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$URL/webhook")
                if [ "$HTTP_CODE" = "405" ] || [ "$HTTP_CODE" = "404" ]; then
                    # 405 é esperado porque estamos fazendo GET em um endpoint POST
                    # 404 também é aceitável se o endpoint não existir exatamente
                    echo -e "${GREEN}✓ Túnel NGROK está acessível${NC}"
                    echo -e ""
                    echo -e "${BLUE}=== Instruções para configurar no Chatwoot ===${NC}"
                    echo -e "1. Acesse o painel administrativo do Chatwoot"
                    echo -e "2. Vá para Configurações > Integrações > Webhooks"
                    echo -e "3. Configure o webhook com a URL:"
                    echo -e "${CYAN}   $URL/webhook${NC}"
                    echo -e "4. Selecione os eventos: messages.created"
                    echo -e "5. Salve as configurações"
                else
                    echo -e "${RED}✗ Túnel NGROK retornou código HTTP inesperado: $HTTP_CODE${NC}"
                    echo -e "${YELLOW}O túnel pode estar com problemas de acesso.${NC}"
                fi
                return 0
            else
                echo -e "${RED}✗ Não foi possível obter a URL do NGROK${NC}"
                return 1
            fi
        else
            echo -e "${RED}✗ Dashboard do NGROK não está acessível${NC}"
            echo -e "${YELLOW}O processo NGROK pode estar em estado inconsistente.${NC}"
            return 1
        fi
    else
        echo -e "${RED}✗ NGROK não está rodando${NC}"
        if [ -f "$NGROK_PID_FILE" ]; then
            rm -f $NGROK_PID_FILE
        fi
        return 1
    fi
}

# Função para parar o NGROK
stop_ngrok() {
    if [ -f "$NGROK_PID_FILE" ]; then
        PID=$(cat $NGROK_PID_FILE)
        if ps -p $PID > /dev/null; then
            echo -e "${YELLOW}Parando o túnel NGROK (PID: $PID)...${NC}"
            kill $PID
            sleep 2
            if ps -p $PID > /dev/null; then
                echo -e "${RED}Falha ao parar o NGROK. Tentando kill -9...${NC}"
                kill -9 $PID
                sleep 1
            fi
            if ! ps -p $PID > /dev/null; then
                echo -e "${GREEN}Túnel NGROK parado com sucesso${NC}"
            else
                echo -e "${RED}Não foi possível parar o NGROK.${NC}"
                return 1
            fi
        else
            echo -e "${YELLOW}O processo NGROK já está parado (PID inválido)${NC}"
        fi
        
        # Remover os arquivos
        rm -f $NGROK_PID_FILE
        if [ -f "$URL_FILE" ]; then
            rm -f $URL_FILE
        fi
    else
        echo -e "${YELLOW}O túnel NGROK já está parado${NC}"
    fi
    return 0
}

# Função para iniciar o NGROK
start_ngrok() {
    # Verificar se o contêiner MCP-Chatwoot está rodando
    if ! check_container; then
        return 1
    fi
    
    # Parar qualquer instância anterior do NGROK
    stop_ngrok
    
    echo -e "${BLUE}=== Iniciando túnel NGROK para MCP-Chatwoot ===${NC}"
    
    # Obter a porta do contêiner Docker
    DOCKER_PORT=$(docker port $CONTAINER_NAME 2>/dev/null | grep $SERVER_PORT | cut -d ':' -f2)
    if [ -z "$DOCKER_PORT" ]; then
        echo -e "${YELLOW}Usando a porta padrão $SERVER_PORT${NC}"
        DOCKER_PORT=$SERVER_PORT
    fi
    
    echo -e "${GREEN}Iniciando NGROK para a porta $DOCKER_PORT...${NC}"
    
    # Criar um script temporário para iniciar o NGROK
    TMP_SCRIPT=$(mktemp)
    echo '#!/bin/bash' > $TMP_SCRIPT
    echo "ngrok http $DOCKER_PORT" >> $TMP_SCRIPT
    chmod +x $TMP_SCRIPT
    
    # Iniciar o NGROK em segundo plano usando screen
    $TMP_SCRIPT > /dev/null 2>&1 &
    NGROK_PID=$!
    
    # Salvar o PID
    echo $NGROK_PID > $NGROK_PID_FILE
    
    # Esperar alguns segundos para o NGROK inicializar
    echo -e "${YELLOW}Aguardando inicialização do NGROK...${NC}"
    sleep 5
    
    # Verificar se o NGROK está acessível via API
    if curl -s http://localhost:4040/api/tunnels > /dev/null; then
        echo -e "${GREEN}NGROK iniciado com sucesso (PID: $NGROK_PID)!${NC}"
        check_ngrok
        rm -f $TMP_SCRIPT
        return 0
    else
        echo -e "${RED}Falha ao iniciar o NGROK ou acessar sua API${NC}"
        echo -e "${YELLOW}Tentando iniciar o NGROK diretamente...${NC}"
        
        # Tentar iniciar o NGROK diretamente
        kill $NGROK_PID 2>/dev/null
        ngrok http $DOCKER_PORT > /dev/null 2>&1 &
        NGROK_PID=$!
        echo $NGROK_PID > $NGROK_PID_FILE
        
        sleep 5
        
        if curl -s http://localhost:4040/api/tunnels > /dev/null; then
            echo -e "${GREEN}NGROK iniciado com sucesso na segunda tentativa!${NC}"
            check_ngrok
            rm -f $TMP_SCRIPT
            return 0
        else
            echo -e "${RED}Falha ao iniciar o NGROK. Por favor, execute manualmente:${NC}"
            echo -e "${YELLOW}ngrok http $DOCKER_PORT${NC}"
            rm -f $NGROK_PID_FILE
            rm -f $TMP_SCRIPT
            return 1
        fi
    fi
}

# Função para mostrar a URL do NGROK
show_url() {
    if [ -f "$URL_FILE" ]; then
        URL=$(cat $URL_FILE)
        echo -e "${GREEN}URL do NGROK: $URL${NC}"
        echo -e "${BLUE}URL para webhook: $URL/webhook${NC}"
    else
        echo -e "${RED}Nenhuma URL do NGROK encontrada${NC}"
        echo -e "${YELLOW}Inicie o NGROK primeiro com: $0 start${NC}"
        return 1
    fi
}

# Função de ajuda
show_help() {
    echo -e "${BLUE}=== Script de Gerenciamento de Túnel NGROK para MCP-Chatwoot ===${NC}"
    echo -e "Uso: $0 [comando]"
    echo -e "\nComandos:"
    echo -e "  ${GREEN}start${NC} - Inicia o túnel NGROK"
    echo -e "  ${GREEN}stop${NC} - Para o túnel NGROK"
    echo -e "  ${GREEN}status${NC} - Verifica o status do túnel NGROK"
    echo -e "  ${GREEN}url${NC} - Mostra a URL pública do NGROK"
    echo -e "  ${GREEN}help${NC} - Mostra esta mensagem de ajuda"
}

# Processamento dos comandos
case "$1" in
    start)
        start_ngrok
        ;;
    stop)
        stop_ngrok
        ;;
    status)
        check_container
        check_ngrok
        ;;
    url)
        show_url
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        if [ -z "$1" ]; then
            check_container
            check_ngrok
        else
            echo -e "${RED}Comando desconhecido: $1${NC}"
            show_help
            exit 1
        fi
        ;;
esac
