#!/bin/bash

MODULE_NAME="product_ai_mass_management"
SOURCE_DIR="/home/giovano/Projetos/ai_stack/custom_addons/$MODULE_NAME"
DOCKER_CONTAINER="odoo16-odoo-1"
DOCKER_TARGET_DIR="/mnt/extra-addons/$MODULE_NAME"
DATABASE_NAME="odoo16"

echo "Transferindo módulo $MODULE_NAME para o contêiner Docker $DOCKER_CONTAINER..."

# Verifica se o contêiner está em execução
if ! docker ps | grep -q $DOCKER_CONTAINER; then
    echo "ERRO: O contêiner $DOCKER_CONTAINER não está em execução."
    exit 1
fi

# Cria um diretório temporário local
TEMP_DIR=$(mktemp -d)
echo "Criando diretório temporário local: $TEMP_DIR"

# Copia os arquivos do módulo para o diretório temporário
cp -r $SOURCE_DIR/* $TEMP_DIR/

# Cria um arquivo tar do módulo
TAR_FILE="/tmp/${MODULE_NAME}.tar"
echo "Criando arquivo tar do módulo: $TAR_FILE"
tar -cf $TAR_FILE -C $TEMP_DIR .

# Copia o arquivo tar para o contêiner
echo "Copiando arquivo tar para o contêiner..."
docker cp $TAR_FILE $DOCKER_CONTAINER:/tmp/

# Executa comandos dentro do contêiner como root para extrair o arquivo tar
echo "Extraindo arquivo tar no contêiner..."
docker exec $DOCKER_CONTAINER bash -c "mkdir -p $DOCKER_TARGET_DIR && rm -rf $DOCKER_TARGET_DIR/* && tar -xf /tmp/${MODULE_NAME}.tar -C $DOCKER_TARGET_DIR && chown -R odoo:odoo $DOCKER_TARGET_DIR && rm /tmp/${MODULE_NAME}.tar"

# Atualiza o módulo usando o Odoo shell
echo "Atualizando o módulo no Odoo..."
docker exec $DOCKER_CONTAINER bash -c "echo \"env['ir.module.module'].search([('name', '=', '$MODULE_NAME')]).button_immediate_upgrade()\" | odoo shell -d $DATABASE_NAME"

# Limpa os arquivos temporários
rm -rf $TEMP_DIR $TAR_FILE

echo "Transferência e atualização do módulo $MODULE_NAME concluídas com sucesso!"
echo "O módulo foi atualizado no Odoo. Você pode acessar o sistema normalmente agora."

exit 0
