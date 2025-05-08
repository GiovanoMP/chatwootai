#!/bin/bash

# Script para verificar configurações no PostgreSQL do microserviço de configuração

# Cores para saída
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Função para exibir título
print_title() {
    echo -e "\n${BLUE}=== $1 ===${NC}\n"
}

# Função para executar consulta SQL
run_query() {
    docker exec -it config-service-db psql -U postgres -d config_service -c "$1"
}

# Função para verificar uma configuração específica
check_config() {
    local tenant_id=$1
    local domain=$2
    local config_type=$3
    local field=$4

    print_title "Verificando $field em $tenant_id/$domain/$config_type"
    
    if [ -z "$field" ]; then
        # Mostrar toda a configuração
        run_query "SELECT json_data FROM crew_configurations WHERE tenant_id='$tenant_id' AND domain='$domain' AND config_type='$config_type' ORDER BY version DESC LIMIT 1;"
    else
        # Mostrar apenas o campo específico
        run_query "SELECT json_data->'$field' FROM crew_configurations WHERE tenant_id='$tenant_id' AND domain='$domain' AND config_type='$config_type' ORDER BY version DESC LIMIT 1;"
    fi
}

# Função para listar todas as configurações
list_configs() {
    print_title "Listando todas as configurações"
    run_query "SELECT tenant_id, domain, config_type, version, created_at FROM crew_configurations ORDER BY tenant_id, domain, config_type, version DESC;"
}

# Função para verificar o mapeamento Chatwoot
check_mapping() {
    print_title "Verificando mapeamento Chatwoot"
    run_query "SELECT mapping_data FROM chatwoot_mapping ORDER BY version DESC LIMIT 1;"
}

# Menu principal
show_menu() {
    echo -e "${GREEN}=== Verificador de Configurações ===${NC}"
    echo -e "1. ${YELLOW}Listar todas as configurações${NC}"
    echo -e "2. ${YELLOW}Verificar configuração específica${NC}"
    echo -e "3. ${YELLOW}Verificar enabled_collections${NC}"
    echo -e "4. ${YELLOW}Verificar mapeamento Chatwoot${NC}"
    echo -e "0. ${RED}Sair${NC}"
    echo -n "Escolha uma opção: "
    read option

    case $option in
        1)
            list_configs
            ;;
        2)
            echo -n "Tenant ID (ex: account_1): "
            read tenant_id
            echo -n "Domain (ex: retail): "
            read domain
            echo -n "Config Type (ex: config, credentials): "
            read config_type
            echo -n "Campo específico (deixe em branco para mostrar tudo): "
            read field
            check_config "$tenant_id" "$domain" "$config_type" "$field"
            ;;
        3)
            echo -n "Tenant ID (ex: account_1): "
            read tenant_id
            echo -n "Domain (ex: retail): "
            read domain
            check_config "$tenant_id" "$domain" "config" "enabled_collections"
            ;;
        4)
            check_mapping
            ;;
        0)
            echo -e "${GREEN}Até logo!${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}Opção inválida!${NC}"
            ;;
    esac

    # Voltar ao menu
    echo -e "\nPressione ENTER para continuar..."
    read
    clear
    show_menu
}

# Verificar se o container do PostgreSQL está rodando
if ! docker ps | grep -q config-service-db; then
    echo -e "${RED}Erro: Container config-service-db não está rodando!${NC}"
    exit 1
fi

# Iniciar o menu
clear
show_menu
