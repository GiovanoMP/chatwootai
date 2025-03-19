#!/bin/bash

# Script para limpar scripts de webhook redundantes
# Autor: Cascade AI
# Data: 2025-03-17

# Definir cores para melhor legibilidade
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Diretório base do projeto
PROJECT_DIR="$(pwd)"
WEBHOOK_SCRIPTS_DIR="${PROJECT_DIR}/scripts/webhook"
BACKUP_DIR="${PROJECT_DIR}/scripts/webhook/backup_$(date +%Y%m%d)"

echo -e "${YELLOW}Iniciando limpeza de scripts de webhook redundantes...${NC}"
echo -e "${YELLOW}Diretório de scripts: ${WEBHOOK_SCRIPTS_DIR}${NC}"

# Função para confirmar ação
confirm() {
    read -p "Deseja continuar? (s/n): " choice
    case "$choice" in 
        s|S ) return 0;;
        * ) return 1;;
    esac
}

# Verificar se o diretório existe
if [ ! -d "$WEBHOOK_SCRIPTS_DIR" ]; then
    echo -e "${RED}Erro: Diretório de scripts de webhook não encontrado: ${WEBHOOK_SCRIPTS_DIR}${NC}"
    exit 1
fi

# Criar diretório de backup
echo -e "${YELLOW}Criando diretório de backup: ${BACKUP_DIR}${NC}"
mkdir -p "$BACKUP_DIR"

# Lista de scripts essenciais que devem ser mantidos
ESSENTIAL_SCRIPTS=(
    "start_webhook_connection.sh"  # Novo script unificado
    "update_webhook_url.sh"        # Script para atualizar a URL do webhook na VPS
    "deploy_webhook_swarm.sh"      # Script para implantar o webhook no Docker Swarm
    "check_webhook_swarm.sh"       # Script para verificar o status do webhook no Docker Swarm
    "README.md"                    # Documentação dos scripts
)

# Lista de scripts redundantes que podem ser removidos
REDUNDANT_SCRIPTS=(
    "start_webhook_local.sh"       # Substituído pelo start_webhook_connection.sh
    "start_test_webhook.sh"        # Funcionalidade incluída em start_webhook_connection.sh
    "start_webhook.sh"             # Substituído por start_webhook_dev.sh ou start_webhook_connection.sh
    "start_ngrok.sh"               # Funcionalidade incluída em start_webhook_connection.sh
    "test_webhook.sh"              # Funcionalidade incluída em start_webhook_connection.sh
    "check_webhook_status.sh"      # Funcionalidade incluída em start_webhook_connection.sh
    "configure_local_webhook.sh"   # Não é mais necessário com o novo script unificado
)

# Listar scripts que serão mantidos
echo -e "${GREEN}Os seguintes scripts serão mantidos:${NC}"
for script in "${ESSENTIAL_SCRIPTS[@]}"; do
    if [ -f "${WEBHOOK_SCRIPTS_DIR}/${script}" ]; then
        echo "- ${script}"
    fi
done

# Listar scripts que serão movidos para backup
echo -e "${YELLOW}Os seguintes scripts serão movidos para backup:${NC}"
for script in "${REDUNDANT_SCRIPTS[@]}"; do
    if [ -f "${WEBHOOK_SCRIPTS_DIR}/${script}" ]; then
        echo "- ${script}"
    fi
done

# Listar outros scripts que não estão nas listas acima
echo -e "${YELLOW}Os seguintes scripts não estão categorizados:${NC}"
for script in "${WEBHOOK_SCRIPTS_DIR}"/*; do
    if [ -f "$script" ]; then
        script_name=$(basename "$script")
        if [[ ! " ${ESSENTIAL_SCRIPTS[@]} " =~ " ${script_name} " ]] && [[ ! " ${REDUNDANT_SCRIPTS[@]} " =~ " ${script_name} " ]]; then
            echo "- ${script_name}"
        fi
    fi
done

# Confirmar antes de prosseguir
echo -e "${YELLOW}Esta operação irá mover os scripts redundantes para o diretório de backup.${NC}"
if confirm; then
    # Mover scripts redundantes para o diretório de backup
    for script in "${REDUNDANT_SCRIPTS[@]}"; do
        if [ -f "${WEBHOOK_SCRIPTS_DIR}/${script}" ]; then
            echo -e "${YELLOW}Movendo ${script} para backup...${NC}"
            mv "${WEBHOOK_SCRIPTS_DIR}/${script}" "${BACKUP_DIR}/"
        fi
    done
    
    echo -e "${GREEN}Limpeza concluída com sucesso!${NC}"
    echo -e "${GREEN}Os scripts redundantes foram movidos para: ${BACKUP_DIR}${NC}"
else
    echo -e "${RED}Operação cancelada.${NC}"
fi

# Perguntar se deseja remover completamente os scripts redundantes
echo -e "${YELLOW}Deseja remover completamente os scripts redundantes (em vez de apenas movê-los para backup)? (s/n)${NC}"
if confirm; then
    echo -e "${YELLOW}Removendo diretório de backup...${NC}"
    rm -rf "${BACKUP_DIR}"
    echo -e "${GREEN}Scripts redundantes removidos permanentemente.${NC}"
else
    echo -e "${GREEN}Scripts redundantes mantidos no diretório de backup: ${BACKUP_DIR}${NC}"
fi

echo -e "${GREEN}Processo de limpeza finalizado.${NC}"
