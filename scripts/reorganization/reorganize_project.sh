#!/bin/bash

# Script para reorganizar a estrutura do projeto ChatwootAI
# Autor: ChatGPT
# Data: 19/03/2025

# Configurações
PROJECT_ROOT="/home/giovano/Projetos/Chatwoot V4"
BACKUP_DIR="$PROJECT_ROOT/backup_$(date +%Y%m%d_%H%M%S)"

# Cores para mensagens
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Função para log com cores
log() {
    local level=$1
    local message=$2
    
    case $level in
        "INFO")
            echo -e "${GREEN}[INFO]${NC} $message"
            ;;
        "WARN")
            echo -e "${YELLOW}[WARN]${NC} $message"
            ;;
        "ERROR")
            echo -e "${RED}[ERROR]${NC} $message"
            ;;
    esac
}

# Verifica se o diretório do projeto existe
if [ ! -d "$PROJECT_ROOT" ]; then
    log "ERROR" "Diretório do projeto não encontrado: $PROJECT_ROOT"
    exit 1
fi

# Cria o diretório de backup
log "INFO" "Criando diretório de backup em: $BACKUP_DIR"
mkdir -p "$BACKUP_DIR"

# Faz backup de arquivos críticos
log "INFO" "Fazendo backup de arquivos importantes..."
cp -r "$PROJECT_ROOT/src/api" "$BACKUP_DIR/"
cp -r "$PROJECT_ROOT/src/agents" "$BACKUP_DIR/"
cp -r "$PROJECT_ROOT/webhook" "$BACKUP_DIR/"
cp -r "$PROJECT_ROOT/webhook_server.py" "$BACKUP_DIR/" 2>/dev/null

log "INFO" "Backup concluído com sucesso!"

# Cria a nova estrutura de diretórios
log "INFO" "Criando nova estrutura de diretórios..."

# 1. Estrutura para agentes
mkdir -p "$PROJECT_ROOT/src/agents/core"
mkdir -p "$PROJECT_ROOT/src/agents/domain/cosmetics"
mkdir -p "$PROJECT_ROOT/src/agents/domain/health"
mkdir -p "$PROJECT_ROOT/src/agents/domain/retail"

# 2. Estrutura para API
mkdir -p "$PROJECT_ROOT/src/api/chatwoot"
mkdir -p "$PROJECT_ROOT/src/api/erp/simulation"

# 3. Estrutura para Webhook
mkdir -p "$PROJECT_ROOT/src/webhook"

# 4. Estrutura para Crews
mkdir -p "$PROJECT_ROOT/src/crews"

log "INFO" "Nova estrutura de diretórios criada com sucesso!"

# Movendo e reorganizando arquivos
log "INFO" "Movendo arquivos para novas localizações..."

# 1. Reorganizar DataProxyAgent
if [ -f "$PROJECT_ROOT/src/agents/data_proxy_agent.py" ]; then
    log "INFO" "Movendo DataProxyAgent para src/agents/core/"
    cp "$PROJECT_ROOT/src/agents/data_proxy_agent.py" "$PROJECT_ROOT/src/agents/core/"
else
    log "WARN" "DataProxyAgent não encontrado"
fi

# 2. Reorganizar Clientes Chatwoot
if [ -f "$PROJECT_ROOT/src/api/chatwoot_client.py" ]; then
    log "INFO" "Movendo cliente Chatwoot principal para src/api/chatwoot/client.py"
    cp "$PROJECT_ROOT/src/api/chatwoot_client.py" "$PROJECT_ROOT/src/api/chatwoot/client.py"
fi

if [ -f "$PROJECT_ROOT/src/api/chatwoot.py" ]; then
    log "INFO" "Movendo chatwoot.py para src/api/chatwoot/legacy_client.py"
    cp "$PROJECT_ROOT/src/api/chatwoot.py" "$PROJECT_ROOT/src/api/chatwoot/legacy_client.py"
fi

# 3. Reorganizar Simulação do Odoo
if [ -f "$PROJECT_ROOT/src/api/odoo_simulation.py" ]; then
    log "INFO" "Movendo simulação do Odoo para src/api/erp/simulation/odoo.py"
    cp "$PROJECT_ROOT/src/api/odoo_simulation.py" "$PROJECT_ROOT/src/api/erp/simulation/odoo.py"
fi

# 4. Reorganizar Webhook Server
if [ -f "$PROJECT_ROOT/src/api/webhook_server.py" ]; then
    log "INFO" "Movendo webhook_server.py para src/webhook/server.py"
    cp "$PROJECT_ROOT/src/api/webhook_server.py" "$PROJECT_ROOT/src/webhook/server.py"
fi

if [ -f "$PROJECT_ROOT/webhook_server.py" ]; then
    log "INFO" "Movendo webhook_server.py (raiz) para src/webhook/root_server.py"
    cp "$PROJECT_ROOT/webhook_server.py" "$PROJECT_ROOT/src/webhook/root_server.py"
fi

# 5. Copiar handler de webhook
if [ -f "$PROJECT_ROOT/src/webhook/webhook_handler.py" ]; then
    log "INFO" "Copiando webhook_handler.py para src/webhook/handler.py"
    cp "$PROJECT_ROOT/src/webhook/webhook_handler.py" "$PROJECT_ROOT/src/webhook/handler.py"
fi

log "INFO" "Arquivos movidos com sucesso!"

# Criação de arquivos __init__.py para garantir imports corretos
log "INFO" "Criando arquivos __init__.py para garantir importações corretas..."

# Cria arquivo __init__.py para src/agents/core
cat > "$PROJECT_ROOT/src/agents/core/__init__.py" << EOF
"""
Agentes core do sistema.

Este pacote contém os agentes fundamentais do sistema, incluindo o DataProxyAgent,
que é o intermediário obrigatório para acesso a dados.
"""

from .data_proxy_agent import DataProxyAgent

__all__ = ["DataProxyAgent"]
EOF

# Cria arquivo __init__.py para src/api/chatwoot
cat > "$PROJECT_ROOT/src/api/chatwoot/__init__.py" << EOF
"""
Clientes para API do Chatwoot.

Este pacote contém os clientes para interagir com a API do Chatwoot,
permitindo enviar mensagens e gerenciar conversas.
"""

from .client import ChatwootClient
from .client import ChatwootWebhookHandler

__all__ = ["ChatwootClient", "ChatwootWebhookHandler"]
EOF

# Cria arquivo __init__.py para src/api/erp/simulation
cat > "$PROJECT_ROOT/src/api/erp/simulation/__init__.py" << EOF
"""
Simulação do sistema ERP.

Este pacote contém a simulação do sistema ERP (Odoo) para desenvolvimento e testes.
"""

# Imports serão atualizados conforme a implementação final
EOF

# Cria arquivo __init__.py para src/webhook
cat > "$PROJECT_ROOT/src/webhook/__init__.py" << EOF
"""
Serviços de webhook.

Este pacote contém o servidor webhook e o handler para processar webhooks do Chatwoot.
"""

from .handler import ChatwootWebhookHandler
from .server import app, webhook, startup_event, health_check

__all__ = ["ChatwootWebhookHandler", "app", "webhook", "startup_event", "health_check"]
EOF

log "INFO" "Arquivos __init__.py criados com sucesso!"

log "INFO" "Reorganização concluída com sucesso!"
log "INFO" "Um backup dos arquivos originais foi criado em: $BACKUP_DIR"
log "WARN" "IMPORTANTE: As importações nos arquivos podem precisar ser atualizadas manualmente para refletir a nova estrutura!"
log "INFO" "Verifique os arquivos e faça as atualizações necessárias antes de fazer commit das alterações."
