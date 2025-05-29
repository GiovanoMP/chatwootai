#!/bin/bash

# Cores para mensagens
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
RED="\033[0;31m"
BLUE="\033[0;34m"
RESET="\033[0m"
BOLD="\033[1m"

# Função para exibir mensagens
function echo_status() {
    local color=$1
    local icon=$2
    local message=$3
    local color_code
    
    case $color in
        "green") color_code=$GREEN ;;
        "yellow") color_code=$YELLOW ;;
        "red") color_code=$RED ;;
        "blue") color_code=$BLUE ;;
        *) color_code="" ;;
    esac
    
    echo -e "${color_code}${icon} ${message}${RESET}"
}

# Diretório base
BASE_DIR="/home/giovano/Projetos/ai_stack"

echo -e "\n${BOLD}Iniciando serviços de vetorização para ChatwootAI...${RESET}\n"

# Verifica se a rede Docker existe
if ! docker network inspect chatwoot-network &>/dev/null; then
    echo_status "blue" "🌐" "Criando rede Docker chatwoot-network..."
    docker network create chatwoot-network
    if [ $? -eq 0 ]; then
        echo_status "green" "✅" "Rede Docker chatwoot-network criada com sucesso!"
    else
        echo_status "red" "❌" "Erro ao criar rede Docker chatwoot-network. Verifique as permissões."
        exit 1
    fi
else
    echo_status "green" "✅" "Rede Docker chatwoot-network já existe."
fi

# Inicia o Qdrant (banco de dados vetorial)
echo_status "blue" "🚀" "Iniciando Qdrant..."
docker-compose -f "$BASE_DIR/docker-compose.qdrant.yml" up -d
if [ $? -eq 0 ]; then
    echo_status "green" "✅" "Qdrant iniciado com sucesso!"
else
    echo_status "red" "❌" "Erro ao iniciar Qdrant. Verifique o arquivo docker-compose.qdrant.yml."
    exit 1
fi

# Aguarda o Qdrant estar pronto
echo_status "blue" "⏳" "Aguardando Qdrant estar pronto..."
for i in {1..30}; do
    if curl -s http://localhost:6333/health &>/dev/null; then
        echo_status "green" "✅" "Qdrant está pronto!"
        break
    fi
    if [ $i -eq 30 ]; then
        echo_status "red" "❌" "Timeout aguardando Qdrant. Verifique os logs."
        exit 1
    fi
    sleep 1
done

# Inicia o MCP-Qdrant
echo_status "blue" "🚀" "Iniciando MCP-Qdrant..."
docker-compose -f "$BASE_DIR/docker-compose.mcp-qdrant.yml" up -d
if [ $? -eq 0 ]; then
    echo_status "green" "✅" "MCP-Qdrant iniciado com sucesso!"
else
    echo_status "red" "❌" "Erro ao iniciar MCP-Qdrant. Verifique o arquivo docker-compose.mcp-qdrant.yml."
    exit 1
fi

# Aguarda o MCP-Qdrant estar pronto
echo_status "blue" "⏳" "Aguardando MCP-Qdrant estar pronto..."
for i in {1..30}; do
    if curl -s http://localhost:8002/health &>/dev/null; then
        echo_status "green" "✅" "MCP-Qdrant está pronto!"
        break
    fi
    if [ $i -eq 30 ]; then
        echo_status "yellow" "⚠️" "Timeout aguardando MCP-Qdrant. Continuando mesmo assim..."
    fi
    sleep 1
done

# Verifica se os serviços estão em execução
echo_status "blue" "🔍" "Verificando serviços em execução..."
docker ps | grep -E "qdrant|mcp-qdrant"

echo -e "\n${BOLD}Serviços de vetorização iniciados!${RESET}\n"
echo_status "blue" "ℹ️" "Qdrant UI disponível em: http://localhost:6333/dashboard"
echo_status "blue" "ℹ️" "MCP-Qdrant disponível em: http://localhost:8002"
echo_status "yellow" "💡" "Para configurar o Odoo, adicione os seguintes parâmetros no sistema:"
echo -e "   ${BLUE}semantic_product_description.qdrant_url${RESET} = ${YELLOW}http://localhost:8002${RESET}"
echo -e "   ${BLUE}semantic_product_description.qdrant_api_key${RESET} = ${YELLOW}development-api-key${RESET}"
echo -e "   ${BLUE}semantic_product_description.account_id${RESET} = ${YELLOW}account_1${RESET}"

exit 0
