#!/bin/bash

# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Teste de Integração: Company Services → MongoDB → MCP-MongoDB ===${NC}\n"

# Etapa 1: Verificar se todos os serviços necessários estão em execução
echo -e "${YELLOW}Verificando serviços necessários...${NC}"

# Verificar MongoDB
if docker ps | grep -q "chatwoot-mongodb"; then
    echo -e "${GREEN}✅ MongoDB está em execução${NC}"
else
    echo -e "${RED}❌ MongoDB não está em execução. Por favor, inicie o MongoDB.${NC}"
    exit 1
fi

# Verificar Webhook
if docker ps | grep -q "chatwoot-webhook-mongo"; then
    echo -e "${GREEN}✅ Webhook está em execução${NC}"
else
    echo -e "${RED}❌ Webhook não está em execução. Por favor, inicie o webhook.${NC}"
    exit 1
fi

# Verificar MCP-MongoDB
if docker ps | grep -q "chatwoot-mcp-mongodb"; then
    echo -e "${GREEN}✅ MCP-MongoDB está em execução${NC}"
else
    echo -e "${RED}❌ MCP-MongoDB não está em execução. Por favor, inicie o MCP-MongoDB.${NC}"
    exit 1
fi

echo -e "\n${YELLOW}Todos os serviços necessários estão em execução.${NC}\n"

# Etapa 2: Testar o webhook enviando dados de exemplo
echo -e "${YELLOW}Testando o webhook com dados de exemplo...${NC}"

# Criar um arquivo temporário para o YAML
TEMP_YAML=$(mktemp)

# Escrever o YAML no arquivo temporário
cat > "$TEMP_YAML" << 'EOF'
modules:
  company_info:
    name: "Empresa Exemplo"
    description: "Uma empresa de exemplo para testes"
    contact:
      phone: "+55 11 1234-5678"
      email: "contato@exemplo.com"
      website: "https://www.exemplo.com"
    address:
      street: "Rua Exemplo, 123"
      city: "São Paulo"
      state: "SP"
      zip: "01234-567"
      country: "Brasil"
  service_settings:
    business_hours:
      monday: true
      monday_start: "08:00"
      monday_end: "18:00"
      tuesday: true
      tuesday_start: "08:00"
      tuesday_end: "18:00"
      wednesday: true
      wednesday_start: "08:00"
      wednesday_end: "18:00"
      thursday: true
      thursday_start: "08:00"
      thursday_end: "18:00"
      friday: true
      friday_start: "08:00"
      friday_end: "18:00"
      saturday: false
      sunday: false
    customer_service:
      greeting_message: "Olá! Como posso ajudar?"
      communication:
        tone: "friendly"
        voice: "professional"
        formality: "semi_formal"
        emoji_usage: "moderate"
      farewell:
        message: "Obrigado por entrar em contato!"
        enabled: true
      rating_request:
        message: "Como você avaliaria este atendimento?"
        enabled: true
  enabled_services:
    services:
      sales:
        enabled: true
        promotions:
          inform_at_start: true
      scheduling:
        enabled: true
      delivery:
        enabled: true
      support:
        enabled: true
enabled_collections:
  - "sales"
  - "scheduling"
  - "delivery"
  - "support"
mcp:
  type: "odoo"
  config:
    url: "http://localhost:8069"
    db: "account_1"
    username: "admin"
    credential_ref: "account_1_db_pwd"
EOF

# Escapar o conteúdo YAML para JSON
ESCAPED_YAML=$(cat "$TEMP_YAML" | sed 's/"/\\"/g' | sed ':a;N;$!ba;s/\n/\\n/g')

# Enviar dados para o webhook
echo -e "${BLUE}Enviando dados para o webhook...${NC}"
RESPONSE=$(curl -s -X POST \
  "http://localhost:8003/company-services/account_1/metadata" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: development-api-key" \
  -d "{\"yaml_content\": \"$ESCAPED_YAML\"}")

# Remover o arquivo temporário
rm "$TEMP_YAML"

if echo "$RESPONSE" | grep -q "success"; then
    echo -e "${GREEN}✅ Dados enviados com sucesso para o webhook${NC}"
else
    echo -e "${RED}❌ Falha ao enviar dados para o webhook: $RESPONSE${NC}"
    exit 1
fi

# Etapa 3: Verificar se os dados foram armazenados no MongoDB
echo -e "\n${YELLOW}Verificando se os dados foram armazenados no MongoDB...${NC}"
sleep 2  # Pequena pausa para garantir que os dados foram processados

MONGO_DATA=$(docker exec chatwoot-mongodb mongosh --quiet --eval "use config_service; db.company_services.findOne({account_id: 'account_1'})")

if echo "$MONGO_DATA" | grep -q "company_info"; then
    echo -e "${GREEN}✅ Dados encontrados no MongoDB${NC}"
    echo -e "${BLUE}Dados armazenados:${NC}"
    echo "$MONGO_DATA" | grep -A 5 "company_info"
    echo "..."
else
    echo -e "${RED}❌ Dados não encontrados no MongoDB${NC}"
    exit 1
fi

# Etapa 4: Testar o acesso aos dados através do MCP-MongoDB
echo -e "\n${YELLOW}Testando o acesso aos dados através do MCP-MongoDB...${NC}"
echo -e "${BLUE}Nota: Esta etapa requer um cliente MCP para testar completamente.${NC}"
echo -e "${BLUE}Por enquanto, vamos apenas verificar se o MCP-MongoDB está respondendo.${NC}"

MCP_RESPONSE=$(curl -s http://localhost:8001/health)
if echo "$MCP_RESPONSE" | grep -q "ok"; then
    echo -e "${GREEN}✅ MCP-MongoDB está respondendo corretamente${NC}"
else
    echo -e "${RED}❌ MCP-MongoDB não está respondendo corretamente: $MCP_RESPONSE${NC}"
fi

echo -e "\n${GREEN}=== Teste de integração concluído com sucesso! ===${NC}"
echo -e "${BLUE}Próximos passos:${NC}"
echo -e "1. Integrar o MCP-MongoDB com o CrewAI para permitir que os agentes acessem as configurações"
echo -e "2. Implementar a lógica para criar coleções baseadas em serviços ativos"
echo -e "3. Desenvolver uma crew básica para um serviço específico"
