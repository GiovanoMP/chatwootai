#!/bin/bash

# Cores para saída
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configurações
CONTAINER_NAME="mcp-chatwoot"
NGROK_CONTAINER="mcp-chatwoot-ngrok"
URL_FILE="ngrok_url.txt"
ENV_FILE="../.env"

# Função de ajuda
show_help() {
    echo -e "${BLUE}=== MCP-Chatwoot Tools ===${NC}"
    echo -e "Uso: $0 [comando]"
    echo -e "\nComandos:"
    echo -e "  ${GREEN}ngrok${NC} [start|stop|status|url] - Gerencia o túnel NGROK"
    echo -e "  ${GREEN}logs${NC} [all|follow|errors|webhook] - Gerencia os logs do MCP-Chatwoot"
    echo -e "  ${GREEN}status${NC} - Verifica o status do MCP-Chatwoot"
    echo -e "  ${GREEN}help${NC} - Exibe esta mensagem de ajuda"
    echo -e "\nExemplos:"
    echo -e "  $0 ngrok start - Inicia o túnel NGROK"
    echo -e "  $0 logs follow - Acompanha os logs em tempo real"
}

# Verificar se o contêiner está em execução
check_container() {
    if ! docker ps -q -f name=$CONTAINER_NAME | grep -q .; then
        echo -e "${RED}Erro: O contêiner $CONTAINER_NAME não está em execução${NC}"
        echo -e "${YELLOW}Inicie o contêiner primeiro com: docker-compose up -d${NC}"
        return 1
    fi
    return 0
}

# Verificar se o NGROK está em execução
check_ngrok_running() {
    if docker ps -q -f name=$NGROK_CONTAINER | grep -q .; then
        return 0  # Está rodando
    else
        return 1  # Não está rodando
    fi
}

# Obter token NGROK do arquivo .env ou criar variável
get_ngrok_token() {
    # Verificar se existe a variável NGROK_AUTHTOKEN no arquivo .env
    if [ -f "$ENV_FILE" ]; then
        NGROK_TOKEN=$(grep "NGROK_AUTHTOKEN" "$ENV_FILE" | cut -d '=' -f2)
    fi
    
    # Se não encontrou ou está vazio, pedir ao usuário
    if [ -z "$NGROK_TOKEN" ]; then
        echo -e "${YELLOW}Token NGROK não encontrado no arquivo .env${NC}"
        echo -e "${YELLOW}Adicione NGROK_AUTHTOKEN=seu_token ao arquivo .env ou forneça abaixo:${NC}"
        read -p "Token NGROK: " NGROK_TOKEN
        
        # Adicionar ao arquivo .env se o usuário forneceu um token
        if [ -n "$NGROK_TOKEN" ] && [ -f "$ENV_FILE" ]; then
            echo "NGROK_AUTHTOKEN=$NGROK_TOKEN" >> "$ENV_FILE"
            echo -e "${GREEN}Token NGROK adicionado ao arquivo .env${NC}"
        fi
    fi
    
    # Verificar se o token foi fornecido
    if [ -z "$NGROK_TOKEN" ]; then
        echo -e "${RED}Erro: Token NGROK não fornecido${NC}"
        return 1
    fi
    
    return 0
}

# Obter a URL pública do NGROK
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

# Gerenciar NGROK
manage_ngrok() {
    case "$1" in
        start)
            if ! check_container; then
                return 1
            fi
            
            if ! get_ngrok_token; then
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
            ;;
            
        stop)
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
            ;;
            
        status)
            if check_ngrok_running; then
                echo -e "${GREEN}✓ Túnel NGROK está ativo${NC}"
                get_ngrok_url
            else
                echo -e "${RED}✗ Túnel NGROK não está ativo${NC}"
            fi
            ;;
            
        url)
            if [ -f "$URL_FILE" ]; then
                URL=$(cat $URL_FILE)
                echo -e "${GREEN}URL do NGROK: $URL${NC}"
                echo -e "${YELLOW}URL do webhook: $URL/webhook${NC}"
            else
                echo -e "${RED}Nenhuma URL do NGROK encontrada${NC}"
                echo -e "${YELLOW}Inicie o túnel NGROK primeiro com: $0 ngrok start${NC}"
            fi
            ;;
            
        *)
            echo -e "${RED}Comando NGROK inválido: $1${NC}"
            echo -e "${YELLOW}Comandos disponíveis: start, stop, status, url${NC}"
            return 1
            ;;
    esac
}

# Gerenciar logs
manage_logs() {
    if ! check_container; then
        return 1
    fi
    
    case "$1" in
        all)
            echo -e "${BLUE}=== Exibindo todos os logs do $CONTAINER_NAME ===${NC}"
            docker logs $CONTAINER_NAME
            ;;
            
        follow)
            echo -e "${BLUE}=== Monitorando logs do $CONTAINER_NAME em tempo real ===${NC}"
            echo -e "${YELLOW}Pressione Ctrl+C para sair${NC}"
            docker logs -f $CONTAINER_NAME
            ;;
            
        errors)
            echo -e "${BLUE}=== Exibindo erros e avisos do $CONTAINER_NAME ===${NC}"
            docker logs $CONTAINER_NAME 2>&1 | grep -E "ERROR|WARN|Exception|Error:|Warning:|Failed|Traceback"
            ;;
            
        webhook)
            echo -e "${BLUE}=== Exibindo logs de webhook do $CONTAINER_NAME ===${NC}"
            docker logs $CONTAINER_NAME 2>&1 | grep -E "webhook|Webhook|WEBHOOK|/webhook"
            ;;
            
        *)
            echo -e "${RED}Comando de logs inválido: $1${NC}"
            echo -e "${YELLOW}Comandos disponíveis: all, follow, errors, webhook${NC}"
            return 1
            ;;
    esac
}

# Verificar status do MCP-Chatwoot
check_status() {
    echo -e "${BLUE}=== Status do MCP-Chatwoot ===${NC}"
    
    # Verificar se o contêiner está em execução
    if check_container; then
        echo -e "${GREEN}✓ MCP-Chatwoot está em execução${NC}"
        
        # Verificar o endpoint de health
        HEALTH_STATUS=$(curl -s http://localhost:8004/health)
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ Endpoint de health está respondendo${NC}"
            echo -e "${CYAN}Status: $HEALTH_STATUS${NC}"
        else
            echo -e "${RED}✗ Endpoint de health não está respondendo${NC}"
        fi
        
        # Verificar status do NGROK
        if check_ngrok_running; then
            echo -e "${GREEN}✓ Túnel NGROK está ativo${NC}"
            get_ngrok_url
        else
            echo -e "${YELLOW}✗ Túnel NGROK não está ativo${NC}"
        fi
    fi
}

# Processamento dos argumentos
case "$1" in
    ngrok)
        manage_ngrok "$2"
        ;;
    logs)
        manage_logs "${2:-all}"
        ;;
    status)
        check_status
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
