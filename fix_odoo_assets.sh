#!/bin/bash

# Script para corrigir problemas de assets no Odoo

echo "=== Corrigindo problemas de assets no Odoo ==="

# Verificar contêineres Docker
echo "Verificando contêineres Docker..."
CONTAINERS=$(docker ps --format "{{.ID}} {{.Names}}" | grep -i odoo)

if [ -z "$CONTAINERS" ]; then
    echo "Erro: Não foi possível encontrar contêineres do Odoo."
    echo "Verifique se o Odoo está em execução com 'docker ps'."
    exit 1
fi

echo "Contêineres do Odoo encontrados:"
echo "$CONTAINERS"

# Perguntar ao usuário qual contêiner usar
echo -e "\nDigite o ID do contêiner que deseja usar:"
read CONTAINER_ID

if [ -z "$CONTAINER_ID" ]; then
    echo "Nenhum ID de contêiner fornecido. Saindo."
    exit 1
fi

# Verificar se o contêiner existe
if ! docker ps | grep -q "$CONTAINER_ID"; then
    echo "Erro: Contêiner $CONTAINER_ID não encontrado ou não está em execução."
    exit 1
fi

echo "Usando contêiner: $CONTAINER_ID"

# Limpar o cache de assets
echo "Limpando cache de assets..."
docker exec $CONTAINER_ID bash -c "find /var/lib/odoo -name '*web_editor*' -type f -delete || echo 'Comando falhou, tentando outro método...'"
docker exec $CONTAINER_ID bash -c "find /var/lib/odoo -name '*assets_*' -type f -delete || echo 'Comando falhou, tentando outro método...'"

# Tentar outros caminhos comuns
echo "Tentando caminhos alternativos..."
docker exec $CONTAINER_ID bash -c "rm -rf /var/lib/odoo/.local/share/Odoo/filestore/*/attachment/*/web_editor_assets* || echo 'Caminho não encontrado'"
docker exec $CONTAINER_ID bash -c "rm -rf /var/lib/odoo/.local/share/Odoo/filestore/*/attachment/*/web_assets* || echo 'Caminho não encontrado'"

# Reiniciar o contêiner do Odoo
echo "Reiniciando o contêiner do Odoo: $CONTAINER_ID"
docker restart $CONTAINER_ID

echo "Aguardando o Odoo reiniciar (30 segundos)..."
sleep 30

echo "=== Processo concluído ==="
echo "Tente acessar o Odoo novamente e verificar se o problema foi resolvido."
echo "Se o problema persistir, pode ser necessário atualizar os módulos manualmente."
