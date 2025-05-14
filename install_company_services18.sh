#!/bin/bash

# Cores para saída
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Diretório de destino para os módulos do Odoo 18
ODOO18_ADDONS_DIR="/home/giovano/Projetos/odoo18/custom_addons"

# Diretório do módulo
MODULE_DIR="addons18/company_services18"

echo -e "${YELLOW}Iniciando instalação do módulo ${MODULE_DIR} para Odoo 18...${NC}"

# Verificar se o diretório de destino existe
if [ ! -d "$ODOO18_ADDONS_DIR" ]; then
    echo -e "${RED}Erro: Diretório de destino $ODOO18_ADDONS_DIR não encontrado.${NC}"
    echo -e "${YELLOW}Por favor, verifique o caminho e tente novamente.${NC}"
    exit 1
fi

# Verificar se o módulo existe
if [ ! -d "$MODULE_DIR" ]; then
    echo -e "${RED}Erro: Módulo $MODULE_DIR não encontrado.${NC}"
    exit 1
fi

# Verificar se os arquivos essenciais existem
essential_files=(
    "__init__.py"
    "__manifest__.py"
    "models/__init__.py"
    "models/company_service.py"
    "models/special_phone.py"
    "models/res_config_settings.py"
    "views/company_service_views.xml"
    "views/special_phone_views.xml"
    "views/res_config_settings_views.xml"
    "views/menu_views.xml"
    "security/company_services_security.xml"
    "security/ir.model.access.csv"
)

for file in "${essential_files[@]}"; do
    if [ ! -f "$MODULE_DIR/$file" ]; then
        echo -e "${RED}Erro: Arquivo essencial $MODULE_DIR/$file não encontrado.${NC}"
        exit 1
    fi
done

# Remover instalação anterior se existir
if [ -d "$ODOO18_ADDONS_DIR/$MODULE_DIR" ]; then
    echo -e "${YELLOW}Removendo instalação anterior...${NC}"
    rm -rf "$ODOO18_ADDONS_DIR/$MODULE_DIR"
fi

# Copiar o módulo para o diretório de destino
echo -e "${YELLOW}Copiando módulo para $ODOO18_ADDONS_DIR...${NC}"
cp -r "$MODULE_DIR" "$ODOO18_ADDONS_DIR/"

# Verificar se a cópia foi bem-sucedida
if [ $? -eq 0 ]; then
    echo -e "${GREEN}Módulo $MODULE_DIR copiado com sucesso para $ODOO18_ADDONS_DIR.${NC}"
    echo -e "${YELLOW}Agora você precisa:${NC}"
    echo -e "1. Reiniciar o servidor Odoo"
    echo -e "2. Atualizar a lista de aplicativos no Odoo"
    echo -e "3. Instalar o módulo 'Empresa e Serviços'"
else
    echo -e "${RED}Erro ao copiar o módulo.${NC}"
    exit 1
fi

echo -e "${GREEN}Processo de instalação concluído!${NC}"
