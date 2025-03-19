#!/bin/bash

# Script para limpar arquivos antigos relacionados ao webhook
# Autor: Cascade AI
# Data: 2025-03-19

# Cores para saída no terminal
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Diretório base do projeto
PROJECT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$PROJECT_DIR"

echo -e "${GREEN}=== Limpeza de Arquivos Antigos de Webhook ===${NC}"
echo -e "${YELLOW}Diretório de trabalho: $PROJECT_DIR${NC}"
echo -e "${YELLOW}Este script irá remover arquivos antigos e obsoletos relacionados ao webhook.${NC}"
echo -e "${RED}ATENÇÃO: Esta operação não pode ser desfeita!${NC}"
echo -e "${YELLOW}Deseja continuar? (s/n)${NC}"
read -r CONTINUE

if [[ ! "$CONTINUE" =~ ^[Ss]$ ]]; then
    echo -e "${YELLOW}Operação cancelada pelo usuário.${NC}"
    exit 0
fi

# Lista de diretórios a serem removidos
echo -e "${YELLOW}Removendo diretórios antigos...${NC}"

# Remover diretório webhook_old
if [ -d "$PROJECT_DIR/webhook_old" ]; then
    echo -e "${YELLOW}Removendo $PROJECT_DIR/webhook_old${NC}"
    rm -rf "$PROJECT_DIR/webhook_old"
    echo -e "${GREEN}✓ Diretório webhook_old removido${NC}"
fi

# Remover backups antigos
if [ -d "$PROJECT_DIR/scripts/webhook/backup_20250317" ]; then
    echo -e "${YELLOW}Removendo $PROJECT_DIR/scripts/webhook/backup_20250317${NC}"
    rm -rf "$PROJECT_DIR/scripts/webhook/backup_20250317"
    echo -e "${GREEN}✓ Diretório de backup removido${NC}"
fi

# Remover arquivos antigos
echo -e "${YELLOW}Removendo arquivos antigos...${NC}"

# Lista de arquivos a serem removidos
FILES_TO_REMOVE=(
    "$PROJECT_DIR/start_webhook_debug.sh"
    "$PROJECT_DIR/start_webhook_standalone.py"
)

for file in "${FILES_TO_REMOVE[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${YELLOW}Removendo $file${NC}"
        rm "$file"
        echo -e "${GREEN}✓ Arquivo removido${NC}"
    fi
done

echo -e "${GREEN}=== Limpeza concluída com sucesso ===${NC}"
echo -e "${YELLOW}Todos os arquivos antigos foram removidos.${NC}"
echo -e "${YELLOW}A nova estrutura organizada está disponível em $PROJECT_DIR/webhook/${NC}"
