#!/bin/bash

# Script para limpar arquivos originais após a reorganização
# Este script deve ser executado somente depois de verificar que a nova estrutura está funcionando corretamente

# Configurações
PROJECT_ROOT="/home/giovano/Projetos/Chatwoot V4"
CURRENT_DATE=$(date +%Y%m%d_%H%M%S)

# Cores para mensagens
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Função para log com cores
log() {
    local level=$1
    local message=$2
    
    case $level in
        "INFO")
            echo -e "${GREEN}[INFO]${NC} $message"
            ;;
        "WARN")
            echo -e "${YELLOW}[WARN]${NC} $message"
            ;;
        "ERROR")
            echo -e "${RED}[ERROR]${NC} $message"
            ;;
    esac
}

# Verifica se o diretório do projeto existe
if [ ! -d "$PROJECT_ROOT" ]; then
    log "ERROR" "Diretório do projeto não encontrado: $PROJECT_ROOT"
    exit 1
fi

# Confirma com o usuário
echo -e "${YELLOW}ATENÇÃO: Este script vai remover os arquivos originais que foram reorganizados.${NC}"
echo -e "${YELLOW}Certifique-se de que a nova estrutura está funcionando corretamente antes de continuar.${NC}"
echo -e "${YELLOW}É recomendável executar o script somente depois de fazer testes.${NC}"
echo
read -p "Deseja continuar? (s/N): " confirm
if [[ "$confirm" != "s" && "$confirm" != "S" ]]; then
    log "INFO" "Operação cancelada pelo usuário."
    exit 0
fi

log "INFO" "Iniciando limpeza dos arquivos originais..."

# Lista de arquivos a serem removidos
FILES_TO_REMOVE=(
    "$PROJECT_ROOT/src/agents/data_proxy_agent.py"
    "$PROJECT_ROOT/src/api/chatwoot.py"
    "$PROJECT_ROOT/src/api/chatwoot_client.py"
    "$PROJECT_ROOT/src/api/odoo_simulation.py"
    "$PROJECT_ROOT/src/api/webhook_server.py"
    "$PROJECT_ROOT/webhook_server.py"
    "$PROJECT_ROOT/src/webhook/webhook_handler.py"
)

# Remove os arquivos
for file in "${FILES_TO_REMOVE[@]}"; do
    if [ -f "$file" ]; then
        log "INFO" "Removendo arquivo: $file"
        rm "$file"
    else
        log "WARN" "Arquivo não encontrado: $file"
    fi
done

log "INFO" "Limpeza concluída com sucesso!"
log "INFO" "A reorganização do projeto está completa."
log "INFO" "Não se esqueça de fazer commit das alterações."
