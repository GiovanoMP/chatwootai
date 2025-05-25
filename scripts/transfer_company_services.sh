#!/bin/bash

# Script para transferir módulos do ambiente de desenvolvimento para produção
# Seguindo os princípios de design Stripe e Linear: simplicidade, feedback claro e experiência do usuário

# Nome do script para exibição
SCRIPT_NAME="$(basename "$0")"

# Detecta o diretório base do projeto
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Configurações padrão
DEFAULT_MODULE="company_services"
TARGET_PARENT_DIR="/home/giovano/Projetos/odoo16/custom-addons"
BACKUP_DIR="/home/giovano/Projetos/backups/modules"
LOG_DIR="$PROJECT_ROOT/logs"

# Inicializa variáveis
MODULE_NAME=""
SOURCE_DIR=""
TARGET_DIR=""
BACKUP_FILE=""
LOG_FILE=""
AUTO_RESTART=false
FORCE_TRANSFER=false
SKIP_BACKUP=false
CUSTOM_SOURCE=""
CUSTOM_TARGET=""

# Cores para mensagens
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
RED="\033[0;31m"
BLUE="\033[0;34m"
MAGENTA="\033[0;35m"
CYAN="\033[0;36m"
RESET="\033[0m"
BOLD="\033[1m"

# Função para exibir mensagens com cores e registrar no log
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
        "magenta") color_code=$MAGENTA ;;
        "cyan") color_code=$CYAN ;;
        *) color_code="" ;;
    esac
    
    echo -e "${color_code}${icon} ${message}${RESET}"
    echo "[$(date +"%Y-%m-%d %H:%M:%S")] ${icon} ${message}" >> "$LOG_FILE"
}

# Função para exibir cabeçalho
function show_header() {
    echo -e "\n${BOLD}${BLUE}=====================================================${RESET}"
    echo -e "${BOLD}${BLUE}       Transferência de Módulo - ${MODULE_NAME}${RESET}"
    echo -e "${BOLD}${BLUE}=====================================================${RESET}\n"
}

# Função para verificar permissões
function check_permissions() {
    # Verifica se o diretório de destino existe
    if [ ! -d "$TARGET_PARENT_DIR" ]; then
        echo_status "yellow" "📁" "Diretório de destino não existe: $TARGET_PARENT_DIR"
        echo_status "blue" "🔧" "Tentando criar o diretório..."
        mkdir -p "$TARGET_PARENT_DIR"
        if [ $? -ne 0 ]; then
            echo_status "red" "❌" "Erro: Não foi possível criar o diretório de destino!"
            echo_status "yellow" "⚠️" "Tente executar o script com sudo ou verifique as permissões."
            return 1
        fi
        echo_status "green" "✅" "Diretório de destino criado com sucesso."
    fi
    
    # Verifica permissões de escrita
    if [ ! -w "$TARGET_PARENT_DIR" ]; then
        echo_status "red" "⛔" "Sem permissão de escrita no diretório de destino: $TARGET_PARENT_DIR"
        echo_status "yellow" "🔧" "Tente executar o script com sudo."
        return 1
    fi
    
    echo_status "green" "✅" "Permissões verificadas com sucesso."
    return 0
}

# Função para criar backup
function create_backup() {
    # Verifica se deve pular o backup
    for arg in "$@"; do
        if [ "$arg" == "--skip-backup" ]; then
            echo_status "yellow" "⚠️" "Backup ignorado conforme solicitado."
            return 0
        fi
    done
    
    if [ -d "$TARGET_DIR" ]; then
        echo_status "blue" "💾" "Criando backup do módulo existente..."
        
        # Cria diretório de backup se não existir
        if [ ! -d "$BACKUP_DIR" ]; then
            mkdir -p "$BACKUP_DIR"
            if [ $? -ne 0 ]; then
                echo_status "yellow" "⚠️" "Não foi possível criar o diretório de backup. Continuando sem backup..."
                return 1
            fi
        fi
        
        # Verifica espaço em disco antes de criar o backup
        local available_space=$(df -k "$BACKUP_DIR" | awk 'NR==2 {print $4}')
        local module_size=$(du -sk "$TARGET_DIR" | awk '{print $1}')
        
        if [ "$available_space" -lt "$((module_size * 2))" ]; then
            echo_status "yellow" "⚠️" "Pouco espaço em disco disponível para backup ($available_space KB). O módulo ocupa $module_size KB."
            echo_status "yellow" "⚠️" "Recomendado pelo menos o dobro do tamanho do módulo para backup seguro."
            
            # Pergunta se deseja continuar sem backup se não estiver em modo automático
            if [ "$AUTO_RESTART" != true ]; then
                echo -e "\n${YELLOW}⚠️  Continuar sem backup? (s/N)${RESET} "
                read -r skip_backup_choice
                if [[ ! "$skip_backup_choice" =~ ^[Ss]$ ]]; then
                    echo_status "red" "❌" "Operação cancelada pelo usuário."
                    exit 1
                fi
            else
                echo_status "yellow" "⚠️" "Continuando sem backup devido ao modo automático."
            fi
            return 1
        fi
        
        # Cria o backup
        tar -czf "$BACKUP_FILE" -C "$(dirname "$TARGET_DIR")" "$(basename "$TARGET_DIR")"
        if [ $? -ne 0 ]; then
            echo_status "yellow" "⚠️" "Falha ao criar backup. Continuando sem backup..."
            return 1
        else
            echo_status "green" "✅" "Backup criado com sucesso em $BACKUP_FILE"
            return 0
        fi
    else
        echo_status "blue" "💾" "Módulo não existe no destino. Nenhum backup necessário."
        return 0
    fi
}

# Função para verificar integridade
function verify_integrity() {
    echo_status "blue" "🔍" "Verificando integridade da transferência..."
    local force_transfer=false
    
    # Verifica se a flag de forçar transferência está ativa
    for arg in "$@"; do
        if [ "$arg" == "--force" ] || [ "$arg" == "-f" ]; then
            force_transfer=true
            echo_status "yellow" "⚠️" "Modo forçado ativado: a verificação de integridade será ignorada em caso de falha."
        fi
    done
    
    # Verifica se o diretório de destino existe
    if [ ! -d "$TARGET_DIR" ]; then
        echo_status "red" "❌" "Falha na verificação: Diretório de destino não existe!"
        if [ "$force_transfer" = true ]; then
            echo_status "yellow" "⚠️" "Ignorando falha devido ao modo forçado."
            return 0
        fi
        return 1
    fi
    
    # Verifica se os arquivos essenciais foram copiados
    local essential_files_missing=false
    for file in "__init__.py" "__manifest__.py" "models"; do
        if [ ! -e "$TARGET_DIR/$file" ] && [ -e "$SOURCE_DIR/$file" ]; then
            echo_status "red" "❌" "Falha na verificação: Arquivo/diretório essencial '$file' não foi copiado!"
            essential_files_missing=true
        fi
    done
    
    if [ "$essential_files_missing" = true ] && [ "$force_transfer" != true ]; then
        return 1
    elif [ "$essential_files_missing" = true ]; then
        echo_status "yellow" "⚠️" "Arquivos essenciais ausentes, mas continuando devido ao modo forçado."
    fi
    
    # Conta o número de arquivos em ambos os diretórios
    local source_count=$(find "$SOURCE_DIR" -type f | wc -l)
    local target_count=$(find "$TARGET_DIR" -type f | wc -l)
    
    echo_status "blue" "📈" "Arquivos na origem: $source_count, Arquivos no destino: $target_count"
    
    if [ "$source_count" -ne "$target_count" ]; then
        echo_status "yellow" "⚠️" "Aviso: O número de arquivos na origem e no destino é diferente."
        
        # Verifica permissões dos arquivos no destino
        local permission_issues=false
        find "$TARGET_DIR" -type f -not -perm -u=rw 2>/dev/null | while read -r file; do
            echo_status "yellow" "⚠️" "Problema de permissão no arquivo: $file"
            permission_issues=true
        done
        
        if [ "$permission_issues" = true ]; then
            echo_status "yellow" "⚠️" "Detectados problemas de permissão que podem ter afetado a transferência."
        fi
    else
        echo_status "green" "✅" "Número de arquivos corresponde entre origem e destino."
    fi
    
    # Verificação adicional de arquivos Python
    local python_files_source=$(find "$SOURCE_DIR" -name "*.py" | wc -l)
    local python_files_target=$(find "$TARGET_DIR" -name "*.py" | wc -l)
    
    if [ "$python_files_source" -ne "$python_files_target" ]; then
        echo_status "yellow" "⚠️" "Aviso: O número de arquivos Python difere entre origem ($python_files_source) e destino ($python_files_target)."
    else
        echo_status "green" "✅" "Número de arquivos Python corresponde entre origem e destino."
    fi
    
    echo_status "green" "✅" "Verificação de integridade concluída."
    return 0
}

# Função para reiniciar o servidor Odoo
function restart_odoo() {
    echo_status "blue" "🔄" "Tentando reiniciar o servidor Odoo..."
    
    # Lista de possíveis nomes de serviço do Odoo
    local odoo_services=("odoo" "odoo16" "odoo-server" "odoo-bin" "odoo15" "odoo14")
    local service_found=false
    local service_name=""
    
    # Verifica se systemctl está disponível
    if ! command -v systemctl &> /dev/null; then
        echo_status "yellow" "⚠️" "systemctl não encontrado. Não é possível reiniciar o serviço automaticamente."
        return 1
    fi
    
    # Tenta encontrar o serviço Odoo ativo
    for service in "${odoo_services[@]}"; do
        if systemctl is-active --quiet "$service"; then
            service_found=true
            service_name="$service"
            break
        fi
    done
    
    # Se encontrou um serviço ativo, tenta reiniciá-lo
    if [ "$service_found" = true ]; then
        echo_status "blue" "🔄" "Serviço $service_name encontrado. Tentando reiniciar..."
        sudo systemctl restart "$service_name"
        if [ $? -eq 0 ]; then
            echo_status "green" "✅" "Servidor Odoo ($service_name) reiniciado com sucesso!"
            return 0
        else
            echo_status "red" "❌" "Falha ao reiniciar o servidor Odoo ($service_name)."
            return 1
        fi
    else
        echo_status "yellow" "⚠️" "Não foi possível detectar o serviço Odoo ou ele não está em execução."
        echo_status "yellow" "ℹ️" "Serviços verificados: ${odoo_services[*]}"
        return 1
    fi
}

# Início do script
# Cria diretório de logs se não existir
if [ ! -d "$LOG_DIR" ]; then
    mkdir -p "$LOG_DIR"
fi

# Limpa o arquivo de log ou cria um novo
echo "[$(date +"%Y-%m-%d %H:%M:%S")] Iniciando script de transferência para $MODULE_NAME" > "$LOG_FILE"

show_header

echo_status "magenta" "🔄" "Iniciando transferência do módulo $MODULE_NAME..."

# Verifica se o diretório de origem existe
if [ ! -d "$SOURCE_DIR" ]; then
    echo_status "red" "❌" "Erro: Diretório de origem $SOURCE_DIR não encontrado!"
    echo_status "yellow" "ℹ️" "Verificando caminhos alternativos..."
    
    # Tenta encontrar o módulo em caminhos alternativos
    ALT_SOURCE_DIR="$PROJECT_ROOT/custom-addons/$MODULE_NAME"
    if [ -d "$ALT_SOURCE_DIR" ]; then
        echo_status "green" "✅" "Módulo encontrado em caminho alternativo: $ALT_SOURCE_DIR"
        SOURCE_DIR="$ALT_SOURCE_DIR"
    else
        echo_status "red" "❌" "Não foi possível encontrar o módulo $MODULE_NAME."
        echo_status "yellow" "ℹ️" "Verifique se o módulo existe e se o caminho está correto."
        exit 1
    fi
fi

echo_status "green" "✅" "Diretório de origem verificado: $SOURCE_DIR"

# Verifica permissões
check_permissions
permission_check=$?

# Cria backup do módulo existente
create_backup "$@"

# Cria o diretório de destino se não existir
if [ ! -d "$TARGET_PARENT_DIR" ]; then
    echo_status "yellow" "📁" "Criando diretório de destino $TARGET_PARENT_DIR..."
    mkdir -p "$TARGET_PARENT_DIR"
    if [ $? -ne 0 ]; then
        echo_status "red" "❌" "Erro: Não foi possível criar o diretório de destino!"
        exit 1
    fi
fi

# Remove o módulo no diretório de destino se existir
if [ -d "$TARGET_DIR" ]; then
    echo_status "yellow" "🚮" "Removendo módulo existente em $TARGET_DIR..."
    rm -rf "$TARGET_DIR"
    if [ $? -ne 0 ]; then
        echo_status "red" "❌" "Erro: Não foi possível remover o módulo existente!"
        exit 1
    fi
fi

# Copia o módulo para o diretório de destino
echo_status "cyan" "📋" "Copiando $MODULE_NAME de $SOURCE_DIR para $TARGET_DIR..."
cp -r "$SOURCE_DIR" "$TARGET_DIR"
if [ $? -ne 0 ]; then
    echo_status "red" "❌" "Erro: Falha ao copiar o módulo!"
    exit 1
fi

# Verifica a integridade da transferência
verify_integrity "$@"

# Função para exibir ajuda
function show_help() {
    echo -e "\n${BOLD}Uso: $0 [módulo] [opções]${RESET}"
    echo -e "\n${BOLD}Argumentos:${RESET}"
    echo -e "  módulo\t\tNome do módulo a ser transferido (padrão: $DEFAULT_MODULE)"
    echo -e "\n${BOLD}Opções:${RESET}"
    echo -e "  -y, --yes\t\tModo não interativo (reinicia o servidor automaticamente)"
    echo -e "  -f, --force\t\tForça a transferência mesmo se a verificação de integridade falhar"
    echo -e "  --skip-backup\t\tNão cria backup do módulo existente"
    echo -e "  -s, --source=DIR\tEspecifica o diretório de origem (ex: --source=/caminho/para/módulo)"
    echo -e "  -t, --target=DIR\tEspecifica o diretório de destino (ex: --target=/caminho/para/destino)"
    echo -e "  -h, --help\t\tMostra esta ajuda\n"
    exit 0
}

# Processa argumentos da linha de comando
AUTO_RESTART=false
FORCE_TRANSFER=false
SKIP_BACKUP=false
CUSTOM_SOURCE=""
CUSTOM_TARGET=""

# Verifica se o primeiro argumento não começa com '-' e assume que é o nome do módulo
if [ $# -gt 0 ] && [[ ! "$1" =~ ^- ]]; then
    MODULE_NAME="$1"
    shift
else
    MODULE_NAME="$DEFAULT_MODULE"
fi

# Processa os argumentos restantes
for arg in "$@"; do
    case "$arg" in
        "-y"|"--yes")
            AUTO_RESTART=true
            echo_status "blue" "ℹ️" "Modo não interativo detectado. Reinicialização automática ativada."
            ;;
        "-f"|"--force")
            FORCE_TRANSFER=true
            echo_status "yellow" "⚠️" "Modo forçado ativado: ignorando falhas na verificação de integridade."
            ;;
        "--skip-backup")
            SKIP_BACKUP=true
            echo_status "yellow" "⚠️" "Backup será ignorado durante a transferência."
            ;;
        -s=*|--source=*)
            CUSTOM_SOURCE="${arg#*=}"
            echo_status "blue" "ℹ️" "Diretório de origem personalizado: $CUSTOM_SOURCE"
            ;;
        -t=*|--target=*)
            CUSTOM_TARGET="${arg#*=}"
            echo_status "blue" "ℹ️" "Diretório de destino personalizado: $CUSTOM_TARGET"
            ;;
        "--help"|-h)
            show_help
            ;;
    esac
done

# Configura diretórios com base nos argumentos
if [ -z "$CUSTOM_SOURCE" ]; then
    SOURCE_DIR="$PROJECT_ROOT/custom_addons/$MODULE_NAME"
    # Verifica caminhos alternativos se o padrão não existir
    if [ ! -d "$SOURCE_DIR" ]; then
        ALT_SOURCE_DIR="$PROJECT_ROOT/custom-addons/$MODULE_NAME"
        if [ -d "$ALT_SOURCE_DIR" ]; then
            SOURCE_DIR="$ALT_SOURCE_DIR"
        fi
    fi
else
    SOURCE_DIR="$CUSTOM_SOURCE"
fi

if [ -z "$CUSTOM_TARGET" ]; then
    TARGET_DIR="$TARGET_PARENT_DIR/$MODULE_NAME"
else
    TARGET_DIR="$CUSTOM_TARGET"
    TARGET_PARENT_DIR="$(dirname "$CUSTOM_TARGET")"
fi

# Configura arquivos de backup e log
BACKUP_FILE="$BACKUP_DIR/${MODULE_NAME}_$(date +%Y%m%d_%H%M%S).tar.gz"
LOG_FILE="$LOG_DIR/transfer_${MODULE_NAME}_$(date +%Y%m%d).log"

# Decide se deve reiniciar automaticamente ou perguntar ao usuário
if [ "$AUTO_RESTART" = true ]; then
    echo_status "blue" "🔄" "Reiniciando o servidor Odoo automaticamente..."
    restart_odoo
    restart_result=$?
    
    if [ $restart_result -eq 0 ]; then
        echo_status "green" "🎉" "Módulo transferido e servidor reiniciado com sucesso!"
    else
        echo_status "yellow" "⚠️" "Módulo transferido, mas o servidor não foi reiniciado automaticamente."
        echo_status "yellow" "🔧" "Você pode reiniciar manualmente com: sudo systemctl restart odoo"
        
        # Lista todos os possíveis serviços Odoo para ajudar o usuário
        echo_status "blue" "ℹ️" "Comandos de reinicialização disponíveis:"
        for service in "odoo" "odoo16" "odoo-server" "odoo-bin" "odoo15" "odoo14"; do
            if systemctl list-unit-files | grep -q "$service\.service"; then
                echo -e "   ${CYAN}sudo systemctl restart $service${RESET}"
            fi
        done
    fi
else
    # Pergunta se deseja reiniciar o servidor Odoo
    echo -e "\n${YELLOW}⚠️  Deseja reiniciar o servidor Odoo agora? (s/N)${RESET} "
    read -r restart_choice

    if [[ "$restart_choice" =~ ^[Ss]$ ]]; then
        restart_odoo
        restart_result=$?
        
        if [ $restart_result -eq 0 ]; then
            echo_status "green" "🎉" "Módulo transferido e servidor reiniciado com sucesso!"
        else
            echo_status "yellow" "⚠️" "Módulo transferido, mas o servidor não foi reiniciado automaticamente."
            echo_status "yellow" "🔧" "Você pode reiniciar manualmente com um dos seguintes comandos:"
            
            # Lista todos os possíveis serviços Odoo para ajudar o usuário
            for service in "odoo" "odoo16" "odoo-server" "odoo-bin" "odoo15" "odoo14"; do
                if systemctl list-unit-files | grep -q "$service\.service"; then
                    echo -e "   ${CYAN}sudo systemctl restart $service${RESET}"
                fi
            done
        fi
    else
        echo_status "green" "✅" "Transferência do módulo $MODULE_NAME concluída com sucesso!"
        echo_status "yellow" "⚠️" "Lembre-se de reiniciar o servidor Odoo para aplicar as alterações."
        echo_status "blue" "ℹ️" "Comandos de reinicialização disponíveis:"
        
        # Lista todos os possíveis serviços Odoo para ajudar o usuário
        for service in "odoo" "odoo16" "odoo-server" "odoo-bin" "odoo15" "odoo14"; do
            if systemctl list-unit-files | grep -q "$service\.service"; then
                echo -e "   ${CYAN}sudo systemctl restart $service${RESET}"
            fi
        done
    fi
fi

# Exibe resumo final
echo -e "\n${BOLD}${BLUE}=====================================================${RESET}"
echo -e "${BOLD}${GREEN}          RESUMO DA TRANSFERÊNCIA${RESET}"
echo -e "${BOLD}${BLUE}=====================================================${RESET}"
echo -e "${CYAN}Módulo:${RESET} $MODULE_NAME"
echo -e "${CYAN}Origem:${RESET} $SOURCE_DIR"
echo -e "${CYAN}Destino:${RESET} $TARGET_DIR"

if [ -f "$BACKUP_FILE" ]; then
    echo -e "${CYAN}Backup:${RESET} $BACKUP_FILE"
fi

echo -e "${CYAN}Log:${RESET} $LOG_FILE"
echo -e "${CYAN}Data/Hora:${RESET} $(date)"
echo -e "${BOLD}${BLUE}=====================================================${RESET}\n"

exit 0
