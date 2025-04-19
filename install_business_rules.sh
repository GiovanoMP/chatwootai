#!/bin/bash

# Definir diretórios
SRC_DIR="./addons/business_rules"
DEST_DIR="/home/giovano/Projetos/odoo14/addons/custom-addons/business_rules"

# Verificar se o diretório de origem existe
if [ ! -d "$SRC_DIR" ]; then
    echo "Diretório de origem $SRC_DIR não encontrado!"
    exit 1
fi

# Criar diretório de destino se não existir
mkdir -p "$DEST_DIR/models"
mkdir -p "$DEST_DIR/views"
mkdir -p "$DEST_DIR/security"
mkdir -p "$DEST_DIR/static/description"
mkdir -p "$DEST_DIR/wizards"
mkdir -p "$DEST_DIR/data"
mkdir -p "$DEST_DIR/controllers"

# Verificar se os diretórios foram criados
echo "Verificando diretórios criados:"
ls -la "$DEST_DIR"

# Copiar arquivos
echo "Copiando arquivos para $DEST_DIR..."
cp "$SRC_DIR/__manifest__.py" "$DEST_DIR/"
cp "$SRC_DIR/__init__.py" "$DEST_DIR/"
cp "$SRC_DIR/README.md" "$DEST_DIR/"

# Copiar modelos
cp "$SRC_DIR/models/__init__.py" "$DEST_DIR/models/"
cp "$SRC_DIR/models/business_rules.py" "$DEST_DIR/models/"
cp "$SRC_DIR/models/business_template.py" "$DEST_DIR/models/"
cp "$SRC_DIR/models/rule_item.py" "$DEST_DIR/models/"
cp "$SRC_DIR/models/temporary_rule.py" "$DEST_DIR/models/"
cp "$SRC_DIR/models/scheduling_rule.py" "$DEST_DIR/models/"
cp "$SRC_DIR/models/dashboard.py" "$DEST_DIR/models/"
cp "$SRC_DIR/models/res_config_settings.py" "$DEST_DIR/models/"
cp "$SRC_DIR/models/business_support_document.py" "$DEST_DIR/models/"

# Copiar vistas
cp "$SRC_DIR/views/business_rules_views.xml" "$DEST_DIR/views/"
cp "$SRC_DIR/views/rule_item_views.xml" "$DEST_DIR/views/"
cp "$SRC_DIR/views/temporary_rule_views.xml" "$DEST_DIR/views/"
cp "$SRC_DIR/views/scheduling_rule_views.xml" "$DEST_DIR/views/"
cp "$SRC_DIR/views/dashboard_view.xml" "$DEST_DIR/views/"
cp "$SRC_DIR/views/menu_views.xml" "$DEST_DIR/views/"
cp "$SRC_DIR/views/res_config_settings_views.xml" "$DEST_DIR/views/"
cp "$SRC_DIR/views/business_support_document_views.xml" "$DEST_DIR/views/"

# Copiar wizards
cp "$SRC_DIR/wizards/__init__.py" "$DEST_DIR/wizards/"
cp "$SRC_DIR/wizards/website_scraper_wizard.py" "$DEST_DIR/wizards/"
cp "$SRC_DIR/wizards/document_upload_wizard.py" "$DEST_DIR/wizards/"
cp "$SRC_DIR/wizards/document_upload_wizard.xml" "$DEST_DIR/wizards/"

# Copiar controladores
cp "$SRC_DIR/controllers/__init__.py" "$DEST_DIR/controllers/"
cp "$SRC_DIR/controllers/sync_controller.py" "$DEST_DIR/controllers/"

# Copiar dados
cp "$SRC_DIR/data/business_template_data.xml" "$DEST_DIR/data/"
cp "$SRC_DIR/data/config_parameter.xml" "$DEST_DIR/data/"

# Copiar segurança
cp "$SRC_DIR/security/ir.model.access.csv" "$DEST_DIR/security/"

# Verificar se os arquivos foram copiados
echo "Verificando arquivos copiados:"
ls -la "$DEST_DIR/models/"
ls -la "$DEST_DIR/views/"
ls -la "$DEST_DIR/wizards/"
ls -la "$DEST_DIR/controllers/"
ls -la "$DEST_DIR/data/"
ls -la "$DEST_DIR/security/"

echo "Instalação concluída!"
echo "Agora você pode atualizar a lista de módulos no Odoo e instalar o módulo 'Regras de Negócio para Sistema de IA'"
echo ""
echo "Para reiniciar o Odoo e aplicar as alterações, execute:"
echo "docker-compose restart odoo"
