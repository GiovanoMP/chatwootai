#!/bin/bash

MODULE_NAME="semantic_product_description"
SOURCE_DIR="/home/giovano/Projetos/ai_stack/custom_addons/$MODULE_NAME"
TARGET_DIR="/home/giovano/Projetos/odoo16/custom-addons/$MODULE_NAME"

echo "Transferindo módulo $MODULE_NAME..."

# Remove o módulo no diretório de destino se existir
if [ -d "$TARGET_DIR" ]; then
    echo "Removendo módulo existente em $TARGET_DIR..."
    rm -rf "$TARGET_DIR"
fi

# Cria o diretório de destino se não existir
mkdir -p "/home/giovano/Projetos/odoo16/custom-addons"

# Copia o módulo para o diretório de destino
echo "Copiando $MODULE_NAME de $SOURCE_DIR para $TARGET_DIR..."
cp -r "$SOURCE_DIR" "$TARGET_DIR"

echo "Transferência do módulo $MODULE_NAME concluída com sucesso!"
echo "Não esqueça de reiniciar o servidor Odoo para aplicar as alterações."

exit 0
