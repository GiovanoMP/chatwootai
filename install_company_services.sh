#!/bin/bash

# Script para transferir o módulo company_services para o diretório de addons do Odoo
# Este script deve ser executado na raiz do projeto atual

# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Diretório de destino (addons do Odoo)
ODOO_ADDONS_DIR="/home/giovano/Projetos/odoo14/addons/custom-addons"

echo -e "${YELLOW}Instalando o módulo company_services no Odoo...${NC}"

# Verificar se o diretório addons existe no projeto atual
if [ ! -d "addons" ]; then
    echo -e "${RED}Diretório 'addons' não encontrado. Execute este script na raiz do projeto.${NC}"
    exit 1
fi

# Verificar se o módulo company_services existe
if [ ! -d "addons/company_services" ]; then
    echo -e "${RED}Módulo company_services não encontrado em addons/company_services.${NC}"
    exit 1
fi

# Verificar se os diretórios necessários existem
for dir in "models" "views" "security" "data" "static/description"; do
    if [ ! -d "addons/company_services/$dir" ]; then
        echo -e "${YELLOW}Criando diretório addons/company_services/$dir...${NC}"
        mkdir -p "addons/company_services/$dir"
    fi
done

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
    if [ ! -f "addons/company_services/$file" ]; then
        echo -e "${RED}Arquivo essencial não encontrado: addons/company_services/$file${NC}"
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
if [ -d "$ODOO_ADDONS_DIR/company_services" ]; then
    echo -e "${YELLOW}O módulo company_services já existe no diretório de destino.${NC}"
    echo -e "${YELLOW}Deseja substituí-lo? (s/n)${NC}"
    read replace_module

    if [ "$replace_module" = "s" ]; then
        echo -e "${YELLOW}Removendo módulo existente...${NC}"
        rm -rf "$ODOO_ADDONS_DIR/company_services"
        echo -e "${GREEN}Módulo existente removido.${NC}"
    else
        echo -e "${RED}Instalação cancelada.${NC}"
        exit 1
    fi
fi

# Copiar o módulo para o diretório de destino
echo -e "${YELLOW}Copiando módulo para $ODOO_ADDONS_DIR...${NC}"
cp -r addons/company_services "$ODOO_ADDONS_DIR/"

# Verificar se a cópia foi bem-sucedida
if [ $? -eq 0 ]; then
    # Verificar se o ícone existe, se não, criar um ícone simples
    if [ ! -f "$ODOO_ADDONS_DIR/company_services/static/description/icon.png" ]; then
        echo -e "${YELLOW}Ícone não encontrado. Criando um ícone simples...${NC}"

        # Verificar se o ImageMagick está instalado
        if command -v convert &> /dev/null; then
            # Criar um ícone simples usando ImageMagick
            convert -size 128x128 xc:#2E7D32 \
                -fill white -draw "circle 64,64 64,32" \
                -fill "#2E7D32" -gravity center -pointsize 40 -annotate 0 "ES" \
                "$ODOO_ADDONS_DIR/company_services/static/description/icon.png"

            echo -e "${GREEN}Ícone criado com sucesso.${NC}"
        else
            echo -e "${YELLOW}ImageMagick não encontrado. Não foi possível criar o ícone.${NC}"
            echo -e "${YELLOW}O módulo funcionará, mas não terá um ícone personalizado.${NC}"
        fi
    fi

    # Criar arquivo de configuração para MCP e banco de dados
    echo -e "${YELLOW}Deseja configurar os parâmetros de MCP e banco de dados agora? (s/n)${NC}"
    read configure_mcp

    if [ "$configure_mcp" = "s" ]; then
        echo -e "${YELLOW}Configurando parâmetros de MCP e banco de dados...${NC}"

        # Criar arquivo SQL para configurar parâmetros
        cat > mcp_config.sql << EOF
-- Configurações de MCP e banco de dados para o módulo company_services
-- Execute este script após instalar o módulo

-- Configurações de MCP
INSERT INTO ir_config_parameter (key, value, create_date, write_date)
VALUES ('company_services.mcp_type', 'odoo', NOW(), NOW())
ON CONFLICT (key) DO UPDATE SET value = 'odoo', write_date = NOW();

INSERT INTO ir_config_parameter (key, value, create_date, write_date)
VALUES ('company_services.mcp_version', '14.0', NOW(), NOW())
ON CONFLICT (key) DO UPDATE SET value = '14.0', write_date = NOW();

-- Configurações de banco de dados
INSERT INTO ir_config_parameter (key, value, create_date, write_date)
VALUES ('company_services.db_url', 'http://localhost:8069', NOW(), NOW())
ON CONFLICT (key) DO UPDATE SET value = 'http://localhost:8069', write_date = NOW();

-- Nota: O nome do banco de dados agora é automaticamente definido como o account_id
-- Este campo não é mais usado diretamente, mas mantido para compatibilidade
INSERT INTO ir_config_parameter (key, value, create_date, write_date)
VALUES ('company_services.db_name', '', NOW(), NOW())
ON CONFLICT (key) DO UPDATE SET value = '', write_date = NOW();

INSERT INTO ir_config_parameter (key, value, create_date, write_date)
VALUES ('company_services.db_user', 'admin', NOW(), NOW())
ON CONFLICT (key) DO UPDATE SET value = 'admin', write_date = NOW();

INSERT INTO ir_config_parameter (key, value, create_date, write_date)
VALUES ('company_services.db_password', '', NOW(), NOW())
ON CONFLICT (key) DO UPDATE SET value = '', write_date = NOW();

INSERT INTO ir_config_parameter (key, value, create_date, write_date)
VALUES ('company_services.db_access_level', 'read', NOW(), NOW())
ON CONFLICT (key) DO UPDATE SET value = 'read', write_date = NOW();

-- Configurações de serviços disponíveis (todos desabilitados por padrão)
INSERT INTO ir_config_parameter (key, value, create_date, write_date)
VALUES ('company_services.enable_sales', 'False', NOW(), NOW())
ON CONFLICT (key) DO UPDATE SET value = 'False', write_date = NOW();

INSERT INTO ir_config_parameter (key, value, create_date, write_date)
VALUES ('company_services.enable_scheduling', 'False', NOW(), NOW())
ON CONFLICT (key) DO UPDATE SET value = 'False', write_date = NOW();

INSERT INTO ir_config_parameter (key, value, create_date, write_date)
VALUES ('company_services.enable_delivery', 'False', NOW(), NOW())
ON CONFLICT (key) DO UPDATE SET value = 'False', write_date = NOW();

INSERT INTO ir_config_parameter (key, value, create_date, write_date)
VALUES ('company_services.enable_support', 'False', NOW(), NOW())
ON CONFLICT (key) DO UPDATE SET value = 'False', write_date = NOW();

-- As descrições dos serviços foram removidas, pois agora são textos estáticos na view
EOF

        echo -e "${GREEN}Arquivo de configuração criado: mcp_config.sql${NC}"
        echo -e "${YELLOW}Execute este arquivo SQL no banco de dados do Odoo após instalar o módulo.${NC}"
    fi

    echo -e "${GREEN}Módulo company_services instalado com sucesso em $ODOO_ADDONS_DIR/company_services${NC}"
    echo -e "${YELLOW}Próximos passos:${NC}"
    echo -e "1. Reinicie o servidor Odoo"
    echo -e "2. Acesse o Odoo e atualize a lista de aplicativos"
    echo -e "3. Instale o módulo 'Empresa e Serviços'"
    echo -e "4. Execute o arquivo mcp_config.sql no banco de dados do Odoo (se criado)"
    echo -e "5. Configure as informações da empresa e serviços"
    echo -e "6. Configure o ID da Conta nas configurações (será usado como nome do banco de dados)"
    echo -e "7. Configure os serviços disponíveis nas configurações do desenvolvedor (Configurações > Empresa e Serviços)"
    echo -e "8. Configure as opções de comunicação, incluindo a nova opção de avaliação"
    echo -e "9. Verifique a aba 'Serviços de IA' para ver os serviços contratados e disponíveis"
    echo -e "10. Sincronize com o sistema de IA usando o botão verde 'Sincronizar com Sistema de IA'"
else
    echo -e "${RED}Erro ao copiar o módulo. Verifique as permissões do diretório de destino.${NC}"
    exit 1
fi

exit 0
