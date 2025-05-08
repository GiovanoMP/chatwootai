#!/bin/bash

# Definir diretórios
SRC_DIR="./addons/ai_credentials_manager"
DEST_DIR="/home/giovano/Projetos/odoo14/addons/custom-addons/ai_credentials_manager"

# Verificar se o diretório de origem existe
if [ ! -d "$SRC_DIR" ]; then
    echo "Diretório de origem $SRC_DIR não encontrado!"
    exit 1
fi

# Criar diretório de destino se não existir
mkdir -p "$DEST_DIR/models"
mkdir -p "$DEST_DIR/views"
mkdir -p "$DEST_DIR/security"
mkdir -p "$DEST_DIR/static/description"
mkdir -p "$DEST_DIR/data"

# Verificar se os diretórios foram criados
echo "Verificando diretórios criados:"
ls -la "$DEST_DIR"

# Copiar arquivos
echo "Copiando arquivos para $DEST_DIR..."
cp "$SRC_DIR/__manifest__.py" "$DEST_DIR/"
cp "$SRC_DIR/__init__.py" "$DEST_DIR/"
cp "$SRC_DIR/README.md" "$DEST_DIR/"
cp "$SRC_DIR/MANUAL_DO_USUARIO.md" "$DEST_DIR/"

# Copiar modelos
cp "$SRC_DIR/models/__init__.py" "$DEST_DIR/models/"
cp "$SRC_DIR/models/ai_credentials.py" "$DEST_DIR/models/"
cp "$SRC_DIR/models/ai_credentials_access_log.py" "$DEST_DIR/models/"
cp "$SRC_DIR/models/ai_sync_queue.py" "$DEST_DIR/models/"
cp "$SRC_DIR/models/ai_channel_mapping.py" "$DEST_DIR/models/"
cp "$SRC_DIR/models/config_service.py" "$DEST_DIR/models/"
cp "$SRC_DIR/models/res_config_settings.py" "$DEST_DIR/models/"
cp "$SRC_DIR/models/config_viewer.py" "$DEST_DIR/models/"

# Copiar vistas
cp "$SRC_DIR/views/credentials_views.xml" "$DEST_DIR/views/"
cp "$SRC_DIR/views/sync_queue_views.xml" "$DEST_DIR/views/"
cp "$SRC_DIR/views/menu_views.xml" "$DEST_DIR/views/"
cp "$SRC_DIR/views/channel_mapping_views.xml" "$DEST_DIR/views/"
cp "$SRC_DIR/views/config_service_views.xml" "$DEST_DIR/views/"
cp "$SRC_DIR/views/config_viewer_views.xml" "$DEST_DIR/views/"

# Copiar segurança
cp "$SRC_DIR/security/security.xml" "$DEST_DIR/security/"
cp "$SRC_DIR/security/ir.model.access.csv" "$DEST_DIR/security/"

# Copiar dados
cp "$SRC_DIR/data/webhook_secret.xml" "$DEST_DIR/data/"

# Verificar se os arquivos foram copiados
echo "Verificando arquivos copiados:"
ls -la "$DEST_DIR/models/"
ls -la "$DEST_DIR/views/"
ls -la "$DEST_DIR/security/"
ls -la "$DEST_DIR/data/"

# Instruções para instalar dependência cryptography
echo "\n=== IMPORTANTE: Instalação de Dependências ==="
echo "O módulo requer a biblioteca 'cryptography' para funcionar corretamente."
echo "Execute o seguinte comando no ambiente Odoo:"
echo "  pip3 install cryptography"
echo "Se estiver usando Docker, execute:"
echo "  docker exec -it seu_container_odoo pip3 install cryptography"
echo "E depois reinicie o servidor Odoo."
echo "==================================\n"

echo "Instalação concluída!"
echo "Agora você pode atualizar a lista de módulos no Odoo e instalar o módulo 'Gerenciador de Credenciais para IA'"
echo ""
echo "IMPORTANTE: Antes de usar o módulo, certifique-se de que a biblioteca 'cryptography' está instalada no ambiente Odoo."
echo "Se estiver usando Docker, você pode executar:"
echo "docker exec -it seu_container_odoo pip3 install cryptography"
echo "E depois reiniciar o container."
echo ""
echo "NOVIDADE: Este módulo agora inclui:"
echo "1. Mapeamento de canais do Chatwoot para o sistema de IA"
echo "   - Você pode configurar mapeamentos para direcionar mensagens do Chatwoot para o domínio e account_id corretos"
echo "   - Também é possível configurar números especiais de WhatsApp para a crew analytics"
echo ""
echo "2. Integração com o microsserviço config-service"
echo "   - Armazenamento centralizado de configurações no PostgreSQL"
echo "   - Envio direto de credenciais para o config-service via webhook"
echo "   - Não depende mais do webhook da stack de IA principal"
echo ""
echo "3. Visualizador de Configurações Web"
echo "   - Botão 'Visualizar Configurações' no formulário de credenciais"
echo "   - Acesso direto à interface web do visualizador de configurações"
echo "   - Busca automática por tenant_id (account_id)"
echo ""
echo "IMPORTANTE: Nova Arquitetura de Microsserviços"
echo "Este módulo agora envia dados diretamente para o microsserviço config-service,"
echo "que armazena as configurações no PostgreSQL. Isso faz parte da nova arquitetura"
echo "que separa a stack de IA dos serviços de configuração."
echo ""
echo "Para configurar o microsserviço config-service, acesse:"
echo "Configurações > Técnico > Parâmetros > Parâmetros do Sistema"
echo "E configure os seguintes parâmetros:"
echo "- config_service.url: URL do microsserviço (ex: http://localhost:8002)"
echo "- config_service.api_key: Chave de API para autenticação"
echo ""
echo "Para configurar o visualizador de configurações web, acesse:"
echo "Configurações > Técnico > Parâmetros > Parâmetros do Sistema"
echo "E configure o seguinte parâmetro:"
echo "- config_viewer.url: URL para o visualizador web (ex: http://localhost:8080)"
