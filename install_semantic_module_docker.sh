#!/bin/bash

# Script para instalar o módulo semantic_product_description em ambiente Docker

echo "=== Instalando semantic_product_description em ambiente Docker ==="

# Identificar o contêiner do Odoo
ODOO_CONTAINER=$(docker ps | grep odoo | awk '{print $1}')

if [ -z "$ODOO_CONTAINER" ]; then
    echo "Erro: Não foi possível encontrar o contêiner do Odoo."
    echo "Verifique se o Odoo está em execução com 'docker ps'."
    exit 1
fi

echo "Contêiner do Odoo encontrado: $ODOO_CONTAINER"

# Diretório de origem (onde estamos criando os arquivos)
SRC_DIR="./addons/semantic_product_description"

# Diretório temporário para preparar os arquivos
TMP_DIR="/tmp/semantic_product_description"
mkdir -p "$TMP_DIR/models"
mkdir -p "$TMP_DIR/views"
mkdir -p "$TMP_DIR/static/description"

# Copiar arquivos para o diretório temporário
echo "Preparando arquivos..."
cp "$SRC_DIR/__manifest__.py" "$TMP_DIR/"
cp "$SRC_DIR/__init__.py" "$TMP_DIR/"
cp "$SRC_DIR/models/__init__.py" "$TMP_DIR/models/"
cp "$SRC_DIR/models/product_template.py" "$TMP_DIR/models/"
cp "$SRC_DIR/views/product_template_views.xml" "$TMP_DIR/views/"

# Verificar o caminho dos addons no contêiner Docker
echo "Verificando o caminho dos addons no contêiner..."
ADDONS_PATH=$(docker exec $ODOO_CONTAINER bash -c "python3 -c 'import os; import odoo; print(os.path.dirname(odoo.__file__) + \"/addons\")'")
CUSTOM_ADDONS_PATH="/mnt/extra-addons"

echo "Caminho dos addons padrão: $ADDONS_PATH"
echo "Caminho dos addons personalizados: $CUSTOM_ADDONS_PATH"

# Copiar os arquivos para o contêiner
echo "Copiando arquivos para o contêiner..."
docker cp "$TMP_DIR" "$ODOO_CONTAINER:$CUSTOM_ADDONS_PATH/semantic_product_description"

# Definir permissões
echo "Definindo permissões..."
docker exec $ODOO_CONTAINER bash -c "chmod -R 755 $CUSTOM_ADDONS_PATH/semantic_product_description"
docker exec $ODOO_CONTAINER bash -c "chown -R odoo:odoo $CUSTOM_ADDONS_PATH/semantic_product_description"

# Limpar o diretório temporário
echo "Limpando diretório temporário..."
rm -rf "$TMP_DIR"

# Reiniciar o contêiner do Odoo
echo "Reiniciando o contêiner do Odoo..."
docker restart $ODOO_CONTAINER

echo "Aguardando o Odoo reiniciar (30 segundos)..."
sleep 30

echo "=== Instalação concluída ==="
echo "Agora você pode atualizar a lista de módulos no Odoo e instalar 'Descrições Inteligentes de Produtos'"
echo ""
echo "=== INSTRUÇÕES ADICIONAIS ==="
echo "1. Para atualizar a lista de módulos no Odoo:"
echo "   - Acesse Configurações > Aplicativos > Atualizar Lista de Aplicativos"
echo "   - Busque por 'Descrições Inteligentes' e instale o módulo"
echo ""
echo "2. Se encontrar erros durante a instalação:"
echo "   - Verifique os logs do Odoo: docker logs $ODOO_CONTAINER"
