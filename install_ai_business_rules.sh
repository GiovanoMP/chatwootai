#!/bin/bash
# Script para instalar o módulo ai_business_rules no Odoo

# Cores para saída
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Diretório de addons do Odoo
ODOO_ADDONS_DIR="/home/giovano/Projetos/odoo14/addons/custom-addons"

echo -e "${BLUE}=== Instalação do Módulo Regras de Negócio IA ===${NC}"

# Verificar se o diretório de addons do Odoo existe
if [ ! -d "$ODOO_ADDONS_DIR" ]; then
    echo -e "${RED}Diretório de addons do Odoo não encontrado: $ODOO_ADDONS_DIR${NC}"
    echo -e "${YELLOW}Por favor, verifique o caminho e tente novamente.${NC}"
    exit 1
fi

# Verificar se o módulo já existe
if [ -d "$ODOO_ADDONS_DIR/ai_business_rules" ]; then
    echo -e "${YELLOW}O módulo ai_business_rules já existe no diretório de addons do Odoo.${NC}"
    echo -e "${YELLOW}Deseja substituí-lo? (s/n)${NC}"
    read -r resposta
    if [[ "$resposta" != "s" && "$resposta" != "S" ]]; then
        echo -e "${YELLOW}Instalação cancelada pelo usuário.${NC}"
        exit 0
    fi
    echo -e "${YELLOW}Removendo módulo existente...${NC}"
    rm -rf "$ODOO_ADDONS_DIR/ai_business_rules"
fi

# Verificar se o diretório do módulo existe
if [ ! -d "@addons/ai_business_rules" ]; then
    echo -e "${RED}Diretório do módulo não encontrado: @addons/ai_business_rules${NC}"
    echo -e "${YELLOW}Por favor, verifique o caminho e tente novamente.${NC}"
    exit 1
fi

# Copiar o módulo para o diretório de addons do Odoo
echo -e "${YELLOW}Copiando módulo para o diretório de addons do Odoo...${NC}"
cp -r "@addons/ai_business_rules" "$ODOO_ADDONS_DIR/"

# Verificar se a cópia foi bem-sucedida
if [ $? -ne 0 ]; then
    echo -e "${RED}Falha ao copiar o módulo.${NC}"
    exit 1
fi

# Definir permissões corretas
echo -e "${YELLOW}Definindo permissões...${NC}"
chown -R root:root "$ODOO_ADDONS_DIR/ai_business_rules"
chmod -R 755 "$ODOO_ADDONS_DIR/ai_business_rules"

# Verificar se o ícone existe
if [ ! -f "$ODOO_ADDONS_DIR/ai_business_rules/static/description/icon.png" ]; then
    echo -e "${YELLOW}Ícone não encontrado. Criando diretório para o ícone...${NC}"
    mkdir -p "$ODOO_ADDONS_DIR/ai_business_rules/static/description"

    # Verificar se o ImageMagick está instalado
    if command -v convert &> /dev/null; then
        echo -e "${YELLOW}Criando ícone simples...${NC}"
        convert -size 128x128 xc:white \
            -fill "#3498db" -draw "circle 64,64 64,32" \
            -pointsize 40 -fill white -gravity center -annotate 0 "AI" \
            "$ODOO_ADDONS_DIR/ai_business_rules/static/description/icon.png"

        if [ $? -ne 0 ]; then
            echo -e "${YELLOW}Falha ao criar o ícone. O módulo funcionará sem um ícone personalizado.${NC}"
        else
            echo -e "${GREEN}Ícone criado com sucesso.${NC}"
        fi
    else
        echo -e "${YELLOW}ImageMagick não encontrado. O módulo funcionará sem um ícone personalizado.${NC}"
    fi
fi

echo -e "${GREEN}Módulo instalado com sucesso!${NC}"

echo -e "${BLUE}=== Próximos Passos ===${NC}"
echo -e "${YELLOW}1. Reinicie o servidor Odoo${NC}"
echo -e "${YELLOW}2. Acesse o Odoo e atualize a lista de aplicativos${NC}"
echo -e "${YELLOW}3. Instale o módulo 'Regras de Negócio IA'${NC}"
echo -e "${YELLOW}4. Configure as regras de negócio${NC}"
echo -e "${YELLOW}5. Configure o ID da Conta nas configurações (será usado como identificador no Qdrant)${NC}"
echo -e "${YELLOW}6. Sincronize com o sistema de IA usando o botão verde 'Sincronizar com Sistema de IA'${NC}"

exit 0
