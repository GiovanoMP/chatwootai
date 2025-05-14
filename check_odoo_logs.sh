#!/bin/bash

# Script para verificar os logs do Odoo no Docker

echo "=== Verificando logs do Odoo no Docker ==="

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

# Perguntar quantas linhas de log mostrar
echo -e "\nQuantas linhas de log deseja ver? (padrão: 100)"
read LINES

if [ -z "$LINES" ]; then
    LINES=100
fi

# Verificar os logs do Odoo
echo "Mostrando as últimas $LINES linhas do log do Odoo:"
docker exec $CONTAINER_ID bash -c "tail -n $LINES /var/log/odoo/odoo-server.log || tail -n $LINES /var/log/odoo.log || echo 'Arquivo de log não encontrado'"

echo -e "\n=== Verificação concluída ==="
echo "Para ver mais logs, execute este script novamente com um número maior de linhas."
