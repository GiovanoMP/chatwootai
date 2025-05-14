#!/bin/bash

# Script para verificar os contêineres Docker em execução

echo "=== Verificando contêineres Docker em execução ==="

# Listar todos os contêineres em execução
echo "Todos os contêineres em execução:"
docker ps

# Tentar identificar o contêiner do Odoo
echo -e "\nTentando identificar o contêiner do Odoo:"
docker ps | grep -i odoo

echo -e "\nPara limpar o cache do Odoo, execute:"
echo "./clear_odoo_cache.sh"

echo -e "\nPara verificar os logs do Odoo, execute:"
echo "docker logs CONTAINER_ID"
echo "Substitua CONTAINER_ID pelo ID do contêiner do Odoo."
