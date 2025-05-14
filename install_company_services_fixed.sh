#!/bin/bash

# Script para instalar o módulo company_services no Odoo 16 com correções para problemas de importação circular
# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Diretório de origem (onde estamos criando os arquivos)
SRC_DIR="./addons/company_services"

# Diretório temporário para modificações
TMP_DIR="/tmp/company_services_fixed"

# Diretório de destino (onde o Odoo 16 procura por módulos)
DEST_DIR="/home/giovano/Projetos/odoo16/custom_addons/company_services"

echo -e "${BLUE}=== Script de Instalação do Módulo company_services Corrigido para Odoo 16 ===${NC}"
echo -e "${YELLOW}Verificando diretório de origem...${NC}"

# Verificar se o diretório de origem existe
if [ ! -d "$SRC_DIR" ]; then
    echo -e "${RED}Diretório de origem $SRC_DIR não encontrado!${NC}"
    exit 1
fi

# Criar diretório temporário
echo -e "${YELLOW}Criando diretório temporário para modificações...${NC}"
rm -rf "$TMP_DIR"
mkdir -p "$TMP_DIR"
mkdir -p "$TMP_DIR/models"
mkdir -p "$TMP_DIR/views"
mkdir -p "$TMP_DIR/data"
mkdir -p "$TMP_DIR/security"
mkdir -p "$TMP_DIR/controllers"
mkdir -p "$TMP_DIR/static/description"

# Copiar arquivos para o diretório temporário
echo -e "${YELLOW}Copiando arquivos para o diretório temporário...${NC}"
cp "$SRC_DIR/__manifest__.py" "$TMP_DIR/"
cp "$SRC_DIR/models/"*.py "$TMP_DIR/models/"
cp "$SRC_DIR/views/"*.xml "$TMP_DIR/views/"
if [ -d "$SRC_DIR/data" ]; then
    cp "$SRC_DIR/data/"*.xml "$TMP_DIR/data/"
fi
cp "$SRC_DIR/security/"*.xml "$TMP_DIR/security/"
cp "$SRC_DIR/security/"*.csv "$TMP_DIR/security/"
cp "$SRC_DIR/controllers/"*.py "$TMP_DIR/controllers/"

# Criar arquivo __init__.py corrigido
echo -e "${YELLOW}Criando arquivo __init__.py corrigido...${NC}"
cat > "$TMP_DIR/__init__.py" << EOF
# -*- coding: utf-8 -*-
# Importação corrigida para evitar problemas de importação circular
from . import models
EOF

# Criar arquivo controllers/__init__.py corrigido
echo -e "${YELLOW}Criando arquivo controllers/__init__.py corrigido...${NC}"
cat > "$TMP_DIR/controllers/__init__.py" << EOF
# -*- coding: utf-8 -*-
from . import main
EOF

# Corrigir o arquivo controllers/main.py
echo -e "${YELLOW}Corrigindo o arquivo controllers/main.py...${NC}"
sed -i 's/from odoo import http, _/from odoo import http, _, fields/g' "$TMP_DIR/controllers/main.py"
sed -i 's/last_sync: fields.Datetime.now()/last_sync: fields.Datetime.now()/g' "$TMP_DIR/controllers/main.py"

# Criar diretório de destino se não existir
echo -e "${YELLOW}Criando diretório de destino...${NC}"
rm -rf "$DEST_DIR"
mkdir -p "$DEST_DIR"

# Copiar arquivos do diretório temporário para o destino
echo -e "${YELLOW}Copiando arquivos para $DEST_DIR...${NC}"
cp -r "$TMP_DIR/"* "$DEST_DIR/"

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
echo -e "${YELLOW}4. Após a instalação bem-sucedida, você pode adicionar o controlador:${NC}"
echo "   - Edite o arquivo $DEST_DIR/__init__.py"
echo "   - Adicione a linha: from . import controllers"
echo "   - Reinicie o serviço Odoo"
