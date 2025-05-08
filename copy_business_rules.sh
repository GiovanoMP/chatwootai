#!/bin/bash

# Definir diretórios
SRC_DIR="./addons/business_rules"
DEST_DIR="/home/giovano/Projetos/odoo14/addons/custom-addons/business_rules"

# Verificar se o diretório de origem existe
if [ ! -d "$SRC_DIR" ]; then
    echo "Erro: Diretório de origem $SRC_DIR não encontrado!"
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

# Copiar arquivos
echo "Copiando arquivos para $DEST_DIR..."

# Copiar arquivos principais
cp -f "$SRC_DIR/__manifest__.py" "$DEST_DIR/" 2>/dev/null || echo "Aviso: Não foi possível copiar __manifest__.py"
cp -f "$SRC_DIR/__init__.py" "$DEST_DIR/" 2>/dev/null || echo "Aviso: Não foi possível copiar __init__.py"
cp -f "$SRC_DIR/README.md" "$DEST_DIR/" 2>/dev/null || echo "Aviso: Não foi possível copiar README.md"

# Copiar modelos
echo "Copiando modelos..."
cp -f "$SRC_DIR/models/__init__.py" "$DEST_DIR/models/" 2>/dev/null || echo "Aviso: Não foi possível copiar models/__init__.py"
cp -f "$SRC_DIR/models/business_rules.py" "$DEST_DIR/models/" 2>/dev/null || echo "Aviso: Não foi possível copiar models/business_rules.py"
cp -f "$SRC_DIR/models/business_template.py" "$DEST_DIR/models/" 2>/dev/null || echo "Aviso: Não foi possível copiar models/business_template.py"
cp -f "$SRC_DIR/models/rule_item.py" "$DEST_DIR/models/" 2>/dev/null || echo "Aviso: Não foi possível copiar models/rule_item.py"
cp -f "$SRC_DIR/models/temporary_rule.py" "$DEST_DIR/models/" 2>/dev/null || echo "Aviso: Não foi possível copiar models/temporary_rule.py"
cp -f "$SRC_DIR/models/scheduling_rule.py" "$DEST_DIR/models/" 2>/dev/null || echo "Aviso: Não foi possível copiar models/scheduling_rule.py"
cp -f "$SRC_DIR/models/dashboard.py" "$DEST_DIR/models/" 2>/dev/null || echo "Aviso: Não foi possível copiar models/dashboard.py"
cp -f "$SRC_DIR/models/res_config_settings.py" "$DEST_DIR/models/" 2>/dev/null || echo "Aviso: Não foi possível copiar models/res_config_settings.py"
cp -f "$SRC_DIR/models/business_support_document.py" "$DEST_DIR/models/" 2>/dev/null || echo "Aviso: Não foi possível copiar models/business_support_document.py"
cp -f "$SRC_DIR/models/unified_rule.py" "$DEST_DIR/models/" 2>/dev/null || echo "Aviso: Não foi possível copiar models/unified_rule.py"
cp -f "$SRC_DIR/models/config_service_adapter.py" "$DEST_DIR/models/" 2>/dev/null || echo "Aviso: Não foi possível copiar models/config_service_adapter.py"
cp -f "$SRC_DIR/models/config_service_client.py" "$DEST_DIR/models/" 2>/dev/null || echo "Aviso: Não foi possível copiar models/config_service_client.py"

# Copiar vistas
echo "Copiando vistas..."
cp -f "$SRC_DIR/views/business_rules_views.xml" "$DEST_DIR/views/" 2>/dev/null || echo "Aviso: Não foi possível copiar views/business_rules_views.xml"
cp -f "$SRC_DIR/views/rule_item_views.xml" "$DEST_DIR/views/" 2>/dev/null || echo "Aviso: Não foi possível copiar views/rule_item_views.xml"
cp -f "$SRC_DIR/views/temporary_rule_views.xml" "$DEST_DIR/views/" 2>/dev/null || echo "Aviso: Não foi possível copiar views/temporary_rule_views.xml"
cp -f "$SRC_DIR/views/scheduling_rule_views.xml" "$DEST_DIR/views/" 2>/dev/null || echo "Aviso: Não foi possível copiar views/scheduling_rule_views.xml"
cp -f "$SRC_DIR/views/dashboard_view.xml" "$DEST_DIR/views/" 2>/dev/null || echo "Aviso: Não foi possível copiar views/dashboard_view.xml"
cp -f "$SRC_DIR/views/menu_views.xml" "$DEST_DIR/views/" 2>/dev/null || echo "Aviso: Não foi possível copiar views/menu_views.xml"
cp -f "$SRC_DIR/views/res_config_settings_views.xml" "$DEST_DIR/views/" 2>/dev/null || echo "Aviso: Não foi possível copiar views/res_config_settings_views.xml"
cp -f "$SRC_DIR/views/business_support_document_views.xml" "$DEST_DIR/views/" 2>/dev/null || echo "Aviso: Não foi possível copiar views/business_support_document_views.xml"

# Copiar wizards
echo "Copiando wizards..."
cp -f "$SRC_DIR/wizards/__init__.py" "$DEST_DIR/wizards/" 2>/dev/null || echo "Aviso: Não foi possível copiar wizards/__init__.py"
cp -f "$SRC_DIR/wizards/website_scraper_wizard.py" "$DEST_DIR/wizards/" 2>/dev/null || echo "Aviso: Não foi possível copiar wizards/website_scraper_wizard.py"
cp -f "$SRC_DIR/wizards/document_upload_wizard.py" "$DEST_DIR/wizards/" 2>/dev/null || echo "Aviso: Não foi possível copiar wizards/document_upload_wizard.py"
cp -f "$SRC_DIR/wizards/document_upload_wizard.xml" "$DEST_DIR/wizards/" 2>/dev/null || echo "Aviso: Não foi possível copiar wizards/document_upload_wizard.xml"

# Copiar controladores
echo "Copiando controladores..."
cp -f "$SRC_DIR/controllers/__init__.py" "$DEST_DIR/controllers/" 2>/dev/null || echo "Aviso: Não foi possível copiar controllers/__init__.py"
cp -f "$SRC_DIR/controllers/sync_controller.py" "$DEST_DIR/controllers/" 2>/dev/null || echo "Aviso: Não foi possível copiar controllers/sync_controller.py"

# Copiar dados
echo "Copiando dados..."
cp -f "$SRC_DIR/data/business_template_data.xml" "$DEST_DIR/data/" 2>/dev/null || echo "Aviso: Não foi possível copiar data/business_template_data.xml"
cp -f "$SRC_DIR/data/config_parameter.xml" "$DEST_DIR/data/" 2>/dev/null || echo "Aviso: Não foi possível copiar data/config_parameter.xml"

# Copiar segurança
echo "Copiando segurança..."
cp -f "$SRC_DIR/security/ir.model.access.csv" "$DEST_DIR/security/" 2>/dev/null || echo "Aviso: Não foi possível copiar security/ir.model.access.csv"

# Verificar se os arquivos foram copiados
echo "Verificando arquivos copiados:"
ls -la "$DEST_DIR/models/"

echo "Cópia concluída!"
echo "Os arquivos foram copiados para $DEST_DIR"
echo ""
echo "IMPORTANTE: Nova Arquitetura de Microsserviços"
echo "Este módulo agora envia dados diretamente para o microsserviço config-service,"
echo "que armazena as configurações no PostgreSQL. Isso faz parte da nova arquitetura"
echo "que separa a stack de IA dos serviços de configuração."
echo ""
echo "Para configurar o microsserviço config-service, acesse:"
echo "Configurações > Técnico > Parâmetros > Parâmetros do Sistema"
echo "E configure os seguintes parâmetros:"
echo "- config_service.url: URL do microsserviço (ex: http://localhost:8002)"
echo "- config_service.api_key: Chave de API para autenticação"
echo "- business_rules.account_id: ID da conta para sincronização de regras de negócio"
echo ""
echo "Para configurar o visualizador de configurações web, acesse:"
echo "Configurações > Técnico > Parâmetros > Parâmetros do Sistema"
echo "E configure o seguinte parâmetro:"
echo "- config_viewer.url: URL para o visualizador web (ex: http://localhost:8080)"
echo ""
echo "Após a cópia, reinicie o servidor Odoo e atualize o módulo através da interface do Odoo:"
echo "1. Acesse Aplicativos > Atualizar Lista de Aplicativos"
echo "2. Acesse Aplicativos > Busque por 'Regras de Negócio'"
echo "3. Clique em 'Atualizar' no módulo 'Regras de Negócio para Sistema de IA'"
