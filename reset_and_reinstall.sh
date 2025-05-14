#!/bin/bash
# Script para remover completamente o módulo business_rules2 e reinstalá-lo

# Cores para saída
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Iniciando processo de reset completo do módulo business_rules2...${NC}"

# Verificar se o Docker está rodando
if ! docker ps > /dev/null 2>&1; then
    echo -e "${RED}Docker não está rodando. Por favor, inicie o Docker e tente novamente.${NC}"
    exit 1
fi

# Verificar se o contêiner do Odoo está rodando
if ! docker ps | grep -q "odoo14-odoo-1"; then
    echo -e "${RED}Contêiner do Odoo não está rodando. Por favor, inicie o contêiner e tente novamente.${NC}"
    exit 1
fi

# Verificar se o contêiner do PostgreSQL está rodando
if ! docker ps | grep -q "odoo14-db-1"; then
    echo -e "${RED}Contêiner do PostgreSQL não está rodando. Por favor, inicie o contêiner e tente novamente.${NC}"
    exit 1
fi

# Perguntar ao usuário qual banco de dados usar
read -p "Digite o nome do banco de dados (ex: account_1): " DB_NAME

# Verificar se o banco de dados existe
if ! docker exec odoo14-db-1 psql -U odoo -lqt | cut -d \| -f 1 | grep -qw $DB_NAME; then
    echo -e "${RED}Banco de dados $DB_NAME não existe. Por favor, verifique o nome e tente novamente.${NC}"
    exit 1
fi

echo -e "${YELLOW}Fazendo backup do banco de dados $DB_NAME...${NC}"
BACKUP_FILE="backup_${DB_NAME}_$(date +%Y%m%d_%H%M%S).sql"
docker exec odoo14-db-1 pg_dump -U odoo -d $DB_NAME > $BACKUP_FILE

if [ $? -ne 0 ]; then
    echo -e "${RED}Falha ao fazer backup do banco de dados. Abortando.${NC}"
    exit 1
fi

echo -e "${GREEN}Backup criado com sucesso: $BACKUP_FILE${NC}"

echo -e "${YELLOW}Executando script SQL para remover completamente o módulo...${NC}"
cat reset_module.sql | docker exec -i odoo14-db-1 psql -U odoo -d $DB_NAME

if [ $? -ne 0 ]; then
    echo -e "${RED}Falha ao executar o script SQL. Verifique os erros acima.${NC}"
    echo -e "${YELLOW}Você pode restaurar o backup com o comando:${NC}"
    echo -e "cat $BACKUP_FILE | docker exec -i odoo14-db-1 psql -U odoo -d $DB_NAME"
    exit 1
fi

echo -e "${GREEN}Script SQL executado com sucesso.${NC}"

echo -e "${YELLOW}Reiniciando o contêiner do Odoo...${NC}"
docker restart odoo14-odoo-1

if [ $? -ne 0 ]; then
    echo -e "${RED}Falha ao reiniciar o contêiner do Odoo.${NC}"
    exit 1
fi

echo -e "${GREEN}Contêiner do Odoo reiniciado com sucesso.${NC}"
echo -e "${YELLOW}Aguardando o Odoo iniciar (30 segundos)...${NC}"
sleep 30

echo -e "${GREEN}Processo de reset concluído.${NC}"
echo -e "${BLUE}=== Próximos Passos ===${NC}"
echo -e "${YELLOW}1. Execute o script install_business_rules2.sh para instalar o módulo corrigido${NC}"
echo -e "${YELLOW}2. Acesse o Odoo e atualize a lista de aplicativos${NC}"
echo -e "${YELLOW}3. Instale o módulo 'Regras de Negócio'${NC}"
echo -e "${YELLOW}4. Configure as regras de negócio${NC}"
echo -e "${YELLOW}5. Configure o ID da Conta nas configurações (será usado como identificador no Qdrant)${NC}"
echo -e "${YELLOW}6. Sincronize com o sistema de IA usando o botão verde 'Sincronizar com Sistema de IA'${NC}"

echo -e "${YELLOW}Se ainda houver problemas, você pode restaurar o backup com o comando:${NC}"
echo -e "cat $BACKUP_FILE | docker exec -i odoo14-db-1 psql -U odoo -d $DB_NAME"

exit 0
