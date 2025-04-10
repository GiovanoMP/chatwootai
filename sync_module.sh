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
if [ ! -d "$DEST_DIR" ]; then
    error "Diretório de destino não existe: $DEST_DIR"
    log "Criando diretório..."
    mkdir -p "$DEST_DIR/models"
    mkdir -p "$DEST_DIR/views"
    mkdir -p "$DEST_DIR/static/description"
fi

# Sincronizar arquivos
log "Sincronizando arquivos de $SRC_DIR para $DEST_DIR..."

# Usar rsync para sincronizar apenas arquivos modificados
if command -v rsync &> /dev/null; then
    rsync -av --progress "$SRC_DIR/" "$DEST_DIR/"
    SYNC_STATUS=$?
else
    # Fallback para cp se rsync não estiver disponível
    cp -rv "$SRC_DIR/"* "$DEST_DIR/"
    SYNC_STATUS=$?
fi

if [ $SYNC_STATUS -eq 0 ]; then
    log "Sincronização concluída com sucesso!"
else
    error "Erro durante a sincronização. Código: $SYNC_STATUS"
    exit 1
fi

# Definir permissões
log "Definindo permissões..."
chmod -R 755 "$DEST_DIR"

# Perguntar se deseja reiniciar o container Docker
read -p "Deseja reiniciar o container Docker do Odoo? (s/n): " RESTART_DOCKER

if [[ $RESTART_DOCKER == "s" || $RESTART_DOCKER == "S" ]]; then
    log "Verificando se o container $DOCKER_CONTAINER existe..."
    
    if docker ps -a | grep -q "$DOCKER_CONTAINER"; then
        log "Reiniciando container $DOCKER_CONTAINER..."
        docker restart "$DOCKER_CONTAINER"
        
        if [ $? -eq 0 ]; then
            log "Container reiniciado com sucesso!"
        else
            error "Erro ao reiniciar o container."
        fi
    else
        warn "Container $DOCKER_CONTAINER não encontrado."
        log "Listando containers disponíveis:"
        docker ps -a
        
        read -p "Digite o nome ou ID do container a ser reiniciado (deixe em branco para pular): " CONTAINER_NAME
        
        if [ ! -z "$CONTAINER_NAME" ]; then
            log "Reiniciando container $CONTAINER_NAME..."
            docker restart "$CONTAINER_NAME"
            
            if [ $? -eq 0 ]; then
                log "Container reiniciado com sucesso!"
            else
                error "Erro ao reiniciar o container."
            fi
        fi
    fi
fi

log "Processo concluído!"
log "Agora você pode atualizar a lista de módulos no Odoo e reinstalar o módulo 'Descrições Semânticas de Produtos'"
log "Dica: Se o módulo já estiver instalado, você pode atualizá-lo em Aplicativos > Atualizar Lista de Aplicativos > Buscar pelo módulo > Atualizar"
