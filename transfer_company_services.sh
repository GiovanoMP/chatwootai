#!/bin/bash

# Cores para mensagens
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
RED="\033[0;31m"
BLUE="\033[0;34m"
RESET="\033[0m"
BOLD="\033[1m"

# Configurações
MODULE_NAME="company_services"
SOURCE_DIR="/home/giovano/Projetos/ai_stack/custom_addons/$MODULE_NAME"
TARGET_DIR="/home/giovano/Projetos/odoo16/custom-addons/$MODULE_NAME"
BACKUP_DIR="/home/giovano/Projetos/backups/modules"

# Função para exibir mensagens
function echo_status() {
    local color=$1
    local icon=$2
    local message=$3
    local color_code
    
    case $color in
        "green") color_code=$GREEN ;;
        "yellow") color_code=$YELLOW ;;
        "red") color_code=$RED ;;
        "blue") color_code=$BLUE ;;
        *) color_code="" ;;
    esac
    
    echo -e "${color_code}${icon} ${message}${RESET}"
}

# Função para verificar arquivos XML
function check_xml_files() {
    local dir=$1
    local has_errors=false
    
    # Verifica se xmllint está instalado
    if ! command -v xmllint &> /dev/null; then
        echo_status "yellow" "⚠️" "xmllint não encontrado. Pulando verificação de XML."
        return 0
    fi
    
    echo_status "blue" "🔍" "Verificando arquivos XML em $dir..."
    
    # Encontra todos os arquivos XML no diretório
    find "$dir" -name "*.xml" | while read -r xml_file; do
        echo_status "blue" "📄" "Verificando $xml_file"
        
        # Verifica a sintaxe do XML
        if ! xmllint --noout "$xml_file" 2>/tmp/xml_error; then
            echo_status "red" "❌" "Erro de XML encontrado em $xml_file:"
            cat /tmp/xml_error
            has_errors=true
        fi
    done
    
    if [ "$has_errors" = true ]; then
        echo_status "yellow" "⚠️" "Foram encontrados erros de XML. Deseja continuar mesmo assim? (s/N)"
        read -r continue_choice
        if [[ ! "$continue_choice" =~ ^[Ss]$ ]]; then
            echo_status "red" "❌" "Transferência cancelada pelo usuário."
            exit 1
        fi
    else
        echo_status "green" "✅" "Todos os arquivos XML estão válidos."
    fi
}

# Função para criar backup
function create_backup() {
    if [ -d "$TARGET_DIR" ]; then
        echo_status "blue" "💾" "Criando backup do módulo existente..."
        
        # Cria diretório de backup se não existir
        if [ ! -d "$BACKUP_DIR" ]; then
            mkdir -p "$BACKUP_DIR"
        fi
        
        # Nome do arquivo de backup
        local backup_file="$BACKUP_DIR/${MODULE_NAME}_$(date +%Y%m%d_%H%M%S).tar.gz"
        
        # Cria o backup
        tar -czf "$backup_file" -C "$(dirname "$TARGET_DIR")" "$(basename "$TARGET_DIR")"
        if [ $? -eq 0 ]; then
            echo_status "green" "✅" "Backup criado com sucesso em $backup_file"
        else
            echo_status "yellow" "⚠️" "Falha ao criar backup. Continuando sem backup..."
        fi
    fi
}

echo -e "\n${BOLD}Transferindo módulo ${MODULE_NAME}...${RESET}\n"

# Verifica se o diretório de origem existe
if [ ! -d "$SOURCE_DIR" ]; then
    # Tenta caminho alternativo
    SOURCE_DIR="/home/giovano/Projetos/ai_stack/custom-addons/$MODULE_NAME"
    if [ ! -d "$SOURCE_DIR" ]; then
        echo_status "red" "❌" "Erro: Não foi possível encontrar o diretório do módulo $MODULE_NAME."
        exit 1
    fi
fi

echo_status "green" "✅" "Diretório de origem encontrado: $SOURCE_DIR"

# Verifica arquivos XML antes da transferência
check_xml_files "$SOURCE_DIR"

# Cria backup do módulo existente
create_backup

# Remove o módulo no diretório de destino se existir
if [ -d "$TARGET_DIR" ]; then
    echo_status "yellow" "🚮" "Removendo módulo existente em $TARGET_DIR..."
    rm -rf "$TARGET_DIR"
fi

# Cria o diretório de destino se não existir
mkdir -p "/home/giovano/Projetos/odoo16/custom-addons"

# Copia o módulo para o diretório de destino
echo_status "blue" "📝" "Copiando $MODULE_NAME de $SOURCE_DIR para $TARGET_DIR..."
cp -r "$SOURCE_DIR" "$TARGET_DIR"

# Verifica se a cópia foi bem-sucedida
if [ $? -eq 0 ]; then
    echo_status "green" "🎉" "Transferência do módulo $MODULE_NAME concluída com sucesso!"
    echo_status "yellow" "ℹ️" "Não esqueça de reiniciar o servidor Odoo para aplicar as alterações."
    echo_status "blue" "🔄" "Comando: sudo systemctl restart odoo"
    
    # Lista todos os possíveis serviços Odoo para ajudar o usuário
    for service in "odoo" "odoo16" "odoo-server" "odoo-bin" "odoo15" "odoo14"; do
        if command -v systemctl &> /dev/null && systemctl list-unit-files | grep -q "$service\.service"; then
            echo -e "   ${BLUE}sudo systemctl restart $service${RESET}"
        fi
    done
else
    echo_status "red" "❌" "Erro ao copiar o módulo. Verifique as permissões e tente novamente."
    exit 1
fi

exit 0
