#!/bin/bash

# Cores para saída
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Diretório de destino para os módulos do Odoo 18
ODOO18_ADDONS_DIR="/home/giovano/Projetos/odoo18/custom_addons"

# Lista de módulos a serem instalados
MODULES=(
    "addons18/business_rules18"
    "addons18/company_services18"
)

echo -e "${YELLOW}Iniciando instalação de todos os módulos para Odoo 18...${NC}"

# Verificar se o diretório de destino existe
if [ ! -d "$ODOO18_ADDONS_DIR" ]; then
    echo -e "${RED}Erro: Diretório de destino $ODOO18_ADDONS_DIR não encontrado.${NC}"
    echo -e "${YELLOW}Por favor, verifique o caminho e tente novamente.${NC}"
    exit 1
fi

# Instalar cada módulo
for MODULE_DIR in "${MODULES[@]}"; do
    MODULE_NAME=$(basename "$MODULE_DIR")
    
    echo -e "\n${YELLOW}Processando módulo $MODULE_NAME...${NC}"
    
    # Verificar se o módulo existe
    if [ ! -d "$MODULE_DIR" ]; then
        echo -e "${RED}Erro: Módulo $MODULE_DIR não encontrado.${NC}"
        continue
    fi
    
    # Verificar se os arquivos essenciais existem
    if [ ! -f "$MODULE_DIR/__init__.py" ] || [ ! -f "$MODULE_DIR/__manifest__.py" ]; then
        echo -e "${RED}Erro: Arquivos essenciais não encontrados em $MODULE_DIR.${NC}"
        continue
    fi
    
    # Remover instalação anterior se existir
    if [ -d "$ODOO18_ADDONS_DIR/$MODULE_NAME" ]; then
        echo -e "${YELLOW}Removendo instalação anterior de $MODULE_NAME...${NC}"
        rm -rf "$ODOO18_ADDONS_DIR/$MODULE_NAME"
    fi
    
    # Copiar o módulo para o diretório de destino
    echo -e "${YELLOW}Copiando módulo $MODULE_NAME para $ODOO18_ADDONS_DIR...${NC}"
    cp -r "$MODULE_DIR" "$ODOO18_ADDONS_DIR/"
    
    # Verificar se a cópia foi bem-sucedida
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Módulo $MODULE_NAME copiado com sucesso para $ODOO18_ADDONS_DIR.${NC}"
    else
        echo -e "${RED}Erro ao copiar o módulo $MODULE_NAME.${NC}"
    fi
done

echo -e "\n${GREEN}Processo de instalação concluído!${NC}"
echo -e "${YELLOW}Agora você precisa:${NC}"
echo -e "1. Reiniciar o servidor Odoo"
echo -e "2. Atualizar a lista de aplicativos no Odoo"
echo -e "3. Instalar os módulos 'Regras de Negócio' e 'Empresa e Serviços'"
