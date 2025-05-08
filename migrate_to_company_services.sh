#!/bin/bash

# Script para migrar do módulo business_rules para o novo módulo company_services
# Este script deve ser executado na raiz do projeto Odoo

# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Iniciando migração do módulo business_rules para company_services...${NC}"

# Verificar se o diretório addons existe
if [ ! -d "addons" ]; then
    echo -e "${RED}Diretório 'addons' não encontrado. Execute este script na raiz do projeto Odoo.${NC}"
    exit 1
fi

# Verificar se o módulo business_rules existe
if [ ! -d "addons/business_rules" ]; then
    echo -e "${RED}Módulo business_rules não encontrado em addons/business_rules.${NC}"
    exit 1
fi

# Verificar se o módulo company_services já existe
if [ ! -d "addons/company_services" ]; then
    echo -e "${RED}Módulo company_services não encontrado em addons/company_services.${NC}"
    echo -e "${YELLOW}Certifique-se de criar o módulo company_services antes de executar este script.${NC}"
    exit 1
fi

# Verificar se o PostgreSQL está instalado
if ! command -v psql &> /dev/null; then
    echo -e "${RED}PostgreSQL não está instalado. Instale-o antes de continuar.${NC}"
    exit 1
fi

# Verificar se o MongoDB está instalado (opcional para migração futura)
if ! command -v mongod &> /dev/null; then
    echo -e "${YELLOW}MongoDB não está instalado. Isso é necessário apenas para a migração futura para MongoDB.${NC}"
fi

echo -e "${GREEN}Todas as verificações iniciais passaram.${NC}"

# Backup do módulo business_rules
echo -e "${YELLOW}Criando backup do módulo business_rules...${NC}"
BACKUP_DIR="backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR
cp -r addons/business_rules $BACKUP_DIR/
echo -e "${GREEN}Backup criado em $BACKUP_DIR/business_rules${NC}"

# Migrar dados do PostgreSQL (se necessário)
echo -e "${YELLOW}Deseja migrar dados do PostgreSQL? (s/n)${NC}"
read migrate_postgres

if [ "$migrate_postgres" = "s" ]; then
    echo -e "${YELLOW}Informe os dados de conexão ao PostgreSQL:${NC}"
    echo -e "${YELLOW}Host (padrão: localhost):${NC}"
    read pg_host
    pg_host=${pg_host:-localhost}
    
    echo -e "${YELLOW}Porta (padrão: 5432):${NC}"
    read pg_port
    pg_port=${pg_port:-5432}
    
    echo -e "${YELLOW}Usuário (padrão: postgres):${NC}"
    read pg_user
    pg_user=${pg_user:-postgres}
    
    echo -e "${YELLOW}Senha:${NC}"
    read -s pg_password
    
    echo -e "${YELLOW}Banco de dados:${NC}"
    read pg_database
    
    # Criar script Python para migração de dados
    echo -e "${YELLOW}Criando script de migração de dados...${NC}"
    cat > migrate_data.py << EOF
#!/usr/bin/env python3
import psycopg2
import json
import yaml
import datetime
import sys

# Função para converter datetime para string
def json_serial(obj):
    if isinstance(obj, datetime.datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

try:
    # Conectar ao PostgreSQL
    conn = psycopg2.connect(
        host="$pg_host",
        port=$pg_port,
        user="$pg_user",
        password="$pg_password",
        dbname="$pg_database"
    )
    
    cursor = conn.cursor()
    
    # Buscar dados do módulo business_rules
    print("Buscando dados do módulo business_rules...")
    cursor.execute("""
        SELECT id, name, description, sync_status, last_sync, error_message
        FROM business_rule
        ORDER BY id
    """)
    
    business_rules = cursor.fetchall()
    
    if not business_rules:
        print("Nenhum dado encontrado no módulo business_rules.")
        sys.exit(0)
    
    print(f"Encontrados {len(business_rules)} registros.")
    
    # Criar arquivo SQL para inserir dados no novo módulo
    with open("migrate_data.sql", "w") as sql_file:
        sql_file.write("-- Script de migração de dados de business_rules para company_services\n\n")
        
        for rule in business_rules:
            rule_id, name, description, sync_status, last_sync, error_message = rule
            
            # Buscar dados adicionais
            cursor.execute("""
                SELECT street, street2, city, state, zip, country,
                       enable_sales, enable_scheduling, enable_delivery, enable_support,
                       greeting_message, communication_style, emoji_usage,
                       start_time, end_time, has_lunch_break, lunch_break_start, lunch_break_end,
                       monday, tuesday, wednesday, thursday, friday, saturday, sunday,
                       saturday_start_time, saturday_end_time,
                       website_url, website_mention, facebook_url, facebook_mention,
                       instagram_url, instagram_mention, share_address, inform_promotions
                FROM business_rule
                WHERE id = %s
            """, (rule_id,))
            
            details = cursor.fetchone()
            
            if not details:
                continue
                
            # Criar SQL para inserir no novo módulo
            sql = f"""
INSERT INTO company_service (
    name, description, sync_status, last_sync, error_message,
    street, street2, city, state, zip, country,
    enable_sales, enable_scheduling, enable_delivery, enable_support,
    greeting_message, communication_style, emoji_usage,
    start_time, end_time, has_lunch_break, lunch_break_start, lunch_break_end,
    monday, tuesday, wednesday, thursday, friday, saturday, sunday,
    saturday_start_time, saturday_end_time,
    website_url, website_mention, facebook_url, facebook_mention,
    instagram_url, instagram_mention, share_address, inform_promotions,
    create_uid, create_date, write_uid, write_date
) VALUES (
    '{name}', '{description or ""}', '{sync_status or "not_synced"}', 
    {f"'{last_sync}'" if last_sync else 'NULL'}, 
    '{error_message or ""}',
    '{details[0] or ""}', '{details[1] or ""}', '{details[2] or ""}', 
    '{details[3] or ""}', '{details[4] or ""}', '{details[5] or ""}',
    {details[6] or 'FALSE'}, {details[7] or 'FALSE'}, {details[8] or 'FALSE'}, {details[9] or 'FALSE'},
    '{details[10] or ""}', '{details[11] or "friendly"}', '{details[12] or "none"}',
    '{details[13] or "09:00"}', '{details[14] or "18:00"}', {details[15] or 'FALSE'},
    '{details[16] or "12:00"}', '{details[17] or "13:00"}',
    {details[18] or 'TRUE'}, {details[19] or 'TRUE'}, {details[20] or 'TRUE'},
    {details[21] or 'TRUE'}, {details[22] or 'TRUE'}, {details[23] or 'FALSE'}, {details[24] or 'FALSE'},
    '{details[25] or "08:00"}', '{details[26] or "12:00"}',
    '{details[27] or ""}', {details[28] or 'FALSE'}, '{details[29] or ""}', {details[30] or 'FALSE'},
    '{details[31] or ""}', {details[32] or 'FALSE'}, {details[33] or 'FALSE'}, {details[34] or 'FALSE'},
    1, NOW(), 1, NOW()
);
"""
            sql_file.write(sql)
            
    print("Script de migração de dados criado: migrate_data.sql")
    
    # Fechar conexão
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"Erro durante a migração: {str(e)}")
    sys.exit(1)
EOF
    
    # Executar script de migração
    echo -e "${YELLOW}Executando script de migração de dados...${NC}"
    python3 migrate_data.py
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Script de migração executado com sucesso.${NC}"
        echo -e "${YELLOW}O arquivo migrate_data.sql foi criado. Você pode executá-lo manualmente no banco de dados Odoo.${NC}"
    else
        echo -e "${RED}Erro ao executar script de migração.${NC}"
    fi
fi

# Verificar se deseja migrar para MongoDB
echo -e "${YELLOW}Deseja preparar a migração para MongoDB? (s/n)${NC}"
read migrate_mongodb

if [ "$migrate_mongodb" = "s" ]; then
    echo -e "${YELLOW}Criando script de migração para MongoDB...${NC}"
    
    cat > migrate_to_mongodb.py << EOF
#!/usr/bin/env python3
import psycopg2
import json
import yaml
import datetime
import sys
from pymongo import MongoClient

# Função para converter datetime para string
def json_serial(obj):
    if isinstance(obj, datetime.datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

try:
    # Conectar ao PostgreSQL
    print("Conectando ao PostgreSQL...")
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        user="postgres",
        password="sua_senha",
        dbname="seu_banco"
    )
    
    cursor = conn.cursor()
    
    # Conectar ao MongoDB
    print("Conectando ao MongoDB...")
    mongo_client = MongoClient('mongodb://localhost:27017/')
    mongo_db = mongo_client['config_service']
    
    # Limpar coleções existentes
    mongo_db.tenants.drop()
    mongo_db.configurations.drop()
    
    # Buscar dados do módulo company_services
    print("Buscando dados do módulo company_services...")
    cursor.execute("""
        SELECT id, name, description, sync_status, last_sync
        FROM company_service
        ORDER BY id
    """)
    
    company_services = cursor.fetchall()
    
    if not company_services:
        print("Nenhum dado encontrado no módulo company_services.")
        sys.exit(0)
    
    print(f"Encontrados {len(company_services)} registros.")
    
    # Migrar dados para MongoDB
    for service in company_services:
        service_id, name, description, sync_status, last_sync = service
        
        # Buscar configurações do tenant
        cursor.execute("""
            SELECT account_id, security_token
            FROM ir_config_parameter
            WHERE key IN ('company_services.account_id', 'company_services.security_token')
        """)
        
        config_params = cursor.fetchall()
        account_id = None
        security_token = None
        
        for param in config_params:
            if param[0] == 'company_services.account_id':
                account_id = param[1]
            elif param[0] == 'company_services.security_token':
                security_token = param[1]
        
        if not account_id:
            account_id = f"account_{service_id}"
        
        # Criar tenant no MongoDB
        tenant_doc = {
            "_id": account_id,
            "name": name,
            "created_at": datetime.datetime.now(),
            "updated_at": datetime.datetime.now(),
            "enabled_modules": ["company_info", "service_settings", "enabled_services"]
        }
        
        mongo_db.tenants.insert_one(tenant_doc)
        print(f"Tenant criado: {account_id}")
        
        # Buscar dados completos do serviço
        cursor.execute("""
            SELECT * FROM company_service WHERE id = %s
        """, (service_id,))
        
        service_data = cursor.fetchone()
        column_names = [desc[0] for desc in cursor.description]
        service_dict = dict(zip(column_names, service_data))
        
        # Preparar documento de configuração
        config_doc = {
            "tenant_id": account_id,
            "version": 1,
            "created_at": datetime.datetime.now(),
            "updated_at": datetime.datetime.now(),
            "config_data": {
                "modules": {
                    "company_info": {
                        "name": service_dict.get('name', ''),
                        "description": service_dict.get('description', ''),
                        "address": {
                            "street": service_dict.get('street', ''),
                            "street2": service_dict.get('street2', ''),
                            "city": service_dict.get('city', ''),
                            "state": service_dict.get('state', ''),
                            "zip": service_dict.get('zip', ''),
                            "country": service_dict.get('country', ''),
                            "share_with_customers": service_dict.get('share_address', False)
                        }
                    },
                    "service_settings": {
                        "business_hours": {
                            "days": [],
                            "start_time": service_dict.get('start_time', '09:00'),
                            "end_time": service_dict.get('end_time', '18:00'),
                            "has_lunch_break": service_dict.get('has_lunch_break', False),
                            "lunch_break_start": service_dict.get('lunch_break_start', '12:00'),
                            "lunch_break_end": service_dict.get('lunch_break_end', '13:00'),
                            "saturday_start_time": service_dict.get('saturday_start_time', '08:00'),
                            "saturday_end_time": service_dict.get('saturday_end_time', '12:00')
                        },
                        "customer_service": {
                            "greeting_message": service_dict.get('greeting_message', ''),
                            "communication_style": service_dict.get('communication_style', 'friendly'),
                            "emoji_usage": service_dict.get('emoji_usage', 'none')
                        },
                        "online_channels": {
                            "website": {
                                "url": service_dict.get('website_url', ''),
                                "mention_at_end": service_dict.get('website_mention', False)
                            },
                            "facebook": {
                                "url": service_dict.get('facebook_url', ''),
                                "mention_at_end": service_dict.get('facebook_mention', False)
                            },
                            "instagram": {
                                "url": service_dict.get('instagram_url', ''),
                                "mention_at_end": service_dict.get('instagram_mention', False)
                            }
                        }
                    },
                    "enabled_services": {
                        "collections": [],
                        "services": {
                            "sales": {
                                "enabled": service_dict.get('enable_sales', False),
                                "promotions": {
                                    "inform_at_start": service_dict.get('inform_promotions', False)
                                }
                            },
                            "scheduling": {
                                "enabled": service_dict.get('enable_scheduling', False)
                            },
                            "delivery": {
                                "enabled": service_dict.get('enable_delivery', False)
                            },
                            "support": {
                                "enabled": service_dict.get('enable_support', False)
                            }
                        }
                    }
                }
            }
        }
        
        # Adicionar dias de funcionamento
        days = []
        if service_dict.get('monday', True):
            days.append(0)
        if service_dict.get('tuesday', True):
            days.append(1)
        if service_dict.get('wednesday', True):
            days.append(2)
        if service_dict.get('thursday', True):
            days.append(3)
        if service_dict.get('friday', True):
            days.append(4)
        if service_dict.get('saturday', False):
            days.append(5)
        if service_dict.get('sunday', False):
            days.append(6)
            
        config_doc["config_data"]["modules"]["service_settings"]["business_hours"]["days"] = days
        
        # Adicionar coleções habilitadas
        collections = []
        if service_dict.get('enable_sales', False):
            collections.append('products_informations')
        if service_dict.get('enable_scheduling', False):
            collections.append('scheduling_rules')
        if service_dict.get('enable_delivery', False):
            collections.append('delivery_rules')
        if service_dict.get('enable_support', False):
            collections.append('support_documents')
            
        config_doc["config_data"]["modules"]["enabled_services"]["collections"] = collections
        
        # Inserir configuração no MongoDB
        mongo_db.configurations.insert_one(config_doc)
        print(f"Configuração criada para tenant: {account_id}")
    
    print("Migração para MongoDB concluída com sucesso!")
    
    # Fechar conexões
    cursor.close()
    conn.close()
    mongo_client.close()
    
except Exception as e:
    print(f"Erro durante a migração para MongoDB: {str(e)}")
    sys.exit(1)
EOF
    
    echo -e "${GREEN}Script de migração para MongoDB criado: migrate_to_mongodb.py${NC}"
    echo -e "${YELLOW}Edite o script para configurar as credenciais corretas antes de executá-lo.${NC}"
fi

echo -e "${GREEN}Migração concluída!${NC}"
echo -e "${YELLOW}Próximos passos:${NC}"
echo -e "1. Instale o módulo company_services no Odoo"
echo -e "2. Execute o script migrate_data.sql no banco de dados Odoo (se aplicável)"
echo -e "3. Configure as credenciais no módulo company_services"
echo -e "4. Teste a sincronização com o config-service"
echo -e "5. Execute o script migrate_to_mongodb.py para migrar para MongoDB (se aplicável)"

exit 0
