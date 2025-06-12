#!/bin/bash

# Cores para saída
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Nome do contêiner NGROK
NGROK_CONTAINER="mcp-chatwoot-ngrok"

# Arquivo para salvar a URL do NGROK
URL_FILE="ngrok_url.txt"

# Função de ajuda
show_help() {
    echo -e "${BLUE}=== Script de Gerenciamento do NGROK para MCP-Chatwoot ===${NC}"
    echo -e "Uso: $0 [opção] <token-ngrok>"
    echo -e "\nOpções:"
    echo -e "  start <token>  - Inicia um novo túnel NGROK"
    echo -e "  stop           - Para o túnel NGROK atual"
    echo -e "  status         - Verifica o status do túnel NGROK"
    echo -e "  url            - Exibe a URL pública atual do NGROK"
    echo -e "  help           - Exibe esta mensagem de ajuda"
    echo -e "\nExemplo: $0 start abc123xyz456"
}

# Função para verificar se o contêiner NGROK está em execução
check_ngrok_running() {
    if docker ps -q -f name=$NGROK_CONTAINER | grep -q .; then
        return 0  # Está rodando
    else
        return 1  # Não está rodando
    fi
}

# Função para obter a URL pública do NGROK
get_ngrok_url() {
    if check_ngrok_running; then
        # Esperar alguns segundos para o NGROK inicializar completamente
        sleep 3
        
        # Obter a URL do NGROK usando a API interna
        URL=$(docker exec $NGROK_CONTAINER curl -s http://localhost:4040/api/tunnels | grep -o '"public_url":"[^"]*"' | grep -o 'https://[^"]*')
        
        if [ -n "$URL" ]; then
            echo "$URL" > $URL_FILE
            echo -e "${GREEN}URL do NGROK: $URL${NC}"
            echo -e "${YELLOW}Esta URL foi salva em $URL_FILE${NC}"
            echo -e "${YELLOW}Configure esta URL no webhook do Chatwoot: $URL/webhook${NC}"
            return 0
        else
            echo -e "${RED}Não foi possível obter a URL do NGROK${NC}"
            return 1
        fi
    else
        echo -e "${RED}O contêiner NGROK não está em execução${NC}"
        return 1
    fi
}

# Função para iniciar o NGROK
start_ngrok() {
    if [ -z "$1" ]; then
        echo -e "${RED}Erro: Token do NGROK não fornecido${NC}"
        echo -e "${YELLOW}Uso: $0 start <seu-token-ngrok>${NC}"
        return 1
    fi
    
    NGROK_TOKEN=$1
    
    # Verificar se o MCP-Chatwoot está em execução
    if ! docker ps -q -f name=mcp-chatwoot | grep -q .; then
        echo -e "${RED}Erro: O contêiner mcp-chatwoot não está em execução${NC}"
        echo -e "${YELLOW}Inicie o MCP-Chatwoot primeiro com: docker-compose up -d${NC}"
        return 1
    fi
    
    # Parar qualquer instância anterior do NGROK
    if check_ngrok_running; then
        echo -e "${YELLOW}Parando instância anterior do NGROK...${NC}"
        docker stop $NGROK_CONTAINER > /dev/null 2>&1
        docker rm $NGROK_CONTAINER > /dev/null 2>&1
    fi
    
    echo -e "${BLUE}=== Iniciando túnel NGROK para MCP-Chatwoot ===${NC}"
    
    # Iniciar o NGROK em um contêiner em segundo plano
    echo -e "${GREEN}Iniciando NGROK...${NC}"
    docker run -d --network=ai-stack -e NGROK_AUTHTOKEN=$NGROK_TOKEN \
        --name $NGROK_CONTAINER ngrok/ngrok http mcp-chatwoot:8004 > /dev/null 2>&1
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}NGROK iniciado com sucesso!${NC}"
        get_ngrok_url
    else
        echo -e "${RED}Falha ao iniciar o NGROK${NC}"
        return 1
    fi
}

# Função para parar o NGROK
stop_ngrok() {
    if check_ngrok_running; then
        echo -e "${YELLOW}Parando o túnel NGROK...${NC}"
        docker stop $NGROK_CONTAINER > /dev/null 2>&1
        docker rm $NGROK_CONTAINER > /dev/null 2>&1
        echo -e "${GREEN}Túnel NGROK parado com sucesso${NC}"
        
        # Remover o arquivo de URL
        if [ -f "$URL_FILE" ]; then
            rm $URL_FILE
        fi
    else
        echo -e "${YELLOW}O túnel NGROK já está parado${NC}"
    fi
}

# Função para verificar o status do NGROK
check_ngrok_status() {
    if check_ngrok_running; then
        echo -e "${GREEN}✓ Túnel NGROK está ativo${NC}"
        get_ngrok_url
    else
        echo -e "${RED}✗ Túnel NGROK não está ativo${NC}"
    fi
}

# Função para exibir a URL atual
show_url() {
    if [ -f "$URL_FILE" ]; then
        URL=$(cat $URL_FILE)
        echo -e "${GREEN}URL do NGROK: $URL${NC}"
        echo -e "${YELLOW}URL do webhook: $URL/webhook${NC}"
    else
        echo -e "${RED}Nenhuma URL do NGROK encontrada${NC}"
        echo -e "${YELLOW}Inicie o túnel NGROK primeiro com: $0 start <token>${NC}"
    fi
}

# Processamento dos argumentos
case "$1" in
    start)
        start_ngrok "$2"
        ;;
    stop)
        stop_ngrok
        ;;
    status)
        check_ngrok_status
        ;;
    url)
        show_url
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
