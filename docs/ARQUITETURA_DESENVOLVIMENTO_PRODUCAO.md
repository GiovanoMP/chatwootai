# Arquitetura de Desenvolvimento e Produção - ChatwootAI

Este documento descreve a arquitetura de desenvolvimento e produção do projeto ChatwootAI, incluindo fluxos de trabalho, configurações e melhores práticas.

## Sumário

1. [Visão Geral da Arquitetura](#visão-geral-da-arquitetura)
2. [Ambiente de Desenvolvimento](#ambiente-de-desenvolvimento)
3. [Ambiente de Produção](#ambiente-de-produção)
4. [Fluxo de Trabalho](#fluxo-de-trabalho)
5. [Monitoramento e Depuração](#monitoramento-e-depuração)
6. [Acesso às Tabelas do PostgreSQL](#acesso-às-tabelas-do-postgresql)
7. [Melhores Práticas](#melhores-práticas)

## Visão Geral da Arquitetura

O ChatwootAI é uma plataforma modular que integra:

1. **Chatwoot**: Hub central de comunicação para múltiplos canais
2. **CrewAI**: Orquestração de agentes de IA especializados
3. **Qdrant**: Banco de dados vetorial para consultas semânticas
4. **Redis**: Sistema de cache em dois níveis
5. **Simulação do Odoo**: API para gerenciar regras de negócio

A arquitetura segue um modelo hierárquico hub-and-spoke com quatro camadas:
- **Camada de Entrada**: Crews para diferentes canais (WhatsApp, Instagram, etc.)
- **Camada de Hub Central**: Chatwoot gerenciando todas as mensagens
- **Camada de Processamento**: Crews especializadas (Vendas, Suporte, Agendamento)
- **Camada de Integração**: Odoo, Qdrant, Redis e outras APIs

## Ambiente de Desenvolvimento

### Configuração Híbrida

Para desenvolvimento, usamos uma configuração híbrida:

1. **Serviços em Docker**:
   - PostgreSQL (`chatwootai_postgres`): Banco de dados para simulação do Odoo
   - Qdrant (`chatwootai_qdrant`): Banco de dados vetorial
   - Redis (`chatwootai_redis`): Serviço de cache
   - API de Simulação do Odoo (`chatwootai_odoo_simulation`): Serviço FastAPI

2. **Componentes Locais**:
   - Agentes CrewAI: Executados localmente para facilitar o desenvolvimento
   - Servidor Webhook: Executado localmente e exposto via ngrok

3. **Serviços Externos**:
   - Chatwoot: Hospedado em VPS externa

### Iniciar o Ambiente de Desenvolvimento

1. **Iniciar os serviços Docker**:
   ```bash
   # No diretório raiz do projeto
   docker-compose up -d
   ```

2. **Iniciar a conexão webhook com o Chatwoot**:
   ```bash
   # No diretório raiz do projeto
   ./scripts/webhook/start_webhook_connection.sh
   ```

3. **Iniciar o ambiente CrewAI**:
   ```bash
   # No diretório raiz do projeto
   python -m src.main
   ```

## Ambiente de Produção

### Configuração com Docker Swarm

Para produção, todos os componentes são executados em Docker Swarm:

1. **Serviços em Docker Swarm**:
   - PostgreSQL: Banco de dados para simulação do Odoo
   - Qdrant: Banco de dados vetorial
   - Redis: Serviço de cache
   - API de Simulação do Odoo: Serviço FastAPI
   - Servidor Webhook: Recebe eventos do Chatwoot
   - Agentes CrewAI: Processam mensagens e geram respostas

2. **Serviços Externos**:
   - Chatwoot: Hospedado em VPS externa

### Implantar em Produção

1. **Implantar o servidor webhook no Docker Swarm**:
   ```bash
   # No diretório raiz do projeto
   ./scripts/webhook/deploy_webhook_swarm.sh
   ```

2. **Verificar o status do servidor webhook**:
   ```bash
   # No diretório raiz do projeto
   ./scripts/webhook/check_webhook_swarm.sh
   ```

3. **Testar o servidor webhook**:
   ```bash
   # No diretório raiz do projeto
   ./scripts/webhook/test_webhook_swarm.sh
   ```

## Fluxo de Trabalho

### Desenvolvimento de Agentes

1. **Desenvolver e testar agentes localmente**:
   - Editar o código dos agentes
   - Executar localmente para testes rápidos
   - Verificar logs e comportamento

2. **Testar integração com Chatwoot**:
   - Iniciar o servidor webhook e ngrok
   - Configurar o webhook no Chatwoot
   - Testar o fluxo completo de mensagens

3. **Monitorar impacto no banco de dados**:
   - Verificar tabelas no PostgreSQL (ver seção [Acesso às Tabelas do PostgreSQL](#acesso-às-tabelas-do-postgresql))
   - Analisar logs e métricas

### Implantação em Produção

1. **Construir imagens Docker**:
   ```bash
   docker build -t chatwootai:latest .
   ```

2. **Implantar no Docker Swarm**:
   ```bash
   docker stack deploy -c docker-stack.yml chatwootai
   ```

3. **Monitorar serviços**:
   ```bash
   docker service ls
   docker service logs chatwootai_webhook_server
   ```

## Monitoramento e Depuração

### Logs

1. **Logs do servidor webhook**:
   ```bash
   # Em desenvolvimento
   tail -f webhook_server.log
   
   # Em produção
   docker service logs chatwootai_webhook_server
   ```

2. **Logs do ngrok**:
   ```bash
   tail -f ngrok.log
   ```

3. **Logs dos agentes CrewAI**:
   ```bash
   # Em desenvolvimento
   tail -f crewai.log
   
   # Em produção
   docker service logs chatwootai_crewai
   ```

### Métricas

O serviço de monitoramento (`chatwootai_monitoring`) coleta métricas dos serviços:

- Acesse o Prometheus em: http://localhost:9090
- Métricas disponíveis:
  - Tempo de resposta dos agentes
  - Número de mensagens processadas
  - Uso de recursos (CPU, memória)

## Acesso às Tabelas do PostgreSQL

### Usando pgAdmin (Interface Gráfica)

1. **Instalar pgAdmin**:
   - Download: https://www.pgadmin.org/download/
   - Ou usar a versão Docker:
     ```bash
     docker run -p 5050:80 -e "PGADMIN_DEFAULT_EMAIL=admin@example.com" -e "PGADMIN_DEFAULT_PASSWORD=admin" dpage/pgadmin4
     ```

2. **Configurar conexão**:
   - Host: localhost
   - Port: 5433 (porta mapeada no docker-compose.yml)
   - Username: postgres (ou o definido em .env)
   - Password: postgres (ou o definido em .env)
   - Database: postgres (ou o definido em .env)

3. **Navegar pelas tabelas**:
   - Expandir: Servers > PostgreSQL > Databases > postgres > Schemas > public > Tables

### Usando CLI do PostgreSQL

1. **Conectar ao banco de dados**:
   ```bash
   docker exec -it chatwootai_postgres psql -U postgres -d postgres
   ```

2. **Listar tabelas**:
   ```sql
   \dt
   ```

3. **Consultar dados**:
   ```sql
   -- Verificar produtos
   SELECT * FROM products LIMIT 10;
   
   -- Verificar pedidos
   SELECT * FROM orders LIMIT 10;
   
   -- Verificar clientes
   SELECT * FROM customers LIMIT 10;
   
   -- Verificar vendas (últimas 10)
   SELECT o.id, o.customer_id, c.name as customer_name, o.total_amount, o.status, o.created_at 
   FROM orders o 
   JOIN customers c ON o.customer_id = c.id 
   ORDER BY o.created_at DESC 
   LIMIT 10;
   ```

### Script para Monitoramento de Vendas

Criamos um script para facilitar o monitoramento de vendas e outras atividades:

```bash
#!/bin/bash
# scripts/monitor_sales.sh

# Definir cores para melhor legibilidade
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Monitoramento de Vendas e Atividades ===${NC}"

# Obter variáveis de ambiente
source .env

# Função para executar consulta SQL
run_query() {
  docker exec -it chatwootai_postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "$1"
}

# Menu de opções
echo -e "${YELLOW}Selecione uma opção:${NC}"
echo "1. Listar últimas 10 vendas"
echo "2. Listar vendas de hoje"
echo "3. Listar clientes recentes"
echo "4. Listar produtos mais vendidos"
echo "5. Resumo de atividades"
echo "q. Sair"

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
    run_query "SELECT 'Vendas hoje' as metric, COUNT(*) as value FROM orders WHERE created_at::date = CURRENT_DATE UNION ALL SELECT 'Clientes novos hoje', COUNT(*) FROM customers WHERE created_at::date = CURRENT_DATE UNION ALL SELECT 'Total de produtos', COUNT(*) FROM products UNION ALL SELECT 'Total de pedidos', COUNT(*) FROM orders;"
    ;;
  q)
    echo "Saindo..."
    exit 0
    ;;
  *)
    echo "Opção inválida!"
    ;;
esac
```

Para usar o script:
```bash
# Tornar o script executável
chmod +x scripts/monitor_sales.sh

# Executar o script
./scripts/monitor_sales.sh
```

## Melhores Práticas

### Desenvolvimento

1. **Controle de Versão**:
   - Use branches para novas funcionalidades
   - Faça commits frequentes e descritivos
   - Mantenha o código principal estável

2. **Testes**:
   - Teste os agentes com diferentes cenários
   - Verifique o comportamento com diferentes tipos de mensagens
   - Monitore o impacto no banco de dados

3. **Documentação**:
   - Documente novas funcionalidades
   - Atualize o README e outros documentos
   - Comente o código complexo

### Implantação

1. **Backup**:
   - Faça backup do banco de dados antes de implantações importantes
   - Use volumes Docker para persistência de dados

2. **Monitoramento**:
   - Configure alertas para erros e falhas
   - Monitore o uso de recursos
   - Verifique logs regularmente

3. **Segurança**:
   - Mantenha as chaves de API seguras
   - Use HTTPS para todas as comunicações
   - Limite o acesso aos serviços

### Escalabilidade

1. **Horizontal**:
   - Use Docker Swarm para escalar serviços
   - Configure réplicas para serviços críticos

2. **Vertical**:
   - Monitore o uso de recursos
   - Aumente recursos para serviços que precisam

3. **Otimização**:
   - Use cache para reduzir consultas ao banco de dados
   - Otimize consultas SQL
   - Implemente rate limiting para APIs externas
