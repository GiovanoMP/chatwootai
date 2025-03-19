#!/bin/bash
# Script para monitorar vendas e atividades no banco de dados PostgreSQL
# Autor: Cascade AI
# Data: 2025-03-17

# Definir cores para melhor legibilidade
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Monitoramento de Vendas e Atividades ===${NC}"

# Obter variáveis de ambiente
if [ -f .env ]; then
  source .env
else
  # Valores padrão se .env não existir
  POSTGRES_USER="postgres"
  POSTGRES_DB="postgres"
  POSTGRES_PASSWORD="postgres"
fi

# Função para executar consulta SQL
run_query() {
  docker exec -it chatwootai_postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "$1"
}

# Menu de opções
show_menu() {
  echo -e "${YELLOW}Selecione uma opção:${NC}"
  echo -e "${BLUE}1.${NC} Listar últimas 10 vendas"
  echo -e "${BLUE}2.${NC} Listar vendas de hoje"
  echo -e "${BLUE}3.${NC} Listar clientes recentes"
  echo -e "${BLUE}4.${NC} Listar produtos mais vendidos"
  echo -e "${BLUE}5.${NC} Resumo de atividades"
  echo -e "${BLUE}6.${NC} Consulta personalizada"
  echo -e "${BLUE}q.${NC} Sair"
  echo ""
  read -p "> " option
  
  case $option in
    1)
      echo -e "${GREEN}Últimas 10 vendas:${NC}"
      run_query "SELECT o.id, o.customer_id, c.name as customer_name, o.total_amount, o.status, o.created_at FROM orders o JOIN customers c ON o.customer_id = c.id ORDER BY o.created_at DESC LIMIT 10;"
      ;;
    2)
      echo -e "${GREEN}Vendas de hoje:${NC}"
      run_query "SELECT o.id, o.customer_id, c.name as customer_name, o.total_amount, o.status, o.created_at FROM orders o JOIN customers c ON o.customer_id = c.id WHERE o.created_at::date = CURRENT_DATE ORDER BY o.created_at DESC;"
      ;;
    3)
      echo -e "${GREEN}Clientes recentes:${NC}"
      run_query "SELECT id, name, email, phone, created_at FROM customers ORDER BY created_at DESC LIMIT 10;"
      ;;
    4)
      echo -e "${GREEN}Produtos mais vendidos:${NC}"
      run_query "SELECT p.id, p.name, COUNT(oi.id) as times_sold, SUM(oi.quantity) as total_quantity FROM products p JOIN order_items oi ON p.id = oi.product_id GROUP BY p.id, p.name ORDER BY times_sold DESC LIMIT 10;"
      ;;
    5)
      echo -e "${GREEN}Resumo de atividades:${NC}"
      run_query "SELECT 'Vendas hoje' as metric, COUNT(*) as value FROM orders WHERE created_at::date = CURRENT_DATE 
                UNION ALL 
                SELECT 'Clientes novos hoje', COUNT(*) FROM customers WHERE created_at::date = CURRENT_DATE 
                UNION ALL 
                SELECT 'Total de produtos', COUNT(*) FROM products 
                UNION ALL 
                SELECT 'Total de pedidos', COUNT(*) FROM orders;"
      ;;
    6)
      echo -e "${YELLOW}Digite sua consulta SQL:${NC}"
      read -p "SQL> " custom_query
      echo -e "${GREEN}Executando consulta personalizada:${NC}"
      run_query "$custom_query"
      ;;
    q)
      echo "Saindo..."
      exit 0
      ;;
    *)
      echo -e "${RED}Opção inválida!${NC}"
      ;;
  esac
  
  echo ""
  echo -e "${YELLOW}Pressione ENTER para continuar...${NC}"
  read
  clear
  show_menu
}

# Verificar se o container PostgreSQL está rodando
if ! docker ps | grep -q chatwootai_postgres; then
  echo -e "${RED}Erro: O container chatwootai_postgres não está rodando!${NC}"
  echo -e "${YELLOW}Inicie os serviços Docker primeiro:${NC}"
  echo -e "docker-compose up -d"
  exit 1
fi

# Iniciar o menu
clear
show_menu
