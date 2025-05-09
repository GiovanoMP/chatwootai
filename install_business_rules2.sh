#!/bin/bash

# Script para transferir o módulo business_rules2 para o diretório de addons do Odoo
# Este script deve ser executado na raiz do projeto atual

# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Diretório de destino (addons do Odoo)
ODOO_ADDONS_DIR="/home/giovano/Projetos/odoo14/addons/custom-addons"

echo -e "${BLUE}=== Script de Transferência do Módulo business_rules2 ===${NC}"
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
    echo -e "${RED}$missing_files arquivos essenciais não encontrados. Verifique se o módulo está completo.${NC}"
    echo -e "${YELLOW}Deseja continuar mesmo assim? (s/n)${NC}"
    read continue_anyway

    if [ "$continue_anyway" != "s" ]; then
        echo -e "${RED}Instalação cancelada.${NC}"
        exit 1
    fi
fi

# Verificar se o diretório de destino existe
if [ ! -d "$ODOO_ADDONS_DIR" ]; then
    echo -e "${RED}Diretório de destino '$ODOO_ADDONS_DIR' não encontrado.${NC}"
    echo -e "${YELLOW}Deseja criar o diretório? (s/n)${NC}"
    read create_dir

    if [ "$create_dir" = "s" ]; then
        mkdir -p "$ODOO_ADDONS_DIR"
        echo -e "${GREEN}Diretório criado.${NC}"
    else
        echo -e "${RED}Instalação cancelada.${NC}"
        exit 1
    fi
fi

# Verificar se o módulo já existe no destino
if [ -d "$ODOO_ADDONS_DIR/business_rules2" ]; then
    echo -e "${YELLOW}O módulo business_rules2 já existe no diretório de destino.${NC}"
    echo -e "${YELLOW}Deseja substituí-lo? (s/n)${NC}"
    read replace_module

    if [ "$replace_module" = "s" ]; then
        echo -e "${YELLOW}Removendo módulo existente...${NC}"
        rm -rf "$ODOO_ADDONS_DIR/business_rules2"
        echo -e "${GREEN}Módulo existente removido.${NC}"
    else
        echo -e "${RED}Instalação cancelada.${NC}"
        exit 1
    fi
fi

# Verificar se há problemas conhecidos no código
echo -e "${YELLOW}Verificando possíveis problemas no código...${NC}"

# Verificar se o controlador de sincronização está correto
if [ -f "@addons/business_rules2/controllers/sync_controller.py" ]; then
    if ! grep -q "business.rules2.sync.controller" "@addons/business_rules2/controllers/sync_controller.py"; then
        echo -e "${YELLOW}Aviso: O controlador de sincronização pode não estar corretamente definido.${NC}"
        echo -e "${YELLOW}Verifique se a classe BusinessRules2SyncController está definida corretamente.${NC}"
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
echo -e "${BLUE}=== Transferindo o módulo ===${NC}"
echo -e "${YELLOW}Copiando módulo para $ODOO_ADDONS_DIR...${NC}"
cp -r @addons/business_rules2 "$ODOO_ADDONS_DIR/"

# Verificar se a cópia foi bem-sucedida
if [ $? -eq 0 ]; then
    echo -e "${GREEN}Módulo copiado com sucesso!${NC}"

    # Verificar se o ícone existe, se não, criar um ícone simples
    if [ ! -f "$ODOO_ADDONS_DIR/business_rules2/static/description/icon.png" ]; then
        echo -e "${YELLOW}Ícone não encontrado. Criando um ícone simples...${NC}"

        # Verificar se o ImageMagick está instalado
        if command -v convert &> /dev/null; then
            # Criar um ícone simples usando ImageMagick
            convert -size 128x128 xc:#1A4B8C \
                -fill white -draw "circle 64,64 64,32" \
                -fill "#1A4B8C" -gravity center -pointsize 40 -annotate 0 "BR" \
                "$ODOO_ADDONS_DIR/business_rules2/static/description/icon.png"

            echo -e "${GREEN}Ícone criado com sucesso.${NC}"
        else
            echo -e "${YELLOW}ImageMagick não encontrado. Não foi possível criar o ícone.${NC}"
            echo -e "${YELLOW}O módulo funcionará, mas não terá um ícone personalizado.${NC}"
        fi
    fi

    # Criar arquivo de configuração para o webhook
    echo -e "${BLUE}=== Configuração do Webhook ===${NC}"
    echo -e "${YELLOW}Deseja configurar os parâmetros do webhook agora? (s/n)${NC}"
    read configure_webhook

    if [ "$configure_webhook" = "s" ]; then
        echo -e "${YELLOW}Configurando parâmetros do webhook...${NC}"

        # Solicitar informações do webhook
        echo -e "${YELLOW}Digite a URL do webhook (padrão: http://localhost:8004):${NC}"
        read webhook_url
        webhook_url=${webhook_url:-http://localhost:8004}

        echo -e "${YELLOW}Digite o token de API (padrão: development-api-key):${NC}"
        read api_token
        api_token=${api_token:-development-api-key}

        echo -e "${YELLOW}Digite o nome da empresa (padrão: Empresa Exemplo):${NC}"
        read company_name
        company_name=${company_name:-Empresa Exemplo}

        echo -e "${YELLOW}Digite o ID da conta (padrão: account_1):${NC}"
        read account_id
        account_id=${account_id:-account_1}

        # Criar arquivo SQL para configurar parâmetros
        cat > webhook_config.sql << EOF
-- Configurações para o webhook do módulo business_rules2
-- Execute este script após instalar o módulo

-- Configurações do webhook
INSERT INTO ir_config_parameter (key, value, create_date, write_date)
VALUES ('business_rules2.webhook_url', '$webhook_url', NOW(), NOW())
ON CONFLICT (key) DO UPDATE SET value = '$webhook_url', write_date = NOW();

INSERT INTO ir_config_parameter (key, value, create_date, write_date)
VALUES ('business_rules2.api_token', '$api_token', NOW(), NOW())
ON CONFLICT (key) DO UPDATE SET value = '$api_token', write_date = NOW();

-- Configurações do tenant
INSERT INTO ir_config_parameter (key, value, create_date, write_date)
VALUES ('business_rules2.company_name', '$company_name', NOW(), NOW())
ON CONFLICT (key) DO UPDATE SET value = '$company_name', write_date = NOW();

INSERT INTO ir_config_parameter (key, value, create_date, write_date)
VALUES ('business_rules2.account_id', '$account_id', NOW(), NOW())
ON CONFLICT (key) DO UPDATE SET value = '$account_id', write_date = NOW();
EOF

        echo -e "${GREEN}Arquivo de configuração criado: webhook_config.sql${NC}"
        echo -e "${YELLOW}Execute este arquivo SQL no banco de dados do Odoo após instalar o módulo.${NC}"
    fi

    echo -e "${BLUE}=== Instalação Concluída ===${NC}"
    echo -e "${GREEN}Módulo business_rules2 transferido com sucesso para $ODOO_ADDONS_DIR/business_rules2${NC}"
    echo -e "${BLUE}=== Próximos Passos ===${NC}"
    echo -e "${YELLOW}1. Reinicie o servidor Odoo${NC}"
    echo -e "${YELLOW}2. Acesse o Odoo e atualize a lista de aplicativos${NC}"
    echo -e "${YELLOW}3. Instale o módulo 'Regras de Negócio 2.0'${NC}"
    echo -e "${YELLOW}4. Execute o arquivo webhook_config.sql no banco de dados do Odoo (se criado)${NC}"
    echo -e "${YELLOW}5. Configure as regras de negócio${NC}"
    echo -e "${YELLOW}6. Configure o ID da Conta nas configurações (será usado como identificador no Qdrant)${NC}"
    echo -e "${YELLOW}7. Sincronize com o sistema de IA usando o botão verde 'Sincronizar com Sistema de IA'${NC}"

    echo -e "${BLUE}=== Observações Importantes ===${NC}"
    echo -e "${YELLOW}• Se encontrar erros durante a instalação do módulo, verifique os logs do Odoo${NC}"
    echo -e "${YELLOW}• O erro 'External ID not found' geralmente indica problemas na ordem de declaração das ações nos arquivos XML${NC}"
    echo -e "${YELLOW}• Certifique-se de que o microsserviço de vetorização esteja configurado e acessível na URL definida${NC}"
else
    echo -e "${RED}Erro ao copiar o módulo. Verifique as permissões do diretório de destino.${NC}"
    exit 1
fi

exit 0
