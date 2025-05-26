#!/bin/bash

# Verifica se o nome do módulo foi fornecido
if [ -z "$1" ]; then
    echo "Uso: $0 <nome_do_modulo>"
    echo "Exemplo: $0 company_services"
    exit 1
fi

MODULE_NAME=$1
SOURCE_DIR="/home/giovano/Projetos/ai_stack/custom_addons/$MODULE_NAME"
TARGET_DIR="/home/giovano/Projetos/odoo16/custom-addons/$MODULE_NAME"

# Verifica se o módulo existe no diretório de origem
if [ ! -d "$SOURCE_DIR" ]; then
    echo "Erro: O módulo $MODULE_NAME não existe em $SOURCE_DIR"
    exit 1
fi

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

echo "Transferência concluída com sucesso!"
echo "Não esqueça de reiniciar o servidor Odoo para aplicar as alterações."
echo "Comando sugerido: docker-compose restart odoo (no diretório do docker-compose do Odoo)"

# Verifica se o usuário quer reiniciar o Odoo
read -p "Deseja reiniciar o servidor Odoo agora? (s/n): " RESTART
if [ "$RESTART" = "s" ] || [ "$RESTART" = "S" ]; then
    echo "Tentando reiniciar o servidor Odoo..."
    # Tenta encontrar o diretório do docker-compose
    if [ -f "/home/giovano/Projetos/odoo16/docker-compose.yml" ]; then
        cd /home/giovano/Projetos/odoo16
        docker-compose restart odoo
    else
        echo "Não foi possível encontrar o arquivo docker-compose.yml."
        echo "Por favor, reinicie o servidor Odoo manualmente."
    fi
fi

exit 0
