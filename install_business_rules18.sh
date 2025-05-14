#!/bin/bash

# Cores para saída
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Diretório de destino para os módulos do Odoo 18
ODOO18_ADDONS_DIR="/home/giovano/Projetos/odoo18/custom_addons"

# Diretório do módulo
MODULE_DIR="addons18/business_rules18"

echo -e "${YELLOW}Iniciando instalação do módulo business_rules18 para Odoo 18...${NC}"
echo -e "${YELLOW}O módulo será instalado diretamente no volume Docker: $ODOO18_ADDONS_DIR${NC}"

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
    "models/business_rules.py"
    "models/rule_item.py"
    "models/temporary_rule.py"
    "models/scheduling_rule.py"
    "models/business_support_document.py"
    "models/business_template.py"
    "models/res_config_settings.py"
    "controllers/__init__.py"
    "controllers/sync_controller.py"
    "wizards/__init__.py"
    "wizards/document_upload_wizard.py"
    "wizards/document_upload_wizard.xml"
    "security/business_rules_security.xml"
    "security/ir.model.access.csv"
    "views/business_rules_views.xml"
    "views/business_support_document_views.xml"
    "views/rule_item_views.xml"
    "views/scheduling_rule_views.xml"
    "views/temporary_rule_views.xml"
    "views/res_config_settings_views.xml"
    "views/menu_views.xml"
    "data/config_parameter.xml"
)

for file in "${essential_files[@]}"; do
    if [ ! -f "$MODULE_DIR/$file" ]; then
        echo -e "${RED}Erro: Arquivo essencial $MODULE_DIR/$file não encontrado.${NC}"
        exit 1
    fi
done

# Remover instalação anterior se existir
if [ -d "$ODOO18_ADDONS_DIR/business_rules18" ]; then
    echo -e "${YELLOW}Removendo instalação anterior...${NC}"
    rm -rf "$ODOO18_ADDONS_DIR/business_rules18"
fi

# Copiar o módulo para o diretório de destino
echo -e "${YELLOW}Copiando módulo para $ODOO18_ADDONS_DIR...${NC}"
cp -r "$MODULE_DIR" "$ODOO18_ADDONS_DIR/"

# Verificar se a cópia foi bem-sucedida
if [ $? -eq 0 ]; then
    echo -e "${GREEN}Módulo business_rules18 copiado com sucesso para $ODOO18_ADDONS_DIR.${NC}"

    # Verificar a ordem de carregamento no __manifest__.py
    echo -e "${YELLOW}Verificando a ordem de carregamento no __manifest__.py...${NC}"
    if grep -A 20 "'data': \[" "$ODOO18_ADDONS_DIR/business_rules18/__manifest__.py" | grep -q "wizards/document_upload_wizard.xml" &&
       grep -A 20 "'data': \[" "$ODOO18_ADDONS_DIR/business_rules18/__manifest__.py" | grep -A 20 "wizards/document_upload_wizard.xml" | grep -q "views/business_rules_views.xml"; then
        echo -e "${GREEN}Ordem de carregamento correta: wizards/document_upload_wizard.xml está antes de views/business_rules_views.xml${NC}"
    else
        echo -e "${RED}AVISO: A ordem de carregamento pode estar incorreta. Verifique se wizards/document_upload_wizard.xml está antes de views/business_rules_views.xml no __manifest__.py${NC}"
    fi

    # Verificar se não há referências ao campo rule_type no modelo business.rules
    echo -e "${YELLOW}Verificando referências ao campo rule_type removido...${NC}"

    # Verificar em todos os arquivos XML
    rule_type_files=$(grep -l "rule_type" "$ODOO18_ADDONS_DIR/business_rules18/views/"*.xml 2>/dev/null)

    if [ -n "$rule_type_files" ]; then
        echo -e "${RED}AVISO: Encontradas referências ao campo 'rule_type' nos seguintes arquivos:${NC}"
        for file in $rule_type_files; do
            echo -e "  - $file"
        done
        echo -e "${RED}Este campo foi removido do modelo business.rules e deve ser removido das views.${NC}"

        # Perguntar se deseja corrigir automaticamente
        echo -e "${YELLOW}Deseja corrigir automaticamente as referências ao campo rule_type? (s/n)${NC}"
        read fix_rule_type

        if [ "$fix_rule_type" = "s" ]; then
            for file in $rule_type_files; do
                echo -e "${YELLOW}Corrigindo arquivo: $file${NC}"

                # Remover a linha inteira que contém apenas o campo rule_type
                sed -i '/<field name="rule_type"\/>/d' "$file"

                # Remover o campo rule_type quando está em uma linha com outros campos
                sed -i 's/<field name="rule_type"\/>//g' "$file"
                sed -i 's/<field name="rule_type">//g' "$file"
            done

            echo -e "${GREEN}Referências ao campo rule_type removidas de todos os arquivos.${NC}"
        fi
    else
        echo -e "${GREEN}Não foram encontradas referências ao campo rule_type removido.${NC}"
    fi

    # Verificar se há referências a campos em modelos relacionados que podem causar problemas
    echo -e "${YELLOW}Verificando referências a campos em modelos relacionados...${NC}"

    # Lista de campos que podem estar em views embutidas
    embedded_fields=(
        "date_start"
        "date_end"
        "rule_type"
        "state"
        "service_type"
        "sequence"
        "duration"
        "document_type"
    )

    # Verificar se há referências a campos em modelos relacionados
    found_fields=()
    for field in "${embedded_fields[@]}"; do
        if grep -q "$field" "$ODOO18_ADDONS_DIR/business_rules18/views/"*.xml; then
            found_fields+=("$field")
        fi
    done

    if [ ${#found_fields[@]} -gt 0 ]; then
        echo -e "${YELLOW}AVISO: Encontradas referências a campos de modelos relacionados nas views:${NC}"
        for field in "${found_fields[@]}"; do
            echo -e "  - $field"
        done
        echo -e "${YELLOW}Estes campos existem apenas nos modelos relacionados, não no modelo principal business.rules.${NC}"
        echo -e "${YELLOW}Isso pode causar problemas de validação no Odoo 18.${NC}"

        # Verificar se os campos dummy já existem no modelo principal
        if ! grep -q "_compute_dummy_fields" "$ODOO18_ADDONS_DIR/business_rules18/models/business_rules.py"; then
            echo -e "${YELLOW}AVISO: O método _compute_dummy_fields não foi encontrado no modelo business.rules.${NC}"
            echo -e "${YELLOW}É necessário adicionar campos dummy e o método _compute_dummy_fields para compatibilidade com views embutidas.${NC}"
            echo -e "${YELLOW}Consulte o arquivo README_ODOO18.md para mais informações sobre como resolver este problema.${NC}"
        else
            echo -e "${GREEN}O modelo business.rules já possui o método _compute_dummy_fields para compatibilidade com views embutidas.${NC}"

            # Verificar se todos os campos encontrados estão definidos como campos dummy
            missing_fields=()
            for field in "${found_fields[@]}"; do
                if ! grep -q "$field = fields\." "$ODOO18_ADDONS_DIR/business_rules18/models/business_rules.py"; then
                    missing_fields+=("$field")
                fi
            done

            if [ ${#missing_fields[@]} -gt 0 ]; then
                echo -e "${YELLOW}AVISO: Os seguintes campos não estão definidos como campos dummy no modelo business.rules:${NC}"
                for field in "${missing_fields[@]}"; do
                    echo -e "  - $field"
                done
                echo -e "${YELLOW}É necessário adicionar estes campos como campos dummy para compatibilidade com views embutidas.${NC}"
                echo -e "${YELLOW}Consulte o arquivo README_ODOO18.md para mais informações sobre como resolver este problema.${NC}"
            else
                echo -e "${GREEN}Todos os campos encontrados nas views estão definidos como campos dummy no modelo business.rules.${NC}"
            fi
        fi
    else
        echo -e "${GREEN}Não foram encontradas referências a campos de modelos relacionados nas views.${NC}"
    fi

    echo -e "${YELLOW}Agora você precisa:${NC}"
    echo -e "1. Reiniciar o servidor Odoo"
    echo -e "2. Atualizar a lista de aplicativos no Odoo"
    echo -e "3. Instalar o módulo 'Regras de Negócio'"
else
    echo -e "${RED}Erro ao copiar o módulo.${NC}"
    exit 1
fi

echo -e "${GREEN}Processo de instalação concluído!${NC}"
echo -e "${YELLOW}Dicas para solução de problemas:${NC}"
echo -e "- Se encontrar erros de 'External ID not found', verifique a ordem de carregamento no __manifest__.py"
echo -e "- Verifique os logs do Odoo para erros detalhados: docker logs -f odoo18"
echo -e "- Consulte o arquivo README_ODOO18.md para mais informações sobre melhores práticas"
