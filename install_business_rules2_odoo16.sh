#!/bin/bash

# Script para transferir o módulo business_rules2 para o diretório de addons do Odoo 16
# Este script deve ser executado na raiz do projeto atual

# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Diretório de destino (addons do Odoo 16)
ODOO_ADDONS_DIR="/home/giovano/Projetos/odoo16/custom_addons"

echo -e "${BLUE}=== Script de Transferência do Módulo business_rules2 para Odoo 16 ===${NC}"
echo -e "${YELLOW}Verificando o módulo business_rules2...${NC}"

# Verificar se o diretório @addons existe no projeto atual
if [ ! -d "@addons" ]; then
    echo -e "${RED}Diretório '@addons' não encontrado. Execute este script na raiz do projeto.${NC}"
    exit 1
fi

# Verificar se o módulo business_rules2 existe
if [ ! -d "@addons/business_rules2" ]; then
    echo -e "${RED}Módulo business_rules2 não encontrado em @addons/business_rules2.${NC}"
    exit 1
fi

# Verificar se os diretórios necessários existem
for dir in "models" "views" "security" "data" "controllers" "wizards" "static/description"; do
    if [ ! -d "@addons/business_rules2/$dir" ]; then
        echo -e "${YELLOW}Criando diretório @addons/business_rules2/$dir...${NC}"
        mkdir -p "@addons/business_rules2/$dir"
    fi
done

# Verificar se o arquivo business_rules_views.xml contém as ações no início
if [ -f "@addons/business_rules2/views/business_rules_views.xml" ]; then
    if ! grep -q "action_view_rule_items" "@addons/business_rules2/views/business_rules_views.xml" | head -n 20; then
        echo -e "${YELLOW}Verificando a ordem das ações no arquivo business_rules_views.xml...${NC}"
        if ! grep -q "<!-- Ações para os modelos relacionados" "@addons/business_rules2/views/business_rules_views.xml" | head -n 5; then
            echo -e "${YELLOW}Aviso: As ações devem ser declaradas no início do arquivo business_rules_views.xml para evitar erros de referência.${NC}"
            echo -e "${YELLOW}Recomenda-se verificar este arquivo antes de instalar o módulo.${NC}"
        fi
    fi
fi

# Verificar se os arquivos essenciais existem
essential_files=(
    "models/__init__.py"
    "models/business_rules.py"
    "models/rule_item.py"
    "models/temporary_rule.py"
    "models/scheduling_rule.py"
    "models/business_support_document.py"
    "models/business_template.py"
    "models/res_config_settings.py"
    "controllers/__init__.py"
    "controllers/sync_controller.py"
    "views/business_rules_views.xml"
    "views/rule_item_views.xml"
    "views/temporary_rule_views.xml"
    "views/scheduling_rule_views.xml"
    "views/business_support_document_views.xml"
    "views/res_config_settings_views.xml"
    "views/menu_views.xml"
    "wizards/__init__.py"
    "wizards/document_upload_wizard.py"
    "wizards/document_upload_wizard.xml"
    "data/config_parameter.xml"
    "security/ir.model.access.csv"
    "__init__.py"
    "__manifest__.py"
)

missing_files=0
for file in "${essential_files[@]}"; do
    if [ ! -f "@addons/business_rules2/$file" ]; then
        echo -e "${RED}Arquivo essencial não encontrado: @addons/business_rules2/$file${NC}"
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

# Verificar se os modelos têm os nomes corretos
if [ -f "@addons/business_rules2/models/business_rules.py" ]; then
    if ! grep -q "_name = 'business.rules2'" "@addons/business_rules2/models/business_rules.py"; then
        echo -e "${YELLOW}Aviso: O modelo principal pode não ter o nome correto.${NC}"
        echo -e "${YELLOW}Verifique se o modelo está definido como _name = 'business.rules2'.${NC}"
    fi
fi

# Copiar o módulo para o diretório de destino
echo -e "${BLUE}=== Transferindo o módulo para Odoo 16 ===${NC}"
echo -e "${YELLOW}Copiando módulo para $ODOO_ADDONS_DIR...${NC}"
cp -r @addons/business_rules2 "$ODOO_ADDONS_DIR/"

# Verificar se a cópia foi bem-sucedida
if [ $? -eq 0 ]; then
    echo -e "${GREEN}Módulo copiado com sucesso!${NC}"
    
    # Definir permissões corretas
    echo -e "${YELLOW}Definindo permissões...${NC}"
    chmod -R 755 "$ODOO_ADDONS_DIR/business_rules2"
    
    echo -e "${GREEN}Instalação concluída!${NC}"
    echo -e "${GREEN}Agora você pode atualizar a lista de módulos no Odoo 16 e instalar 'Regras de Negócio 2.0'${NC}"
else
    echo -e "${RED}Falha ao copiar o módulo.${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}=== INSTRUÇÕES ADICIONAIS ===${NC}"
echo -e "${YELLOW}1. Para atualizar a lista de módulos no Odoo:${NC}"
echo "   - Acesse Configurações > Aplicativos > Atualizar Lista de Aplicativos"
echo "   - Busque por 'Regras de Negócio' e instale o módulo"
echo ""
echo -e "${YELLOW}2. Para verificar os logs do módulo:${NC}"
echo "   - Logs do Odoo: sudo tail -f /var/log/odoo/odoo-server.log | grep business_rules2"
echo ""
echo -e "${YELLOW}3. Se encontrar erros durante a instalação:${NC}"
echo "   - Verifique os logs do Odoo: sudo tail -f /var/log/odoo/odoo-server.log"
echo "   - Desinstale o módulo antes de tentar novamente: sudo rm -rf $ODOO_ADDONS_DIR/business_rules2"
echo ""
echo -e "${YELLOW}4. Nota sobre compatibilidade com Odoo 16:${NC}"
echo "   - Este módulo foi originalmente desenvolvido para Odoo 14"
echo "   - Pode ser necessário ajustar o código para compatibilidade com Odoo 16"
echo "   - Verifique os logs para identificar possíveis problemas de compatibilidade"
