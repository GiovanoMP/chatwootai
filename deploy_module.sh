#!/bin/bash

# Cores para saída
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Diretório de origem (onde estamos desenvolvendo)
SRC_DIR="./addons/semantic_product_description"

# Diretório de destino (onde o Docker acessa)
DEST_DIR="/home/giovano/Projetos/odoo14/addons/custom-addons/semantic_product_description"

# Nome do container Docker (altere para o nome correto do seu container)
DOCKER_CONTAINER="odoo"

# Função para exibir mensagens
log() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Verificar se o diretório de destino existe
if [ -d "$DEST_DIR" ]; then
    warn "ATENÇÃO: O diretório de destino já existe."
    warn "Certifique-se de excluir manualmente o módulo anterior antes de continuar:"
    warn "  sudo rm -rf $DEST_DIR"

    read -p "Você já excluiu o módulo anterior? (s/n): " CONTINUE
    if [[ $CONTINUE != "s" && $CONTINUE != "S" ]]; then
        error "Operação cancelada pelo usuário."
        exit 1
    fi
fi

# Criar diretórios necessários
log "Criando estrutura de diretórios..."
mkdir -p "$DEST_DIR/models"
mkdir -p "$DEST_DIR/views"
mkdir -p "$DEST_DIR/static/description"

# Copiar todos os arquivos
log "Copiando arquivos de $SRC_DIR para $DEST_DIR..."
cp -r "$SRC_DIR/"* "$DEST_DIR/"

if [ $? -eq 0 ]; then
    log "Cópia concluída com sucesso!"
else
    error "Erro durante a cópia. Código: $?"
    exit 1
fi

# Definir permissões
log "Definindo permissões..."
chmod -R 755 "$DEST_DIR"

# Perguntar se deseja reiniciar o container Docker
read -p "Deseja reiniciar o container Docker do Odoo? (s/n): " RESTART_DOCKER

if [[ $RESTART_DOCKER == "s" || $RESTART_DOCKER == "S" ]]; then
    log "Verificando containers Docker disponíveis..."
    docker ps -a

    read -p "Digite o nome ou ID do container a ser reiniciado: " CONTAINER_NAME

    if [ ! -z "$CONTAINER_NAME" ]; then
        log "Reiniciando container $CONTAINER_NAME..."
        docker restart "$CONTAINER_NAME"

        if [ $? -eq 0 ]; then
            log "Container reiniciado com sucesso!"
        else
            error "Erro ao reiniciar o container."
        fi
    else
        warn "Nenhum container especificado. Pulando reinicialização."
    fi
fi

log "Processo concluído!"
log "Agora você pode:"
log "1. Atualizar a lista de módulos no Odoo: Aplicativos > Atualizar Lista de Aplicativos"
log "2. Se o módulo já estiver instalado, desinstale-o primeiro"
log "3. Instale o módulo novamente: Busque por 'Descrições Inteligentes de Produtos' e instale"
log ""
log "Dica: Se encontrar erros, verifique os logs do Odoo no container Docker:"
log "docker logs <nome_do_container>"
