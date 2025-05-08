#!/bin/bash

# Definir diretórios
SRC_DIR="./config-service"
DEST_DIR="/home/giovano/Projetos/config-service"

# Verificar se o diretório de origem existe
if [ ! -d "$SRC_DIR" ]; then
    echo "Diretório de origem $SRC_DIR não encontrado!"
    exit 1
fi

# Criar diretório de destino se não existir
mkdir -p "$DEST_DIR"
mkdir -p "$DEST_DIR/app"
mkdir -p "$DEST_DIR/app/api"
mkdir -p "$DEST_DIR/app/core"
mkdir -p "$DEST_DIR/app/models"
mkdir -p "$DEST_DIR/app/schemas"
mkdir -p "$DEST_DIR/app/services"
mkdir -p "$DEST_DIR/migrations"
mkdir -p "$DEST_DIR/tests"

# Verificar se os diretórios foram criados
echo "Verificando diretórios criados:"
ls -la "$DEST_DIR"

# Copiar arquivos
echo "Copiando arquivos para $DEST_DIR..."
cp "$SRC_DIR/.env" "$DEST_DIR/"
cp "$SRC_DIR/.env.example" "$DEST_DIR/"
cp "$SRC_DIR/docker-compose.yml" "$DEST_DIR/"
cp "$SRC_DIR/docker-compose.prod.yml" "$DEST_DIR/"
cp "$SRC_DIR/Dockerfile" "$DEST_DIR/"
cp "$SRC_DIR/requirements.txt" "$DEST_DIR/"
cp "$SRC_DIR/README.md" "$DEST_DIR/"
cp "$SRC_DIR/run.py" "$DEST_DIR/"
cp "$SRC_DIR/start.sh" "$DEST_DIR/"
cp "$SRC_DIR/migrate_configs.py" "$DEST_DIR/"

# Copiar arquivos da aplicação
echo "Copiando arquivos da aplicação..."
cp "$SRC_DIR/app/__init__.py" "$DEST_DIR/app/"
cp "$SRC_DIR/app/main.py" "$DEST_DIR/app/"

# Copiar API
cp "$SRC_DIR/app/api/__init__.py" "$DEST_DIR/app/api/"
cp "$SRC_DIR/app/api/mapping.py" "$DEST_DIR/app/api/"
cp "$SRC_DIR/app/api/config.py" "$DEST_DIR/app/api/"

# Copiar Core
cp "$SRC_DIR/app/core/__init__.py" "$DEST_DIR/app/core/"
cp "$SRC_DIR/app/core/config.py" "$DEST_DIR/app/core/"
cp "$SRC_DIR/app/core/database.py" "$DEST_DIR/app/core/"
cp "$SRC_DIR/app/core/security.py" "$DEST_DIR/app/core/"

# Copiar Models
cp "$SRC_DIR/app/models/__init__.py" "$DEST_DIR/app/models/"
cp "$SRC_DIR/app/models/mapping.py" "$DEST_DIR/app/models/"
cp "$SRC_DIR/app/models/config.py" "$DEST_DIR/app/models/"

# Copiar Schemas
cp "$SRC_DIR/app/schemas/__init__.py" "$DEST_DIR/app/schemas/"
cp "$SRC_DIR/app/schemas/mapping.py" "$DEST_DIR/app/schemas/"
cp "$SRC_DIR/app/schemas/config.py" "$DEST_DIR/app/schemas/"

# Copiar Services
cp "$SRC_DIR/app/services/__init__.py" "$DEST_DIR/app/services/"
cp "$SRC_DIR/app/services/mapping_service.py" "$DEST_DIR/app/services/"
cp "$SRC_DIR/app/services/config_service.py" "$DEST_DIR/app/services/"

# Tornar scripts executáveis
chmod +x "$DEST_DIR/start.sh"
chmod +x "$DEST_DIR/run.py"
chmod +x "$DEST_DIR/migrate_configs.py"

# Verificar se os arquivos foram copiados
echo "Verificando arquivos copiados:"
ls -la "$DEST_DIR/"
ls -la "$DEST_DIR/app/"

echo "Instalação concluída!"
echo "O microserviço de configuração foi instalado em $DEST_DIR"
echo ""
echo "Para iniciar o microserviço, execute:"
echo "cd $DEST_DIR && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt && python run.py"
echo ""
echo "Para migrar configurações existentes, execute:"
echo "cd $DEST_DIR && source venv/bin/activate && python migrate_configs.py"
echo ""
echo "IMPORTANTE: Certifique-se de configurar o banco de dados PostgreSQL na porta 5433"
echo "Você pode usar o Docker Compose para iniciar o banco de dados:"
echo "cd $DEST_DIR && docker-compose up -d db"
echo ""
echo "Para configurar o microserviço no módulo Odoo, acesse:"
echo "Configurações > Técnico > Parâmetros > Parâmetros do Sistema"
echo "E configure os seguintes parâmetros:"
echo "- config_service_enabled: True"
echo "- config_service_url: http://localhost:8002"
echo "- config_service_api_key: development-api-key"
