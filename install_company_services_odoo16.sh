#!/bin/bash

# Script para instalar o módulo company_services no Odoo 16
# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Diretório de origem (onde estamos criando os arquivos)
SRC_DIR="./addons/company_services"

# Diretório de destino (onde o Odoo 16 procura por módulos)
DEST_DIR="/home/giovano/Projetos/odoo16/custom_addons/company_services"

echo -e "${BLUE}=== Script de Instalação do Módulo company_services para Odoo 16 ===${NC}"
echo -e "${YELLOW}Verificando diretório de origem...${NC}"

# Verificar se o diretório de origem existe
if [ ! -d "$SRC_DIR" ]; then
    echo -e "${RED}Diretório de origem $SRC_DIR não encontrado!${NC}"
    exit 1
fi

# Verificar se os arquivos essenciais existem
essential_files=(
    "models/__init__.py"
    "models/company_service.py"
    "models/sync_service.py"
    "models/res_config_settings.py"
    "models/init_config.py"
    "data/init_data.xml"
    "views/company_service_views.xml"
    "views/res_config_settings_views.xml"
    "views/menu_views.xml"
    "security/security.xml"
    "security/ir.model.access.csv"
    "__init__.py"
    "__manifest__.py"
)

missing_files=0
for file in "${essential_files[@]}"; do
    if [ ! -f "$SRC_DIR/$file" ]; then
        echo -e "${RED}Arquivo essencial não encontrado: $SRC_DIR/$file${NC}"
        missing_files=$((missing_files+1))
    fi
done

if [ $missing_files -gt 0 ]; then
    echo -e "${RED}$missing_files arquivos essenciais não foram encontrados.${NC}"
    read -p "Deseja continuar mesmo assim? (s/n): " choice
    if [ "$choice" != "s" ]; then
        echo -e "${RED}Instalação cancelada.${NC}"
        exit 1
    fi
fi

# Criar diretório de destino se não existir
echo -e "${YELLOW}Criando diretórios de destino...${NC}"
mkdir -p "$DEST_DIR/models"
mkdir -p "$DEST_DIR/views"
mkdir -p "$DEST_DIR/data"
mkdir -p "$DEST_DIR/security"
mkdir -p "$DEST_DIR/controllers"
mkdir -p "$DEST_DIR/static/description"

# Copiar arquivos
echo -e "${YELLOW}Copiando arquivos para $DEST_DIR...${NC}"

# Arquivos principais
cp "$SRC_DIR/__manifest__.py" "$DEST_DIR/"
cp "$SRC_DIR/__init__.py" "$DEST_DIR/"

# Modelos
cp "$SRC_DIR/models/__init__.py" "$DEST_DIR/models/"
cp "$SRC_DIR/models/"*.py "$DEST_DIR/models/"

# Vistas
cp "$SRC_DIR/views/"*.xml "$DEST_DIR/views/"

# Dados
if [ -d "$SRC_DIR/data" ]; then
    cp "$SRC_DIR/data/"*.xml "$DEST_DIR/data/"
fi

# Segurança
cp "$SRC_DIR/security/"*.xml "$DEST_DIR/security/"
cp "$SRC_DIR/security/"*.csv "$DEST_DIR/security/"

# Controllers
cp "$SRC_DIR/controllers/__init__.py" "$DEST_DIR/controllers/"
cp "$SRC_DIR/controllers/"*.py "$DEST_DIR/controllers/"

# Verificar se os arquivos foram copiados
echo -e "${YELLOW}Verificando arquivos copiados:${NC}"
ls -la "$DEST_DIR"
ls -la "$DEST_DIR/models/"
ls -la "$DEST_DIR/views/"
ls -la "$DEST_DIR/security/"

# Definir permissões
echo -e "${YELLOW}Definindo permissões...${NC}"
chmod -R 755 "$DEST_DIR"

echo -e "${GREEN}Instalação concluída!${NC}"
echo -e "${GREEN}Agora você pode atualizar a lista de módulos no Odoo 16 e instalar 'Empresa e Serviços'${NC}"

echo ""
echo -e "${BLUE}=== INSTRUÇÕES ADICIONAIS ===${NC}"
echo -e "${YELLOW}1. Para atualizar a lista de módulos no Odoo:${NC}"
echo "   - Acesse Configurações > Aplicativos > Atualizar Lista de Aplicativos"
echo "   - Busque por 'Empresa e Serviços' e instale o módulo"
echo ""
echo -e "${YELLOW}2. Para verificar os logs do módulo:${NC}"
echo "   - Logs do Odoo: sudo tail -f /var/log/odoo/odoo-server.log | grep company_services"
echo ""
echo -e "${YELLOW}3. Se encontrar erros durante a instalação:${NC}"
echo "   - Verifique os logs do Odoo: sudo tail -f /var/log/odoo/odoo-server.log"
echo "   - Desinstale o módulo antes de tentar novamente: sudo rm -rf $DEST_DIR"
echo ""
echo -e "${YELLOW}4. Nota sobre compatibilidade com Odoo 16:${NC}"
echo "   - Este módulo foi originalmente desenvolvido para Odoo 14"
echo "   - Pode ser necessário ajustar o código para compatibilidade com Odoo 16"
echo "   - Verifique os logs para identificar possíveis problemas de compatibilidade"
