#!/bin/bash

# Script para instalar o módulo semantic_product_description no Odoo 16
# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Diretório de origem (onde estamos criando os arquivos)
SRC_DIR="./addons/semantic_product_description"

# Diretório de destino (onde o Odoo 16 procura por módulos)
DEST_DIR="/home/giovano/Projetos/odoo16/custom_addons/semantic_product_description"

echo -e "${BLUE}=== Script de Instalação do Módulo semantic_product_description para Odoo 16 ===${NC}"
echo -e "${YELLOW}Verificando diretório de origem...${NC}"

# Verificar se o diretório de origem existe
if [ ! -d "$SRC_DIR" ]; then
    echo -e "${RED}Diretório de origem $SRC_DIR não encontrado!${NC}"
    exit 1
fi

# Criar diretório de destino se não existir
echo -e "${YELLOW}Criando diretórios de destino...${NC}"
mkdir -p "$DEST_DIR/models"
mkdir -p "$DEST_DIR/views"
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
cp "$SRC_DIR/views/product_template_views.xml" "$DEST_DIR/views/"

# Verificar se os arquivos foram copiados
echo -e "${YELLOW}Verificando arquivos copiados:${NC}"
ls -la "$DEST_DIR"
ls -la "$DEST_DIR/models/"
ls -la "$DEST_DIR/views/"

# Definir permissões
echo -e "${YELLOW}Definindo permissões...${NC}"
chmod -R 755 "$DEST_DIR"

echo -e "${GREEN}Instalação concluída!${NC}"
echo -e "${GREEN}Agora você pode atualizar a lista de módulos no Odoo 16 e instalar 'Descrições Inteligentes de Produtos'${NC}"

echo ""
echo -e "${BLUE}=== INSTRUÇÕES ADICIONAIS ===${NC}"
echo -e "${YELLOW}1. Para atualizar a lista de módulos no Odoo:${NC}"
echo "   - Acesse Configurações > Aplicativos > Atualizar Lista de Aplicativos"
echo "   - Busque por 'Descrições Inteligentes' e instale o módulo"
echo ""
echo -e "${YELLOW}2. Para verificar os logs do módulo:${NC}"
echo "   - Logs do Odoo: sudo tail -f /var/log/odoo/odoo-server.log | grep semantic_product"
echo ""
echo -e "${YELLOW}3. Se encontrar erros durante a instalação:${NC}"
echo "   - Verifique os logs do Odoo: sudo tail -f /var/log/odoo/odoo-server.log"
echo "   - Desinstale o módulo antes de tentar novamente: sudo rm -rf $DEST_DIR"
echo ""
echo -e "${YELLOW}4. Nota sobre compatibilidade com Odoo 16:${NC}"
echo "   - Este módulo foi originalmente desenvolvido para Odoo 14"
echo "   - Pode ser necessário ajustar o código para compatibilidade com Odoo 16"
echo "   - Verifique os logs para identificar possíveis problemas de compatibilidade"
