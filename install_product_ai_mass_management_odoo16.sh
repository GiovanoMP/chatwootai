#!/bin/bash

# Script para instalar o módulo product_ai_mass_management no Odoo 16
# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Diretório de origem (onde estamos criando os arquivos)
SRC_DIR="./addons/product_ai_mass_management"

# Diretório de destino (onde o Odoo 16 procura por módulos)
DEST_DIR="/home/giovano/Projetos/odoo16/custom_addons/product_ai_mass_management"

echo -e "${BLUE}=== Script de Instalação do Módulo product_ai_mass_management para Odoo 16 ===${NC}"
echo -e "${YELLOW}Verificando diretório de origem...${NC}"

# Verificar se o diretório de origem existe
if [ ! -d "$SRC_DIR" ]; then
    echo -e "${RED}Diretório de origem $SRC_DIR não encontrado!${NC}"
    exit 1
fi

# Verificar se o módulo semantic_product_description está instalado
echo -e "${YELLOW}Verificando dependência: semantic_product_description...${NC}"
if [ ! -d "/home/giovano/Projetos/odoo16/custom_addons/semantic_product_description" ]; then
    echo -e "${RED}Atenção: O módulo semantic_product_description não foi encontrado!${NC}"
    echo -e "${YELLOW}Este módulo é uma dependência necessária. Execute primeiro o script install_semantic_module_odoo16.sh${NC}"
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
mkdir -p "$DEST_DIR/wizards"
mkdir -p "$DEST_DIR/security"
mkdir -p "$DEST_DIR/static/description"

# Verificar se os diretórios foram criados
echo -e "${YELLOW}Verificando diretórios criados:${NC}"
ls -la "$DEST_DIR"

# Copiar arquivos
echo -e "${YELLOW}Copiando arquivos para $DEST_DIR...${NC}"
cp "$SRC_DIR/__manifest__.py" "$DEST_DIR/"
cp "$SRC_DIR/__init__.py" "$DEST_DIR/"
cp "$SRC_DIR/models/__init__.py" "$DEST_DIR/models/"
cp "$SRC_DIR/models/product_template.py" "$DEST_DIR/models/"
cp "$SRC_DIR/views/product_views.xml" "$DEST_DIR/views/"
cp "$SRC_DIR/views/menu_views.xml" "$DEST_DIR/views/"
cp "$SRC_DIR/wizards/__init__.py" "$DEST_DIR/wizards/"
cp "$SRC_DIR/wizards/adjust_ai_prices_wizard.py" "$DEST_DIR/wizards/"
cp "$SRC_DIR/wizards/adjust_ai_prices_wizard_views.xml" "$DEST_DIR/wizards/"
cp "$SRC_DIR/security/ir.model.access.csv" "$DEST_DIR/security/"
if [ -f "$SRC_DIR/security/security.xml" ]; then
    cp "$SRC_DIR/security/security.xml" "$DEST_DIR/security/"
fi

# Verificar se os arquivos foram copiados
echo -e "${YELLOW}Verificando arquivos copiados:${NC}"
ls -la "$DEST_DIR"
ls -la "$DEST_DIR/models/"
ls -la "$DEST_DIR/views/"
ls -la "$DEST_DIR/wizards/"
ls -la "$DEST_DIR/security/"

# Definir permissões
echo -e "${YELLOW}Definindo permissões...${NC}"
chmod -R 755 "$DEST_DIR"

echo -e "${GREEN}Instalação concluída!${NC}"
echo -e "${GREEN}Agora você pode atualizar a lista de módulos no Odoo 16 e instalar 'Gerenciamento em Massa de Produtos no Sistema de IA'${NC}"

echo ""
echo -e "${BLUE}=== INSTRUÇÕES ADICIONAIS ===${NC}"
echo -e "${YELLOW}1. Para atualizar a lista de módulos no Odoo:${NC}"
echo "   - Acesse Configurações > Aplicativos > Atualizar Lista de Aplicativos"
echo "   - Busque por 'Gerenciamento em Massa' e instale o módulo"
echo ""
echo -e "${YELLOW}2. Para verificar os logs do módulo:${NC}"
echo "   - Logs do Odoo: sudo tail -f /var/log/odoo/odoo-server.log | grep product_ai_mass"
echo ""
echo -e "${YELLOW}3. Se encontrar erros durante a instalação:${NC}"
echo "   - Verifique os logs do Odoo: sudo tail -f /var/log/odoo/odoo-server.log"
echo "   - Desinstale o módulo antes de tentar novamente: sudo rm -rf $DEST_DIR"
echo ""
echo -e "${YELLOW}4. Nota sobre compatibilidade com Odoo 16:${NC}"
echo "   - Este módulo foi originalmente desenvolvido para Odoo 14"
echo "   - Pode ser necessário ajustar o código para compatibilidade com Odoo 16"
echo "   - Verifique os logs para identificar possíveis problemas de compatibilidade"
