#!/bin/bash

# Cores para mensagens
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
RED="\033[0;31m"
BLUE="\033[0;34m"
RESET="\033[0m"
BOLD="\033[1m"

# Configurações padrão
MODULE_NAME="company_services"
SOURCE_DIR="/home/giovano/Projetos/ai_stack/custom_addons/$MODULE_NAME"
TARGET_DIR="/home/giovano/Projetos/odoo16/custom-addons/$MODULE_NAME"
BACKUP_DIR="/home/giovano/Projetos/backups/modules"
AUTO_RESTART=false
SKIP_XML_CHECK=false
SKIP_BACKUP=false

# Função para exibir ajuda
function show_help() {
    echo -e "${BOLD}Uso:${RESET} $0 [opções]"
    echo
    echo -e "${BOLD}Opções:${RESET}"
    echo -e "  -m, --module NOME      Nome do módulo a ser transferido (padrão: $MODULE_NAME)"
    echo -e "  -s, --source DIR       Diretório de origem (padrão: $SOURCE_DIR)"
    echo -e "  -t, --target DIR       Diretório de destino (padrão: $TARGET_DIR)"
    echo -e "  -b, --backup DIR       Diretório de backup (padrão: $BACKUP_DIR)"
    echo -e "  -r, --restart          Reiniciar o servidor Odoo automaticamente após a transferência"
    echo -e "  --skip-xml-check       Pular verificação de arquivos XML"
    echo -e "  --skip-backup          Pular criação de backup"
    echo -e "  -h, --help             Exibir esta ajuda"
    echo
    exit 0
}

# Processar argumentos de linha de comando
while [[ $# -gt 0 ]]; do
    case $1 in
        -m|--module)
            MODULE_NAME="$2"
            SOURCE_DIR="/home/giovano/Projetos/ai_stack/custom_addons/$MODULE_NAME"
            TARGET_DIR="/home/giovano/Projetos/odoo16/custom-addons/$MODULE_NAME"
            shift 2
            ;;
        -s|--source)
            SOURCE_DIR="$2"
            shift 2
            ;;
        -t|--target)
            TARGET_DIR="$2"
            shift 2
            ;;
        -b|--backup)
            BACKUP_DIR="$2"
            shift 2
            ;;
        -r|--restart)
            AUTO_RESTART=true
            shift
            ;;
        --skip-xml-check)
            SKIP_XML_CHECK=true
            shift
            ;;
        --skip-backup)
            SKIP_BACKUP=true
            shift
            ;;
        -h|--help)
            show_help
            ;;
        *)
            echo -e "${RED}Opção desconhecida: $1${RESET}"
            echo "Use '$0 --help' para ver as opções disponíveis."
            exit 1
            ;;
    esac
done

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
        echo_status "blue" "📝" "Verificando $xml_file"
        
        # Verifica a sintaxe do XML
        if ! xmllint --noout "$xml_file" 2>/tmp/xml_error; then
            echo_status "red" "❌" "Erro de XML encontrado em $xml_file:"
            cat /tmp/xml_error
            has_errors=true
        fi
        
        # Verifica problemas comuns em arquivos XML do Odoo
        echo_status "blue" "🔎" "Verificando problemas comuns do Odoo em $xml_file..."
        
        # Verifica labels sem atributo for e sem a classe o_form_label
        if grep -q "<label " "$xml_file"; then
            # Conta labels problemáticos (sem for e sem o_form_label)
            invalid_labels=$(grep -n "<label " "$xml_file" | grep -v "for=" | grep -v "o_form_label")
            if [ -n "$invalid_labels" ]; then
                echo_status "yellow" "⚠️" "Possíveis elementos <label> problemáticos encontrados em $xml_file:"
                echo "$invalid_labels"
                echo_status "yellow" "💡" "Dica: Todo elemento <label> deve ter um atributo 'for' ou usar a classe 'o_form_label' exclusivamente."
                has_errors=true
            fi
            
            # Verifica labels com o_form_label combinada com outras classes
            mixed_labels=$(grep -n "<label " "$xml_file" | grep "o_form_label" | grep -E "class=\"[^\"]*o_form_label[^\"]*\s[^\"]*\"")
            if [ -n "$mixed_labels" ]; then
                echo_status "yellow" "⚠️" "Elementos <label> com classe o_form_label combinada com outras classes em $xml_file:"
                echo "$mixed_labels"
                echo_status "yellow" "💡" "Dica: A classe 'o_form_label' deve ser usada exclusivamente, sem outras classes."
                has_errors=true
            fi
        fi
    done
    
    if [ "$has_errors" = true ]; then
        echo_status "yellow" "⚠️" "Foram encontrados erros ou avisos nos arquivos XML. Deseja continuar mesmo assim? (s/N)"
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

# Verificação de permissões no diretório de destino
TARGET_PARENT_DIR="$(dirname "$TARGET_DIR")"
if [ ! -w "$TARGET_PARENT_DIR" ] && [ -d "$TARGET_PARENT_DIR" ]; then
    echo_status "red" "⚠️" "Sem permissão de escrita no diretório de destino: $TARGET_PARENT_DIR"
    echo_status "yellow" "🔐" "Você pode precisar executar o script com sudo ou ajustar as permissões."
    exit 1
fi

# Verifica arquivos XML antes da transferência (se não estiver desativado)
if [ "$SKIP_XML_CHECK" = false ]; then
    check_xml_files "$SOURCE_DIR"
else
    echo_status "blue" "⏭️" "Verificação de XML ignorada conforme solicitado."
fi

# Cria backup do módulo existente (se não estiver desativado)
if [ "$SKIP_BACKUP" = false ]; then
    create_backup
else
    echo_status "blue" "⏭️" "Criação de backup ignorada conforme solicitado."
fi

# Remove o módulo no diretório de destino se existir
if [ -d "$TARGET_DIR" ]; then
    echo_status "yellow" "🚩" "Removendo módulo existente em $TARGET_DIR..."
    rm -rf "$TARGET_DIR"
    if [ $? -ne 0 ]; then
        echo_status "red" "❌" "Erro ao remover o módulo existente. Verifique as permissões."
        exit 1
    fi
fi

# Cria o diretório de destino se não existir
if [ ! -d "$(dirname "$TARGET_DIR")" ]; then
    echo_status "blue" "💾" "Criando diretório de destino $(dirname "$TARGET_DIR")..."
    mkdir -p "$(dirname "$TARGET_DIR")"
    if [ $? -ne 0 ]; then
        echo_status "red" "❌" "Erro ao criar o diretório de destino. Verifique as permissões."
        exit 1
    fi
fi

# Copia o módulo para o diretório de destino
echo_status "blue" "📝" "Copiando $MODULE_NAME de $SOURCE_DIR para $TARGET_DIR..."
cp -r "$SOURCE_DIR" "$TARGET_DIR"

# Verifica se a cópia foi bem-sucedida
if [ $? -eq 0 ]; then
    echo_status "green" "🎉" "Transferência do módulo $MODULE_NAME concluída com sucesso!"
    
    # Configura permissões para garantir que o Odoo possa acessar os arquivos
    echo_status "blue" "🔒" "Ajustando permissões do módulo..."
    chmod -R 755 "$TARGET_DIR"
    
    # Detecta o serviço Odoo disponível
    ODOO_SERVICE=""
    for service in "odoo" "odoo16" "odoo-server" "odoo-bin" "odoo15" "odoo14"; do
        if command -v systemctl &> /dev/null && systemctl list-unit-files | grep -q "$service\.service"; then
            ODOO_SERVICE="$service"
            break
        fi
    done
    
    # Reinicia o servidor Odoo automaticamente se solicitado
    if [ "$AUTO_RESTART" = true ] && [ -n "$ODOO_SERVICE" ]; then
        echo_status "blue" "🔄" "Reiniciando o servidor Odoo ($ODOO_SERVICE)..."
        if sudo systemctl restart "$ODOO_SERVICE"; then
            echo_status "green" "✅" "Servidor Odoo reiniciado com sucesso!"
        else
            echo_status "red" "❌" "Erro ao reiniciar o servidor Odoo. Tente manualmente:"
            echo -e "   ${BLUE}sudo systemctl restart $ODOO_SERVICE${RESET}"
        fi
    else
        echo_status "yellow" "ℹ️" "Não esqueça de reiniciar o servidor Odoo para aplicar as alterações."
        
        if [ -n "$ODOO_SERVICE" ]; then
            echo_status "blue" "🔄" "Comando: sudo systemctl restart $ODOO_SERVICE"
        else
            echo_status "blue" "🔄" "Comando: sudo systemctl restart odoo"
            
            # Lista todos os possíveis serviços Odoo para ajudar o usuário
            for service in "odoo" "odoo16" "odoo-server" "odoo-bin" "odoo15" "odoo14"; do
                if command -v systemctl &> /dev/null && systemctl list-unit-files | grep -q "$service\.service"; then
                    echo -e "   ${BLUE}sudo systemctl restart $service${RESET}"
                fi
            done
        fi
    fi
else
    echo_status "red" "❌" "Erro ao copiar o módulo. Verifique as permissões e tente novamente."
    exit 1
fi

exit 0
