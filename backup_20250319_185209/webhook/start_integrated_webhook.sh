#!/bin/bash

# Script para iniciar o webhook integrado com o sistema de agentes
# Autor: Cascade AI
# Data: 2025-03-19

# Cores para saída no terminal
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Diretório raiz do projeto (um nível acima do diretório webhook)
PROJECT_DIR="$(dirname "$(dirname "$(readlink -f "$0")")")"
cd "$PROJECT_DIR"

echo -e "${GREEN}=== Iniciando Sistema Integrado de Webhook para ChatwootAI ===${NC}"
echo -e "${YELLOW}Diretório do projeto: $PROJECT_DIR${NC}"

# Verificar existência de arquivos essenciais
if [ ! -f "$PROJECT_DIR/webhook_server.py" ]; then
    echo -e "${RED}Erro: webhook_server.py não encontrado${NC}"
    exit 1
fi

# Verificar se o ambiente virtual está ativado
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${YELLOW}Ambiente virtual não detectado. Tentando ativar...${NC}"
    
    # Verifica se o venv existe
    if [ -d "$PROJECT_DIR/venv" ]; then
        source "$PROJECT_DIR/venv/bin/activate"
        echo -e "${GREEN}✓ Ambiente virtual ativado${NC}"
    else
        echo -e "${YELLOW}Criando novo ambiente virtual...${NC}"
        python -m venv venv
        source "$PROJECT_DIR/venv/bin/activate"
        echo -e "${GREEN}✓ Ambiente virtual criado e ativado${NC}"
        
        # Instalar dependências
        echo -e "${YELLOW}Instalando dependências...${NC}"
        pip install -r requirements.txt
        echo -e "${GREEN}✓ Dependências instaladas${NC}"
    fi
fi

# Verificar dependências
echo -e "${YELLOW}Verificando dependências...${NC}"
pip install -q fastapi uvicorn python-dotenv requests

# Cria diretório de logs se não existir
mkdir -p "$PROJECT_DIR/logs"

# Verificar se o servidor webhook está rodando
if curl -s http://localhost:8001/health > /dev/null; then
    echo -e "${RED}⚠ Servidor webhook já está rodando na porta 8001${NC}"
    echo -e "${YELLOW}Deseja reiniciar? (s/n)${NC}"
    read -r RESTART
    
    if [[ "$RESTART" =~ ^[Ss]$ ]]; then
        echo -e "${YELLOW}Procurando processo...${NC}"
        WEBHOOK_PID=$(lsof -t -i:8001)
        if [ -n "$WEBHOOK_PID" ]; then
            echo -e "${YELLOW}Matando processo $WEBHOOK_PID...${NC}"
            kill -9 $WEBHOOK_PID
            sleep 2
        fi
    else
        echo -e "${YELLOW}Mantendo servidor atual${NC}"
        
        # Verificar ngrok
        if curl -s http://localhost:4040/api/tunnels > /dev/null; then
            NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | grep -o '"public_url":"[^"]*' | grep -o 'https://[^"]*')
            echo -e "${GREEN}✓ Ngrok já está rodando: $NGROK_URL${NC}"
            echo -e "${YELLOW}URL do Webhook: $NGROK_URL/webhook${NC}"
        fi
        
        exit 0
    fi
fi

# Definir variáveis de ambiente
echo -e "${YELLOW}Configurando variáveis de ambiente...${NC}"
export PYTHONPATH=$PROJECT_DIR

# Verifica se .env existe
if [ -f "$PROJECT_DIR/.env" ]; then
    echo -e "${GREEN}✓ Arquivo .env encontrado${NC}"
else
    echo -e "${YELLOW}Criando arquivo .env com configurações padrão${NC}"
    cat > "$PROJECT_DIR/.env" << EOF
# Configurações do Chatwoot
CHATWOOT_API_KEY=sua_api_key
CHATWOOT_BASE_URL=https://seu-chatwoot.com/api/v1
CHATWOOT_ACCOUNT_ID=1

# Configurações do Webhook
WEBHOOK_PORT=8001
WEBHOOK_HOST=0.0.0.0

# Configurações de Domínio
ACTIVE_DOMAIN=cosmetics
EOF
    echo -e "${GREEN}✓ Arquivo .env criado${NC}"
    echo -e "${YELLOW}⚠ IMPORTANTE: Edite o arquivo .env com suas configurações reais${NC}"
fi

# Iniciar o servidor webhook em background
echo -e "${YELLOW}Iniciando servidor webhook integrado...${NC}"
python "$PROJECT_DIR/webhook_server.py" > "$PROJECT_DIR/logs/webhook_server.log" 2>&1 &
WEBHOOK_PID=$!

# Aguardar alguns segundos para o servidor iniciar
echo -e "${YELLOW}Aguardando o servidor iniciar...${NC}"
sleep 5

# Verificar se o servidor está em execução
if ps -p $WEBHOOK_PID > /dev/null; then
    echo -e "${GREEN}✓ Servidor webhook iniciado com PID: $WEBHOOK_PID${NC}"
else
    echo -e "${RED}✗ Falha ao iniciar o servidor webhook${NC}"
    echo -e "${RED}Verifique o arquivo logs/webhook_server.log para mais informações${NC}"
    exit 1
fi

# Verificar se o ngrok está rodando
if curl -s http://localhost:4040/api/tunnels > /dev/null; then
    echo -e "${GREEN}✓ Ngrok já está rodando${NC}"
    
    # Obter a URL do ngrok
    NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | grep -o '"public_url":"[^"]*' | grep -o 'https://[^"]*')
    echo -e "${GREEN}✓ URL do ngrok: $NGROK_URL${NC}"
else
    echo -e "${YELLOW}Iniciando ngrok...${NC}"
    
    # Iniciar o ngrok em segundo plano
    nohup ngrok http 8001 --log=stdout > "$PROJECT_DIR/ngrok.log" 2>&1 &
    NGROK_PID=$!
    
    # Aguardar alguns segundos para o ngrok iniciar
    echo -e "${YELLOW}Aguardando o ngrok iniciar...${NC}"
    sleep 5
    
    # Verificar se o ngrok está em execução
    if curl -s http://localhost:4040/api/tunnels > /dev/null; then
        # Obter a URL do ngrok
        NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | grep -o '"public_url":"[^"]*' | grep -o 'https://[^"]*')
        echo -e "${GREEN}✓ Ngrok iniciado com sucesso${NC}"
        echo -e "${GREEN}✓ URL do ngrok: $NGROK_URL${NC}"
    else
        echo -e "${RED}✗ Falha ao iniciar o ngrok${NC}"
        echo -e "${RED}Verifique o arquivo ngrok.log para mais informações${NC}"
        exit 1
    fi
fi

# Perguntar se deseja atualizar a URL na VPS
echo -e "${YELLOW}Deseja atualizar a URL do webhook na VPS? (s/n)${NC}"
read -r UPDATE_VPS

if [[ "$UPDATE_VPS" =~ ^[Ss]$ ]]; then
    echo -e "${YELLOW}Atualizando URL na VPS...${NC}"
    # Assumimos que o script para atualizar a URL existe
    if [ -f "$PROJECT_DIR/webhook/scripts/update_vps_webhook_url.sh" ]; then
        "$PROJECT_DIR/webhook/scripts/update_vps_webhook_url.sh"
    else
        echo -e "${RED}✗ Script para atualizar URL na VPS não encontrado${NC}"
    fi
else
    echo -e "${YELLOW}Pulando atualização da URL na VPS${NC}"
fi

echo -e "${GREEN}=== Sistema de Webhook Integrado iniciado com sucesso ===${NC}"
echo -e "${YELLOW}URL do Webhook: $NGROK_URL/webhook${NC}"
echo -e "${YELLOW}Para verificar os logs do servidor webhook:${NC}"
echo -e "tail -f $PROJECT_DIR/logs/webhook_server.log"
echo -e "${YELLOW}Para verificar os logs do ngrok:${NC}"
echo -e "tail -f $PROJECT_DIR/ngrok.log"
echo -e ""
echo -e "${GREEN}Para testar o webhook:${NC}"
echo -e "curl -X POST $NGROK_URL/webhook -H \"Content-Type: application/json\" -d '{\"event\": \"test\"}'"
